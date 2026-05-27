# OSINT → Native macOS Corporate Intelligence App — Rewrite Plan

## Context

The current tool is a small Python project (Streamlit UI + recursive crawler using
`lxml`/`requests` + page→PDF via `pdfkit`/`wkhtmltopdf`). It covers a thin slice of one
domain (web content). We are **discarding the Python entirely** and rewriting as a native,
single-user **Swift + SwiftUI macOS app** that becomes a full corporate-intelligence tool
able to learn a lot about a company quickly.

Decisions locked with the user:
- **Single-user macOS app**, no server backend.
- **Full Swift rewrite** (not a Python sidecar). Page→PDF moves to native WebKit.
- **Active recon is approved at the AGGRESSIVE level**, but every active module must show
  an explicit warning/consent gate before running.
- **v1 collection domains:** (1) Corporate Identity, (2) Web Contents, (3) Technology
  Profiling / Active Recon — plus a **synthesis layer using the OpenAI API**.
- **Corporate identity = Australia only** via the ABR / ABN Lookup API. ASIC is paywalled
  and deferred.

## Architecture

Five layers in one sandboxed process, communicating via Swift concurrency (actor-isolated
store, `async`/`await` collectors, `AsyncStream` for live progress).

```
SwiftUI UI  ──AsyncStream──▶  Investigation Coordinator (actor)
                                 │ owns run lifecycle, passive/active gate,
                                 │ rate-limit budgets, cancellation
        ┌───────────┬───────────┼───────────┬────────────┐
   Identity      Web         Tech/Recon   Synthesis
   (ABR)         (crawl/PDF) (DNS/ports)  (OpenAI+RAG)
        └───────────┴───────────┴───────────┘
                       ▼ records + provenance
                 Store actor (GRDB + SQLite)
```

- **Collectors** expose `async` methods returning typed results + provenance; fan-out via
  `withThrowingTaskGroup` with bounded workers.
- **Store** is an `actor` wrapping GRDB — single serialized write path, async surface.
- **Coordinator** is an `actor` owning a run, token-bucket rate limits, the passive/active
  gate, and an `AsyncStream<RunEvent>` the UI subscribes to. Cancellation flows via
  structured concurrency.
- **Passive vs active** are distinct protocols (`PassiveCollector` / `ActiveCollector`).
  The Coordinator refuses to start any `ActiveCollector` until a per-run consent flag is
  set, surfaced as a blocking warning sheet.

## Verified libraries / APIs

| Concern | Choice | Notes |
|---|---|---|
| HTML parsing | [SwiftSoup](https://github.com/scinfu/SwiftSoup) | Pure-Swift Jsoup port, MIT, maintained. Replaces lxml. |
| HTTP | `URLSession` | Identifiable User-Agent, per-host limits. Drop fake-UA rotation. |
| Page → PDF | [`WKWebView.createPDF`](https://developer.apple.com/documentation/webkit/wkwebview/createpdf(configuration:completionhandler:)) | Off-screen hidden `NSWindow` + `didFinish` + settle delay. Main-actor bound → small render pool (1–3). Refs: [HTML2PDFRenderer](https://github.com/radianttap/HTML2PDFRenderer), [swift-webster](https://github.com/aaronland/swift-webster) (cautionary). |
| PDF metadata | PDFKit (`PDFDocument`) | Native. |
| XLSX | [CoreXLSX](https://github.com/CoreOffice/CoreXLSX) | Pure Swift, read-only. |
| DOCX | [DocReader](https://github.com/germanhl36/DocReader) — verify license/maint | Fallback: [ZIPFoundation](https://github.com/weichsel/ZIPFoundation) + parse `word/document.xml`. |
| Archive | Wayback Availability + CDX JSON APIs | Plain REST, no lib. |
| Corporate identity | [ABR ABN Lookup JSON](https://abr.business.gov.au/json/) | Free; **requires registration → auth GUID**; responses are **JSONP** (must unwrap `callback(...)`). |
| DNS | [apple/swift-async-dns-resolver](https://github.com/apple/swift-async-dns-resolver) | Official, async, A/AAAA/MX/TXT/SRV. |
| CT subdomains | [crt.sh JSON](https://crt.sh) | Slow/rate-limited → timeout+retry+cache. Passive. |
| Port scan | `Network` framework `NWConnection` | TCP-connect scan, bounded TaskGroup. Active. SwiftNIO considered & rejected (overkill). |
| Fingerprinting | [enthec/webappanalyzer](https://github.com/enthec/webappanalyzer) ruleset | **GPL-3.0 — licensing decision needed.** No native engine; we write the matcher. |
| OpenAI client | [MacPaw/OpenAI](https://github.com/MacPaw/OpenAI) | MIT, async, chat + embeddings. Key in Keychain. |
| RAG store | In-memory cosine over GRDB BLOBs (v1) | Upgrade to [sqlite-vec](https://github.com/asg017/sqlite-vec) / [SQLiteVec](https://github.com/jkrukowski/SQLiteVec) if corpus grows. |
| Persistence | [GRDB.swift](https://github.com/groue/GRDB.swift) | Relational + graph-like + FTS/vector in one SQLite file. SwiftData/Core Data rejected. |
| Timeline | Swift Charts | Native. |
| Graph viz | SwiftUI `Canvas` + simple force layout (v1) | No native graph component; WebKit+JS (Cytoscape/D3) as later option. |

## Data model (sketch)

`investigation` (target, settings, active-recon-consent) → owns everything below:
`entity` (person/company/domain/host/asset/technology), `entity_edge` (graph),
`fact` (key/value/confidence), `source` (url/api/file, fetched_at, collector, http_status),
generic `provenance` join (**every fact and edge references ≥1 source**),
`crawl_page`, `document`, `pdf_render`, `dns_record`, `subdomain`, `open_port`,
`tech_fingerprint`, `embedding` (vector BLOB), `timeline_event`.

## Phased build order (v1)

- **Phase 0 — Skeleton + storage spine.** App shell, sandbox entitlements, GRDB Store
  actor, core schema + migrations, Keychain secrets, provenance plumbing.
- **Phase 1 — Vertical slice (Identity).** ABR collector (JSONP, GUID from Keychain) →
  store entity+facts+source → Overview tab. Proves collector→store→UI loop.
- **Phase 2 — Web collector.** Same-domain crawler (URLSession + SwiftSoup, bounded
  TaskGroup, politeness, robots-aware) → pages + documents. **Early WKWebView PDF spike.**
  Document extraction (PDFKit/CoreXLSX/DocReader). Wayback enrichment.
- **Phase 3 — Recon.** Passive (crt.sh, DNS) first; then active behind consent gate
  (subdomain brute force, TCP-connect port scan, fingerprinting). Validate sandbox here.
- **Phase 4 — Synthesis.** Embeddings → in-memory cosine RAG → OpenAI dossier + Q&A with
  source citations.
- **Phase 5 — Graph, timeline, export.** Swift Charts timeline, Canvas graph,
  PDF/Markdown/JSON export.

Each phase ends usable; Phase 1 alone is a minimal working app.

## App Sandbox / entitlements

- `com.apple.security.network.client` — all outbound HTTP/DNS/TCP. **No port allowlist on
  outbound `connect()` → TCP-connect port scanning is feasible sandboxed** (verify early).
- Sandbox blocks raw sockets → **no SYN/stealth scans, no ICMP**. TCP-connect only.
- `com.apple.security.files.user-selected.read-write` for export (`NSSavePanel`).
- Keychain for OpenAI key + ABR GUID.
- Sandbox-compatible end to end **if we accept TCP-connect-only scanning** (fine for OSINT;
  raw-socket scanning would mean shipping un-sandboxed / no App Store).

## Key risks

1. **WKWebView headless PDF reliability (highest)** — sizing quirks, main-actor render cap.
   Mitigate with an early dedicated spike; fallbacks via `WKPDFConfiguration.rect` / paged.
2. **ABR access + JSONP** — registration lead time unknown; unwrap JSONP; cache.
3. **Port scanning under sandbox** — high confidence but verify empirically in Phase 3.
4. **Wappalyzer GPL-3.0** — bundling has copyleft implications; fetch-at-runtime or build a
   small in-house ruleset. **User decision.**
5. **DOCX parser maturity** — fallback to ZIPFoundation + manual XML parse.
6. **sqlite-vec extension friction** — ship in-memory cosine first.
7. **crt.sh reliability** — best-effort with retry/cache.

## Verification per phase

- Phase 1: ABR lookup of a known ABN returns and persists entity+source; visible in UI.
- Phase 2: crawl a small site → pages stored, ≥1 page rendered to a valid non-blank PDF,
  a discovered PDF/XLSX harvested with extracted metadata.
- Phase 3: DNS + crt.sh enumerate subdomains; consent gate blocks active until accepted;
  TCP-connect scan reports correct open/closed against a known host.
- Phase 4: dossier generated with inline source citations; Q&A answers cite stored sources.
- Phase 5: export produces valid PDF, Markdown, and JSON; timeline + graph render.
```
