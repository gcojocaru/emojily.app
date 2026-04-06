import AppKit
import SwiftUI

private let canvasSize = CGSize(width: 1024, height: 1024)

private struct ClosedEyeShape: Shape {
    let mirrored: Bool

    func path(in rect: CGRect) -> Path {
        var path = Path()
        let start = CGPoint(x: rect.minX, y: rect.maxY * 0.72)
        let end = CGPoint(x: rect.maxX, y: rect.maxY * 0.72)
        let control = CGPoint(x: rect.midX, y: rect.minY + (mirrored ? rect.height * 0.02 : rect.height * 0.04))
        path.move(to: start)
        path.addQuadCurve(to: end, control: control)
        return path
    }
}

private struct SmileShape: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        path.move(to: CGPoint(x: rect.minX, y: rect.minY + rect.height * 0.18))
        path.addCurve(
            to: CGPoint(x: rect.maxX, y: rect.minY + rect.height * 0.18),
            control1: CGPoint(x: rect.minX + rect.width * 0.18, y: rect.maxY),
            control2: CGPoint(x: rect.maxX - rect.width * 0.18, y: rect.maxY)
        )
        return path
    }
}

private struct DotsField: View {
    let origin: CGPoint
    let rows: Int
    let columns: Int
    let spacing: CGFloat

    var body: some View {
        ForEach(0..<rows, id: \.self) { row in
            ForEach(0..<columns, id: \.self) { column in
                Circle()
                    .fill(.white.opacity(0.68))
                    .frame(width: 8, height: 8)
                    .position(
                        x: origin.x + CGFloat(column) * spacing,
                        y: origin.y + CGFloat(row) * spacing
                    )
            }
        }
    }
}

private struct IconConceptView: View {
    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 196, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: [
                            Color(red: 0.95, green: 0.96, blue: 0.98),
                            Color(red: 0.90, green: 0.93, blue: 0.98),
                            Color(red: 0.97, green: 0.93, blue: 0.90)
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )

            Circle()
                .fill(Color(red: 0.35, green: 0.64, blue: 1.0).opacity(0.32))
                .frame(width: 320, height: 320)
                .blur(radius: 40)
                .offset(x: -150, y: -180)

            Circle()
                .fill(Color(red: 1.0, green: 0.70, blue: 0.42).opacity(0.24))
                .frame(width: 280, height: 280)
                .blur(radius: 42)
                .offset(x: 210, y: 230)

            Circle()
                .fill(.white.opacity(0.18))
                .frame(width: 200, height: 200)
                .blur(radius: 32)
                .offset(x: 170, y: -120)

            DotsField(origin: CGPoint(x: 240, y: 240), rows: 2, columns: 4, spacing: 38)
            DotsField(origin: CGPoint(x: 708, y: 760), rows: 2, columns: 4, spacing: 38)

            RoundedRectangle(cornerRadius: 156, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: [.white.opacity(0.64), .white.opacity(0.24)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .overlay {
                    RoundedRectangle(cornerRadius: 156, style: .continuous)
                        .stroke(
                            LinearGradient(
                                colors: [.white.opacity(0.86), .white.opacity(0.34)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            lineWidth: 1.5
                        )
                }
                .overlay(alignment: .top) {
                    RoundedRectangle(cornerRadius: 30, style: .continuous)
                        .fill(.white.opacity(0.22))
                        .frame(width: 420, height: 68)
                        .overlay(alignment: .leading) {
                            HStack(spacing: 14) {
                                Circle().fill(Color(red: 0.06, green: 0.43, blue: 0.96)).frame(width: 20, height: 20)
                                Circle().fill(.white.opacity(0.72)).frame(width: 20, height: 20)
                                Circle().fill(.white.opacity(0.52)).frame(width: 20, height: 20)
                            }
                            .padding(.leading, 32)
                        }
                        .padding(.top, 52)
                }
                .frame(width: 524, height: 524)
                .shadow(color: Color.black.opacity(0.12), radius: 28, y: 24)
                .overlay {
                    LazyVGrid(
                        columns: Array(repeating: GridItem(.fixed(84), spacing: 20), count: 4),
                        spacing: 20
                    ) {
                        ForEach(0..<12, id: \.self) { index in
                            RoundedRectangle(cornerRadius: 24, style: .continuous)
                                .fill(index == 6 ? AnyShapeStyle(
                                    LinearGradient(
                                        colors: [
                                            Color(red: 0.28, green: 0.63, blue: 1.0),
                                            Color(red: 0.05, green: 0.43, blue: 0.96)
                                        ],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                ) : AnyShapeStyle(
                                    LinearGradient(
                                        colors: [.white.opacity(0.80), .white.opacity(0.44)],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                ))
                                .frame(width: 84, height: 84)
                                .overlay {
                                    RoundedRectangle(cornerRadius: 24, style: .continuous)
                                        .stroke(.white.opacity(index == 6 ? 0.28 : 0.68), lineWidth: 1.5)
                                }
                                .shadow(
                                    color: index == 6 ? Color(red: 0.05, green: 0.43, blue: 0.96).opacity(0.22) : .clear,
                                    radius: 12,
                                    y: 6
                                )
                        }
                    }
                    .padding(.top, 88)
                    .frame(width: 396)
                }

            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [
                                Color(red: 1.00, green: 0.91, blue: 0.45),
                                Color(red: 1.00, green: 0.79, blue: 0.17),
                                Color(red: 0.95, green: 0.60, blue: 0.00)
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                Circle()
                    .fill(
                        RadialGradient(
                            colors: [.white.opacity(0.72), .white.opacity(0.16), .clear],
                            center: .topLeading,
                            startRadius: 20,
                            endRadius: 180
                        )
                    )
                Circle()
                    .stroke(Color(red: 0.95, green: 0.63, blue: 0.00).opacity(0.36), lineWidth: 8)

                ClosedEyeShape(mirrored: false)
                    .stroke(Color(red: 0.42, green: 0.21, blue: 0.00), style: StrokeStyle(lineWidth: 16, lineCap: .round))
                    .frame(width: 52, height: 32)
                    .offset(x: -68, y: -48)

                ClosedEyeShape(mirrored: true)
                    .stroke(Color(red: 0.42, green: 0.21, blue: 0.00), style: StrokeStyle(lineWidth: 16, lineCap: .round))
                    .frame(width: 52, height: 32)
                    .offset(x: 68, y: -48)

                SmileShape()
                    .stroke(Color(red: 0.42, green: 0.21, blue: 0.00), style: StrokeStyle(lineWidth: 18, lineCap: .round))
                    .frame(width: 216, height: 96)
                    .offset(y: 66)

                Circle()
                    .fill(.white.opacity(0.32))
                    .frame(width: 44, height: 44)
                    .offset(x: 130, y: -114)

                Circle()
                    .fill(.white.opacity(0.42))
                    .frame(width: 20, height: 20)
                    .offset(x: 126, y: -120)
            }
            .frame(width: 336, height: 336)
            .shadow(color: Color(red: 0.16, green: 0.22, blue: 0.34).opacity(0.22), radius: 18, y: 18)
        }
        .frame(width: canvasSize.width, height: canvasSize.height)
        .padding(80)
        .background(Color.clear)
    }
}

private func renderIcon(to outputURL: URL) throws {
    let renderer = ImageRenderer(content: IconConceptView())
    renderer.proposedSize = .init(canvasSize)
    renderer.scale = 1

    guard let nsImage = renderer.nsImage else {
        throw NSError(domain: "AppIconRender", code: 1, userInfo: [NSLocalizedDescriptionKey: "Failed to create image renderer output."])
    }

    guard
        let tiffData = nsImage.tiffRepresentation,
        let bitmap = NSBitmapImageRep(data: tiffData),
        let pngData = bitmap.representation(using: .png, properties: [:])
    else {
        throw NSError(domain: "AppIconRender", code: 2, userInfo: [NSLocalizedDescriptionKey: "Failed to encode PNG data."])
    }

    try pngData.write(to: outputURL)
}

let outputPath = CommandLine.arguments.dropFirst().first ?? "/tmp/everydayemoji-app-icon-concept.png"
let outputURL = URL(fileURLWithPath: outputPath)

do {
    try renderIcon(to: outputURL)
    print("Rendered icon concept to \(outputURL.path)")
} catch {
    fputs("Render failed: \(error.localizedDescription)\n", stderr)
    exit(1)
}
