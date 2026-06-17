// Terminal live + barre de progression alimentés par le WebSocket de job.
import { useEffect, useRef } from "react";

export default function ProvisionConsole({ lines, progress }) {
  const endRef = useRef(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  return (
    <div>
      <div className="progress">
        <div style={{ width: `${Math.round((progress || 0) * 100)}%` }} />
      </div>
      <div className="terminal">
        {lines.map((l, i) => (
          <div key={i} className={`line ${l.kind}`}>{l.text}</div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
