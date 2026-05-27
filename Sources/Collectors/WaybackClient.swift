import Foundation

/// Internet Archive Wayback enrichment. Plain JSON APIs, no dependency. Used to recover
/// the most recent archived snapshot of a page (e.g. when the live page is gone).
struct WaybackClient: Sendable {
    let http = HTTPClient()

    struct Availability: Decodable {
        struct Snapshots: Decodable { let closest: Snapshot? }
        struct Snapshot: Decodable { let available: Bool?; let url: String?; let timestamp: String? }
        let archived_snapshots: Snapshots?
    }

    /// Returns the closest archived snapshot URL for `pageURL`, if any.
    func closestSnapshot(of pageURL: String) async -> (url: String, timestamp: String)? {
        guard let q = pageURL.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed),
              let url = URL(string: "https://archive.org/wayback/available?url=\(q)")
        else { return nil }
        guard let result = try? await http.getJSON(url, as: Availability.self),
              let snap = result.archived_snapshots?.closest,
              snap.available == true, let u = snap.url else { return nil }
        return (u, snap.timestamp ?? "")
    }
}
