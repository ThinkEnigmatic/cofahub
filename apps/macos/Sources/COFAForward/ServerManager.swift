import Foundation

/// Launches and supervises the local FastAPI server that hosts COFAHUB.
///
/// The server runs the Python app via the ``uv``-managed virtualenv so the React
/// frontend + JSON API are both served from ``127.0.0.1:8700`` and displayed in
/// the app's WKWebView.
struct ServerManager {
    let port = 8700
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

    /// Build the argv for the FastAPI (uvicorn) server, preferring a pre-built venv.
    private static func uvicornCommand() -> (String, [String]) {
        let appDir = self.appDir
        let venvUvicorn = appDir.appendingPathComponent(".venv/bin/uvicorn")
        let commonArgs = [
            "cofa_forward.api:app",
            "--host", "127.0.0.1",
            "--port", "8700",
        ]
        if FileManager.default.fileExists(atPath: venvUvicorn.path) {
            return (venvUvicorn.path, commonArgs)
        }
        return (resolveUv(), ["run", "uvicorn"] + commonArgs)
    }

    mutating func start(offline: Bool, onStatus: @escaping (AppState.ServerStatus) -> Void) {
        stop()
        let (exe, args) = Self.uvicornCommand()
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
            // Give uvicorn a moment to bind; then report running.
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
