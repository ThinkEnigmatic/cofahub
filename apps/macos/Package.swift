// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "COFAForward",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(
            name: "COFAForward",
            path: "Sources/COFAForward"
        )
    ]
)
