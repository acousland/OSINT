import Foundation

/// Simple async token-bucket rate limiter. Collectors call `await wait()` before each
/// outbound request so we stay polite to a host. One limiter per host/budget.
actor RateLimiter {
    private let minInterval: TimeInterval
    private var lastFire: Date = .distantPast

    /// - Parameter requestsPerSecond: sustained request rate.
    init(requestsPerSecond: Double) {
        self.minInterval = requestsPerSecond > 0 ? 1.0 / requestsPerSecond : 0
    }

    func wait() async {
        guard minInterval > 0 else { return }
        let now = Date()
        let earliest = lastFire.addingTimeInterval(minInterval)
        if earliest > now {
            let delay = earliest.timeIntervalSince(now)
            try? await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
        }
        lastFire = Date()
    }
}

/// Bounds the number of concurrent tasks (used for crawl/scan fan-out). Backed by a
/// counting semaphore implemented with continuations.
actor ConcurrencyLimiter {
    private let limit: Int
    private var active = 0
    private var waiters: [CheckedContinuation<Void, Never>] = []

    init(limit: Int) { self.limit = max(1, limit) }

    func acquire() async {
        if active < limit {
            active += 1
            return
        }
        await withCheckedContinuation { (c: CheckedContinuation<Void, Never>) in
            waiters.append(c)
        }
        active += 1
    }

    func release() {
        active -= 1
        if !waiters.isEmpty {
            let c = waiters.removeFirst()
            c.resume()
        }
    }

    /// Run `body` while holding a permit, releasing deterministically on return or throw.
    /// `nonisolated` so `body` executes in the caller's context, not serialized on the actor.
    nonisolated func withPermit<T>(_ body: () async throws -> T) async rethrows -> T {
        await acquire()
        do {
            let result = try await body()
            await release()
            return result
        } catch {
            await release()
            throw error
        }
    }
}
