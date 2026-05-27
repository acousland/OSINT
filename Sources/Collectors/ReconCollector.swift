import Foundation

/// Technology profiling + reconnaissance. Passive methods (CT logs, DNS, fingerprinting)
/// run freely; active methods (subdomain brute force, port scan) are only invoked by the
/// Coordinator after explicit user consent.
struct ReconCollector {
    let name = "ReconCollector"
    let store: Store
    let investigationId: Int64
    let http = HTTPClient()
    let doh = DoHClient()

    private let resolveLimiter = ConcurrencyLimiter(limit: 25)
    private let scanLimiter = ConcurrencyLimiter(limit: 200)

    // MARK: Passive — certificate transparency (crt.sh)

    struct CrtEntry: Decodable { let name_value: String?; let common_name: String? }

    func certificateTransparency(host: String, emit: @Sendable (RunEvent) -> Void) async throws {
        let apex = Self.apexDomain(host)
        guard let url = URL(string: "https://crt.sh/?q=%25.\(apex)&output=json") else { return }
        emit(.progress(stage: "Recon", message: "Querying certificate transparency…", done: 0, total: nil))
        let entries: [CrtEntry] = (try? await http.getJSON(url, as: [CrtEntry].self)) ?? []

        var names = Set<String>()
        for e in entries {
            for field in [e.name_value, e.common_name] {
                field?.split(whereSeparator: { $0 == "\n" }).forEach { part in
                    let n = part.trimmingCharacters(in: .whitespaces).lowercased()
                    if !n.hasPrefix("*"), n.hasSuffix(apex) { names.insert(n) }
                }
            }
        }
        let src = try await store.recordSource(Source(
            id: nil, investigationId: investigationId, kind: "ct",
            ref: url.absoluteString, collector: name, httpStatus: 200, fetchedAt: Date()))
        let rows = names.map { Subdomain(id: nil, investigationId: investigationId, host: $0,
                                         discoveredVia: "ct", resolved: false, sourceId: src) }
        try await store.insertMany(rows)
        emit(.progress(stage: "Recon", message: "CT: \(names.count) subdomain(s)", done: names.count, total: names.count))
    }

    // MARK: Passive — DNS enumeration

    func dnsEnumeration(host: String, emit: @Sendable (RunEvent) -> Void) async throws {
        let apex = Self.apexDomain(host)
        let src = try await store.recordSource(Source(
            id: nil, investigationId: investigationId, kind: "dns",
            ref: "dns:\(apex)", collector: name, httpStatus: nil, fetchedAt: Date()))
        // Query all record types concurrently, then persist serially.
        let results = await withTaskGroup(of: (String, [String]).self) { group -> [(String, [String])] in
            for (typeName, _) in DoHClient.types {
                group.addTask { (typeName, await self.doh.query(apex, type: typeName)) }
            }
            var out: [(String, [String])] = []
            for await r in group { out.append(r) }
            return out
        }
        var count = 0
        for (typeName, values) in results {
            for v in values {
                _ = try await store.insert(DNSRecord(
                    id: nil, investigationId: investigationId, name: apex,
                    type: typeName, value: v, sourceId: src))
                count += 1
            }
        }
        emit(.progress(stage: "Recon", message: "DNS: \(count) record(s)", done: count, total: count))
    }

    // MARK: Passive — technology fingerprinting

    func fingerprint(host: String, emit: @Sendable (RunEvent) -> Void) async throws {
        guard let url = URL(string: "https://\(host)") else { return }
        emit(.progress(stage: "Recon", message: "Fingerprinting \(host)…", done: 0, total: nil))
        guard let (data, status) = try? await http.get(url) else { return }
        let html = String(data: data, encoding: .utf8) ?? ""

        // Re-request to capture headers as a dictionary.
        var headers: [String: String] = [:]
        var req = URLRequest(url: url)
        req.httpMethod = "GET"
        if let (_, resp) = try? await http.session.data(for: req),
           let http = resp as? HTTPURLResponse {
            for (k, v) in http.allHeaderFields {
                if let ks = k as? String, let vs = v as? String { headers[ks] = vs }
            }
        }

        let matches = Fingerprinter().detect(headers: headers, html: html)
        let src = try await store.recordSource(Source(
            id: nil, investigationId: investigationId, kind: "web",
            ref: url.absoluteString, collector: name, httpStatus: status, fetchedAt: Date()))
        for m in matches {
            _ = try await store.insert(TechFingerprint(
                id: nil, investigationId: investigationId, host: host,
                technology: m.technology, category: m.category, version: m.version,
                evidence: m.evidence, sourceId: src))
            _ = try await store.insert(Entity(
                id: nil, investigationId: investigationId, type: EntityType.technology.rawValue,
                name: m.technology, attributes: "{}", createdAt: Date()))
        }
        emit(.progress(stage: "Recon", message: "Fingerprint: \(matches.count) technologies", done: matches.count, total: matches.count))
    }

    // MARK: Active — subdomain brute force (requires consent)

    func subdomainBruteForce(host: String, emit: @Sendable (RunEvent) -> Void) async throws {
        let apex = Self.apexDomain(host)
        let words = Self.loadWordlist()
        emit(.progress(stage: "Recon", message: "Brute-forcing \(words.count) subdomains…", done: 0, total: words.count))
        let src = try await store.recordSource(Source(
            id: nil, investigationId: investigationId, kind: "dns",
            ref: "brute:\(apex)", collector: name, httpStatus: nil, fetchedAt: Date()))

        let found = await withTaskGroup(of: String?.self) { group -> [String] in
            for word in words {
                group.addTask {
                    await self.resolveLimiter.acquire()
                    defer { Task { await self.resolveLimiter.release() } }
                    let candidate = "\(word).\(apex)"
                    return await self.doh.resolves(candidate) ? candidate : nil
                }
            }
            var hits: [String] = []
            for await r in group { if let r { hits.append(r) } }
            return hits
        }
        let rows = found.map { Subdomain(id: nil, investigationId: investigationId, host: $0,
                                         discoveredVia: "brute", resolved: true, sourceId: src) }
        try await store.insertMany(rows)
        emit(.progress(stage: "Recon", message: "Brute force: \(found.count) live subdomain(s)", done: words.count, total: words.count))
    }

    // MARK: Active — TCP-connect port scan (requires consent)

    func portScan(host: String, emit: @Sendable (RunEvent) -> Void) async throws {
        let scanner = PortScanner()
        let ports = Array(1...1024) + Array(PortScanner.commonServices.keys).filter { $0 > 1024 }
        emit(.progress(stage: "Recon", message: "Scanning \(ports.count) ports on \(host)…", done: 0, total: ports.count))
        let src = try await store.recordSource(Source(
            id: nil, investigationId: investigationId, kind: "port",
            ref: "scan:\(host)", collector: name, httpStatus: nil, fetchedAt: Date()))

        let open = await withTaskGroup(of: Int?.self) { group -> [Int] in
            for port in ports {
                group.addTask {
                    await self.scanLimiter.acquire()
                    defer { Task { await self.scanLimiter.release() } }
                    return await scanner.probe(host: host, port: port) ? port : nil
                }
            }
            var hits: [Int] = []
            for await r in group { if let r { hits.append(r) } }
            return hits
        }
        for port in open.sorted() {
            _ = try await store.insert(OpenPort(
                id: nil, investigationId: investigationId, host: host, port: port,
                service: PortScanner.commonServices[port], sourceId: src))
        }
        emit(.progress(stage: "Recon", message: "Port scan: \(open.count) open port(s)", done: ports.count, total: ports.count))
    }

    // MARK: Helpers

    static func apexDomain(_ host: String) -> String {
        let parts = host.split(separator: ".")
        guard parts.count > 2 else { return host }
        return parts.suffix(2).joined(separator: ".")
    }

    static func loadWordlist() -> [String] {
        guard let url = Bundle.main.url(forResource: "subdomains", withExtension: "txt"),
              let text = try? String(contentsOf: url, encoding: .utf8) else { return [] }
        return text.split(whereSeparator: \.isNewline).map(String.init)
    }
}
