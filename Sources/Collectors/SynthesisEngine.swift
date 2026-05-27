import Foundation

/// The "learn fast" layer. Builds a RAG index over collected text, generates an executive
/// dossier from the structured findings, and answers questions with source citations.
struct SynthesisEngine {
    let store: Store
    let investigationId: Int64
    let openai = OpenAIClient()

    private let chunkSize = 1200   // characters per chunk
    private let topK = 6

    // MARK: Index building

    /// Chunk collected document text, embed it, and persist vectors for retrieval.
    func buildIndex(emit: @Sendable (RunEvent) -> Void) async throws {
        let corpus = try await store.corpusText(investigationId: investigationId)
        var chunks: [(sourceId: Int64, text: String)] = []
        for item in corpus {
            for chunk in Self.chunk(item.text, size: chunkSize) {
                chunks.append((item.sourceId, chunk))
            }
        }
        guard !chunks.isEmpty else {
            emit(.progress(stage: "Synthesis", message: "No text corpus to index", done: 0, total: 0))
            return
        }
        emit(.progress(stage: "Synthesis", message: "Embedding \(chunks.count) chunks…", done: 0, total: chunks.count))

        // Batch embeddings to keep requests reasonable.
        let batchSize = 64
        var done = 0
        for start in stride(from: 0, to: chunks.count, by: batchSize) {
            let slice = Array(chunks[start..<min(start + batchSize, chunks.count)])
            let vectors = try await openai.embed(slice.map { $0.text })
            for (i, vec) in vectors.enumerated() {
                _ = try await store.insert(EmbeddingChunk(
                    id: nil, investigationId: investigationId, sourceId: slice[i].sourceId,
                    chunkText: slice[i].text, vector: VectorMath.data(from: vec)))
            }
            done += slice.count
            emit(.progress(stage: "Synthesis", message: "Embedded \(done) chunks", done: done, total: chunks.count))
        }
    }

    // MARK: Q&A (RAG)

    struct Answer { let text: String; let citations: [String] }

    func ask(_ question: String) async throws -> Answer {
        let stored = try await store.embeddings(investigationId: investigationId)
        guard !stored.isEmpty else {
            return Answer(text: "No indexed corpus yet — build the index first.", citations: [])
        }
        let qVec = try await openai.embed([question]).first ?? []
        let ranked = stored
            .map { (chunk: $0, score: VectorMath.cosine(qVec, VectorMath.vector(from: $0.vector))) }
            .sorted { $0.score > $1.score }
            .prefix(topK)

        var context = ""
        var citations: [String] = []
        for (i, item) in ranked.enumerated() {
            let src = try await store.source(id: item.chunk.sourceId)
            let ref = src?.ref ?? "unknown source"
            context += "[\(i + 1)] (\(ref))\n\(item.chunk.chunkText)\n\n"
            citations.append("[\(i + 1)] \(ref)")
        }

        let system = """
        You are a corporate-intelligence analyst. Answer ONLY from the provided context. \
        Cite sources inline using their bracket numbers, e.g. [1]. If the context does not \
        contain the answer, say so plainly.
        """
        let user = "Context:\n\(context)\nQuestion: \(question)"
        let text = try await openai.chat(system: system, user: user)
        return Answer(text: text, citations: citations)
    }

    // MARK: Executive dossier

    /// Build a markdown dossier from the structured findings (entities, facts, recon).
    func generateDossier() async throws -> String {
        let entities = try await store.entities(investigationId: investigationId)
        let facts = try await store.facts(investigationId: investigationId)
        let subs = try await store.subdomains(investigationId: investigationId)
        let ports = try await store.openPorts(investigationId: investigationId)
        let techs = try await store.fingerprints(investigationId: investigationId)

        var summary = "ENTITIES:\n"
        for e in entities.prefix(50) { summary += "- [\(e.type)] \(e.name)\n" }
        summary += "\nFACTS:\n"
        for f in facts.prefix(80) { summary += "- \(f.key): \(f.value)\n" }
        summary += "\nSUBDOMAINS (\(subs.count)):\n"
        for s in subs.prefix(40) { summary += "- \(s.host)\n" }
        summary += "\nOPEN PORTS:\n"
        for p in ports.prefix(40) { summary += "- \(p.port) \(p.service ?? "")\n" }
        summary += "\nTECHNOLOGIES:\n"
        for t in techs.prefix(40) { summary += "- \(t.technology) (\(t.category ?? ""))\n" }

        let system = """
        You are a corporate-intelligence analyst. Produce a concise executive dossier in \
        Markdown from the structured findings. Sections: Overview, Corporate Identity, \
        Digital Footprint, Technology Profile, Notable Observations, and Gaps/Next Steps. \
        Be factual and do not invent data not present in the findings.
        """
        return try await openai.chat(system: system, user: summary)
    }

    // MARK: Chunking

    static func chunk(_ text: String, size: Int) -> [String] {
        guard !text.isEmpty else { return [] }
        var chunks: [String] = []
        var idx = text.startIndex
        while idx < text.endIndex {
            let end = text.index(idx, offsetBy: size, limitedBy: text.endIndex) ?? text.endIndex
            chunks.append(String(text[idx..<end]))
            idx = end
        }
        return chunks
    }
}
