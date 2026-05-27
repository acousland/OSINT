# OSIntel

A native macOS corporate-intelligence app for enterprise-architecture consulting. Point it
at an organisation and it builds a picture of both the **business** and the **technology
landscape**, then synthesises a consulting-grade briefing — including PESTLE, SWOT, and EA
engagement opportunities — that you can take into a meeting.

Built in Swift + SwiftUI. Single-user, runs entirely on your Mac.

> ⚠️ **Authorised use only.** The active-reconnaissance features (port scanning, subdomain
> brute force) send direct probes to the target and are gated behind an explicit consent
> prompt. Only run them against assets you are authorised to test.

## Download

Grab the latest build from the [Releases page](https://github.com/acousland/OSINT/releases/latest):

- **`OSIntel-Installer.dmg`** — open it and drag **OSIntel** onto **Applications**.
- `OSIntel-macos.zip` — the plain app bundle, for scripting.

The build is **ad-hoc signed (not notarized)**, so the first launch is blocked by Gatekeeper.
Right-click the app → **Open**, or clear the quarantine flag once:

```bash
xattr -dr com.apple.quarantine /Applications/OSIntel.app
```

## What it does

| Domain | Collected |
|---|---|
| **Corporate identity** | Australian Business Register (ABN/ACN lookup, name search) |
| **Web contents** | Same-domain crawl, page body text, document harvest (PDF/XLSX/DOCX), page→PDF rendering |
| **Technology / recon** | DNS, certificate-transparency subdomains, technology fingerprinting (passive); subdomain brute force, TCP-connect port scanning (active, consent-gated) |
| **Synthesis** | OpenAI-backed executive dossier (PESTLE + SWOT + EA opportunities) and RAG Q&A over everything collected, with source citations |

Every collected fact links back to a source record for provenance. Findings are organised
into an **Entity graph** and a **Timeline**, and exportable as PDF / Markdown / JSON.

## Setup

After installing, open **Settings (⌘,)** and add:

- **ABR auth GUID** — free, [register here](https://abr.business.gov.au/Tools/WebServices).
- **OpenAI API key** — for the dossier and Q&A.

Both are stored in the macOS Keychain, never on disk or in the database. Then create an
investigation, choose what to collect on the **Run** tab, and go.

## Building from source

Requires Xcode, [XcodeGen](https://github.com/yonaskolb/XcodeGen), and
[create-dmg](https://github.com/create-dmg/create-dmg) (for the installer).

```bash
brew install xcodegen create-dmg

# Generate the Xcode project (it is git-ignored; project.yml is the source of truth)
xcodegen generate

# Build + install to /Applications
./install.sh            # Release; use --debug for a debug build

# Build the drag-to-Applications DMG
./make_dmg.sh

# Build, package, and publish the rolling "latest" GitHub release
./release.sh
```

To open in Xcode directly: `xcodegen generate && open OSIntel.xcodeproj`.

## Architecture

Five layers in one sandboxed process, communicating via Swift concurrency. See
[`docs/REWRITE_PLAN.md`](docs/REWRITE_PLAN.md) for the design and
[`CLAUDE.md`](CLAUDE.md) for a contributor's map of the codebase.

- **UI** (`Sources/UI`, `Sources/App`) — SwiftUI `NavigationSplitView`; `AppState` drives runs.
- **Coordinator** (`Sources/Core`) — an actor sequencing collectors, enforcing the
  passive/active gate, streaming progress.
- **Collectors** (`Sources/Collectors`) — ABR, web crawl/PDF/docs, recon (DNS/CT/ports/
  fingerprint), and OpenAI synthesis + RAG.
- **Store** (`Sources/Storage`) — a GRDB-backed actor; single serialized write path.

## Licence & notices

See [`LICENSE`](LICENSE) and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). Note the
bundled technology-fingerprint ruleset path carries **GPL-3.0** obligations if the full
dataset is embedded.
