import Foundation

/// Launches and supervises the local Streamlit server that hosts COFA FORWARD,
/// and (optionally) the offline-snapshot prefetch.
///
/// The server runs the Python app via a ``uv``-managed virtualenv (or an already
/// built ``.venv``) so the whole UI is served from ``127.0.0.1:8501`` and
/// displayed in the app's WKWebView.
struct ServerManager {
    let port = 8501
    var serverURL: URL { URL(string: "http://127.0.0.1:\(port)")! }

    private var process: Process?

    /// Resolve the cofa-forward app directory (env override or ~/cofa-forward).
    private static var appDir: URL {
        if let env = ProcessInfo.processInfo.environment["COFA_APP_DIR"], !env.isEmpty {
            return URL(fileURLWithPath: env)
        }
        return FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("cofa-forward")
    }

    /// Resolve `uv` (needed only when no pre-built `.venv` exists).
    private static func resolveUv() -> String {
        let home = FileManager.default.homeDirectoryForCurrentUser
        let candidates = [
            home.appendingPathComponent(".local/bin/uv").path,
            "/opt/homebrew/bin/uv",
            "/usr/local/bin/uv",
            "/usr/bin/env", // last resort: uv must be on PATH
        ]
        for c in candidates where FileManager.default.fileExists(atPath: c) {
            return c
        }
        return "/usr/bin/env"
    }

    /// Build the argv for the Streamlit server, preferring a pre-built venv.
    private static func streamlitCommand(offline: Bool) -> (String, [String]) {
        let appDir = self.appDir
        let venvStreamlit = appDir.appendingPathComponent(".venv/bin/streamlit")
        let commonArgs = [
            "run", "src/cofa_forward/ui/app.py",
            "--server.headless", "true",
            "--server.address", "127.0.0.1",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false",
        ]
        if FileManager.default.fileExists(atPath: venvStreamlit.path) {
            return (venvStreamlit.path, commonArgs)
        }
        return (resolveUv(), ["run", "streamlit"] + commonArgs)
    }

    mutating func start(offline: Bool, onStatus: @escaping (AppState.ServerStatus) -> Void) {
        stop()
        let (exe, args) = Self.streamlitCommand(offline: offline)
        let p = Process()
        p.executableURL = URL(fileURLWithPath: exe)
        p.arguments = args
        p.currentDirectoryURL = Self.appDir

        var env = ProcessInfo.processInfo.environment
        if offline {
            env["COFA_OFFLINE"] = "1"
        } else {
            env["COFA_OFFLINE"] = "0"
        }
        p.environment = env

        p.terminationHandler = { proc in
            if proc.terminationStatus != 0 {
                onStatus(.failed("server exited with code \(proc.terminationStatus)"))
            }
        }

        do {
            try p.run()
            process = p
            // Give Streamlit a moment to bind; then report running.
            DispatchQueue.global().asyncAfter(deadline: .now() + 2.0) {
                if p.isRunning {
                    onStatus(.running)
                } else {
                    onStatus(.failed("server failed to start"))
                }
            }
        } catch {
            onStatus(.failed(error.localizedDescription))
        }
    }

    mutating func stop() {
        process?.terminate()
        process = nil
    }

    /// Run the offline-snapshot prefetch and return its stdout.
    mutating func refreshSnapshot(completion: @escaping (String) -> Void) {
        let appDir = Self.appDir
        let p = Process()
        p.executableURL = URL(fileURLWithPath: Self.resolveUv())
        p.arguments = [
            "run", "python", "scripts/prefetch_snapshot.py", "--skip-ibtracs",
        ]
        p.currentDirectoryURL = appDir

        let pipe = Pipe()
        p.standardOutput = pipe
        p.standardError = pipe

        do {
            try p.run()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            let text = String(data: data, encoding: .utf8) ?? ""
            completion(text)
        } catch {
            completion("prefetch failed: \(error.localizedDescription)")
        }
    }
}
