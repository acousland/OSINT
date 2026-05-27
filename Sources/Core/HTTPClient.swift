import Foundation

enum HTTPError: LocalizedError {
    case badStatus(Int)
    case missingCredential(String)
    case decode(String)
    case invalidURL(String)

    var errorDescription: String? {
        switch self {
        case .badStatus(let c): return "HTTP status \(c)"
        case .missingCredential(let s): return "Missing credential: \(s)"
        case .decode(let s): return "Decode failure: \(s)"
        case .invalidURL(let s): return "Invalid URL: \(s)"
        }
    }
}

/// Shared URLSession with an identifiable User-Agent. Passive collection identifies
/// itself honestly rather than spoofing — important legally and for politeness.
struct HTTPClient: Sendable {
    static let userAgent = "OSIntel/1.0 (+https://github.com/acousland/OSINT; corporate-intelligence research tool)"

    let session: URLSession

    init(timeout: TimeInterval = 30) {
        let config = URLSessionConfiguration.default
        config.httpAdditionalHeaders = ["User-Agent": HTTPClient.userAgent]
        config.timeoutIntervalForRequest = timeout
        config.httpMaximumConnectionsPerHost = 6
        self.session = URLSession(configuration: config)
    }

    /// GET returning raw data + HTTP status.
    func get(_ url: URL) async throws -> (Data, Int) {
        let (data, response) = try await session.data(from: url)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        return (data, status)
    }

    /// GET decoding JSON into `T`.
    func getJSON<T: Decodable>(_ url: URL, as type: T.Type) async throws -> T {
        let (data, status) = try await get(url)
        guard (200..<300).contains(status) else { throw HTTPError.badStatus(status) }
        do { return try JSONDecoder().decode(T.self, from: data) }
        catch { throw HTTPError.decode("\(error)") }
    }

    /// HEAD-style content-type sniff via a ranged GET (some servers reject HEAD).
    func contentType(_ url: URL) async -> String? {
        var req = URLRequest(url: url)
        req.httpMethod = "HEAD"
        guard let (_, response) = try? await session.data(for: req) else { return nil }
        return (response as? HTTPURLResponse)?.value(forHTTPHeaderField: "Content-Type")
    }
}
