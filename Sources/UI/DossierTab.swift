import SwiftUI

struct DossierTab: View {
    let investigation: Investigation
    @EnvironmentObject var state: AppState

    @State private var dossier = ""
    @State private var question = ""
    @State private var answer = ""
    @State private var citations: [String] = []
    @State private var busy = false
    @State private var status = ""

    var body: some View {
        HSplitView {
            dossierPane
            qaPane
        }
        .padding()
    }

    private var dossierPane: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Executive Dossier").font(.headline)
                Spacer()
                Button("Generate") { generate() }.disabled(busy)
                Menu("Export") {
                    Button("Markdown…") {
                        ExportService.saveText(dossier, suggestedName: "\(investigation.name)-dossier.md", type: "md")
                    }
                    Button("PDF…") {
                        Task {
                            let html = ExportService.htmlWrap(dossier, title: investigation.name)
                            await ExportService.saveDossierPDF(markdownHTML: html,
                                suggestedName: "\(investigation.name)-dossier.pdf")
                        }
                    }
                    Button("Raw data (JSON)…") {
                        Task {
                            guard let store = state.store else { return }
                            let json = await ExportService.buildJSON(store: store, investigation: investigation)
                            await MainActor.run {
                                ExportService.saveText(json, suggestedName: "\(investigation.name).json", type: "json")
                            }
                        }
                    }
                }.disabled(dossier.isEmpty)
            }
            if busy { ProgressView().controlSize(.small) }
            if !status.isEmpty { Text(status).font(.caption).foregroundStyle(.secondary) }
            ScrollView {
                Text(dossier.isEmpty ? "No dossier generated yet." : dossier)
                    .textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .background(Color(nsColor: .textBackgroundColor))
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
        .padding(.trailing, 8)
    }

    private var qaPane: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Ask the Corpus").font(.headline)
            Button("Build / refresh index") { buildIndex() }.disabled(busy)
            HStack {
                TextField("e.g. Who is the CEO? What cloud do they use?", text: $question)
                    .onSubmit { ask() }
                Button("Ask") { ask() }.disabled(busy || question.isEmpty)
            }
            ScrollView {
                VStack(alignment: .leading, spacing: 8) {
                    if !answer.isEmpty {
                        Text(answer).textSelection(.enabled)
                        if !citations.isEmpty {
                            Divider()
                            ForEach(citations, id: \.self) { Text($0).font(.caption).foregroundStyle(.secondary) }
                        }
                    }
                }.frame(maxWidth: .infinity, alignment: .leading)
            }
            .background(Color(nsColor: .textBackgroundColor))
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
        .padding(.leading, 8)
    }

    private func engine() -> SynthesisEngine? {
        guard let store = state.store, let id = investigation.id else { return nil }
        return SynthesisEngine(store: store, investigationId: id)
    }

    private func generate() {
        guard let engine = engine() else { return }
        busy = true; status = "Generating dossier…"
        Task {
            do { dossier = try await engine.generateDossier(); status = "" }
            catch { status = error.localizedDescription }
            busy = false
        }
    }

    private func buildIndex() {
        guard let engine = engine() else { return }
        busy = true; status = "Building index…"
        Task {
            do { try await engine.buildIndex { e in
                if case .progress(_, let m, _, _) = e { Task { @MainActor in status = m } } }
                status = "Index ready"
            } catch { status = error.localizedDescription }
            busy = false
        }
    }

    private func ask() {
        guard let engine = engine() else { return }
        busy = true; status = ""
        Task {
            do {
                let result = try await engine.ask(question)
                answer = result.text; citations = result.citations
            } catch { status = error.localizedDescription }
            busy = false
        }
    }
}
