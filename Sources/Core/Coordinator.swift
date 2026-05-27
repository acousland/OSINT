import Foundation

/// What the user asked a run to do. Active modules are ignored unless `activeConsent`.
struct RunPlan: Sendable {
    var abn: String?              // optional ABN/ACN for identity lookup
    var companyName: String?      // optional name search
    var crawlDomain: String?      // root URL to crawl
    var maxDepth: Int = 3
    var renderPDFs: Bool = true
    var harvestDocuments: Bool = true
    var dnsEnumeration: Bool = true
    var ctSubdomains: Bool = true
    var fingerprint: Bool = true
    // Active (gated):
    var subdomainBruteForce: Bool = false
    var portScan: Bool = false
    var activeConsent: Bool = false
}

/// Owns a single investigation run. Sequences collectors, enforces the passive/active
/// gate, and streams progress to the UI via an AsyncStream.
actor Coordinator {
    let store: Store
    let investigationId: Int64

    init(store: Store, investigationId: Int64) {
        self.store = store
        self.investigationId = investigationId
    }

    /// Returns a stream the UI subscribes to. The run executes as the stream is consumed.
    func run(_ plan: RunPlan) -> AsyncStream<RunEvent> {
        AsyncStream { continuation in
            let task = Task {
                await self.execute(plan, emit: { continuation.yield($0) })
                continuation.yield(.completed)
                continuation.finish()
            }
            continuation.onTermination = { _ in task.cancel() }
        }
    }

    private func execute(_ plan: RunPlan, emit: @escaping @Sendable (RunEvent) -> Void) async {
        // 1. Corporate identity (passive)
        if plan.abn != nil || plan.companyName != nil {
            emit(.started(stage: "Identity"))
            do {
                let collector = ABRCollector(store: store, investigationId: investigationId)
                let summary = try await collector.run(abn: plan.abn, name: plan.companyName, emit: emit)
                emit(.finishedStage(stage: "Identity", summary: summary))
            } catch {
                emit(.error(stage: "Identity", message: error.localizedDescription))
            }
        }

        // 2. Web contents (passive)
        if let domain = plan.crawlDomain, !domain.isEmpty {
            emit(.started(stage: "Web"))
            do {
                let collector = WebCollector(store: store, investigationId: investigationId)
                let summary = try await collector.run(
                    rootURL: domain, maxDepth: plan.maxDepth,
                    renderPDFs: plan.renderPDFs, harvestDocs: plan.harvestDocuments, emit: emit)
                emit(.finishedStage(stage: "Web", summary: summary))
            } catch {
                emit(.error(stage: "Web", message: error.localizedDescription))
            }
        }

        // 3. Tech / recon — passive parts always; active parts gated on consent.
        let host = Coordinator.host(from: plan.crawlDomain) ?? plan.companyName
        if let host, !host.isEmpty {
            emit(.started(stage: "Recon"))
            let recon = ReconCollector(store: store, investigationId: investigationId)
            // Passive stages are independent — run them concurrently. Each isolates its
            // own errors; all writes go through the Store actor so there's no race.
            await withTaskGroup(of: Void.self) { group in
                if plan.ctSubdomains {
                    group.addTask {
                        do { try await recon.certificateTransparency(host: host, emit: emit) }
                        catch { emit(.error(stage: "Recon", message: "CT: \(error.localizedDescription)")) }
                    }
                }
                if plan.dnsEnumeration {
                    group.addTask {
                        do { try await recon.dnsEnumeration(host: host, emit: emit) }
                        catch { emit(.error(stage: "Recon", message: "DNS: \(error.localizedDescription)")) }
                    }
                }
                if plan.fingerprint {
                    group.addTask {
                        do { try await recon.fingerprint(host: host, emit: emit) }
                        catch { emit(.error(stage: "Recon", message: "Fingerprint: \(error.localizedDescription)")) }
                    }
                }
            }
            // Active — only with explicit consent.
            let wantsActive = plan.subdomainBruteForce || plan.portScan
            if wantsActive {
                if plan.activeConsent {
                    emit(.warning("Running AGGRESSIVE active reconnaissance against \(host). Ensure you are authorised to test this target."))
                    if plan.subdomainBruteForce {
                        do { try await recon.subdomainBruteForce(host: host, emit: emit) }
                        catch { emit(.error(stage: "Recon", message: "Brute force: \(error.localizedDescription)")) }
                    }
                    if plan.portScan {
                        do { try await recon.portScan(host: host, emit: emit) }
                        catch { emit(.error(stage: "Recon", message: "Port scan: \(error.localizedDescription)")) }
                    }
                } else {
                    emit(.warning("Active recon was requested but consent was not granted — skipping port scan / brute force."))
                }
            }
            emit(.finishedStage(stage: "Recon", summary: "Reconnaissance complete"))
        }
    }

    /// Extract a bare host from a URL or naked domain string.
    static func host(from urlOrDomain: String?) -> String? {
        guard let s = urlOrDomain, !s.isEmpty else { return nil }
        if let url = URL(string: s), let h = url.host { return h }
        if let url = URL(string: "https://\(s)"), let h = url.host { return h }
        return s
    }
}
