# Third-Party Notices

## Swift package dependencies (resolved via SwiftPM)

| Package | License | Use |
|---|---|---|
| [SwiftSoup](https://github.com/scinfu/SwiftSoup) | MIT | HTML parsing / link extraction |
| [GRDB.swift](https://github.com/groue/GRDB.swift) | MIT | SQLite persistence |
| [CoreXLSX](https://github.com/CoreOffice/CoreXLSX) | Apache-2.0 | XLSX text extraction |
| [ZIPFoundation](https://github.com/weichsel/ZIPFoundation) | MIT | DOCX (OOXML) unzip |

## Bundled data

### Technology fingerprint ruleset — **GPL-3.0**

`Sources/Resources/fingerprints.json` currently ships a small, original starter ruleset
in the Wappalyzer schema. The project owner has elected to bundle the full
[enthec/webappanalyzer](https://github.com/enthec/webappanalyzer) dataset, which is
licensed under **GPL-3.0**.

> ⚠️ **Copyleft implication:** once the full GPL-3.0 dataset is embedded and the app is
> distributed, the application as a whole is subject to GPL-3.0 obligations (source
> availability, license propagation). This was an explicit, accepted decision. To import
> the full dataset, merge the JSON files from `src/technologies/*.json` of that repository
> into the `technologies` object of `fingerprints.json`.

## External services used at runtime

- **Australian Business Register (ABN Lookup)** — requires a free registered auth GUID;
  governed by the ABR web services agreement.
- **Internet Archive Wayback API**, **crt.sh**, **Google DNS-over-HTTPS** — public APIs.
- **OpenAI API** — requires a user-supplied API key (stored in Keychain).
