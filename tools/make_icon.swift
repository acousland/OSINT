#!/usr/bin/env swift
//
// Generates the OSIntel macOS app icon at every required size and writes them, plus a
// Contents.json, into Sources/Resources/Assets.xcassets/AppIcon.appiconset.
//
// Run from the repo root:  swift tools/make_icon.swift
//
// Design: a rounded "squircle" with a deep navy gradient, a small entity-graph (nodes +
// links) suggesting OSINT relationships, and a magnifying glass for investigation.
//
import AppKit
import ImageIO

let fm = FileManager.default
let root = fm.currentDirectoryPath
let outDir = "\(root)/Sources/Resources/Assets.xcassets/AppIcon.appiconset"
try? fm.createDirectory(atPath: outDir, withIntermediateDirectories: true)

func draw(size pixels: Int) -> Data {
    let S = CGFloat(pixels)
    // Draw into an exact-pixel CGContext so output dimensions match the requested size
    // (NSImage.lockFocus would render at the display's 2x backing scale).
    let cs = CGColorSpaceCreateDeviceRGB()
    guard let ctx = CGContext(data: nil, width: pixels, height: pixels, bitsPerComponent: 8,
                              bytesPerRow: 0, space: cs,
                              bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return Data() }

    // Rounded background with a vertical navy gradient.
    let radius = S * 0.2237   // macOS continuous-corner ratio
    let rect = CGRect(x: 0, y: 0, width: S, height: S)
    let path = CGPath(roundedRect: rect, cornerWidth: radius, cornerHeight: radius, transform: nil)
    ctx.addPath(path); ctx.clip()
    let colors = [
        CGColor(red: 0.043, green: 0.094, blue: 0.196, alpha: 1),
        CGColor(red: 0.067, green: 0.196, blue: 0.392, alpha: 1),
    ] as CFArray
    let gradient = CGGradient(colorsSpace: CGColorSpaceCreateDeviceRGB(),
                              colors: colors, locations: [0, 1])!
    ctx.drawLinearGradient(gradient, start: CGPoint(x: 0, y: S),
                           end: CGPoint(x: 0, y: 0), options: [])

    let teal = CGColor(red: 0.30, green: 0.82, blue: 0.85, alpha: 1)
    let tealDim = CGColor(red: 0.30, green: 0.82, blue: 0.85, alpha: 0.45)
    let lightNode = CGColor(red: 0.82, green: 0.95, blue: 0.97, alpha: 1)

    // Entity graph: a central node with satellites, in the upper-left two-thirds.
    func p(_ x: CGFloat, _ y: CGFloat) -> CGPoint { CGPoint(x: S * x, y: S * y) }
    let center = p(0.40, 0.60)
    let satellites = [p(0.20, 0.74), p(0.24, 0.46), p(0.58, 0.78), p(0.60, 0.50), p(0.42, 0.84)]

    // Links
    ctx.setStrokeColor(tealDim)
    ctx.setLineWidth(max(1, S * 0.012))
    for s in satellites {
        ctx.move(to: center); ctx.addLine(to: s)
    }
    // A couple of inter-satellite links for a network feel.
    ctx.move(to: satellites[0]); ctx.addLine(to: satellites[1])
    ctx.move(to: satellites[2]); ctx.addLine(to: satellites[3])
    ctx.strokePath()

    // Nodes
    func dot(_ c: CGPoint, _ r: CGFloat, _ color: CGColor) {
        ctx.setFillColor(color)
        ctx.fillEllipse(in: CGRect(x: c.x - r, y: c.y - r, width: r * 2, height: r * 2))
    }
    for s in satellites { dot(s, S * 0.028, teal) }
    dot(center, S * 0.045, lightNode)

    // Magnifying glass over the lower-right.
    let lensCenter = p(0.66, 0.40)
    let lensR = S * 0.16
    ctx.setStrokeColor(lightNode)
    ctx.setLineWidth(S * 0.035)
    ctx.strokeEllipse(in: CGRect(x: lensCenter.x - lensR, y: lensCenter.y - lensR,
                                 width: lensR * 2, height: lensR * 2))
    // Handle
    let handleStart = CGPoint(x: lensCenter.x + lensR * 0.72, y: lensCenter.y - lensR * 0.72)
    let handleEnd = p(0.86, 0.18)
    ctx.setLineCap(.round)
    ctx.setLineWidth(S * 0.05)
    ctx.move(to: handleStart); ctx.addLine(to: handleEnd); ctx.strokePath()
    // Faint lens fill
    ctx.setFillColor(CGColor(red: 0.30, green: 0.82, blue: 0.85, alpha: 0.12))
    ctx.fillEllipse(in: CGRect(x: lensCenter.x - lensR, y: lensCenter.y - lensR,
                               width: lensR * 2, height: lensR * 2))

    guard let cgImage = ctx.makeImage() else { return Data() }
    let out = NSMutableData()
    guard let dest = CGImageDestinationCreateWithData(out, "public.png" as CFString, 1, nil) else { return Data() }
    CGImageDestinationAddImage(dest, cgImage, nil)
    CGImageDestinationFinalize(dest)
    return out as Data
}

// macOS icon set: (pixel size, filename)
let pixelSizes: [Int] = [16, 32, 64, 128, 256, 512, 1024]
for px in pixelSizes {
    let data = draw(size: px)
    let url = URL(fileURLWithPath: "\(outDir)/icon_\(px).png")
    try? data.write(to: url)
    print("wrote icon_\(px).png")
}

// Contents.json mapping the standard macOS idiom sizes to the pixel files.
let entries: [(String, String, String)] = [
    // (size, scale, filename)
    ("16x16", "1x", "icon_16.png"),
    ("16x16", "2x", "icon_32.png"),
    ("32x32", "1x", "icon_32.png"),
    ("32x32", "2x", "icon_64.png"),
    ("128x128", "1x", "icon_128.png"),
    ("128x128", "2x", "icon_256.png"),
    ("256x256", "1x", "icon_256.png"),
    ("256x256", "2x", "icon_512.png"),
    ("512x512", "1x", "icon_512.png"),
    ("512x512", "2x", "icon_1024.png"),
]
var images = entries.map { """
    { "size" : "\($0.0)", "idiom" : "mac", "filename" : "\($0.2)", "scale" : "\($0.1)" }
""" }
let contents = """
{
  "images" : [
\(images.joined(separator: ",\n"))
  ],
  "info" : { "version" : 1, "author" : "xcode" }
}
"""
try? contents.write(toFile: "\(outDir)/Contents.json", atomically: true, encoding: .utf8)
print("wrote Contents.json")
