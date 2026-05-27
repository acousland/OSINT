import Foundation

/// Wappalyzer-style technology detection. Matches HTTP response headers and HTML body
/// against a bundled ruleset (fingerprints.json). The matching engine is ours; only the
/// rule *data* is reused from the Wappalyzer-format dataset.
struct Fingerprinter: Sendable {
    struct Rule {
        let category: String
        let headers: [String: String]   // header name -> regex (empty = presence only)
        let html: String?                // regex over body
    }

    struct Match: Sendable {
        let technology: String
        let category: String
        let version: String?
        let evidence: String
    }

    let rules: [String: Rule]

    init() {
        self.rules = Fingerprinter.loadRules()
    }

    func detect(headers: [String: String], html: String) -> [Match] {
        var matches: [Match] = []
        // Case-insensitive header lookup.
        let lowerHeaders = Dictionary(headers.map { ($0.key.lowercased(), $0.value) },
                                      uniquingKeysWith: { a, _ in a })
        for (tech, rule) in rules {
            // Header rules.
            for (hname, pattern) in rule.headers {
                guard let value = lowerHeaders[hname.lowercased()] else { continue }
                if pattern.isEmpty {
                    matches.append(Match(technology: tech, category: rule.category,
                                         version: nil, evidence: "header \(hname)"))
                    break
                }
                if let version = Fingerprinter.firstMatch(pattern, in: value, captureGroup: true) {
                    matches.append(Match(technology: tech, category: rule.category,
                                         version: version.isEmpty ? nil : version,
                                         evidence: "header \(hname): \(value)"))
                    break
                }
            }
            // HTML rule (only if not already matched via headers).
            if !matches.contains(where: { $0.technology == tech }), let pattern = rule.html,
               Fingerprinter.firstMatch(pattern, in: html, captureGroup: false) != nil {
                matches.append(Match(technology: tech, category: rule.category,
                                     version: nil, evidence: "html match"))
            }
        }
        return matches
    }

    // MARK: Ruleset loading

    private static func loadRules() -> [String: Rule] {
        guard let url = Bundle.main.url(forResource: "fingerprints", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let techs = obj["technologies"] as? [String: Any] else { return [:] }

        var out: [String: Rule] = [:]
        for (name, raw) in techs {
            guard let dict = raw as? [String: Any] else { continue }
            let category = (dict["category"] as? String) ?? "Other"
            var headers: [String: String] = [:]
            if let h = dict["headers"] as? [String: String] { headers = h }
            let html = dict["html"] as? String
            out[name] = Rule(category: category, headers: headers, html: html)
        }
        return out
    }

    /// Returns the first capture group (or "" if matched without a group), or nil if no match.
    private static func firstMatch(_ pattern: String, in text: String, captureGroup: Bool) -> String? {
        guard let re = try? NSRegularExpression(pattern: pattern, options: [.caseInsensitive]) else { return nil }
        let range = NSRange(text.startIndex..., in: text)
        guard let m = re.firstMatch(in: text, options: [], range: range) else { return nil }
        if captureGroup, m.numberOfRanges > 1, let r = Range(m.range(at: 1), in: text) {
            return String(text[r])
        }
        return ""
    }
}
