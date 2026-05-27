import SwiftUI

struct OverviewTab: View {
    let investigation: Investigation
    @EnvironmentObject var state: AppState
    @State private var entities: [Entity] = []
    @State private var facts: [Fact] = []
    @State private var pages = 0
    @State private var subs = 0
    @State private var ports = 0
    @State private var techs = 0

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text(investigation.name).font(.largeTitle.bold())
                Text(investigation.target).foregroundStyle(.secondary)

                HStack(spacing: 12) {
                    StatCard(title: "Entities", value: entities.count, system: "person.2")
                    StatCard(title: "Facts", value: facts.count, system: "list.bullet")
                    StatCard(title: "Pages", value: pages, system: "globe")
                    StatCard(title: "Subdomains", value: subs, system: "network")
                    StatCard(title: "Open Ports", value: ports, system: "lock.open")
                    StatCard(title: "Technologies", value: techs, system: "cpu")
                }

                if !facts.isEmpty {
                    GroupBox("Key Facts") {
                        VStack(alignment: .leading, spacing: 4) {
                            ForEach(facts.prefix(20)) { f in
                                HStack {
                                    Text(f.key).bold().frame(width: 160, alignment: .leading)
                                    Text(f.value)
                                    Spacer()
                                }.font(.callout)
                            }
                        }.frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
            }
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .task { await load() }
    }

    private func load() async {
        guard let store = state.store, let id = investigation.id else { return }
        entities = (try? await store.entities(investigationId: id)) ?? []
        facts = (try? await store.facts(investigationId: id)) ?? []
        pages = (try? await store.crawlPages(investigationId: id).count) ?? 0
        subs = (try? await store.subdomains(investigationId: id).count) ?? 0
        ports = (try? await store.openPorts(investigationId: id).count) ?? 0
        techs = (try? await store.fingerprints(investigationId: id).count) ?? 0
    }
}

struct StatCard: View {
    let title: String; let value: Int; let system: String
    var body: some View {
        VStack(spacing: 6) {
            Image(systemName: system).font(.title2).foregroundStyle(.tint)
            Text("\(value)").font(.title.bold().monospacedDigit())
            Text(title).font(.caption).foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 12)
        .background(Color(nsColor: .controlBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}

struct EntitiesTab: View {
    let investigation: Investigation
    @EnvironmentObject var state: AppState
    @State private var entities: [Entity] = []

    var body: some View {
        Table(entities) {
            TableColumn("Type") { Text($0.type.capitalized) }
            TableColumn("Name", value: \.name)
            TableColumn("Attributes") { Text($0.attributes == "{}" ? "" : $0.attributes).font(.caption) }
        }
        .task {
            guard let store = state.store, let id = investigation.id else { return }
            entities = (try? await store.entities(investigationId: id)) ?? []
        }
    }
}

struct WebTab: View {
    let investigation: Investigation
    @EnvironmentObject var state: AppState
    @State private var pages: [CrawlPage] = []
    @State private var docs: [HarvestedDocument] = []
    @State private var pdfs: [PdfRender] = []
    @State private var section: WebSection = .pdfs

    enum WebSection: String, CaseIterable, Identifiable { case pages, pdfs, documents; var id: String { rawValue } }

    var body: some View {
        VStack(spacing: 10) {
            HStack {
                Picker("", selection: $section) {
                    Text("Pages (\(pages.count))").tag(WebSection.pages)
                    Text("PDFs (\(pdfs.count))").tag(WebSection.pdfs)
                    Text("Documents (\(docs.count))").tag(WebSection.documents)
                }
                .pickerStyle(.segmented).labelsHidden().fixedSize()
                Spacer()
                Button { openOutputFolder() } label: {
                    Label("Open Output Folder", systemImage: "folder")
                }
            }
            switch section {
            case .pages: pagesTable
            case .pdfs: pdfsTable
            case .documents: docsTable
            }
        }
        .padding()
        .task { await load() }
    }

    private var pagesTable: some View {
        Table(pages) {
            TableColumn("Title") { Text($0.title ?? "—") }
            TableColumn("URL", value: \.url)
            TableColumn("Status") { Text($0.statusCode.map(String.init) ?? "—") }
        }
    }

    @ViewBuilder private var pdfsTable: some View {
        if pdfs.isEmpty {
            ContentUnavailableView("No rendered PDFs", systemImage: "doc.richtext",
                description: Text("Enable “Render pages to PDF” on the Run tab, then run."))
        } else {
            Table(pdfs) {
                TableColumn("Page URL", value: \.url)
                TableColumn("Actions") { pdf in
                    HStack {
                        Button("Open") { FileAccess.open(pdf.localPath) }
                        Button("Reveal") { FileAccess.reveal(pdf.localPath) }
                    }
                }
                .width(160)
            }
        }
    }

    @ViewBuilder private var docsTable: some View {
        if docs.isEmpty {
            ContentUnavailableView("No harvested documents", systemImage: "doc",
                description: Text("Enable “Harvest documents” on the Run tab, then run."))
        } else {
            Table(docs) {
                TableColumn("Type") { Text($0.type.uppercased()) }.width(60)
                TableColumn("URL", value: \.url)
                TableColumn("Text") { Text("\($0.extractedText?.count ?? 0) chars") }.width(90)
                TableColumn("Actions") { doc in
                    HStack {
                        Button("Open") { FileAccess.open(doc.localPath) }.disabled(doc.localPath == nil)
                        Button("Reveal") { FileAccess.reveal(doc.localPath) }.disabled(doc.localPath == nil)
                    }
                }
                .width(160)
            }
        }
    }

    private func openOutputFolder() {
        guard let id = investigation.id,
              let dir = try? AppDatabase.filesDirectory(investigationId: id) else { return }
        FileAccess.openFolder(dir)
    }

    private func load() async {
        guard let store = state.store, let id = investigation.id else { return }
        pages = (try? await store.crawlPages(investigationId: id)) ?? []
        docs = (try? await store.documents(investigationId: id)) ?? []
        pdfs = (try? await store.pdfRenders(investigationId: id)) ?? []
    }
}

struct ReconTab: View {
    let investigation: Investigation
    @EnvironmentObject var state: AppState
    @State private var subs: [Subdomain] = []
    @State private var ports: [OpenPort] = []
    @State private var techs: [TechFingerprint] = []
    @State private var dns: [DNSRecord] = []

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                GroupBox("DNS Records (\(dns.count))") {
                    ForEach(dns) { r in
                        HStack { Text(r.type).bold().frame(width: 60, alignment: .leading)
                            Text(r.value); Spacer() }.font(.callout)
                    }.frame(maxWidth: .infinity, alignment: .leading)
                }
                GroupBox("Subdomains (\(subs.count))") {
                    ForEach(subs) { s in
                        HStack { Text(s.host); Spacer()
                            Text(s.discoveredVia).font(.caption).foregroundStyle(.secondary) }
                    }.frame(maxWidth: .infinity, alignment: .leading)
                }
                GroupBox("Open Ports (\(ports.count))") {
                    ForEach(ports) { p in
                        HStack { Text("\(p.port)").bold().frame(width: 60, alignment: .leading)
                            Text(p.service ?? "unknown"); Spacer() }
                    }.frame(maxWidth: .infinity, alignment: .leading)
                }
                GroupBox("Technologies (\(techs.count))") {
                    ForEach(techs) { t in
                        HStack { Text(t.technology).bold()
                            Text(t.category ?? "").foregroundStyle(.secondary)
                            if let v = t.version { Text(v).font(.caption) }
                            Spacer() }
                    }.frame(maxWidth: .infinity, alignment: .leading)
                }
            }.padding()
        }
        .task {
            guard let store = state.store, let id = investigation.id else { return }
            subs = (try? await store.subdomains(investigationId: id)) ?? []
            ports = (try? await store.openPorts(investigationId: id)) ?? []
            techs = (try? await store.fingerprints(investigationId: id)) ?? []
            dns = (try? await store.dnsRecords(investigationId: id)) ?? []
        }
    }
}
