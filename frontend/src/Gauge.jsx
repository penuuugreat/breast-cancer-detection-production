const SIZE = 260;
const STROKE = 16;
const R = (SIZE - STROKE) / 2;
const CX = SIZE / 2;
const CY = SIZE / 2;

// semicircle from 180deg (left) to 0deg (right), sweeping through the top
function polarToCartesian(cx, cy, r, angleDeg) {
  const angleRad = (angleDeg * Math.PI) / 180;
  return { x: cx + r * Math.cos(angleRad), y: cy + r * Math.sin(angleRad) };
}

function arcPath(startAngle, endAngle) {
  const start = polarToCartesian(CX, CY, R, startAngle);
  const end = polarToCartesian(CX, CY, R, endAngle);
  const largeArc = endAngle - startAngle <= 180 ? 0 : 1;
  return `M ${start.x} ${start.y} A ${R} ${R} 0 ${largeArc} 1 ${end.x} ${end.y}`;
}

export default function Gauge({ probability }) {
  const pct = Math.max(0, Math.min(1, probability));
  const needleAngle = 180 + pct * 180; // 180deg..360deg

  const needleLen = R - STROKE;
  const needleTip = polarToCartesian(CX, CY, needleLen, needleAngle);

  return (
    <svg
      viewBox={`0 0 ${SIZE} ${SIZE / 2 + 30}`}
      className="gauge"
      role="img"
      aria-label={`Malignancy probability ${(pct * 100).toFixed(1)} percent`}
    >
      <path
        d={arcPath(180, 360)}
        fill="none"
        stroke="var(--gauge-track)"
        strokeWidth={STROKE}
        strokeLinecap="round"
      />
      <path
        d={arcPath(180, 180 + pct * 180)}
        fill="none"
        stroke="var(--accent)"
        strokeWidth={STROKE}
        strokeLinecap="round"
        className="gauge-fill"
      />
      <line
        x1={CX}
        y1={CY}
        x2={needleTip.x}
        y2={needleTip.y}
        stroke="var(--ink)"
        strokeWidth={3}
        strokeLinecap="round"
        className="gauge-needle"
      />
      <circle cx={CX} cy={CY} r={7} fill="var(--ink)" />
      <text x={12} y={SIZE / 2 + 24} className="gauge-label">
        0
      </text>
      <text x={SIZE - 12} y={SIZE / 2 + 24} className="gauge-label" textAnchor="end">
        1
      </text>
    </svg>
  );
}
