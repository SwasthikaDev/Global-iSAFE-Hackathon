import type { Severity } from "../types";

interface Props {
  severity: Severity | string;
  size?: "sm" | "md";
}

export function SeverityBadge({ severity, size = "sm" }: Props) {
  const classes: Record<string, string> = {
    critical: "badge-critical",
    high: "badge-high",
    medium: "badge-medium",
    low: "badge-low",
    safe: "badge-safe",
  };
  const cls = classes[severity.toLowerCase()] ?? "badge-low";
  return (
    <span className={`${cls} ${size === "md" ? "text-sm px-3 py-1" : ""}`}>
      {severity.toUpperCase()}
    </span>
  );
}
