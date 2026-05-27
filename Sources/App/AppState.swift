import SwiftUI

/// Top-level observable app state. Owns the Store actor and drives investigation runs,
/// streaming Coordinator events into a live log the UI renders.
@MainActor
final class AppState: ObservableObject {
    @Published var investigations: [Investigation] = []
    @Published var selected: Investigation?
    @Published var runLog: [String] = []
    @Published var isRunning = false
    @Published var showingNew = false
    @Published var initError: String?

    let store: Store?

    init() {
        do { self.store = try Store() }
        catch { self.store = nil; self.initError = error.localizedDescription }
    }

    func reload() async {
        guard let store else { return }
        do {
            investigations = try await store.allInvestigations()
            if selected == nil { selected = investigations.first }
        } catch { initError = error.localizedDescription }
    }

    func createInvestigation(name: String, target: String) async {
        guard let store else { return }
        do {
            let inv = try await store.createInvestigation(name: name, target: target)
            await reload()
            selected = investigations.first { $0.id == inv.id }
        } catch { initError = error.localizedDescription }
    }

    /// Run a collection plan against the selected investigation, streaming progress.
    func startRun(_ plan: RunPlan) async {
        guard let store, let inv = selected, let id = inv.id else { return }
        isRunning = true
        runLog = []
        if plan.activeConsent {
            try? await store.setActiveReconConsent(true, investigationId: id)
        }
        let coordinator = Coordinator(store: store, investigationId: id)
        let stream = await coordinator.run(plan)
        for await event in stream {
            append(event)
        }
        isRunning = false
        await reload()
    }

    private func append(_ event: RunEvent) {
        switch event {
        case .started(let stage): runLog.append("▶︎ \(stage)")
        case .progress(_, let message, let done, let total):
            let suffix = total.map { " (\(done)/\($0))" } ?? ""
            runLog.append("  \(message)\(suffix)")
        case .finishedStage(_, let summary): runLog.append("✓ \(summary)")
        case .warning(let w): runLog.append("⚠︎ \(w)")
        case .error(let stage, let message): runLog.append("✗ [\(stage)] \(message)")
        case .completed: runLog.append("● Run complete")
        }
    }
}
