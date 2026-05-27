import Foundation

/// Corporate identity via the Australian Business Register ABN Lookup web service.
/// Free, but requires a registered auth GUID (stored in Keychain). The JSON endpoints
/// return JSONP — a `callback({...})` wrapper we must strip before decoding.
///
/// Register for a GUID: https://abr.business.gov.au/Tools/WebServices
struct ABRCollector: PassiveCollector {
    let name = "ABRCollector"
    let store: Store
    let investigationId: Int64
    let http = HTTPClient()

    private let base = "https://abr.business.gov.au/json"
    private let rate = RateLimiter(requestsPerSecond: 2)

    func run(abn: String?, name companyName: String?,
             emit: @Sendable (RunEvent) -> Void) async throws -> String {
        guard let guid = Secrets.get(.abrGuid), !guid.isEmpty else {
            throw HTTPError.missingCredential("ABR auth GUID (set it in Settings)")
        }

        if let abn, !abn.isEmpty {
            emit(.progress(stage: "Identity", message: "Looking up ABN \(abn)…", done: 0, total: 1))
            let json = try await lookupABN(abn, guid: guid)
            try await persist(json, query: "ABN \(abn)", emit: emit)
            emit(.progress(stage: "Identity", message: "ABN resolved", done: 1, total: 1))
            return "Resolved entity for ABN \(abn)"
        }

        if let companyName, !companyName.isEmpty {
            emit(.progress(stage: "Identity", message: "Searching name '\(companyName)'…", done: 0, total: 1))
            let matches = try await searchName(companyName, guid: guid)
            // Resolve the top match to a full record.
            if let topAbn = matches.first?.abn, !topAbn.isEmpty {
                let json = try await lookupABN(topAbn, guid: guid)
                try await persist(json, query: "name '\(companyName)'", emit: emit)
            } else {
                // Persist the name matches as low-confidence candidate facts.
                let src = try await store.recordSource(Source(
                    id: nil, investigationId: investigationId, kind: "api",
                    ref: "\(base)/MatchingNames.aspx?name=\(companyName)",
                    collector: name, httpStatus: 200, fetchedAt: Date()))
                for m in matches.prefix(10) {
                    _ = try await store.insert(Fact(
                        id: nil, investigationId: investigationId, entityId: nil,
                        key: "name-match", value: "\(m.name) (ABN \(m.abn))",
                        confidence: m.score, sourceId: src))
                }
            }
            emit(.progress(stage: "Identity", message: "Name search complete", done: 1, total: 1))
            return "Found \(matches.count) name match(es) for '\(companyName)'"
        }

        return "No ABN or company name provided"
    }

    // MARK: ABN detail lookup

    private func lookupABN(_ abn: String, guid: String) async throws -> [String: Any] {
        await rate.wait()
        let digits = abn.filter(\.isNumber)
        let endpoint = digits.count == 9 ? "AcnDetails.aspx" : "AbnDetails.aspx"
        let param = digits.count == 9 ? "acn" : "abn"
        guard let url = URL(string: "\(base)/\(endpoint)?\(param)=\(digits)&guid=\(guid)&callback=cb") else {
            throw HTTPError.invalidURL("\(base)/\(endpoint)")
        }
        let (data, status) = try await http.get(url)
        guard (200..<300).contains(status) else { throw HTTPError.badStatus(status) }
        return try ABRCollector.unwrapJSONP(data)
    }

    struct NameMatch { let name: String; let abn: String; let score: Double }

    private func searchName(_ query: String, guid: String) async throws -> [NameMatch] {
        await rate.wait()
        var comps = URLComponents(string: "\(base)/MatchingNames.aspx")!
        comps.queryItems = [
            .init(name: "name", value: query),
            .init(name: "maxResults", value: "10"),
            .init(name: "guid", value: guid),
            .init(name: "callback", value: "cb"),
        ]
        guard let url = comps.url else { throw HTTPError.invalidURL("MatchingNames") }
        let (data, status) = try await http.get(url)
        guard (200..<300).contains(status) else { throw HTTPError.badStatus(status) }
        let json = try ABRCollector.unwrapJSONP(data)
        guard let names = json["Names"] as? [[String: Any]] else { return [] }
        return names.map { n in
            NameMatch(
                name: (n["Name"] as? String) ?? "",
                abn: (n["Abn"] as? String) ?? "",
                score: ((n["Score"] as? NSNumber)?.doubleValue ?? 0) / 100.0)
        }
    }

    // MARK: Persist an ABN detail record as an entity + facts

    private func persist(_ json: [String: Any], query: String,
                         emit: @Sendable (RunEvent) -> Void) async throws {
        let entityName = (json["EntityName"] as? String)
            ?? (json["MainName"] as? [String: Any])?["OrganisationName"] as? String
            ?? "Unknown entity"

        let src = try await store.recordSource(Source(
            id: nil, investigationId: investigationId, kind: "api",
            ref: "ABR \(query)", collector: name, httpStatus: 200, fetchedAt: Date()))

        var attributes: [String: String] = [:]
        for key in ["Abn", "AbnStatus", "EntityTypeName", "Gst", "AddressState", "AddressPostcode", "AddressDate"] {
            if let v = json[key] as? String, !v.isEmpty { attributes[key] = v }
        }
        let attrData = (try? JSONSerialization.data(withJSONObject: attributes)) ?? Data("{}".utf8)

        let entity = try await store.insert(Entity(
            id: nil, investigationId: investigationId, type: EntityType.company.rawValue,
            name: entityName, attributes: String(data: attrData, encoding: .utf8) ?? "{}",
            createdAt: Date()))

        for (k, v) in attributes {
            _ = try await store.insert(Fact(
                id: nil, investigationId: investigationId, entityId: entity.id,
                key: k, value: v, confidence: 1.0, sourceId: src))
        }

        _ = try await store.insert(TimelineEvent(
            id: nil, investigationId: investigationId, timestamp: Date(),
            kind: "identity", summary: "Identified \(entityName) via ABR",
            entityId: entity.id, sourceId: src))

        emit(.progress(stage: "Identity", message: "Stored \(entityName)", done: 1, total: 1))
    }

    // MARK: JSONP unwrapping

    /// ABR JSON endpoints wrap the payload as `callback({...});`. Strip everything outside
    /// the outermost braces and decode the JSON object.
    static func unwrapJSONP(_ data: Data) throws -> [String: Any] {
        guard var s = String(data: data, encoding: .utf8) else {
            throw HTTPError.decode("non-UTF8 ABR response")
        }
        guard let first = s.firstIndex(of: "{"), let last = s.lastIndex(of: "}") else {
            throw HTTPError.decode("no JSON object in ABR response")
        }
        s = String(s[first...last])
        guard let obj = try JSONSerialization.jsonObject(with: Data(s.utf8)) as? [String: Any] else {
            throw HTTPError.decode("ABR payload was not a JSON object")
        }
        return obj
    }
}
