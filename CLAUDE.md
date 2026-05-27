# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A native macOS corporate-intelligence app (Swift + SwiftUI), rewriting the original
Python crawler. It collects across three domains plus a synthesis layer:
1. **Corporate identity** — Australian Business Register (ABN Lookup).
2. **Web contents** — same-domain crawl, document harvest (PDF/XLSX/DOCX), page→PDF.
3. **Technology profiling / recon** — DNS, certificate-transparency subdomains,
   fingerprinting (passive); subdomain brute force, TCP-connect port scan (active, gated).
4. **Synthesis** — OpenAI-backed executive dossier + RAG Q&A over collected text.

This was rewritten from an earlier Python crawler; see `docs/REWRITE_PLAN.md` for the
design history.

## Commands

**Generate the Xcode project** (project is git-ignored; `project.yml` is the source of truth):
```bash
xcodegen generate
```

**Build:**
```bash
xcodebuild -project OSIntel.xcodeproj -scheme OSIntel -destination 'platform=macOS' -derivedDataPath .build build
```

**Run:** open `OSIntel.xcodeproj` in Xcode and run, or launch the built
`.build/Build/Products/Debug/OSIntel.app`.

Dependencies are SwiftPM packages declared in `project.yml` (SwiftSoup, GRDB, CoreXLSX,
ZIPFoundation) and resolve automatically on first build (needs network).

## Architecture

Five layers in one sandboxed process, communicating via Swift concurrency:

- **UI** (`Sources/UI`, `Sources/App`) — SwiftUI `NavigationSplitView`; `AppState`
  (`@MainActor ObservableObject`) owns the `Store` and drives runs, streaming
  `RunEvent`s into a live log.
- **Coordinator** (`Sources/Core/Coordinator.swift`) — an `actor` that sequences
  collectors per `RunPlan`, enforces the passive/active gate, and returns an
  `AsyncStream<RunEvent>`. **Active collectors run only when `RunPlan.activeConsent` is
  true** (set via the `ConsentSheet`).
- **Collectors** (`Sources/Collectors`) — `ABRCollector`, `WebCollector`,
  `ReconCollector`, `SynthesisEngine`, plus helpers (`PDFRenderer`, `DocumentExtractor`,
  `Fingerprinter`, `PortScanner`, `DoHClient`, `OpenAIClient`). Each conforms to
  `PassiveCollector` or `ActiveCollector` (marker protocols in `Sources/Core/RunEvent.swift`).
- **Store** (`Sources/Storage`) — an `actor` wrapping a GRDB `DatabaseQueue`; single
  serialized write path. Schema + migrations in `Database.swift`, records in
  `Sources/Models/Models.swift`. **Every fact/record references a `Source` row** for
  provenance.
- **Secrets** (`Sources/Core/Secrets.swift`) — ABR GUID and OpenAI key live in Keychain
  only, never on disk or in the DB.

### Key constraints to respect

- **WKWebView PDF rendering** (`PDFRenderer`) is `@MainActor` and renders through a single
  off-screen window — renders are serialized, not parallel. This is the highest-risk area
  (page-sizing quirks); a blank PDF means revisit the settle delay / `WKPDFConfiguration`.
- **Port scanning is TCP-connect only** (`NWConnection`). Raw-socket SYN/ICMP scans are
  impossible under the App Sandbox and are out of scope.
- **DNS uses DNS-over-HTTPS** (`DoHClient`) rather than a native resolver dependency.
- **OpenAI is called directly over `URLSession`** (`OpenAIClient`), not via an SDK.
- **Fingerprint ruleset is GPL-3.0** when the full dataset is bundled — see
  `THIRD_PARTY_NOTICES.md`.

## Output

The SQLite database and harvested files live in
`~/Library/Application Support/OSIntel/` (sandboxed container). Exports (dossier
PDF/Markdown, raw JSON) are written via `NSSavePanel` to user-chosen locations.
