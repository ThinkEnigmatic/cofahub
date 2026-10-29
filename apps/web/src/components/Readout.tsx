interface ReadoutProps {
  label: string;
  value: string;
  unit?: string;
  tone?: "default" | "key" | "pink" | "warn";
  provenance?: string;
}

/** A large numeric readout with provenance beneath. The number is the hero. */
export default function Readout({ label, value, unit, tone, provenance }: ReadoutProps) {
  return (
    <div className="readout">
      <div className="readout-label">{label}</div>
      <div className="readout-value" data-tone={tone ?? "default"}>
        {value}
        {unit && <span className="readout-unit">{unit}</span>}
      </div>
      {provenance && <div className="readout-prov">{provenance}</div>}
    </div>
  );
}
