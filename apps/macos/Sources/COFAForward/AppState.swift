import Foundation
import SwiftUI

/// App-wide state: server lifecycle, offline mode, and snapshot status.
final class AppState: ObservableObject {
    enum ServerStatus: Equatable {
        case stopped
        case starting
        case running
        case failed(String)
    }

    @Published var serverStatus: ServerStatus = .stopped
    @Published var offlineMode: Bool {
        didSet {
            UserDefaults.standard.set(offlineMode, forKey: "offlineMode")
        }
    }
    @Published var snapshotSummary: String = ""

    private var server = ServerManager()

    init() {
        offlineMode = UserDefaults.standard.bool(forKey: "offlineMode")
    }

    var isRunning: Bool {
        if case .running = serverStatus { return true }
        return false
    }

    func startServer() {
        guard !isRunning else { return }
        serverStatus = .starting
        server.start(offline: offlineMode) { [weak self] status in
            DispatchQueue.main.async {
                self?.serverStatus = status
            }
        }
    }

    func stopServer() {
        server.stop()
        serverStatus = .stopped
    }

    func refreshSnapshot() {
        serverStatus = .starting
        server.refreshSnapshot { [weak self] output in
            DispatchQueue.main.async {
                self?.snapshotSummary = output
                self?.serverStatus = .running
            }
        }
    }
}
