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

    /// Build an enterprise-architecture consulting briefing: business context + technology
    /// landscape, with PESTLE, SWOT, and EA engagement opportunities. Draws on the website
    /// business text, harvested documents, ABR identity, and the observed tech footprint.
    func generateDossier() async throws -> String {
        let id = investigationId
        let entities = try await store.entities(investigationId: id)
        let facts = try await store.facts(investigationId: id)
        let techs = try await store.fingerprints(investigationId: id)
        let subs = try await store.subdomains(investigationId: id)
        let ports = try await store.openPorts(investigationId: id)
        let dns = try await store.dnsRecords(investigationId: id)
        let pages = try await store.crawlPages(investigationId: id)
        let docs = try await store.documents(investigationId: id)

        // Assemble evidence within a character budget, prioritising business-rich content.
        var sections: [String] = []
        var used = 0
        let budget = 70_000
        func add(_ header: String, _ body: String) {
            let trimmed = body.trimmingCharacters(in: .whitespacesAndNewlines)
            guard used < budget, !trimmed.isEmpty else { return }
            let slice = String(trimmed.prefix(budget - used))
            sections.append("## \(header)\n\(slice)")
            used += slice.count
        }

        // Corporate identity (ABR + facts).
        var identity = ""
        for e in entities where e.type == EntityType.company.rawValue { identity += "Legal entity: \(e.name)\n" }
        for f in facts.prefix(80) { identity += "- \(f.key): \(f.value)\n" }
        add("Corporate identity (ABR + collected facts)", identity)

        // Business content from the site — prioritise informative pages.
        let keywords = ["about", "company", "who-we-are", "our-story", "leadership", "team",
                        "management", "board", "director", "investor", "product", "service",
                        "solution", "platform", "customer", "client", "case-stud", "industr",
                        "sector", "news", "media", "press", "report", "annual", "sustainab",
                        "esg", "career", "contact", "partner"]
        let scoredPages = pages.compactMap { p -> (Int, CrawlPage)? in
            guard let t = p.textContent, !t.isEmpty else { return nil }
            let hay = (p.url + " " + (p.title ?? "")).lowercased()
            let score = keywords.reduce(0) { $0 + (hay.contains($1) ? 1 : 0) }
            return (score, p)
        }.sorted { $0.0 > $1.0 }
        for (_, p) in scoredPages.prefix(30) {
            add("Web page — \(p.title ?? p.url)\nURL: \(p.url)", p.textContent ?? "")
        }
        for d in docs.prefix(15) where (d.extractedText?.isEmpty == false) {
            add("Document — \(d.url)", String(d.extractedText!.prefix(6000)))
        }

        // Technology & infrastructure footprint — first-class for EA analysis.
        var tech = ""
        if !techs.isEmpty {
            tech += "Detected technologies:\n"
            for t in techs.prefix(60) {
                let v = t.version.map { " \($0)" } ?? ""
                tech += "- \(t.technology)\(v) [\(t.category ?? "")]\n"
            }
        }
        if !dns.isEmpty {
            tech += "\nDNS records:\n"
            for r in dns.prefix(40) { tech += "- \(r.type): \(r.value)\n" }
        }
        if !subs.isEmpty {
            tech += "\nSubdomains discovered (\(subs.count)) — sample:\n"
            for s in subs.prefix(40) { tech += "- \(s.host)\n" }
        }
        if !ports.isEmpty {
            tech += "\nOpen ports:\n"
            for p in ports.prefix(40) { tech += "- \(p.port) \(p.service ?? "")\n" }
        }
        add("Technology & infrastructure footprint (observed)", tech)

        let evidence = sections.joined(separator: "\n\n")

        let system = """
        You are a principal enterprise-architecture consultant preparing a pre-engagement \
        briefing on a target organisation. Your reader must walk into a meeting demonstrating \
        deep understanding of BOTH the organisation's business AND its technology landscape, \
        and identify credible enterprise-architecture engagement opportunities.

        Using ONLY the evidence provided (corporate registry data, the organisation's own \
        website text, documents, and the observed technology/infrastructure footprint), \
        produce a polished, executive-ready Markdown dossier with these sections:

        1. **Executive Summary** — 4–6 sentences: what they do, scale, and the headline \
           EA-relevant observations.
        2. **Company Overview** — legal entity and registration (per ABR), structure, size, \
           locations, history.
        3. **Products, Services & Value Proposition.**
        4. **Market & Competitive Positioning** — customers, segments, differentiators, industry.
        5. **Technology & Architecture Profile** — interpret the observed technology stack, \
           web/hosting/CDN footprint, subdomain landscape and exposed services. Infer likely \
           architecture patterns, platform choices, integration surface, and maturity.
        6. **PESTLE Analysis** — Political, Economic, Social, Technological, Legal, \
           Environmental. Make the Technological dimension concrete using the observed stack.
        7. **SWOT Analysis** — integrate BOTH business and technology factors (e.g. legacy vs \
           modern stack, cloud adoption, security posture, market position).
        8. **Enterprise Architecture Observations & Opportunities** — modernisation, \
           application/infrastructure consolidation, cloud migration, integration, data, \
           security/risk, and digital-experience opportunities. Frame each as a credible \
           hypothesis an EA consultant could explore.
        9. **Commercial Angles & Conversation Starters** — specific, tailored talking points \
           that connect their business priorities to EA value, so the consultant sounds \
           informed and relevant.
        10. **Confidence & Gaps** — what is well-evidenced vs inferred, and the highest-value \
            things to research next.

        Rules:
        - Ground every factual claim in the evidence; note the source kind where useful \
          (e.g. "per ABR", "per their site", "observed in tech fingerprint").
        - Clearly mark informed inference (industry-typical factors, architectural hypotheses) \
          as such — never present inference as fact.
        - Be specific and substantive; avoid generic filler that could apply to any company.
        - Do not fabricate names, figures, leadership, or quotes not in the evidence.
        - Keep it tight and senior — this is a briefing, not an essay.
        """
        return try await openai.chat(system: system, user: "EVIDENCE:\n\n\(evidence)",
                                     model: openai.dossierModel, temperature: nil)
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
