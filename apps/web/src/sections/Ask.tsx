import { useState, type FormEvent } from "react";
import { ragQuery, type RagChunk } from "../lib/data";

const KIND_LABEL: Record<string, string> = {
  doc: "documentation",
  plan: "national plan",
  source: "data source",
  geography: "location",
};

/** Ask COFAHUB — retrieval over the project's own knowledge (RAG). */
export default function Ask() {
  const [query, setQuery] = useState("");
  const [chunks, setChunks] = useState<RagChunk[]>([]);
  const [answer, setAnswer] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setBusy(true);
    setAnswer(null);
    setChunks([]);
    try {
      const r = await ragQuery(query.trim(), true);
      setChunks(r.chunks);
      setAnswer(r.answer);
    } catch {
      /* noop */
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="section">
      <div className="section-head">
        <h1>Ask COFAHUB</h1>
        <p className="deck">
          Ask about the project's methods, data sources, national drought plans, and
          findings. Answers are grounded in the project's own documents — every result
          carries its source, and nothing is invented.
        </p>
      </div>

      <form onSubmit={submit} style={{ display: "flex", gap: "0.6rem", marginBottom: "1.5rem" }}>
        <input
          className="ask-input"
          aria-label="Question"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. What is the PEAC 4/8-inch drought threshold?"
          style={{ flex: 1 }}
        />
        <button className="btn" type="submit" disabled={busy} style={{ width: "auto", padding: "0.7rem 1.2rem" }}>
          {busy ? "…" : "Ask"}
        </button>
      </form>

      {answer && (
        <div className="panel" style={{ marginBottom: "1rem" }}>
          <h2>Answer</h2>
          <div className="panel-sub">generated from the retrieved sources</div>
          <p style={{ color: "var(--nn-ink)", lineHeight: 1.6 }}>{answer}</p>
        </div>
      )}

      {chunks.length > 0 && (
        <div className="panel">
          <h2>Sources</h2>
          <div className="panel-sub">retrieved from the knowledge base</div>
          <div className="stack">
            {chunks.map((c, i) => (
              <div className="plan" key={i}>
                <h3>{c.title}</h3>
                <div className="plan-meta">
                  {KIND_LABEL[c.kind] ?? c.kind} · {c.source} · relevance {c.score.toFixed(2)}
                </div>
                <p className="muted" style={{ fontSize: "0.875rem", maxHeight: 96, overflow: "hidden" }}>
                  {c.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {!busy && !chunks.length && (
        <p className="muted" style={{ maxWidth: "60ch" }}>
          Try: "what drove the 2015-16 El Niño drought?", "what does the FSM national drought
          plan cover?", or "which data sources does COFAHUB use for sea level?".
        </p>
      )}
    </div>
  );
}
