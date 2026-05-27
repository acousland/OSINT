import Foundation
import GRDB

/// Actor wrapping the GRDB queue. All reads and writes funnel through here, giving
/// collectors a clean async API and a single serialized write path free of data races.
actor Store {
    private let dbQueue: DatabaseQueue

    init() throws {
        self.dbQueue = try AppDatabase.makeQueue()
    }

    // MARK: Investigations

    func createInvestigation(name: String, target: String) throws -> Investigation {
        var inv = Investigation(id: nil, name: name, target: target,
                                createdAt: Date(), activeReconConsent: false)
        try dbQueue.write { db in try inv.insert(db) }
        return inv
    }

    func allInvestigations() throws -> [Investigation] {
        try dbQueue.read { db in
            try Investigation.order(Column("createdAt").desc).fetchAll(db)
        }
    }

    func setActiveReconConsent(_ consent: Bool, investigationId: Int64) throws {
        try dbQueue.write { db in
            try db.execute(sql: "UPDATE investigation SET activeReconConsent = ? WHERE id = ?",
                           arguments: [consent, investigationId])
        }
    }

    // MARK: Provenance — create a source row and return its id

    func recordSource(_ source: Source) throws -> Int64 {
        var s = source
        try dbQueue.write { db in try s.insert(db) }
        return s.id!
    }

    // MARK: Generic insert helpers

    func insert<T: MutablePersistableRecord>(_ record: T) throws -> T {
        var r = record
        try dbQueue.write { db in try r.insert(db) }
        return r
    }

    func insertMany<T: MutablePersistableRecord>(_ records: [T]) throws {
        try dbQueue.write { db in
            for var r in records { try r.insert(db) }
        }
    }

    // MARK: Typed fetches used by the UI

    func entities(investigationId: Int64) throws -> [Entity] {
        try dbQueue.read { db in
            try Entity.filter(Column("investigationId") == investigationId)
                .order(Column("type")).fetchAll(db)
        }
    }

    func edges(investigationId: Int64) throws -> [EntityEdge] {
        try dbQueue.read { db in
            try EntityEdge.filter(Column("investigationId") == investigationId).fetchAll(db)
        }
    }

    func facts(investigationId: Int64) throws -> [Fact] {
        try dbQueue.read { db in
            try Fact.filter(Column("investigationId") == investigationId).fetchAll(db)
        }
    }

    func crawlPages(investigationId: Int64) throws -> [CrawlPage] {
        try dbQueue.read { db in
            try CrawlPage.filter(Column("investigationId") == investigationId)
                .order(Column("fetchedAt").desc).fetchAll(db)
        }
    }

    func documents(investigationId: Int64) throws -> [HarvestedDocument] {
        try dbQueue.read { db in
            try HarvestedDocument.filter(Column("investigationId") == investigationId).fetchAll(db)
        }
    }

    func pdfRenders(investigationId: Int64) throws -> [PdfRender] {
        try dbQueue.read { db in
            try PdfRender.filter(Column("investigationId") == investigationId)
                .order(Column("url")).fetchAll(db)
        }
    }

    func subdomains(investigationId: Int64) throws -> [Subdomain] {
        try dbQueue.read { db in
            try Subdomain.filter(Column("investigationId") == investigationId)
                .order(Column("host")).fetchAll(db)
        }
    }

    func openPorts(investigationId: Int64) throws -> [OpenPort] {
        try dbQueue.read { db in
            try OpenPort.filter(Column("investigationId") == investigationId)
                .order(Column("port")).fetchAll(db)
        }
    }

    func fingerprints(investigationId: Int64) throws -> [TechFingerprint] {
        try dbQueue.read { db in
            try TechFingerprint.filter(Column("investigationId") == investigationId).fetchAll(db)
        }
    }

    func dnsRecords(investigationId: Int64) throws -> [DNSRecord] {
        try dbQueue.read { db in
            try DNSRecord.filter(Column("investigationId") == investigationId).fetchAll(db)
        }
    }

    func timeline(investigationId: Int64) throws -> [TimelineEvent] {
        try dbQueue.read { db in
            try TimelineEvent.filter(Column("investigationId") == investigationId)
                .order(Column("timestamp")).fetchAll(db)
        }
    }

    func embeddings(investigationId: Int64) throws -> [EmbeddingChunk] {
        try dbQueue.read { db in
            try EmbeddingChunk.filter(Column("investigationId") == investigationId).fetchAll(db)
        }
    }

    func source(id: Int64) throws -> Source? {
        try dbQueue.read { db in try Source.fetchOne(db, key: id) }
    }

    /// Collected text (pages + documents) used to build the RAG corpus, paired with
    /// the source id each chunk should attribute to.
    func corpusText(investigationId: Int64) throws -> [(sourceId: Int64, text: String)] {
        let rows: [(Int64, String)] = try dbQueue.read { db in
            var out: [(Int64, String)] = []
            let pages = try CrawlPage
                .filter(Column("investigationId") == investigationId).fetchAll(db)
            for p in pages {
                if let t = p.textContent, !t.isEmpty {
                    let header = p.title.map { "\($0)\n" } ?? ""
                    out.append((p.sourceId, header + t))
                }
            }
            let docs = try HarvestedDocument
                .filter(Column("investigationId") == investigationId).fetchAll(db)
            for d in docs where (d.extractedText?.isEmpty == false) {
                out.append((d.sourceId, d.extractedText!))
            }
            return out
        }
        return rows.map { (sourceId: $0.0, text: $0.1) }
    }
}
