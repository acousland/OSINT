import Foundation
import GRDB

/// Owns the SQLite file and schema migrations. The on-disk database lives in the
/// app's Application Support container (sandbox-friendly).
enum AppDatabase {
    static func makeQueue() throws -> DatabaseQueue {
        let support = try FileManager.default.url(
            for: .applicationSupportDirectory, in: .userDomainMask,
            appropriateFor: nil, create: true)
        let dir = support.appendingPathComponent("OSIntel", isDirectory: true)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let dbURL = dir.appendingPathComponent("osintel.sqlite")
        let queue = try DatabaseQueue(path: dbURL.path)
        try migrator.migrate(queue)
        return queue
    }

    /// Directory where rendered PDFs and harvested documents are written.
    static func filesDirectory(investigationId: Int64) throws -> URL {
        let support = try FileManager.default.url(
            for: .applicationSupportDirectory, in: .userDomainMask,
            appropriateFor: nil, create: true)
        let dir = support
            .appendingPathComponent("OSIntel", isDirectory: true)
            .appendingPathComponent("files", isDirectory: true)
            .appendingPathComponent("\(investigationId)", isDirectory: true)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    private static var migrator: DatabaseMigrator {
        var migrator = DatabaseMigrator()
        migrator.registerMigration("v1") { db in
            try db.create(table: "investigation") { t in
                t.autoIncrementedPrimaryKey("id")
                t.column("name", .text).notNull()
                t.column("target", .text).notNull()
                t.column("createdAt", .datetime).notNull()
                t.column("activeReconConsent", .boolean).notNull().defaults(to: false)
            }
            try db.create(table: "source") { t in
                t.autoIncrementedPrimaryKey("id")
                t.belongsTo("investigation", onDelete: .cascade).notNull()
                t.column("kind", .text).notNull()
                t.column("ref", .text).notNull()
                t.column("collector", .text).notNull()
                t.column("httpStatus", .integer)
                t.column("fetchedAt", .datetime).notNull()
            }
            try db.create(table: "entity") { t in
                t.autoIncrementedPrimaryKey("id")
                t.belongsTo("investigation", onDelete: .cascade).notNull()
                t.column("type", .text).notNull()
                t.column("name", .text).notNull()
                t.column("attributes", .text).notNull().defaults(to: "{}")
                t.column("createdAt", .datetime).notNull()
            }
            try db.create(table: "entity_edge") { t in
                t.autoIncrementedPrimaryKey("id")
                t.belongsTo("investigation", onDelete: .cascade).notNull()
                t.column("fromEntityId", .integer).notNull()
                t.column("toEntityId", .integer).notNull()
                t.column("relationship", .text).notNull()
                t.column("weight", .double).notNull().defaults(to: 1.0)
            }
            try db.create(table: "fact") { t in
                t.autoIncrementedPrimaryKey("id")
                t.belongsTo("investigation", onDelete: .cascade).notNull()
                t.column("entityId", .integer)
                t.column("key", .text).notNull()
                t.column("value", .text).notNull()
                t.column("confidence", .double).notNull().defaults(to: 1.0)
                t.column("sourceId", .integer).notNull()
            }
            try db.create(table: "crawl_page") { t in
                t.autoIncrementedPrimaryKey("id")
                t.belongsTo("investigation", onDelete: .cascade).notNull()
                t.column("url", .text).notNull()
                t.column("title", .text)
                t.column("statusCode", .integer)
                t.column("contentType", .text)
                t.column("fetchedAt", .datetime).notNull()
                t.column("sourceId", .integer).notNull()
            }
            try db.create(table: "document") { t in
                t.autoIncrementedPrimaryKey("id")
                t.belongsTo("investigation", onDelete: .cascade).notNull()
                t.column("url", .text).notNull()
                t.column("localPath", .text)
                t.column("type", .text).notNull()
                t.column("extractedText", .text)
                t.column("metadata", .text).notNull().defaults(to: "{}")
                t.column("sourceId", .integer).notNull()
            }
            try db.create(table: "pdf_render") { t in
                t.autoIncrementedPrimaryKey("id")
                t.belongsTo("investigation", onDelete: .cascade).notNull()
                t.column("url", .text).notNull()
                t.column("localPath", .text).notNull()
                t.column("sourceId", .integer).notNull()
            }
            try db.create(table: "dns_record") { t in
                t.autoIncrementedPrimaryKey("id")
                t.belongsTo("investigation", onDelete: .cascade).notNull()
                t.column("name", .text).notNull()
                t.column("type", .text).notNull()
                t.column("value", .text).notNull()
                t.column("sourceId", .integer).notNull()
            }
            try db.create(table: "subdomain") { t in
                t.autoIncrementedPrimaryKey("id")
                t.belongsTo("investigation", onDelete: .cascade).notNull()
                t.column("host", .text).notNull()
                t.column("discoveredVia", .text).notNull()
                t.column("resolved", .boolean).notNull().defaults(to: false)
                t.column("sourceId", .integer).notNull()
            }
            try db.create(table: "open_port") { t in
                t.autoIncrementedPrimaryKey("id")
                t.belongsTo("investigation", onDelete: .cascade).notNull()
                t.column("host", .text).notNull()
                t.column("port", .integer).notNull()
                t.column("service", .text)
                t.column("sourceId", .integer).notNull()
            }
            try db.create(table: "tech_fingerprint") { t in
                t.autoIncrementedPrimaryKey("id")
                t.belongsTo("investigation", onDelete: .cascade).notNull()
                t.column("host", .text).notNull()
                t.column("technology", .text).notNull()
                t.column("category", .text)
                t.column("version", .text)
                t.column("evidence", .text)
                t.column("sourceId", .integer).notNull()
            }
            try db.create(table: "embedding") { t in
                t.autoIncrementedPrimaryKey("id")
                t.belongsTo("investigation", onDelete: .cascade).notNull()
                t.column("sourceId", .integer).notNull()
                t.column("chunkText", .text).notNull()
                t.column("vector", .blob).notNull()
            }
            try db.create(table: "timeline_event") { t in
                t.autoIncrementedPrimaryKey("id")
                t.belongsTo("investigation", onDelete: .cascade).notNull()
                t.column("timestamp", .datetime).notNull()
                t.column("kind", .text).notNull()
                t.column("summary", .text).notNull()
                t.column("entityId", .integer)
                t.column("sourceId", .integer)
            }
        }
        // v2: store the visible body text of crawled pages so the synthesis layer has
        // business content (not just technical metadata) to reason over.
        migrator.registerMigration("v2-pagetext") { db in
            try db.alter(table: "crawl_page") { t in
                t.add(column: "textContent", .text)
            }
        }
        return migrator
    }
}
