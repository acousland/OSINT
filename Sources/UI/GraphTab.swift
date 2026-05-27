import SwiftUI

/// Entity graph rendered with a simple force-directed layout on a SwiftUI Canvas.
/// (macOS has no first-class graph component; Canvas keeps it dependency-free.)
struct GraphTab: View {
    let investigation: Investigation
    @EnvironmentObject var state: AppState
    @State private var nodes: [GraphNode] = []
    @State private var edges: [(Int, Int)] = []

    var body: some View {
        GeometryReader { geo in
            Canvas { ctx, size in
                // Edges
                for (a, b) in edges where a < nodes.count && b < nodes.count {
                    var path = Path()
                    path.move(to: nodes[a].position)
                    path.addLine(to: nodes[b].position)
                    ctx.stroke(path, with: .color(.gray.opacity(0.4)), lineWidth: 1)
                }
                // Nodes
                for node in nodes {
                    let r: CGFloat = 6
                    let rect = CGRect(x: node.position.x - r, y: node.position.y - r, width: r * 2, height: r * 2)
                    ctx.fill(Path(ellipseIn: rect), with: .color(color(for: node.type)))
                    ctx.draw(Text(node.label).font(.caption2),
                             at: CGPoint(x: node.position.x, y: node.position.y - 12))
                }
            }
            .onAppear { Task { await load(in: geo.size) } }
        }
        .overlay(alignment: .bottomLeading) { legend.padding() }
    }

    private var legend: some View {
        HStack(spacing: 12) {
            ForEach(EntityType.allCases, id: \.self) { t in
                HStack(spacing: 4) {
                    Circle().fill(color(for: t.rawValue)).frame(width: 8, height: 8)
                    Text(t.rawValue).font(.caption2)
                }
            }
        }
        .padding(6)
        .background(.thinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 6))
    }

    private func color(for type: String) -> Color {
        switch EntityType(rawValue: type) {
        case .company: return .blue
        case .person: return .green
        case .domain: return .orange
        case .host: return .purple
        case .technology: return .pink
        default: return .gray
        }
    }

    private func load(in size: CGSize) async {
        guard let store = state.store, let id = investigation.id else { return }
        let entities = (try? await store.entities(investigationId: id)) ?? []
        let dbEdges = (try? await store.edges(investigationId: id)) ?? []
        var indexById: [Int64: Int] = [:]
        var built: [GraphNode] = []
        for (i, e) in entities.enumerated() {
            indexById[e.id ?? -1] = i
            // Seed positions on a circle, then relax.
            let angle = Double(i) / Double(max(1, entities.count)) * 2 * .pi
            let pos = CGPoint(x: size.width / 2 + cos(angle) * 200,
                              y: size.height / 2 + sin(angle) * 200)
            built.append(GraphNode(label: e.name, type: e.type, position: pos))
        }
        let mappedEdges = dbEdges.compactMap { e -> (Int, Int)? in
            guard let a = indexById[e.fromEntityId], let b = indexById[e.toEntityId] else { return nil }
            return (a, b)
        }
        relax(&built, edges: mappedEdges, in: size)
        nodes = built
        edges = mappedEdges
    }

    /// A few iterations of crude force-directed relaxation.
    private func relax(_ nodes: inout [GraphNode], edges: [(Int, Int)], in size: CGSize) {
        let center = CGPoint(x: size.width / 2, y: size.height / 2)
        for _ in 0..<60 {
            var disp = Array(repeating: CGPoint.zero, count: nodes.count)
            // Repulsion
            for i in 0..<nodes.count {
                for j in (i+1)..<nodes.count {
                    let dx = nodes[i].position.x - nodes[j].position.x
                    let dy = nodes[i].position.y - nodes[j].position.y
                    let dist = max(1, (dx*dx + dy*dy).squareRoot())
                    let force = 4000 / (dist * dist)
                    disp[i].x += dx / dist * force; disp[i].y += dy / dist * force
                    disp[j].x -= dx / dist * force; disp[j].y -= dy / dist * force
                }
            }
            // Attraction along edges
            for (a, b) in edges {
                let dx = nodes[a].position.x - nodes[b].position.x
                let dy = nodes[a].position.y - nodes[b].position.y
                let dist = max(1, (dx*dx + dy*dy).squareRoot())
                let force = dist * dist / 12000
                disp[a].x -= dx / dist * force; disp[a].y -= dy / dist * force
                disp[b].x += dx / dist * force; disp[b].y += dy / dist * force
            }
            for i in 0..<nodes.count {
                nodes[i].position.x += max(-10, min(10, disp[i].x)) + (center.x - nodes[i].position.x) * 0.01
                nodes[i].position.y += max(-10, min(10, disp[i].y)) + (center.y - nodes[i].position.y) * 0.01
            }
        }
    }
}

struct GraphNode { let label: String; let type: String; var position: CGPoint }
