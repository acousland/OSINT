#!/usr/bin/env swift
//
// Generates the DMG installer window background (660x400) into dist/dmg-background.png.
// Matches the icon palette: navy gradient, a title, and an arrow guiding the drag from
// the app (left) to the Applications drop link (right).
//
// Run from the repo root:  swift tools/make_dmg_background.swift
//
import AppKit
import ImageIO

let W = 660, H = 400
let cs = CGColorSpaceCreateDeviceRGB()
let ctx = CGContext(data: nil, width: W, height: H, bitsPerComponent: 8, bytesPerRow: 0,
                    space: cs, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!

// Background gradient (CGContext origin is bottom-left).
let colors = [
    CGColor(red: 0.043, green: 0.094, blue: 0.196, alpha: 1),
    CGColor(red: 0.067, green: 0.196, blue: 0.392, alpha: 1),
] as CFArray
let gradient = CGGradient(colorsSpace: cs, colors: colors, locations: [0, 1])!
ctx.drawLinearGradient(gradient, start: CGPoint(x: 0, y: H), end: CGPoint(x: 0, y: 0), options: [])

// Arrow pointing right, centred between the two icon slots (~x 165 and ~495, y 200 from top).
// Convert "from top" y=200 to bottom-left: yB = H - 200 = 200.
let teal = CGColor(red: 0.30, green: 0.82, blue: 0.85, alpha: 0.9)
ctx.setStrokeColor(teal); ctx.setFillColor(teal)
ctx.setLineWidth(10); ctx.setLineCap(.round)
let yB: CGFloat = 200
ctx.move(to: CGPoint(x: 270, y: yB)); ctx.addLine(to: CGPoint(x: 380, y: yB)); ctx.strokePath()
// Arrowhead
ctx.move(to: CGPoint(x: 372, y: yB + 16))
ctx.addLine(to: CGPoint(x: 398, y: yB))
ctx.addLine(to: CGPoint(x: 372, y: yB - 16))
ctx.closePath(); ctx.fillPath()

// Title + subtitle text near the top. NSString drawing uses a flipped (top-left) context.
let nsCtx = NSGraphicsContext(cgContext: ctx, flipped: false)
NSGraphicsContext.current = nsCtx
func drawCentered(_ s: String, font: NSFont, color: NSColor, yFromTop: CGFloat) {
    let style = NSMutableParagraphStyle(); style.alignment = .center
    let attrs: [NSAttributedString.Key: Any] = [.font: font, .foregroundColor: color, .paragraphStyle: style]
    let str = NSAttributedString(string: s, attributes: attrs)
    let size = str.size()
    // yFromTop -> bottom-left baseline rect
    let rect = NSRect(x: 0, y: CGFloat(H) - yFromTop - size.height, width: CGFloat(W), height: size.height)
    str.draw(in: rect)
}
drawCentered("OSIntel", font: .systemFont(ofSize: 34, weight: .bold), color: .white, yFromTop: 40)
drawCentered("Drag the app onto the Applications folder to install",
             font: .systemFont(ofSize: 14, weight: .regular),
             color: NSColor(calibratedWhite: 0.8, alpha: 1), yFromTop: 84)
NSGraphicsContext.current = nil

let img = ctx.makeImage()!
let out = NSMutableData()
let dest = CGImageDestinationCreateWithData(out, "public.png" as CFString, 1, nil)!
CGImageDestinationAddImage(dest, img, nil)
CGImageDestinationFinalize(dest)

let fm = FileManager.default
try? fm.createDirectory(atPath: "\(fm.currentDirectoryPath)/dist", withIntermediateDirectories: true)
try? (out as Data).write(to: URL(fileURLWithPath: "\(fm.currentDirectoryPath)/dist/dmg-background.png"))
print("wrote dist/dmg-background.png (\(W)x\(H))")
