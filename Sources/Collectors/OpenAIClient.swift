import Foundation

/// Minimal OpenAI REST client (chat + embeddings) over URLSession. Avoids a third-party
/// SDK dependency and version drift. API key is read from Keychain, never stored on disk.
struct OpenAIClient: Sendable {
    let chatModel = "gpt-4o-mini"
    let embeddingModel = "text-embedding-3-small"
    private let base = URL(string: "https://api.openai.com/v1")!

    private func apiKey() throws -> String {
        guard let key = Secrets.get(.openAIKey), !key.isEmpty else {
            throw HTTPError.missingCredential("OpenAI API key (set it in Settings)")
        }
        return key
    }

    private func request(_ path: String, body: [String: Any]) throws -> URLRequest {
        var req = URLRequest(url: base.appendingPathComponent(path))
        req.httpMethod = "POST"
        req.setValue("Bearer \(try apiKey())", forHTTPHeaderField: "Authorization")
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        req.timeoutInterval = 120
        return req
    }

    // MARK: Chat

    struct ChatResponse: Decodable {
        struct Choice: Decodable { struct Message: Decodable { let content: String }; let message: Message }
        let choices: [Choice]
    }

    func chat(system: String, user: String) async throws -> String {
        let body: [String: Any] = [
            "model": chatModel,
            "messages": [
                ["role": "system", "content": system],
                ["role": "user", "content": user],
            ],
            "temperature": 0.2,
        ]
        let req = try request("chat/completions", body: body)
        let (data, resp) = try await URLSession.shared.data(for: req)
        let status = (resp as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(status) else {
            throw HTTPError.badStatus(status)
        }
        let decoded = try JSONDecoder().decode(ChatResponse.self, from: data)
        return decoded.choices.first?.message.content ?? ""
    }

    // MARK: Embeddings

    struct EmbeddingResponse: Decodable {
        struct Item: Decodable { let embedding: [Double] }
        let data: [Item]
    }

    func embed(_ texts: [String]) async throws -> [[Float]] {
        guard !texts.isEmpty else { return [] }
        let body: [String: Any] = ["model": embeddingModel, "input": texts]
        let req = try request("embeddings", body: body)
        let (data, resp) = try await URLSession.shared.data(for: req)
        let status = (resp as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(status) else { throw HTTPError.badStatus(status) }
        let decoded = try JSONDecoder().decode(EmbeddingResponse.self, from: data)
        return decoded.data.map { $0.embedding.map(Float.init) }
    }
}

/// Float32 vector <-> Data, plus cosine similarity for in-memory RAG retrieval.
enum VectorMath {
    static func data(from vector: [Float]) -> Data {
        vector.withUnsafeBytes { Data($0) }
    }
    static func vector(from data: Data) -> [Float] {
        data.withUnsafeBytes { Array($0.bindMemory(to: Float.self)) }
    }
    static func cosine(_ a: [Float], _ b: [Float]) -> Float {
        guard a.count == b.count, !a.isEmpty else { return 0 }
        var dot: Float = 0, na: Float = 0, nb: Float = 0
        for i in 0..<a.count { dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i] }
        let denom = (na.squareRoot() * nb.squareRoot())
        return denom == 0 ? 0 : dot / denom
    }
}
