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

    var body: some View {
        VSplitView {
            VStack(alignment: .leading) {
                Text("Crawled Pages (\(pages.count))").font(.headline)
                Table(pages) {
                    TableColumn("Title") { Text($0.title ?? "—") }
                    TableColumn("URL", value: \.url)
                    TableColumn("Status") { Text($0.statusCode.map(String.init) ?? "—") }
                }
            }
            VStack(alignment: .leading) {
                Text("Harvested Documents (\(docs.count))").font(.headline)
                Table(docs) {
                    TableColumn("Type") { Text($0.type.uppercased()) }
                    TableColumn("URL", value: \.url)
                    TableColumn("Text length") { Text("\($0.extractedText?.count ?? 0)") }
                }
            }
        }
        .task {
            guard let store = state.store, let id = investigation.id else { return }
            pages = (try? await store.crawlPages(investigationId: id)) ?? []
            docs = (try? await store.documents(investigationId: id)) ?? []
        }
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
