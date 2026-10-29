import { useEffect, useState } from "react";
import { getPlans } from "../lib/data";

interface Plan {
  title: string;
  country: string;
  docType: string;
  date: string | null;
  publisher: string;
  url: string;
  keyFacts: string[];
  summary: string;
}

export default function Plans() {
  const [plans, setPlans] = useState<Plan[]>([]);
  useEffect(() => {
    getPlans().then(setPlans).catch(() => {});
  }, []);

  return (
    <div className="section">
      <div className="section-head">
        <h1>National plans &amp; guidance</h1>
        <p className="deck">
          The government frameworks that turn the scientific indices into action — each
          country's drought plan and the emergency declarations from the 2023–24 El Niño.
        </p>
      </div>

      <div className="stack">
        {plans.map((p) => (
          <div className="plan" key={p.title}>
            <h3>{p.title}</h3>
            <div className="plan-meta">
              {p.country} · {p.docType.replace(/_/g, " ")} · {p.date ?? "n.d."} · {p.publisher}
            </div>
            <p className="muted" style={{ fontSize: "0.875rem" }}>{p.summary}</p>
            <ul>
              {p.keyFacts.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
            <a href={p.url} target="_blank" rel="noreferrer">
              source ↗
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}
