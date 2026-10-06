// Dependency free SVG charts. They read real backend data and scale to their container.

type Point = { label: string; value: number };

export function TrendChart({
  points,
  height = 220,
  max = 100,
  title,
}: {
  points: Point[];
  height?: number;
  max?: number;
  title?: string;
}) {
  if (points.length < 2) {
    return (
      <div className="state-block state-empty">
        <p className="state-title">Not enough history to plot a trend</p>
        <p className="muted">
          {points.length === 0
            ? "Recalculate your readiness score to create the first snapshot."
            : "Recalculate again after making improvements to see a trend line."}
        </p>
      </div>
    );
  }

  const width = 640;
  const padding = { top: 18, right: 18, bottom: 34, left: 34 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  const stepX = plotWidth / (points.length - 1);
  const toY = (value: number) => padding.top + plotHeight - (Math.max(0, Math.min(max, value)) / max) * plotHeight;

  const path = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${padding.left + index * stepX} ${toY(point.value)}`)
    .join(" ");

  const areaPath = `${path} L ${padding.left + (points.length - 1) * stepX} ${
    padding.top + plotHeight
  } L ${padding.left} ${padding.top + plotHeight} Z`;

  const gridValues = [0, 25, 50, 75, 100];

  return (
    <div className="chart-block">
      {title && <p className="chart-title">{title}</p>}
      <svg className="trend-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title ?? "Trend chart"}>
        {gridValues.map((value) => (
          <g key={value}>
            <line
              x1={padding.left}
              x2={width - padding.right}
              y1={toY(value)}
              y2={toY(value)}
              className="chart-grid"
            />
            <text className="chart-axis" x={4} y={toY(value) + 4}>
              {value}
            </text>
          </g>
        ))}

        <path className="chart-area" d={areaPath} />
        <path className="chart-line" d={path} />

        {points.map((point, index) => (
          <g key={`${point.label}-${index}`}>
            <circle className="chart-dot" cx={padding.left + index * stepX} cy={toY(point.value)} r={4} />
            <title>{`${point.label}: ${point.value}`}</title>
            {(index === 0 || index === points.length - 1 || points.length <= 8) && (
              <text
                className="chart-axis"
                textAnchor={index === 0 ? "start" : index === points.length - 1 ? "end" : "middle"}
                x={padding.left + index * stepX}
                y={height - 10}
              >
                {point.label}
              </text>
            )}
          </g>
        ))}
      </svg>
    </div>
  );
}

export function ComponentBarChart({ items }: { items: { label: string; value: number }[] }) {
  return (
    <div className="component-bars">
      {items.map((item) => {
        const tone = item.value >= 70 ? "good" : item.value >= 50 ? "medium" : "low";
        return (
          <div className="component-bar" key={item.label}>
            <span className="component-label">{item.label}</span>
            <div className="component-track">
              <div className={`component-fill component-${tone}`} style={{ width: `${Math.max(2, item.value)}%` }} />
            </div>
            <strong>{item.value}</strong>
          </div>
        );
      })}
    </div>
  );
}
