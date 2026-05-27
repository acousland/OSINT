import Foundation

/// DNS-over-HTTPS client (Google's resolver). Avoids a fragile native DNS dependency and
/// works uniformly for all record types under the App Sandbox with just network.client.
struct DoHClient: Sendable {
    let http = HTTPClient()

    struct Response: Decodable {
        struct Answer: Decodable { let name: String; let type: Int; let data: String }
        let Answer: [Answer]?
    }

    /// Record type names mapped to their numeric codes.
    static let types: [(name: String, code: Int)] = [
        ("A", 1), ("AAAA", 28), ("MX", 15), ("TXT", 16), ("NS", 2), ("CNAME", 5),
    ]

    func query(_ name: String, type: String) async -> [String] {
        guard let url = URL(string: "https://dns.google/resolve?name=\(name)&type=\(type)") else { return [] }
        guard let resp = try? await http.getJSON(url, as: Response.self) else { return [] }
        return (resp.Answer ?? []).map { $0.data }
    }

    /// True if the name resolves to at least one A/AAAA record.
    func resolves(_ name: String) async -> Bool {
        if !(await query(name, type: "A")).isEmpty { return true }
        return !(await query(name, type: "AAAA")).isEmpty
    }
}
