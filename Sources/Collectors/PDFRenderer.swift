import Foundation
import WebKit

enum PDFRenderError: LocalizedError {
    case loadTimeout
    var errorDescription: String? { "Page load timed out" }
}

/// Renders a web page to PDF using native WebKit (`WKWebView.createPDF`), replacing
/// wkhtmltopdf. One renderer owns one off-screen WKWebView and renders one page at a
/// time, but many renderers run concurrently (see `PDFRenderPool`) — the main-actor
/// requirement only governs the API calls, while the actual page loads happen in
/// WebKit content processes and overlap while each render is suspended awaiting its load.
///
/// KNOWN RISK: `createPDF` has documented page-sizing quirks. We render at a fixed
/// viewport width and allow a short settle delay after navigation finishes. If a page
/// returns a blank/zero-size PDF, the settle delay is the first thing to revisit.
@MainActor
final class PDFRenderer: NSObject, WKNavigationDelegate {
    private var webView: WKWebView?
    private var window: NSWindow?
    private var continuation: CheckedContinuation<Void, Error>?
    private var timeoutWork: DispatchWorkItem?
    private let viewport = NSRect(x: 0, y: 0, width: 1024, height: 1366)
    private let settleDelay: TimeInterval
    private let loadTimeout: TimeInterval

    /// - Parameters:
    ///   - settleDelay: pause after `didFinish` to let late JS/images settle (default 0.6s).
    ///   - loadTimeout: abort a page that never finishes loading (default 20s).
    init(settleDelay: TimeInterval = 0.6, loadTimeout: TimeInterval = 20) {
        self.settleDelay = settleDelay
        self.loadTimeout = loadTimeout
        super.init()
    }

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

    /// Load `url`, wait for navigation (or timeout) + settle, then write a PDF.
    func render(url: URL, to outputURL: URL) async throws {
        let wv = ensureWebView()
        try await load(wv) { wv.load(URLRequest(url: url)) }
        try? await Task.sleep(nanoseconds: UInt64(settleDelay * 1_000_000_000))
        let pdfData = try await createPDF(wv)
        try pdfData.write(to: outputURL)
    }

    /// Render an HTML string (e.g. a generated dossier) to PDF.
    func renderHTML(_ html: String, to outputURL: URL) async throws {
        let wv = ensureWebView()
        try await load(wv) { wv.loadHTMLString(html, baseURL: nil) }
        try? await Task.sleep(nanoseconds: UInt64(settleDelay * 1_000_000_000))
        let pdfData = try await createPDF(wv)
        try pdfData.write(to: outputURL)
    }

    /// Begin a navigation and suspend until `didFinish`/`didFail` or the load timeout.
    private func load(_ wv: WKWebView, start: () -> Void) async throws {
        try await withCheckedThrowingContinuation { (c: CheckedContinuation<Void, Error>) in
            self.continuation = c
            let work = DispatchWorkItem { [weak self, weak wv] in
                guard let self, let cont = self.continuation else { return }
                self.continuation = nil
                wv?.stopLoading()
                cont.resume(throwing: PDFRenderError.loadTimeout)
            }
            self.timeoutWork = work
            DispatchQueue.main.asyncAfter(deadline: .now() + loadTimeout, execute: work)
            start()
        }
    }

    private func finishLoad(_ result: Result<Void, Error>) {
        timeoutWork?.cancel()
        timeoutWork = nil
        guard let cont = continuation else { return }
        continuation = nil
        cont.resume(with: result)
    }

    private func createPDF(_ wv: WKWebView) async throws -> Data {
        try await withCheckedThrowingContinuation { (c: CheckedContinuation<Data, Error>) in
            wv.createPDF(configuration: WKPDFConfiguration()) { result in
                switch result {
                case .success(let data): c.resume(returning: data)
                case .failure(let error): c.resume(throwing: error)
                }
            }
        }
    }

    // MARK: WKNavigationDelegate

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        finishLoad(.success(()))
    }
    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        finishLoad(.failure(error))
    }
    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        finishLoad(.failure(error))
    }
}
