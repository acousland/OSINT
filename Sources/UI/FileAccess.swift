import AppKit

/// Opens / reveals files the app produced in its sandbox container. NSWorkspace handles
/// the sandbox handoff so Preview (etc.) and Finder can access these files.
enum FileAccess {
    /// Open a file with its default application (e.g. a PDF in Preview).
    static func open(_ path: String?) {
        guard let path, !path.isEmpty else { return }
        NSWorkspace.shared.open(URL(fileURLWithPath: path))
    }

    /// Reveal a file in Finder, selected.
    static func reveal(_ path: String?) {
        guard let path, !path.isEmpty else { return }
        NSWorkspace.shared.activateFileViewerSelecting([URL(fileURLWithPath: path)])
    }

    /// Open a folder in Finder.
    static func openFolder(_ url: URL) {
        NSWorkspace.shared.open(url)
    }
}
