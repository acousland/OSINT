import SwiftUI

struct ContentView: View {
    @EnvironmentObject var state: AppState

    var body: some View {
        NavigationSplitView {
            sidebar
        } detail: {
            if let inv = state.selected {
                InvestigationDetail(investigation: inv)
                    .id(inv.id)
            } else {
                ContentUnavailableView(
                    "No Investigation",
                    systemImage: "magnifyingglass",
                    description: Text("Create an investigation to begin collecting intelligence."))
            }
        }
        .sheet(isPresented: $state.showingNew) { NewInvestigationSheet() }
        .alert("Database error", isPresented: .constant(state.initError != nil)) {
            Button("OK") { state.initError = nil }
        } message: { Text(state.initError ?? "") }
    }

    private var sidebar: some View {
        List(selection: $state.selected) {
            Section("Investigations") {
                ForEach(state.investigations) { inv in
                    VStack(alignment: .leading, spacing: 2) {
                        Text(inv.name).font(.body)
                        Text(inv.target).font(.caption).foregroundStyle(.secondary)
                    }
                    .tag(inv)
                }
            }
        }
        .navigationTitle("OSIntel")
        .toolbar {
            ToolbarItem {
                Button { state.showingNew = true } label: { Image(systemName: "plus") }
                    .help("New investigation")
            }
        }
        .frame(minWidth: 220)
    }
}

struct NewInvestigationSheet: View {
    @EnvironmentObject var state: AppState
    @Environment(\.dismiss) private var dismiss
    @State private var name = ""
    @State private var target = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("New Investigation").font(.title2.bold())
            TextField("Name (e.g. Zen Energy)", text: $name)
            TextField("Primary target (domain, e.g. zenenergy.com.au)", text: $target)
            HStack {
                Spacer()
                Button("Cancel") { dismiss() }
                Button("Create") {
                    let n = name.isEmpty ? target : name
                    Task { await state.createInvestigation(name: n, target: target); dismiss() }
                }
                .keyboardShortcut(.defaultAction)
                .disabled(target.isEmpty)
            }
        }
        .padding(24)
        .frame(width: 420)
    }
}
