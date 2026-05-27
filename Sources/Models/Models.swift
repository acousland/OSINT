import Foundation
import GRDB

// MARK: - Investigation

/// A saved project. Every collected record carries `investigationId`, so a single
/// database can hold many independent investigations side by side.
struct Investigation: Codable, Identifiable, Hashable, FetchableRecord, MutablePersistableRecord {
    var id: Int64?
    var name: String
    /// Primary target — a domain (example.com) and/or company name.
    var target: String
    var createdAt: Date
    /// Set true only after the user accepts the active-recon warning sheet for this run.
    var activeReconConsent: Bool

    static let databaseTableName = "investigation"
    mutating func didInsert(_ inserted: InsertionSuccess) { id = inserted.rowID }
}

// MARK: - Provenance

/// Where a fact came from. Every `Fact`, `Entity` attribute, and collected record
/// references a `Source`, satisfying the "every claim is attributable" requirement.
struct Source: Codable, Identifiable, Hashable, FetchableRecord, MutablePersistableRecord {
    var id: Int64?
    var investigationId: Int64
    /// api | web | file | dns | ct | port | wayback | synthesis
    var kind: String
    /// URL, API endpoint, or file path the data came from.
    var ref: String
    /// Which collector produced it (e.g. "ABRCollector").
    var collector: String
    var httpStatus: Int?
    var fetchedAt: Date

    static let databaseTableName = "source"
    mutating func didInsert(_ inserted: InsertionSuccess) { id = inserted.rowID }
}

// MARK: - Entity graph

enum EntityType: String, Codable, CaseIterable {
    case company, person, domain, host, asset, technology
}

struct Entity: Codable, Identifiable, Hashable, FetchableRecord, MutablePersistableRecord {
    var id: Int64?
    var investigationId: Int64
    var type: String          // EntityType raw value
    var name: String
    var attributes: String     // JSON object of extra fields
    var createdAt: Date

    static let databaseTableName = "entity"
    mutating func didInsert(_ inserted: InsertionSuccess) { id = inserted.rowID }

    var entityType: EntityType { EntityType(rawValue: type) ?? .asset }
}

struct EntityEdge: Codable, Identifiable, Hashable, FetchableRecord, MutablePersistableRecord {
    var id: Int64?
    var investigationId: Int64
    var fromEntityId: Int64
    var toEntityId: Int64
    var relationship: String
    var weight: Double

    static let databaseTableName = "entity_edge"
    mutating func didInsert(_ inserted: InsertionSuccess) { id = inserted.rowID }
}

struct Fact: Codable, Identifiable, Hashable, FetchableRecord, MutablePersistableRecord {
    var id: Int64?
    var investigationId: Int64
    var entityId: Int64?
    var key: String
    var value: String
    var confidence: Double
    var sourceId: Int64

    static let databaseTableName = "fact"
    mutating func didInsert(_ inserted: InsertionSuccess) { id = inserted.rowID }
}

// MARK: - Web collection

struct CrawlPage: Codable, Identifiable, Hashable, FetchableRecord, MutablePersistableRecord {
    var id: Int64?
    var investigationId: Int64
    var url: String
    var title: String?
    var statusCode: Int?
    var contentType: String?
    var fetchedAt: Date
    var sourceId: Int64

    static let databaseTableName = "crawl_page"
    mutating func didInsert(_ inserted: InsertionSuccess) { id = inserted.rowID }
}

struct HarvestedDocument: Codable, Identifiable, Hashable, FetchableRecord, MutablePersistableRecord {
    var id: Int64?
    var investigationId: Int64
    var url: String
    var localPath: String?
    var type: String          // pdf | xlsx | docx
    var extractedText: String?
    var metadata: String       // JSON
    var sourceId: Int64

    static let databaseTableName = "document"
    mutating func didInsert(_ inserted: InsertionSuccess) { id = inserted.rowID }
}

struct PdfRender: Codable, Identifiable, Hashable, FetchableRecord, MutablePersistableRecord {
    var id: Int64?
    var investigationId: Int64
    var url: String
    var localPath: String
    var sourceId: Int64

    static let databaseTableName = "pdf_render"
    mutating func didInsert(_ inserted: InsertionSuccess) { id = inserted.rowID }
}

// MARK: - Recon

struct DNSRecord: Codable, Identifiable, Hashable, FetchableRecord, MutablePersistableRecord {
    var id: Int64?
    var investigationId: Int64
    var name: String
    var type: String          // A | AAAA | MX | TXT | NS | CNAME
    var value: String
    var sourceId: Int64

    static let databaseTableName = "dns_record"
    mutating func didInsert(_ inserted: InsertionSuccess) { id = inserted.rowID }
}

struct Subdomain: Codable, Identifiable, Hashable, FetchableRecord, MutablePersistableRecord {
    var id: Int64?
    var investigationId: Int64
    var host: String
    var discoveredVia: String  // ct | brute | dns
    var resolved: Bool
    var sourceId: Int64

    static let databaseTableName = "subdomain"
    mutating func didInsert(_ inserted: InsertionSuccess) { id = inserted.rowID }
}

struct OpenPort: Codable, Identifiable, Hashable, FetchableRecord, MutablePersistableRecord {
    var id: Int64?
    var investigationId: Int64
    var host: String
    var port: Int
    var service: String?
    var sourceId: Int64

    static let databaseTableName = "open_port"
    mutating func didInsert(_ inserted: InsertionSuccess) { id = inserted.rowID }
}

struct TechFingerprint: Codable, Identifiable, Hashable, FetchableRecord, MutablePersistableRecord {
    var id: Int64?
    var investigationId: Int64
    var host: String
    var technology: String
    var category: String?
    var version: String?
    var evidence: String?
    var sourceId: Int64

    static let databaseTableName = "tech_fingerprint"
    mutating func didInsert(_ inserted: InsertionSuccess) { id = inserted.rowID }
}

// MARK: - Synthesis (RAG)

struct EmbeddingChunk: Codable, Identifiable, Hashable, FetchableRecord, MutablePersistableRecord {
    var id: Int64?
    var investigationId: Int64
    var sourceId: Int64
    var chunkText: String
    /// Raw little-endian Float32 vector.
    var vector: Data

    static let databaseTableName = "embedding"
    mutating func didInsert(_ inserted: InsertionSuccess) { id = inserted.rowID }
}

// MARK: - Timeline

struct TimelineEvent: Codable, Identifiable, Hashable, FetchableRecord, MutablePersistableRecord {
    var id: Int64?
    var investigationId: Int64
    var timestamp: Date
    var kind: String
    var summary: String
    var entityId: Int64?
    var sourceId: Int64?

    static let databaseTableName = "timeline_event"
    mutating func didInsert(_ inserted: InsertionSuccess) { id = inserted.rowID }
}
