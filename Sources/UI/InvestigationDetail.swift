import SwiftUI

struct InvestigationDetail: View {
    let investigation: Investigation

    var body: some View {
        TabView {
            RunConfigView(investigation: investigation)
                .tabItem { Label("Run", systemImage: "play.circle") }
            OverviewTab(investigation: investigation)
                .tabItem { Label("Overview", systemImage: "doc.text.magnifyingglass") }
            EntitiesTab(investigation: investigation)
                .tabItem { Label("Entities", systemImage: "person.2") }
            WebTab(investigation: investigation)
                .tabItem { Label("Web", systemImage: "globe") }
            ReconTab(investigation: investigation)
                .tabItem { Label("Recon", systemImage: "network") }
            GraphTab(investigation: investigation)
                .tabItem { Label("Graph", systemImage: "point.3.connected.trianglepath.dotted") }
            TimelineTab(investigation: investigation)
                .tabItem { Label("Timeline", systemImage: "clock") }
            DossierTab(investigation: investigation)
                .tabItem { Label("Dossier", systemImage: "sparkles") }
        }
        .padding()
        .navigationTitle(investigation.name)
    }
}

struct RunConfigView: View {
    let investigation: Investigation
    @EnvironmentObject var state: AppState

    @State private var abn = ""
    @State private var companyName = ""
    @State private var crawlDomain = ""
    @State private var maxDepth = 3.0
    @State private var renderPDFs = true
    @State private var harvestDocs = true
    @State private var dnsEnum = true
    @State private var ctSubs = true
    @State private var fingerprint = true
    @State private var bruteForce = false
    @State private var portScan = false
    @State private var showingConsent = false

    private var wantsActive: Bool { bruteForce || portScan }

    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            Form {
                Section("Corporate Identity (ABR — Australia)") {
                    TextField("ABN or ACN", text: $abn)
                    TextField("Company name search", text: $companyName)
                }
                Section("Web Contents") {
                    TextField("Crawl domain", text: $crawlDomain)
                    VStack(alignment: .leading) {
                        Text("Max depth: \(Int(maxDepth))")
                        Slider(value: $maxDepth, in: 1...10, step: 1)
                    }
                    Toggle("Render pages to PDF", isOn: $renderPDFs)
                    Toggle("Harvest documents (PDF/XLSX/DOCX)", isOn: $harvestDocs)
                }
                Section("Technology & Passive Recon") {
                    Toggle("DNS enumeration", isOn: $dnsEnum)
                    Toggle("Certificate-transparency subdomains", isOn: $ctSubs)
                    Toggle("Technology fingerprinting", isOn: $fingerprint)
                }
                Section {
                    Toggle("Subdomain brute force", isOn: $bruteForce)
                    Toggle("Port scan (1–1024 + common)", isOn: $portScan)
                } header: {
                    Label("Active Reconnaissance (Aggressive)", systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(.orange)
                } footer: {
                    Text("Active recon sends direct probes to the target. Only enable against assets you are authorised to test.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Button {
                    if wantsActive { showingConsent = true } else { launch(consent: false) }
                } label: {
                    Label(state.isRunning ? "Running…" : "Start Run", systemImage: "play.fill")
                        .frame(maxWidth: .infinity)
                }
                .controlSize(.large)
                .disabled(state.isRunning || !hasAnyTask)
            }
            .formStyle(.grouped)
            .frame(maxWidth: 420)

            RunLogView()
        }
        .onAppear { if crawlDomain.isEmpty { crawlDomain = investigation.target } }
        .sheet(isPresented: $showingConsent) {
            ConsentSheet(target: Coordinator.host(from: crawlDomain) ?? investigation.target) {
                launch(consent: true)
            }
        }
    }

    private var hasAnyTask: Bool {
        !abn.isEmpty || !companyName.isEmpty || !crawlDomain.isEmpty
    }

    private func launch(consent: Bool) {
        var plan = RunPlan()
        plan.abn = abn.isEmpty ? nil : abn
        plan.companyName = companyName.isEmpty ? nil : companyName
        plan.crawlDomain = crawlDomain.isEmpty ? nil : crawlDomain
        plan.maxDepth = Int(maxDepth)
        plan.renderPDFs = renderPDFs
        plan.harvestDocuments = harvestDocs
        plan.dnsEnumeration = dnsEnum
        plan.ctSubdomains = ctSubs
        plan.fingerprint = fingerprint
        plan.subdomainBruteForce = bruteForce
        plan.portScan = portScan
        plan.activeConsent = consent
        Task { await state.startRun(plan) }
    }
}

struct RunLogView: View {
    @EnvironmentObject var state: AppState
    var body: some View {
        VStack(alignment: .leading) {
            HStack {
                Text("Run Log").font(.headline)
                if state.isRunning { ProgressView().controlSize(.small) }
            }
            ScrollView {
                VStack(alignment: .leading, spacing: 2) {
                    ForEach(Array(state.runLog.enumerated()), id: \.offset) { _, line in
                        Text(line).font(.system(.caption, design: .monospaced))
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
            }
            .background(Color(nsColor: .textBackgroundColor))
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
    }
}

struct ConsentSheet: View {
    let target: String
    let onConsent: () -> Void
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Label("Aggressive Active Reconnaissance", systemImage: "exclamationmark.triangle.fill")
                .font(.title2.bold()).foregroundStyle(.orange)
            Text("You are about to run active reconnaissance (subdomain brute force and/or TCP port scanning) against:")
            Text(target).font(.headline).textSelection(.enabled)
            Text("""
            This sends direct probes that may be logged or trigger defensive systems. \
            Only proceed if you are authorised to test this target. You are responsible \
            for ensuring your activity is lawful.
            """)
            .font(.callout).foregroundStyle(.secondary)
            HStack {
                Spacer()
                Button("Cancel", role: .cancel) { dismiss() }
                Button("I am authorised — proceed") { onConsent(); dismiss() }
                    .keyboardShortcut(.defaultAction)
                    .tint(.orange)
            }
        }
        .padding(24)
        .frame(width: 460)
    }
}
