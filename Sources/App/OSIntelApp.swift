import SwiftUI
import AppKit

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
            // Custom About panel showing version + the exact git commit the build came from.
            CommandGroup(replacing: .appInfo) {
                Button("About OSIntel") {
                    NSApplication.shared.orderFrontStandardAboutPanel(options: [
                        .applicationName: "OSIntel",
                        .applicationVersion: BuildInfo.version,
                        .version: BuildInfo.commit,
                        NSApplication.AboutPanelOptionKey(rawValue: "Copyright"):
                            "Commit \(BuildInfo.commit) · built \(BuildInfo.date)",
                    ])
                }
            }
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
