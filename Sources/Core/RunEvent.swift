import Foundation

/// Progress events streamed from the Coordinator to the UI via AsyncStream.
enum RunEvent: Sendable {
    case started(stage: String)
    case progress(stage: String, message: String, done: Int, total: Int?)
    case finishedStage(stage: String, summary: String)
    case warning(String)
    case error(stage: String, message: String)
    case completed
}

/// Marker protocols enforce the passive/active separation at the type level.
/// The Coordinator will not run an `ActiveCollector` without per-run consent.
protocol Collector: Sendable {
    var name: String { get }
}

/// Low-noise collection: public records, crawling, CT logs, DNS lookups, archives.
protocol PassiveCollector: Collector {}

/// Direct, potentially noisy probing: port scans, subdomain brute force.
/// Requires explicit user consent before the Coordinator will run it.
protocol ActiveCollector: Collector {}
