# Improvements Log

A running log of notable changes to OSIntel. Newest first.

## 2026-05-27

### Synthesis
- **Enterprise-architecture consulting dossier.** Reframed the dossier from a
  technology-only summary into a consulting/sales briefing covering business *and*
  technology: Executive Summary, Company Overview, Products/Services, Market Positioning,
  Technology & Architecture Profile, **PESTLE**, **SWOT** (business + tech integrated),
  EA Observations & Opportunities, Commercial Angles, and Confidence & Gaps.
- **Business corpus.** The crawler now captures visible page body text (`textContent`,
  migration v2), which feeds both the dossier and the RAG Q&A — previously only document
  text was available, so the model had little business context.
- **Model: `gpt-5.5`** for the dossier (verified available in the Chat Completions API,
  snapshot `gpt-5.5-2026-04-23`). Q&A remains on `gpt-4o-mini`. `temperature` is now
  optional and omitted on the dossier call (newer models accept only the default).

### Performance
- **Faster PDF rendering.** Pages now render through a pool of up to 4 off-screen
  `WKWebView`s instead of one serial view, so loads overlap and the per-page settle delays
  no longer sum. Settle delay cut 1.2s → 0.6s (configurable). Added a 20s load timeout —
  previously a hung page could block the entire render queue indefinitely.

### Usability
- **View collected files.** The Web tab now has a Pages / PDFs / Documents switcher, lists
  rendered PDFs (previously invisible in the UI), and offers Open / Reveal-in-Finder
  actions plus an Open Output Folder button.
- **App icon.** Added a generated icon (node-graph + magnifying glass) via
  `tools/make_icon.swift` and an asset catalog.

### Distribution
- **GitHub release.** Rolling `latest` release with downloadable binaries; `release.sh`
  builds, packages, moves the tag, and publishes.
- **DMG installer.** `make_dmg.sh` builds a standard drag-to-Applications `.dmg` (app +
  Applications shortcut + custom background). Published alongside the zip.
- **`install.sh`** builds Release and installs to `/Applications`.

### Hygiene
- Removed the superseded Python tool (`mapStructure.py`, `scrape.py`, `app.py`,
  `OSintel.py`, `requirements.txt`, `run.sh`).
- Removed unused `WaybackClient`; converted `ReconCollector` to the `withPermit` limiter
  pattern; cleared compiler warnings (redundant `try`).
- Stopped tracking `.DS_Store`; rewrote `README.md` for the Swift app; trimmed stale
  references in `CLAUDE.md`.

### Concurrency (correctness)
- Fixed a data race in the crawler (concurrent tasks had mutated shared arrays via sink
  closures); tasks now return results aggregated serially.
- Parallelised document harvest, DNS record-type queries, and the passive recon stages.
- Added `ConcurrencyLimiter.withPermit` for deterministic permit release.

## Initial build

- Native macOS rewrite (Swift + SwiftUI) of the Python crawler: corporate identity (ABR),
  web crawl/harvest/PDF, DNS/CT/fingerprint + gated active recon (subdomain brute force,
  TCP-connect port scan), OpenAI dossier + RAG, GRDB storage, entity graph, timeline,
  exports. See `docs/REWRITE_PLAN.md`.
