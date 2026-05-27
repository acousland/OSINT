import Foundation
import PDFKit
import CoreXLSX
import ZIPFoundation

/// Extracts text + metadata from harvested documents. PDF via PDFKit, XLSX via CoreXLSX,
/// DOCX by unzipping the OOXML package and stripping `word/document.xml` (robust — a .docx
/// is just a zip of XML, so we avoid depending on a less-maintained DOCX library).
enum DocumentExtractor {
    struct Result { var text: String; var metadata: [String: String] }

    static func extract(data: Data, type: String, filename: String) -> Result {
        switch type.lowercased() {
        case "pdf": return extractPDF(data)
        case "xlsx": return extractXLSX(data)
        case "docx": return extractDOCX(data)
        default: return Result(text: "", metadata: [:])
        }
    }

    /// Classify a URL into a supported document type, or nil if it's not a document.
    static func documentType(for url: String, contentType: String?) -> String? {
        let lower = url.lowercased()
        if lower.hasSuffix(".pdf") || (contentType?.contains("pdf") ?? false) { return "pdf" }
        if lower.hasSuffix(".xlsx") || (contentType?.contains("spreadsheetml") ?? false) { return "xlsx" }
        if lower.hasSuffix(".docx") || (contentType?.contains("wordprocessingml") ?? false) { return "docx" }
        return nil
    }

    // MARK: PDF

    private static func extractPDF(_ data: Data) -> Result {
        guard let doc = PDFDocument(data: data) else { return Result(text: "", metadata: [:]) }
        var meta: [String: String] = [:]
        if let attrs = doc.documentAttributes {
            for (k, v) in attrs {
                if let key = k as? String, let val = v as? String { meta[key] = val }
            }
        }
        meta["PageCount"] = String(doc.pageCount)
        return Result(text: doc.string ?? "", metadata: meta)
    }

    // MARK: XLSX

    private static func extractXLSX(_ data: Data) -> Result {
        let tmp = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString + ".xlsx")
        defer { try? FileManager.default.removeItem(at: tmp) }
        do {
            try data.write(to: tmp)
            guard let file = XLSXFile(filepath: tmp.path) else { return Result(text: "", metadata: [:]) }
            let shared = try file.parseSharedStrings()
            var lines: [String] = []
            for path in try file.parseWorksheetPaths() {
                let ws = try file.parseWorksheet(at: path)
                for row in ws.data?.rows ?? [] {
                    let cells = row.cells.compactMap { cell -> String? in
                        if let s = shared, let str = cell.stringValue(s) { return str }
                        return cell.value
                    }
                    if !cells.isEmpty { lines.append(cells.joined(separator: "\t")) }
                }
            }
            return Result(text: lines.joined(separator: "\n"),
                          metadata: ["Sheets": String(try file.parseWorksheetPaths().count)])
        } catch {
            return Result(text: "", metadata: ["error": "\(error)"])
        }
    }

    // MARK: DOCX (unzip + strip word/document.xml)

    private static func extractDOCX(_ data: Data) -> Result {
        do {
            let archive = try Archive(data: data, accessMode: .read)
            guard let entry = archive["word/document.xml"] else { return Result(text: "", metadata: [:]) }
            var xml = Data()
            _ = try archive.extract(entry) { xml.append($0) }
            let raw = String(data: xml, encoding: .utf8) ?? ""
            // Convert paragraph/break tags to newlines, then strip all remaining tags.
            let withBreaks = raw
                .replacingOccurrences(of: "</w:p>", with: "\n")
                .replacingOccurrences(of: "<w:br/>", with: "\n")
            let text = withBreaks.replacingOccurrences(
                of: "<[^>]+>", with: "", options: .regularExpression)
            return Result(text: decodeEntities(text), metadata: [:])
        } catch {
            return Result(text: "", metadata: ["error": "\(error)"])
        }
    }

    private static func decodeEntities(_ s: String) -> String {
        s.replacingOccurrences(of: "&amp;", with: "&")
            .replacingOccurrences(of: "&lt;", with: "<")
            .replacingOccurrences(of: "&gt;", with: ">")
            .replacingOccurrences(of: "&quot;", with: "\"")
            .replacingOccurrences(of: "&apos;", with: "'")
    }
}
