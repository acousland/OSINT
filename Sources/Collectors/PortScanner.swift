import Foundation
import Network

/// TCP-connect port scanner built on the Network framework. A successful transition to
/// `.ready` means the port accepts connections (open). This is the only scan type possible
/// under the App Sandbox — raw-socket SYN/stealth/ICMP scans require entitlements the
/// sandbox does not grant, and are intentionally out of scope.
struct PortScanner: Sendable {
    /// Common service ports probed at the "aggressive" level (plus a full 1–1024 sweep).
    static let commonServices: [Int: String] = [
        21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns", 80: "http",
        110: "pop3", 143: "imap", 443: "https", 445: "smb", 465: "smtps",
        587: "submission", 993: "imaps", 995: "pop3s", 1433: "mssql", 3306: "mysql",
        3389: "rdp", 5432: "postgres", 5900: "vnc", 6379: "redis", 8080: "http-alt",
        8443: "https-alt", 9200: "elasticsearch", 27017: "mongodb",
    ]

    let timeout: TimeInterval
    init(timeout: TimeInterval = 2.0) { self.timeout = timeout }

    /// Probe one port. Returns true if open.
    func probe(host: String, port: Int) async -> Bool {
        guard let nwPort = NWEndpoint.Port(rawValue: UInt16(port)) else { return false }
        let conn = NWConnection(host: NWEndpoint.Host(host), port: nwPort, using: .tcp)

        return await withCheckedContinuation { (c: CheckedContinuation<Bool, Never>) in
            let resumed = ResumeGuard()
            conn.stateUpdateHandler = { state in
                switch state {
                case .ready:
                    if resumed.tryResume() { conn.cancel(); c.resume(returning: true) }
                case .failed, .cancelled:
                    if resumed.tryResume() { conn.cancel(); c.resume(returning: false) }
                default:
                    break
                }
            }
            conn.start(queue: .global())
            // Timeout guard.
            DispatchQueue.global().asyncAfter(deadline: .now() + timeout) {
                if resumed.tryResume() { conn.cancel(); c.resume(returning: false) }
            }
        }
    }

    /// One-shot resume guard so the continuation is resumed exactly once.
    private final class ResumeGuard: @unchecked Sendable {
        private let lock = NSLock()
        private var done = false
        func tryResume() -> Bool {
            lock.lock(); defer { lock.unlock() }
            if done { return false }
            done = true
            return true
        }
    }
}
