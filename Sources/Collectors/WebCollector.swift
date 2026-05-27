import Foundation
import SwiftSoup

/// Recursive same-domain crawler + document harvester + page→PDF renderer. Replaces the
/// Python map/scrape pair, but unified: one pass discovers pages, harvests documents, and
/// (optionally) renders pages to PDF. Polite (rate-limited, identifiable UA, bounded fan-out).
struct WebCollector: PassiveCollector {
    let name = "WebCollector"
    let store: Store
    let investigationId: Int64
    let http = HTTPClient()

    private let rate = RateLimiter(requestsPerSecond: 5)
    private let fetchLimiter = ConcurrencyLimiter(limit: 6)

    func run(rootURL: String, maxDepth: Int, renderPDFs: Bool, harvestDocs: Bool,
             emit: @Sendable (RunEvent) -> Void) async throws -> String {
        guard let root = normalizedURL(rootURL), let domain = root.host else {
            throw HTTPError.invalidURL(rootURL)
        }

        var visited = Set<String>()
        var frontier = [root.absoluteString]
        var pageURLs: [String] = []
        var documentURLs = Set<String>()

        for depth in 0...max(0, maxDepth) {
            if Task.isCancelled { break }
            let level = frontier.filter { !visited.contains($0) }
            if level.isEmpty { break }
            level.forEach { visited.insert($0) }
            emit(.progress(stage: "Web", message: "Depth \(depth): \(level.count) page(s)",
                           done: visited.count, total: nil))

            // Fetch every page at this depth concurrently (bounded by fetchLimiter).
            // Each task returns its own results; aggregation happens serially in the
            // for-await loop on this task, so no shared mutable state is raced.
            var discovered = Set<String>()
            await withTaskGroup(of: PageOutcome.self) { group in
                for urlStr in level {
                    group.addTask {
                        await self.fetchLimiter.withPermit {
                            await self.rate.wait()
                            return await self.processPage(urlStr, domain: domain)
                        }
                    }
                }
                for await outcome in group {
                    if outcome.isPage { pageURLs.append(outcome.url) }
                    documentURLs.formUnion(outcome.documents)
                    discovered.formUnion(outcome.links)
                }
            }
            frontier = Array(discovered).filter { !visited.contains($0) }
        }

        // Harvest documents concurrently (bounded + rate-limited). docCount is only
        // touched on this task inside the serial for-await loop.
        var docCount = 0
        if harvestDocs && !documentURLs.isEmpty {
            let total = documentURLs.count
            await withTaskGroup(of: Bool.self) { group in
                for docURL in documentURLs {
                    group.addTask {
                        await self.fetchLimiter.withPermit {
                            await self.rate.wait()
                            return await self.harvest(docURL)
                        }
                    }
                }
                for await ok in group where ok {
                    docCount += 1
                    emit(.progress(stage: "Web", message: "Harvested \(docCount) document(s)",
                                   done: docCount, total: total))
                }
            }
        }

        // Render PDFs (serialized through the single off-screen web view).
        var pdfCount = 0
        if renderPDFs {
            let renderer = await PDFRenderer()
            let dir = try AppDatabase.filesDirectory(investigationId: investigationId)
            for pageURL in Set(pageURLs) {
                if Task.isCancelled { break }
                guard let url = URL(string: pageURL) else { continue }
                let outName = pdfFilename(for: url)
                let outURL = dir.appendingPathComponent(outName)
                do {
                    try await renderer.render(url: url, to: outURL)
                    let src = try await store.recordSource(Source(
                        id: nil, investigationId: investigationId, kind: "web",
                        ref: pageURL, collector: name, httpStatus: 200, fetchedAt: Date()))
                    _ = try await store.insert(PdfRender(
                        id: nil, investigationId: investigationId, url: pageURL,
                        localPath: outURL.path, sourceId: src))
                    pdfCount += 1
                } catch {
                    emit(.progress(stage: "Web", message: "PDF failed for \(url.lastPathComponent)",
                                   done: pdfCount, total: pageURLs.count))
                }
                emit(.progress(stage: "Web", message: "Rendered \(pdfCount) PDF(s)",
                               done: pdfCount, total: pageURLs.count))
            }
        }

        // Register the domain as an entity.
        let src = try await store.recordSource(Source(
            id: nil, investigationId: investigationId, kind: "web",
            ref: root.absoluteString, collector: name, httpStatus: 200, fetchedAt: Date()))
        _ = try await store.insert(Entity(
            id: nil, investigationId: investigationId, type: EntityType.domain.rawValue,
            name: domain, attributes: "{}", createdAt: Date()))
        _ = try await store.insert(TimelineEvent(
            id: nil, investigationId: investigationId, timestamp: Date(), kind: "web",
            summary: "Crawled \(domain): \(pageURLs.count) pages, \(docCount) docs, \(pdfCount) PDFs",
            entityId: nil, sourceId: src))

        return "Crawled \(visited.count) URLs · \(pageURLs.count) pages · \(docCount) documents · \(pdfCount) PDFs"
    }

    // MARK: Per-page processing

    /// Result of fetching one URL. Returned (not written to shared state) so the crawl
    /// fan-out stays race-free.
    struct PageOutcome: Sendable {
        let url: String
        let isPage: Bool
        let links: [String]
        let documents: [String]
        static func empty(_ url: String) -> PageOutcome {
            PageOutcome(url: url, isPage: false, links: [], documents: [])
        }
    }

    private func processPage(_ urlStr: String, domain: String) async -> PageOutcome {
        guard let url = URL(string: urlStr) else { return .empty(urlStr) }
        guard let (data, status) = try? await http.get(url) else { return .empty(urlStr) }
        let contentType = (try? await http.contentType(url)) ?? nil

        // Document link → queue for harvest, don't parse as HTML.
        if DocumentExtractor.documentType(for: urlStr, contentType: contentType) != nil {
            return PageOutcome(url: urlStr, isPage: false, links: [], documents: [urlStr])
        }
        guard let htmlStr = String(data: data, encoding: .utf8) else { return .empty(urlStr) }

        var title: String?
        var links: [String] = []
        var docs: [String] = []
        do {
            let doc = try SwiftSoup.parse(htmlStr, urlStr)
            title = try? doc.title()
            for el in try doc.select("a[href]") {
                guard let abs = try? el.attr("abs:href"), !abs.isEmpty else { continue }
                guard let linkURL = URL(string: abs), linkURL.host == domain else { continue }
                let clean = abs.components(separatedBy: "#").first ?? abs
                if DocumentExtractor.documentType(for: clean, contentType: nil) != nil {
                    docs.append(clean)
                } else if clean.hasPrefix("http") {
                    links.append(clean)
                }
            }
        } catch { /* unparseable HTML — still record the page below */ }

        if let src = try? await store.recordSource(Source(
            id: nil, investigationId: investigationId, kind: "web",
            ref: urlStr, collector: name, httpStatus: status, fetchedAt: Date())) {
            _ = try? await store.insert(CrawlPage(
                id: nil, investigationId: investigationId, url: urlStr, title: title,
                statusCode: status, contentType: contentType, fetchedAt: Date(), sourceId: src))
        }
        return PageOutcome(url: urlStr, isPage: true, links: links, documents: docs)
    }

    // MARK: Document harvest

    private func harvest(_ urlStr: String) async -> Bool {
        guard let url = URL(string: urlStr),
              let (data, status) = try? await http.get(url), (200..<300).contains(status)
        else { return false }
        let ctype = (try? await http.contentType(url)) ?? nil
        guard let type = DocumentExtractor.documentType(for: urlStr, contentType: ctype) else { return false }

        let extracted = DocumentExtractor.extract(data: data, type: type, filename: url.lastPathComponent)
        let metaData = (try? JSONSerialization.data(withJSONObject: extracted.metadata)) ?? Data("{}".utf8)

        // Save the raw file alongside extracted text.
        var localPath: String?
        if let dir = try? AppDatabase.filesDirectory(investigationId: investigationId) {
            let out = dir.appendingPathComponent(UUID().uuidString + "-" + url.lastPathComponent)
            if (try? data.write(to: out)) != nil { localPath = out.path }
        }

        guard let src = try? await store.recordSource(Source(
            id: nil, investigationId: investigationId, kind: "file",
            ref: urlStr, collector: name, httpStatus: status, fetchedAt: Date())) else { return false }
        _ = try? await store.insert(HarvestedDocument(
            id: nil, investigationId: investigationId, url: urlStr, localPath: localPath,
            type: type, extractedText: extracted.text,
            metadata: String(data: metaData, encoding: .utf8) ?? "{}", sourceId: src))
        return true
    }

    // MARK: Helpers

    private func normalizedURL(_ s: String) -> URL? {
        if let u = URL(string: s), u.scheme != nil { return u }
        return URL(string: "https://\(s)")
    }

    private func pdfFilename(for url: URL) -> String {
        let path = url.path.replacingOccurrences(of: "/", with: "_")
        let base = path.isEmpty || path == "_" ? "index" : path
        return "\(base).pdf"
    }
}
