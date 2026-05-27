import SwiftUI
import Charts

struct TimelineTab: View {
    let investigation: Investigation
    @EnvironmentObject var state: AppState
    @State private var events: [TimelineEvent] = []

    var body: some View {
        VStack(alignment: .leading) {
            if events.isEmpty {
                ContentUnavailableView("No timeline events yet", systemImage: "clock")
            } else {
                Chart(events) { e in
                    PointMark(
                        x: .value("Time", e.timestamp),
                        y: .value("Kind", e.kind))
                    .foregroundStyle(by: .value("Kind", e.kind))
                    .symbolSize(120)
                }
                .frame(height: 220)
                .padding(.bottom)

                Table(events.sorted { $0.timestamp < $1.timestamp }) {
                    TableColumn("When") { Text($0.timestamp.formatted(date: .abbreviated, time: .shortened)) }
                    TableColumn("Kind") { Text($0.kind) }
                    TableColumn("Summary", value: \.summary)
                }
            }
        }
        .padding()
        .task {
            guard let store = state.store, let id = investigation.id else { return }
            events = (try? await store.timeline(investigationId: id)) ?? []
        }
    }
}
