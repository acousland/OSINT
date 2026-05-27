import SwiftUI
import AppKit

/// Exports an investigation's findings. Raw data as JSON, the dossier as Markdown or PDF.
/// All writes go through NSSavePanel (sandbox-friendly user-selected URLs).
enum ExportService {
    @MainActor
    static func saveText(_ text: String, suggestedName: String, type: String) {
        let panel = NSSavePanel()
        panel.nameFieldStringValue = suggestedName
        panel.canCreateDirectories = true
        guard panel.runModal() == .OK, let url = panel.url else { return }
        try? text.data(using: .utf8)?.write(to: url)
    }

    @MainActor
    static func saveDossierPDF(markdownHTML html: String, suggestedName: String) async {
        let panel = NSSavePanel()
        panel.nameFieldStringValue = suggestedName
        guard panel.runModal() == .OK, let url = panel.url else { return }
        let renderer = PDFRenderer()
        try? await renderer.renderHTML(html, to: url)
    }

    /// Assemble a JSON export of the whole investigation from the store.
    static func buildJSON(store: Store, investigation: Investigation) async -> String {
        guard let id = investigation.id else { return "{}" }
        var root: [String: Any] = [
            "name": investigation.name,
            "target": investigation.target,
        ]
        root["entities"] = (try? await store.entities(investigationId: id))?.map {
            ["type": $0.type, "name": $0.name, "attributes": $0.attributes]
        } ?? []
        root["facts"] = (try? await store.facts(investigationId: id))?.map {
            ["key": $0.key, "value": $0.value, "confidence": $0.confidence]
        } ?? []
        root["subdomains"] = (try? await store.subdomains(investigationId: id))?.map { $0.host } ?? []
        root["openPorts"] = (try? await store.openPorts(investigationId: id))?.map {
            ["port": $0.port, "service": $0.service ?? ""]
        } ?? []
        root["technologies"] = (try? await store.fingerprints(investigationId: id))?.map {
            ["technology": $0.technology, "category": $0.category ?? "", "version": $0.version ?? ""]
        } ?? []
        root["dns"] = (try? await store.dnsRecords(investigationId: id))?.map {
            ["type": $0.type, "value": $0.value]
        } ?? []
        guard let data = try? JSONSerialization.data(withJSONObject: root, options: [.prettyPrinted, .sortedKeys]),
              let s = String(data: data, encoding: .utf8) else { return "{}" }
        return s
    }

    /// Wrap markdown text in minimal HTML for PDF rendering.
    static func htmlWrap(_ markdown: String, title: String) -> String {
        let escaped = markdown
            .replacingOccurrences(of: "&", with: "&amp;")
            .replacingOccurrences(of: "<", with: "&lt;")
        return """
        <html><head><meta charset="utf-8"><style>
        body { font-family: -apple-system, Helvetica, sans-serif; padding: 40px; line-height: 1.5; }
        pre { white-space: pre-wrap; font-family: ui-monospace, monospace; }
        h1 { border-bottom: 2px solid #333; }
        </style></head><body><h1>\(title)</h1><pre>\(escaped)</pre></body></html>
        """
    }
}
