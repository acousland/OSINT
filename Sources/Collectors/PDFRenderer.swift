import Foundation
import WebKit

/// Renders a web page to PDF using native WebKit (`WKWebView.createPDF`), replacing
/// wkhtmltopdf. WKWebView is main-actor-bound and needs a real (hidden) window to lay
/// out reliably, so renders are serialized here through one off-screen web view.
///
/// KNOWN RISK: `createPDF` has documented page-sizing quirks. We render at a fixed
/// viewport width and allow a settle delay after navigation finishes. If a page returns
/// a blank/zero-size PDF, that's the issue to revisit first.
@MainActor
final class PDFRenderer: NSObject, WKNavigationDelegate {
    private var webView: WKWebView?
    private var window: NSWindow?
    private var continuation: CheckedContinuation<Void, Error>?
    private let viewport = NSRect(x: 0, y: 0, width: 1024, height: 1366)
    private let settleDelay: TimeInterval = 1.2

    private func ensureWebView() -> WKWebView {
        if let webView { return webView }
        let config = WKWebViewConfiguration()
        let wv = WKWebView(frame: viewport, configuration: config)
        wv.navigationDelegate = self
        // A hidden window gives WebKit a layout context; a detached view often renders blank.
        let win = NSWindow(contentRect: viewport, styleMask: [.borderless],
                           backing: .buffered, defer: false)
        win.contentView = wv
        win.alphaValue = 0
        win.orderOut(nil)
        self.webView = wv
        self.window = win
        return wv
    }

    /// Load `url`, wait for navigation + settle, then write a PDF to `outputURL`.
    func render(url: URL, to outputURL: URL) async throws {
        let wv = ensureWebView()
        try await withCheckedThrowingContinuation { (c: CheckedContinuation<Void, Error>) in
            self.continuation = c
            wv.load(URLRequest(url: url))
        }
        // Let late layout/async content settle before snapshotting.
        try? await Task.sleep(nanoseconds: UInt64(settleDelay * 1_000_000_000))
        let pdfData = try await createPDF(wv)
        try pdfData.write(to: outputURL)
    }

    /// Render an HTML string (e.g. a generated dossier) to PDF.
    func renderHTML(_ html: String, to outputURL: URL) async throws {
        let wv = ensureWebView()
        try await withCheckedThrowingContinuation { (c: CheckedContinuation<Void, Error>) in
            self.continuation = c
            wv.loadHTMLString(html, baseURL: nil)
        }
        try? await Task.sleep(nanoseconds: UInt64(settleDelay * 1_000_000_000))
        let pdfData = try await createPDF(wv)
        try pdfData.write(to: outputURL)
    }

    private func createPDF(_ wv: WKWebView) async throws -> Data {
        try await withCheckedThrowingContinuation { (c: CheckedContinuation<Data, Error>) in
            let config = WKPDFConfiguration()
            wv.createPDF(configuration: config) { result in
                switch result {
                case .success(let data): c.resume(returning: data)
                case .failure(let error): c.resume(throwing: error)
                }
            }
        }
    }

    // MARK: WKNavigationDelegate

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        continuation?.resume()
        continuation = nil
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        continuation?.resume(throwing: error)
        continuation = nil
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        continuation?.resume(throwing: error)
        continuation = nil
    }
}
