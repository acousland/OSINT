import SwiftUI

@main
struct OSIntelApp: App {
    @StateObject private var state = AppState()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(state)
                .frame(minWidth: 1000, minHeight: 680)
                .task { await state.reload() }
        }
        .commands {
            CommandGroup(after: .newItem) {
                Button("New Investigation…") { state.showingNew = true }
                    .keyboardShortcut("n", modifiers: [.command])
            }
        }
        Settings {
            SettingsView().environmentObject(state)
        }
    }
}
