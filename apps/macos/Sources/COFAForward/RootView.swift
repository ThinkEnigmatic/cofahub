import SwiftUI

struct RootView: View {
    @EnvironmentObject private var state: AppState

    var body: some View {
        VStack(spacing: 0) {
            toolbar
            content
        }
    }

    private var toolbar: some View {
        HStack(spacing: 12) {
            Image(systemName: "cloud.sun.fill")
                .foregroundColor(.accentColor)
            Text("COFA FORWARD")
                .font(.headline)

            Spacer()

            Toggle("Offline", isOn: $state.offlineMode)
                .toggleStyle(.switch)
                .controlSize(.small)
                .help("Serve data from the pre-fetched snapshot (no network)")

            Button {
                state.refreshSnapshot()
            } label: {
                Label("Refresh snapshot", systemImage: "arrow.clockwise")
            }
            .help("Re-fetch all live sources into the offline snapshot")

            Button {
                if state.isRunning {
                    state.stopServer()
                } else {
                    state.startServer()
                }
            } label: {
                Label(
                    state.isRunning ? "Stop" : "Start",
                    systemImage: state.isRunning ? "stop.fill" : "play.fill"
                )
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(.bar)
    }

    @ViewBuilder
    private var content: some View {
        switch state.serverStatus {
        case .stopped:
            placeholder(
                icon: "power",
                title: "COFA FORWARD is stopped",
                message: "Start the server to open the weather-intelligence dashboard."
            )
        case .starting:
            placeholder(
                icon: "hourglass",
                title: "Starting server…",
                message: "Booting the local Streamlit app (first launch installs dependencies)."
            )
        case .running:
            WebView(url: URL(string: "http://127.0.0.1:8501")!)
        case .failed(let message):
            placeholder(
                icon: "exclamationmark.triangle",
                title: "Server failed to start",
                message: message
            )
        }
    }

    private func placeholder(icon: String, title: String, message: String) -> some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 44))
                .foregroundColor(.secondary)
            Text(title).font(.title3).fontWeight(.semibold)
            Text(message).font(.callout).foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 420)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
