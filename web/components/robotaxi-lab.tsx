"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { LoadingCar } from "./loading-car";
import { DEFAULT_CONFIG, PRESETS, REGIONS } from "../lib/data";
import { validateConfig } from "../lib/simulation";
import type {
  DistributionRange,
  ScenarioSeries,
  SimulationConfig,
  SimulationResult,
  WorkerMessage,
} from "../lib/types";

type InputMode = "simple" | "advanced";
type ResultDepth = "overview" | "explore";
type MetricKey =
  | "miles"
  | "fleet"
  | "production"
  | "discontinued"
  | "milesPerCar"
  | "vmt"
  | "revenue"
  | "co2"
  | "cars"
  | "pollution"
  | "hours"
  | "years"
  | "gdp";
let activeRunDraws = DEFAULT_CONFIG.numSimulations;

function cloneConfig(config: SimulationConfig): SimulationConfig {
  return {
    ...config,
    growth: { ...config.growth },
    generalInputs: Object.fromEntries(
      Object.entries(config.generalInputs).map(([key, range]) => [
        key,
        { ...range },
      ]),
    ) as SimulationConfig["generalInputs"],
    growthByYear: Object.fromEntries(
      Object.entries(config.growthByYear).map(([year, range]) => [
        year,
        { ...range },
      ]),
    ),
    regionalDistribution: Object.fromEntries(
      Object.entries(config.regionalDistribution).map(([region, range]) => [
        region,
        { ...range },
      ]),
    ) as SimulationConfig["regionalDistribution"],
    regionalShares: { ...config.regionalShares },
    deploymentDates: Object.fromEntries(
      Object.entries(config.deploymentDates).map(([region, dates]) => [
        region,
        { ...dates },
      ]),
    ) as SimulationConfig["deploymentDates"],
    impact: {
      ...config.impact,
      co2PerMile: Object.fromEntries(
        Object.entries(config.impact.co2PerMile).map(([region, values]) => [
          region,
          { ...values },
        ]),
      ) as SimulationConfig["impact"]["co2PerMile"],
      co2Produced: { ...config.impact.co2Produced },
      productivityPerHour: { ...config.impact.productivityPerHour },
      gdpByRegion: { ...config.impact.gdpByRegion },
    },
    vmt: {
      ...config.vmt,
      arimaOrder: [...config.vmt.arimaOrder] as [number, number, number],
    },
  };
}

function formatCompact(value: number, digits = 1): string {
  const absolute = Math.abs(value);
  if (absolute >= 1e12) return `${(value / 1e12).toFixed(digits)}T`;
  if (absolute >= 1e9) return `${(value / 1e9).toFixed(digits)}B`;
  if (absolute >= 1e6) return `${(value / 1e6).toFixed(digits)}M`;
  if (absolute >= 1e3) return `${(value / 1e3).toFixed(digits)}k`;
  return value.toFixed(digits);
}

function formatDollars(value: number): string {
  return `$${formatCompact(value)}`;
}
function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}
function stretchBearRange(
  range: DistributionRange,
  value: number,
): DistributionRange {
  return {
    min: Math.min(range.min, value),
    bear: value,
    bull: Math.max(range.bull, value),
    max: Math.max(range.max, value),
  };
}
function yearIndex(result: SimulationResult, year: number): number {
  const index = result.years.indexOf(year);
  return index >= 0 ? index : Math.max(0, result.years.length - 1);
}

function quantile(values: number[], probability: number): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((left, right) => left - right);
  const position = (sorted.length - 1) * probability;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  return lower === upper
    ? sorted[lower]
    : sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower);
}

function ScenarioChart({
  years,
  series,
  color,
  formatter = formatCompact,
  selectedIndex,
  onPin,
}: {
  years: number[];
  series: ScenarioSeries;
  color: string;
  formatter?: (value: number) => string;
  selectedIndex?: number;
  onPin?: (index: number) => void;
}) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const chartContainer = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(840);
  useEffect(() => {
    const node = chartContainer.current;
    if (!node) return;
    const observer = new ResizeObserver((entries) =>
      setWidth(Math.max(300, entries[0].contentRect.width)),
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  const height = width < 500 ? 260 : 300;
  const padding = { top: 22, right: 24, bottom: 34, left: 68 };
  const values = [...series.p25, ...series.p75, ...series.average];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(max - min, Math.abs(max) * 0.03, 1);
  const yMin = min >= 0 ? 0 : min - span * 0.08;
  const yMax = max + span * 0.08;
  const x = (index: number) =>
    padding.left +
    (index / Math.max(years.length - 1, 1)) *
      (width - padding.left - padding.right);
  const y = (value: number) =>
    height -
    padding.bottom -
    ((value - yMin) / (yMax - yMin)) * (height - padding.top - padding.bottom);
  const path = (line: number[]) =>
    line
      .map(
        (value, index) =>
          `${index === 0 ? "M" : "L"}${x(index).toFixed(1)},${y(value).toFixed(1)}`,
      )
      .join(" ");
  const band = `${path(series.p75)} ${series.p25
    .slice()
    .reverse()
    .map(
      (value, index) =>
        `L${x(series.p25.length - 1 - index).toFixed(1)},${y(value).toFixed(1)}`,
    )
    .join(" ")} Z`;
  const activeIndex =
    hoveredIndex ?? selectedIndex ?? Math.max(0, years.length - 1);
  const todayYear = new Date().getFullYear();
  const todayIndex = years.indexOf(todayYear);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map(
    (fraction) => yMin + (yMax - yMin) * fraction,
  );
  const pointerIndex = (event: React.MouseEvent<SVGRectElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const fraction = Math.min(
      1,
      Math.max(0, (event.clientX - bounds.left) / bounds.width),
    );
    return Math.round(fraction * Math.max(years.length - 1, 1));
  };

  return (
    <div className="chart-wrap" ref={chartContainer}>
      <div className="chart-stage">
        <svg
          className="chart"
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label="Average forecast with 25th to 75th percentile uncertainty band"
        >
          {ticks.map((tick) => (
            <g key={tick}>
              <line
                x1={padding.left}
                x2={width - padding.right}
                y1={y(tick)}
                y2={y(tick)}
                className="chart-grid"
              />
              <text
                x={padding.left - 12}
                y={y(tick) + 4}
                textAnchor="end"
                className="chart-label"
              >
                {formatter(tick)}
              </text>
            </g>
          ))}
          <path d={band} fill={color} opacity="0.13" />
          <path
            d={path(series.p75)}
            fill="none"
            stroke="#ff6b6b"
            strokeWidth="1.4"
            opacity="0.8"
            strokeDasharray="5 5"
          />
          <path
            d={path(series.p25)}
            fill="none"
            stroke="#ff6b6b"
            strokeWidth="1.4"
            opacity="0.8"
            strokeDasharray="5 5"
          />
          <path
            d={path(series.average)}
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="chart-average"
          />
          {years.map((year, index) =>
            index %
              Math.max(1, Math.ceil(years.length / (width < 500 ? 4 : 7))) ===
              0 || index === years.length - 1 ? (
              <text
                key={year}
                x={x(index)}
                y={height - 9}
                textAnchor="middle"
                className="chart-label"
              >
                {year}
              </text>
            ) : null,
          )}
          {todayIndex >= 0 ? (
            <g aria-label={`Today, ${todayYear}`}>
              <line
                x1={x(todayIndex)}
                x2={x(todayIndex)}
                y1={padding.top}
                y2={height - padding.bottom}
                className="chart-today"
              />
              <text
                x={x(todayIndex)}
                y={padding.top - 8}
                textAnchor="middle"
                className="chart-today-label"
              >
                today · {todayYear}
              </text>
              <circle
                cx={x(todayIndex)}
                cy={y(series.average[todayIndex])}
                r="4"
                fill={color}
                className="chart-today-point"
              />
            </g>
          ) : null}
          <line
            x1={x(activeIndex)}
            x2={x(activeIndex)}
            y1={padding.top}
            y2={height - padding.bottom}
            className="chart-cursor"
            opacity={hoveredIndex === null ? 0.35 : 0.9}
          />
          <circle
            cx={x(activeIndex)}
            cy={y(series.average[activeIndex])}
            r="5"
            fill={color}
            className="chart-point"
          />
          <rect
            x={padding.left}
            y={padding.top}
            width={width - padding.left - padding.right}
            height={height - padding.top - padding.bottom}
            fill="transparent"
            onMouseMove={(event) => setHoveredIndex(pointerIndex(event))}
            onMouseLeave={() => setHoveredIndex(null)}
            onClick={(event) => onPin?.(pointerIndex(event))}
            onKeyDown={(event) => {
              if (event.key === "Escape") setHoveredIndex(null);
              if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
                event.preventDefault();
                onPin?.(
                  Math.max(
                    0,
                    Math.min(
                      years.length - 1,
                      activeIndex + (event.key === "ArrowRight" ? 1 : -1),
                    ),
                  ),
                );
              }
              if (event.key === "Enter" || event.key === " ")
                onPin?.(activeIndex);
            }}
            tabIndex={0}
            aria-label="Hover to preview a year, then click to pin it"
          />
        </svg>
        <div
          className={`chart-tooltip ${hoveredIndex === null ? "is-hidden" : ""}`}
          style={{
            left: `${Math.min(82, Math.max(18, (x(activeIndex) / width) * 100))}%`,
          }}
        >
          <strong>{years[activeIndex]}</strong>
          <span>Mean {formatter(series.average[activeIndex])}</span>
          <span>
            P25–P75 {formatter(series.p25[activeIndex])}–
            {formatter(series.p75[activeIndex])}
          </span>
        </div>
      </div>
      <div className="chart-legend">
        <span className="legend-line" style={{ backgroundColor: color }} /> mean{" "}
        <span className="legend-band" style={{ backgroundColor: color }} />{" "}
        middle 50%{" "}
        {todayIndex >= 0 ? (
          <>
            <span className="legend-today" /> today
          </>
        ) : null}
        <span className="legend-hint">hover to preview · click to pin</span>
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  range,
  tone = "red",
}: {
  label: string;
  value: string;
  range: string;
  tone?: "red" | "blue" | "amber" | "green";
}) {
  return (
    <article className={`metric-card tone-${tone}`}>
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{range}</span>
    </article>
  );
}

function SliderField({
  label,
  value,
  min,
  max,
  step,
  display,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  display: string;
  onChange: (value: number) => void;
}) {
  return (
    <label className="slider-field">
      <span className="field-label">
        <span>{label}</span>
        <em>{display}</em>
      </span>
      <input
        type="range"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}

function NumberField({
  label,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="number-field">
      <span>{label}</span>
      <div>
        <input
          type="number"
          value={value}
          min={min}
          max={max}
          step={step}
          onChange={(event) => {
            const next = Number(event.target.value);
            if (Number.isFinite(next)) onChange(next);
          }}
        />
      </div>
    </label>
  );
}

function LoadingPanel({
  progress,
  status,
  onCancel,
}: {
  progress: number;
  status: string;
  onCancel: () => void;
}) {
  const [paused, setPaused] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const startedAt = useRef(Date.now());
  const lastUpdate = useRef(Date.now());
  useEffect(() => {
    lastUpdate.current = Date.now();
  }, [progress]);
  useEffect(() => {
    const timer = window.setInterval(
      () => setElapsed((Date.now() - startedAt.current) / 1000),
      300,
    );
    return () => window.clearInterval(timer);
  }, []);
  const milestones = [0.12, 0.26, 0.49, 0.68, 0.9].filter(
    (value) => progress >= value,
  ).length;
  const messages = [
    "Preparing model",
    "Operating assumptions sampled",
    "Production scenarios sampled",
    "Fleet timeline built",
    "Network operations calculated",
    "Finishing result summaries",
  ];
  return (
    <section className="loading-panel" aria-label="Simulation progress">
      {elapsed >= 0.3 && <LoadingCar paused={paused} />}
      <div className="loading-copy">
        <p className="eyebrow">Simulation in progress</p>
        <h2 role="status">{messages[milestones]}</h2>
        <p>
          {milestones > 0 && milestones < 5
            ? "Last update from the model worker."
            : "Your simulation runs locally in this browser."}
        </p>
        <div
          className="milestones"
          aria-label={`${milestones} of 5 model milestones reported`}
        >
          {[0, 1, 2, 3, 4].map((i) => (
            <i key={i} className={i < milestones ? "done" : ""} />
          ))}
        </div>
        <div className="loading-meta">
          <span>
            {activeRunDraws.toLocaleString()} draws · {Math.floor(elapsed)}s
            elapsed
          </span>
          <span>{milestones} / 5 milestones</span>
        </div>
        {Date.now() - lastUpdate.current > 10000 && (
          <p>Still working. The next milestone may take longer.</p>
        )}
        <div className="loading-actions">
          <button
            className="text-button"
            aria-pressed={paused}
            onClick={() => setPaused(!paused)}
          >
            {paused ? "Resume motion" : "Pause motion"}
          </button>
          <button className="text-button" onClick={onCancel}>
            Cancel run
          </button>
        </div>
      </div>
    </section>
  );
}

function AdvancedEditor({
  configJson,
  setConfigJson,
  jsonError,
  onApply,
  onClose,
}: {
  configJson: string;
  setConfigJson: (value: string) => void;
  jsonError: string;
  onApply: () => boolean;
  onClose: () => void;
}) {
  const [tab, setTab] = useState("generalInputs");
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  let draft: Record<string, unknown> | null = null;
  try {
    draft = JSON.parse(configJson);
  } catch {
    /* Keep invalid JSON editable. */
  }
  const labels: Record<string, string> = {
    generalInputs: "Operating ranges",
    growthByYear: "Annual growth",
    regionalDistribution: "Regional distribution",
    regionalShares: "Fallback shares",
    deploymentDates: "Deployment dates",
    impact: "Environment & productivity",
    vmt: "US vehicle miles",
    run: "Run settings",
    json: "Import / export",
  };
  const change = (path: string[], value: unknown) => {
    if (!draft) return;
    const next = structuredClone(draft);
    let target = next;
    path.slice(0, -1).forEach((key) => {
      target = target[key] as Record<string, unknown>;
    });
    target[path.at(-1)!] = value;
    setConfigJson(JSON.stringify(next, null, 2));
  };
  const fields = (value: unknown, path: string[]): React.ReactNode => {
    if (value && typeof value === "object")
      return (
        <div
          className={
            "min" in value && "max" in value ? "range-fields" : "nested-fields"
          }
        >
          {Object.entries(value).map(([key, child]) => (
            <div key={key} className="advanced-field">
              <label>
                {(
                  (path[0] === "deploymentDates"
                    ? {
                        bear: "Pessimistic date",
                        bull: "Optimistic date",
                        min: "Earliest",
                        max: "Latest",
                      }
                    : {
                        bear: "Lower assumption",
                        bull: "Upper assumption",
                        min: "Minimum",
                        max: "Maximum",
                      }) as Record<string, string>
                )[key] ??
                  (
                    {
                      "Price/Mile": "Fare · USD / mile",
                      "Price/Mile Asia": "Asia fare · USD / mile",
                      "Costs/Mile": "Operating cost · USD / mile",
                      "% ocupacy": "Occupancy · fraction",
                      "Car Lifespan": "Vehicle lifespan · years",
                      co2PerMile: "Emissions · grams CO₂ / mile",
                      co2Produced: "Annual baseline emissions · tonnes CO₂",
                      productivityPerHour: "Productivity · USD / hour",
                      gdpByRegion: "Regional GDP · USD / year",
                    } as Record<string, string>
                  )[key] ??
                  key.replace(/([a-z])([A-Z])/g, "$1 $2")}
              </label>
              {fields(child, [...path, key])}
            </div>
          ))}
        </div>
      );
    const name = path.join(" / ");
    if (path[0] === "deploymentDates" && typeof value === "string") {
      const parts = value.split("/");
      const iso =
        parts.length === 3
          ? `${parts[2]}-${parts[1].padStart(2, "0")}-${parts[0].padStart(2, "0")}`
          : "";
      return (
        <input
          aria-label={name}
          type="date"
          value={iso}
          onChange={(e) => {
            const [year, month, day] = e.target.value.split("-");
            if (year && month && day) change(path, `${day}/${month}/${year}`);
          }}
        />
      );
    }
    return typeof value === "boolean" ? (
      <input
        aria-label={name}
        type="checkbox"
        checked={value}
        onChange={(e) => change(path, e.target.checked)}
      />
    ) : (
      <input
        aria-label={name}
        type={typeof value === "number" ? "number" : "text"}
        step="any"
        value={String(value ?? "")}
        onChange={(e) =>
          change(
            path,
            typeof value === "number" ? Number(e.target.value) : e.target.value,
          )
        }
      />
    );
  };
  return (
    <dialog
      ref={dialog}
      className="advanced-modal"
      onCancel={onClose}
      onClose={onClose}
    >
      <header className="modal-header">
        <div>
          <p className="eyebrow">Scenario editor</p>
          <h2>Advanced assumptions</h2>
          <p>
            Adjust distributions and regional constants. Changes apply together
            after validation.
          </p>
        </div>
        <button
          className="icon-button"
          aria-label="Close advanced editor"
          onClick={onClose}
        >
          ×
        </button>
      </header>
      <div className="editor-layout">
        <nav className="editor-nav">
          {Object.entries(labels).map(([key, label]) => (
            <button
              key={key}
              className={tab === key ? "active" : ""}
              onClick={() => setTab(key)}
            >
              {label}
            </button>
          ))}
        </nav>
        <div className="editor-content">
          <h3>{labels[tab]}</h3>
          <p className="control-note">
            {tab === "deploymentDates"
              ? "Dates are displayed in your browser locale. The model stores day/month/year. Optimistic deployment precedes pessimistic deployment."
              : "Ranges use native model units. Fractions: 0.20 = 20%. Minimum ≤ lower ≤ upper ≤ maximum."}
          </p>
          {tab === "json" ? (
            <>
              <textarea
                aria-label="Full notebook configuration JSON"
                value={configJson}
                onChange={(e) => setConfigJson(e.target.value)}
                spellCheck={false}
              />
              <button
                className="secondary-button"
                onClick={() => {
                  const url = URL.createObjectURL(
                    new Blob([configJson], { type: "application/json" }),
                  );
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = "robotaxi-assumptions.json";
                  a.click();
                  URL.revokeObjectURL(url);
                }}
              >
                Export JSON
              </button>
              <label className="import-label">
                Import JSON
                <input
                  type="file"
                  accept=".json,application/json"
                  onChange={async (e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      setConfigJson(await file.text());
                      setTab("json");
                    }
                  }}
                />
              </label>
            </>
          ) : draft ? (
            tab === "run" ? (
              <>
                {["yearsToSimulate", "numSimulations", "seed"].map((key) => (
                  <div className="advanced-field" key={key}>
                    <label>{key}</label>
                    {fields(draft![key], [key])}
                  </div>
                ))}
              </>
            ) : (
              fields(draft[tab], [tab])
            )
          ) : (
            <p role="alert">
              Fix the JSON syntax in Import / export to use the form.
            </p>
          )}
          {jsonError && (
            <p className="validation" role="alert">
              {jsonError}
            </p>
          )}
        </div>
      </div>
      <footer className="modal-footer">
        <span>
          {jsonError ? (
            <span className="validation" role="alert">
              {jsonError}
            </span>
          ) : (
            "Closing preserves unapplied edits."
          )}
        </span>
        <button
          className="primary-button"
          onClick={() => {
            if (onApply()) onClose();
          }}
        >
          Validate & apply
        </button>
      </footer>
    </dialog>
  );
}

function getMetric(
  result: SimulationResult,
  metric: MetricKey,
): {
  title: string;
  unit: string;
  color: string;
  series: ScenarioSeries | null;
  formatter: (value: number) => string;
} {
  switch (metric) {
    case "revenue":
      return {
        title: "Tesla platform revenue",
        unit: "USD / annual",
        color: "#7bc7a4",
        series: result.revenue,
        formatter: formatDollars,
      };
    case "fleet":
      return {
        title: "Tesla fleet in service",
        unit: "vehicles / surviving stock",
        color: "#77a8d7",
        series: result.fleet,
        formatter: formatCompact,
      };
    case "production":
      return {
        title: "Tesla production",
        unit: "vehicles / annual",
        color: "#8aaed2",
        series: result.production,
        formatter: formatCompact,
      };
    case "discontinued":
      return {
        title: "Vehicles retired",
        unit: "vehicles / annual",
        color: "#657f9a",
        series: result.discontinued,
        formatter: formatCompact,
      };
    case "milesPerCar":
      return {
        title: "Miles per participating car",
        unit: "miles / car / year",
        color: "#9da7df",
        series: result.milesPerCar,
        formatter: formatCompact,
      };
    case "co2":
      return {
        title: "CO₂ avoided",
        unit: "tonnes / annual",
        color: "#e9b86b",
        series: result.co2Saved,
        formatter: (value) => `${formatCompact(value)} t`,
      };
    case "cars":
      return {
        title: "Cars displaced",
        unit: "vehicles / annual",
        color: "#cf8de1",
        series: result.carsDisplaced,
        formatter: formatCompact,
      };
    case "pollution":
      return {
        title: "US pollution savings",
        unit: "USD / annual",
        color: "#d67fa5",
        series: result.pollutionSavings,
        formatter: formatDollars,
      };
    case "hours":
      return {
        title: "Hours unlocked",
        unit: "hours / annual",
        color: "#6cc4cc",
        series: result.hoursSaved,
        formatter: formatCompact,
      };
    case "years":
      return {
        title: "Person-years unlocked",
        unit: "person-years / annual",
        color: "#6fa4a6",
        series: result.yearsSaved,
        formatter: formatCompact,
      };
    case "gdp":
      return {
        title: "Potential GDP",
        unit: "USD / annual",
        color: "#d99d77",
        series: result.extraGdp,
        formatter: formatDollars,
      };
    case "vmt":
      return {
        title: "US VMT share",
        unit: "share / annual",
        color: "#b3c777",
        series: result.usPercentageVmt,
        formatter: formatPercent,
      };
    default:
      return {
        title: "Robotaxi miles",
        unit: "miles / annual",
        color: "#cc0000",
        series: result.robotaxiMiles,
        formatter: formatCompact,
      };
  }
}

const metricItems: {
  key: MetricKey;
  label: string;
  note: string;
  category: "Network" | "Economics" | "Impact";
}[] = [
  {
    key: "miles",
    label: "Robotaxi miles",
    note: "network demand",
    category: "Network",
  },
  {
    key: "fleet",
    label: "Fleet in service",
    note: "vehicles",
    category: "Network",
  },
  {
    key: "production",
    label: "Production",
    note: "vehicles built",
    category: "Network",
  },
  {
    key: "discontinued",
    label: "Retirements",
    note: "vehicles retired",
    category: "Network",
  },
  {
    key: "milesPerCar",
    label: "Miles per car",
    note: "operating intensity",
    category: "Network",
  },
  { key: "vmt", label: "US VMT share", note: "coverage", category: "Network" },
  {
    key: "revenue",
    label: "Platform revenue",
    note: "Tesla economics",
    category: "Economics",
  },
  { key: "co2", label: "CO₂ avoided", note: "emissions", category: "Impact" },
  {
    key: "cars",
    label: "Cars displaced",
    note: "mobility",
    category: "Impact",
  },
  {
    key: "pollution",
    label: "Pollution savings",
    note: "US externality",
    category: "Impact",
  },
  { key: "hours", label: "Hours unlocked", note: "time", category: "Impact" },
  {
    key: "years",
    label: "Person-years",
    note: "time conversion",
    category: "Impact",
  },
  {
    key: "gdp",
    label: "Potential GDP",
    note: "productivity",
    category: "Impact",
  },
];

export function RobotaxiLab() {
  const [config, setConfig] = useState<SimulationConfig>(() =>
    cloneConfig(DEFAULT_CONFIG),
  );
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [lastRunConfig, setLastRunConfig] = useState<SimulationConfig | null>(
    null,
  );
  const [targetYear, setTargetYear] = useState(2030);
  const [status, setStatus] = useState("Ready when you are");
  const [progress, setProgress] = useState(0);
  const [running, setRunning] = useState(false);
  const [inputMode, setInputMode] = useState<InputMode>("simple");
  const [resultDepth, setResultDepth] = useState<ResultDepth>("overview");
  const [activeMetric, setActiveMetric] = useState<MetricKey>("miles");
  const [activePreset, setActivePreset] = useState<
    "base" | "conservative" | "aggressive" | "custom"
  >("base");
  const [mobileInputs, setMobileInputs] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [configJson, setConfigJson] = useState(() =>
    JSON.stringify(DEFAULT_CONFIG, null, 2),
  );
  const [jsonError, setJsonError] = useState("");
  const workerRef = useRef<Worker | null>(null);
  const errors = useMemo(() => validateConfig(config), [config]);
  const selectedYear = result?.years.includes(targetYear)
    ? targetYear
    : (result?.years.at(-1) ?? 2030);
  const selectedIndex = result ? yearIndex(result, selectedYear) : 0;
  const draftChanged = Boolean(
    lastRunConfig && JSON.stringify(config) !== JSON.stringify(lastRunConfig),
  );
  const advancedChangedCount = useMemo(
    () =>
      [
        "growthByYear",
        "regionalDistribution",
        "regionalShares",
        "deploymentDates",
        "impact",
        "vmt",
        "generalInputs",
      ].filter(
        (key) =>
          JSON.stringify(config[key as keyof SimulationConfig]) !==
          JSON.stringify(DEFAULT_CONFIG[key as keyof SimulationConfig]),
      ).length,
    [config],
  );

  useEffect(() => () => workerRef.current?.terminate(), []);
  useEffect(() => setConfigJson(JSON.stringify(config, null, 2)), [config]);

  const run = () => {
    if (errors.length > 0 || running) return;
    activeRunDraws = config.numSimulations;
    workerRef.current?.terminate();
    const worker = new Worker(
      new URL("../lib/simulation.worker.ts", import.meta.url),
    );
    workerRef.current = worker;
    setMobileInputs(false);
    setRunning(true);
    setProgress(0.01);
    setStatus(
      `Starting ${config.numSimulations.toLocaleString()} Monte Carlo draws`,
    );
    worker.onmessage = (event: MessageEvent<WorkerMessage>) => {
      if (workerRef.current !== worker) return;
      const message = event.data;
      if (message.type === "progress") {
        setProgress(message.value);
        setStatus(message.label);
      } else if (message.type === "success") {
        setResult(message.result);
        setLastRunConfig(cloneConfig(config));
        setProgress(1);
        setRunning(false);
        setStatus(
          `Complete in ${(message.result.runtimeMs / 1000).toFixed(2)}s`,
        );
        worker.terminate();
      } else {
        setRunning(false);
        setStatus(message.message);
        setProgress(0);
        worker.terminate();
      }
    };
    worker.onerror = () => {
      if (workerRef.current === worker) {
        setRunning(false);
        setStatus("Simulation failed. Retry the run.");
        worker.terminate();
      }
    };
    worker.postMessage({ config: cloneConfig(config) });
  };
  useEffect(() => {
    run();
    return () => {
      workerRef.current?.terminate();
      workerRef.current = null;
    };
  }, []);
  const cancel = () => {
    workerRef.current?.terminate();
    workerRef.current = null;
    setRunning(false);
    setStatus("Run cancelled · draft and previous result preserved");
    setProgress(0);
  };
  const update = (changes: Partial<SimulationConfig>) => {
    setActivePreset("custom");
    setConfig((current) => {
      const next = { ...current, ...changes };
      if (changes.networkParticipation !== undefined)
        next.generalInputs = {
          ...next.generalInputs,
          "Network Participation": stretchBearRange(
            next.generalInputs["Network Participation"],
            changes.networkParticipation,
          ),
        };
      if (changes.hoursPerDay !== undefined)
        next.generalInputs = {
          ...next.generalInputs,
          "Hours/day": stretchBearRange(
            next.generalInputs["Hours/day"],
            changes.hoursPerDay,
          ),
        };
      if (changes.milesPerHour !== undefined)
        next.generalInputs = {
          ...next.generalInputs,
          "Miles/hour": stretchBearRange(
            next.generalInputs["Miles/hour"],
            changes.milesPerHour,
          ),
        };
      if (changes.occupancyPct !== undefined)
        next.generalInputs = {
          ...next.generalInputs,
          "% ocupacy": stretchBearRange(
            next.generalInputs["% ocupacy"],
            changes.occupancyPct,
          ),
        };
      if (changes.carLifespan !== undefined)
        next.generalInputs = {
          ...next.generalInputs,
          "Car Lifespan": stretchBearRange(
            next.generalInputs["Car Lifespan"],
            changes.carLifespan,
          ),
        };
      if (changes.pricePerMile !== undefined)
        next.generalInputs = {
          ...next.generalInputs,
          "Price/Mile": stretchBearRange(
            next.generalInputs["Price/Mile"],
            changes.pricePerMile,
          ),
        };
      if (changes.platformFee !== undefined)
        next.generalInputs = {
          ...next.generalInputs,
          "Platform fee": stretchBearRange(
            next.generalInputs["Platform fee"],
            changes.platformFee,
          ),
        };
      return cloneConfig(next);
    });
  };
  const applyPreset = (preset: "base" | "conservative" | "aggressive") => {
    setActivePreset(preset);
    setConfig((current) => {
      const next = cloneConfig(current);
      const source = preset === "base" ? DEFAULT_CONFIG : PRESETS[preset];
      next.networkParticipation = source.networkParticipation!;
      next.generalInputs["Network Participation"] = {
        ...source.generalInputs!["Network Participation"],
      };
      next.growth = { ...source.growth! };
      next.growthByYear =
        preset === "base"
          ? structuredClone(DEFAULT_CONFIG.growthByYear)
          : Object.fromEntries(
              Object.keys(next.growthByYear).map((year) => [
                year,
                { ...next.growth },
              ]),
            );
      return next;
    });
    setStatus(
      "Preset updated participation and annual growth. Run to update results.",
    );
  };
  const applyJson = (): boolean => {
    try {
      const parsed = JSON.parse(configJson) as Partial<SimulationConfig>;
      const defaults = cloneConfig(DEFAULT_CONFIG);
      const next = cloneConfig({
        ...defaults,
        ...parsed,
        generalInputs: {
          ...defaults.generalInputs,
          ...(parsed.generalInputs ?? {}),
        },
        growthByYear: {
          ...defaults.growthByYear,
          ...(parsed.growthByYear ?? {}),
        },
        regionalDistribution: {
          ...defaults.regionalDistribution,
          ...(parsed.regionalDistribution ?? {}),
        },
        regionalShares: {
          ...defaults.regionalShares,
          ...(parsed.regionalShares ?? {}),
        },
        deploymentDates: {
          ...defaults.deploymentDates,
          ...(parsed.deploymentDates ?? {}),
        },
        impact: {
          ...defaults.impact,
          ...(parsed.impact ?? {}),
          co2PerMile: {
            ...defaults.impact.co2PerMile,
            ...(parsed.impact?.co2PerMile ?? {}),
          },
          co2Produced: {
            ...defaults.impact.co2Produced,
            ...(parsed.impact?.co2Produced ?? {}),
          },
          productivityPerHour: {
            ...defaults.impact.productivityPerHour,
            ...(parsed.impact?.productivityPerHour ?? {}),
          },
          gdpByRegion: {
            ...defaults.impact.gdpByRegion,
            ...(parsed.impact?.gdpByRegion ?? {}),
          },
        },
        vmt: { ...defaults.vmt, ...(parsed.vmt ?? {}) },
      });
      const nextErrors = validateConfig(next);
      if (nextErrors.length > 0) {
        setJsonError(nextErrors.join(" "));
        return false;
      }
      const aliases = {
        networkParticipation: "Network Participation",
        hoursPerDay: "Hours/day",
        occupancyPct: "% ocupacy",
        pricePerMile: "Price/Mile",
        platformFee: "Platform fee",
      } as const;
      for (const [scalar, key] of Object.entries(aliases))
        (next as unknown as Record<string, unknown>)[scalar] =
          next.generalInputs[key].bear;
      setConfig(next);
      setActivePreset("custom");
      setJsonError("");
      setStatus("Configuration staged · run to update results");
      return true;
    } catch (error) {
      setJsonError(
        error instanceof Error
          ? error.message
          : "Configuration JSON is invalid.",
      );
      return false;
    }
  };

  const active = result ? getMetric(result, activeMetric) : null;
  const setYearFromChart = (index: number) => {
    if (result) setTargetYear(result.years[index]);
  };
  const yearLabel = result
    ? `${result.years[0]}–${result.years.at(-1)}`
    : `2022–${config.yearsToSimulate}`;

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top">
          <img src="/robotaxi-outline.svg" width="72" height="24" alt="" />
          <span>
            <strong>Robotaxi thesis lab</strong>
            <small>browser workbench · research prototype</small>
          </span>
        </a>
        <div className="top-actions">
          <span className="local-status">
            <i /> local execution
          </span>
          <a href="#method">Method</a>
        </div>
      </header>
      <div className="app-grid" id="top">
        <button
          className="mobile-input-toggle secondary-button"
          aria-expanded={mobileInputs}
          onClick={() => setMobileInputs(!mobileInputs)}
        >
          {mobileInputs ? "Close assumptions" : "Edit assumptions"}{" "}
          <span>{draftChanged ? "Unsaved run" : "Scenario controls"}</span>
        </button>
        <aside
          className={`controls-panel ${mobileInputs ? "mobile-open" : ""}`}
          aria-label="Model assumptions"
        >
          <div className="controls-heading">
            <div>
              <p className="eyebrow">01 / Inputs</p>
              <h2>Assumptions</h2>
            </div>
            <span className="draft-chip">
              {activePreset === "base" ? "reference" : activePreset}
            </span>
          </div>
          <div className="segmented" aria-label="Input detail">
            <button
              type="button"
              className={inputMode === "simple" ? "active" : ""}
              onClick={() => setInputMode("simple")}
            >
              Simple
            </button>
            <button
              type="button"
              className={inputMode === "advanced" ? "active" : ""}
              onClick={() => {
                setInputMode("advanced");
                setAdvancedOpen(true);
              }}
            >
              Advanced
              {advancedChangedCount > 0 ? <b>{advancedChangedCount}</b> : null}
            </button>
          </div>
          {inputMode === "simple" ? (
            <>
              <div className="preset-block">
                <span className="control-label">Starting point</span>
                <div className="preset-buttons">
                  {(["conservative", "base", "aggressive"] as const).map(
                    (preset) => (
                      <button
                        type="button"
                        className={activePreset === preset ? "active" : ""}
                        key={preset}
                        onClick={() => applyPreset(preset)}
                      >
                        {preset === "base" ? "Reference" : preset}
                      </button>
                    ),
                  )}
                </div>
                <p className="control-note">
                  Reference values from the thesis. Controls edit the lower
                  assumption, not a fixed outcome.
                </p>
              </div>
              <div className="control-section">
                <div className="section-kicker">Scenario controls</div>
                <SliderField
                  label="Network participation"
                  value={config.networkParticipation}
                  min={0.05}
                  max={0.8}
                  step={0.01}
                  display={formatPercent(config.networkParticipation)}
                  onChange={(value) => update({ networkParticipation: value })}
                />
                <SliderField
                  label="Hours per day"
                  value={config.hoursPerDay}
                  min={1}
                  max={24}
                  step={0.5}
                  display={`${config.hoursPerDay.toFixed(1)} h`}
                  onChange={(value) => update({ hoursPerDay: value })}
                />
                <SliderField
                  label="Occupancy"
                  value={config.occupancyPct}
                  min={0.05}
                  max={1}
                  step={0.01}
                  display={formatPercent(config.occupancyPct)}
                  onChange={(value) => update({ occupancyPct: value })}
                />
                <SliderField
                  label="Price per mile"
                  value={config.pricePerMile}
                  min={0.1}
                  max={5}
                  step={0.05}
                  display={`$${config.pricePerMile.toFixed(2)}`}
                  onChange={(value) => update({ pricePerMile: value })}
                />
                <SliderField
                  label="Platform fee"
                  value={config.platformFee}
                  min={0}
                  max={0.8}
                  step={0.01}
                  display={formatPercent(config.platformFee)}
                  onChange={(value) => update({ platformFee: value })}
                />
              </div>
              <div className="control-section compact-controls">
                <div className="section-kicker">Run shape</div>
                <NumberField
                  label="End year"
                  value={config.yearsToSimulate}
                  min={2022}
                  max={2050}
                  step={1}
                  onChange={(value) => update({ yearsToSimulate: value })}
                />
                <NumberField
                  label="Draws"
                  value={config.numSimulations}
                  min={100}
                  max={5000}
                  step={100}
                  onChange={(value) => update({ numSimulations: value })}
                />
              </div>
              <button
                className="advanced-link"
                type="button"
                onClick={() => {
                  setInputMode("advanced");
                  setAdvancedOpen(true);
                }}
              >
                Edit full notebook configuration <span>↗</span>
              </button>
            </>
          ) : (
            <div className="advanced-callout">
              <p className="eyebrow">Full editor</p>
              <h3>Every assumption stays in one draft.</h3>
              <p>
                Open the advanced editor to inspect year-by-year growth,
                regional deployment, impact constants and the exact JSON
                contract.
              </p>
              <button
                className="secondary-button"
                type="button"
                onClick={() => setAdvancedOpen(true)}
              >
                Open advanced editor <span>↗</span>
              </button>
              <button
                className="text-button"
                type="button"
                onClick={() => setInputMode("simple")}
              >
                Back to Simple inputs
              </button>
            </div>
          )}
          {errors.length > 0 ? (
            <div className="validation">
              {errors.map((error) => (
                <p key={error}>{error}</p>
              ))}
            </div>
          ) : null}
          <button
            className="text-button reset-button"
            onClick={() => {
              setConfig(cloneConfig(DEFAULT_CONFIG));
              setActivePreset("base");
            }}
          >
            Reset to thesis reference
          </button>
          <div className="run-area">
            <button
              className="run-button"
              type="button"
              disabled={errors.length > 0 || running}
              onClick={run}
            >
              {running
                ? "Running model"
                : draftChanged
                  ? "Run updated scenario"
                  : "Run simulation"}
              <span>{running ? "···" : "↗"}</span>
            </button>
            <div className="run-line">
              <div className="progress-track">
                <span style={{ width: `${progress * 100}%` }} />
              </div>
              <span className="status" aria-live="polite">
                {status}
              </span>
            </div>
          </div>
        </aside>
        <section
          className="results-canvas"
          id="results"
          aria-label="Model results"
        >
          <div className="results-heading">
            <div>
              <p className="eyebrow">02 / Results · {yearLabel}</p>
              <h1>
                {metricItems.find((item) => item.key === activeMetric)
                  ?.category === "Economics"
                  ? "What could the network earn?"
                  : metricItems.find((item) => item.key === activeMetric)
                        ?.category === "Impact"
                    ? "What changes beyond the ride?"
                    : "How far could a robotaxi network go?"}
              </h1>
              <p>
                Change the assumptions, run the draws locally, and read the
                uncertainty as a range rather than a single forecast.
              </p>
            </div>
            <div className="segmented result-toggle" aria-label="Result detail">
              <button
                type="button"
                className={resultDepth === "overview" ? "active" : ""}
                onClick={() => setResultDepth("overview")}
              >
                Overview
              </button>
              <button
                type="button"
                className={resultDepth === "explore" ? "active" : ""}
                onClick={() => setResultDepth("explore")}
              >
                Explore
              </button>
            </div>
          </div>
          {draftChanged ? (
            <div className="stale-banner">
              <span>
                <i />
                Inputs changed since the visible run.
              </span>
              <button type="button" onClick={run} disabled={running}>
                {running ? "Running…" : "Run to update ↗"}
              </button>
            </div>
          ) : null}
          {running ? (
            <LoadingPanel
              progress={progress}
              status={status}
              onCancel={cancel}
            />
          ) : null}
          {!result && !running ? (
            <div className="empty-state">
              <div className="empty-mark">
                <img src="/robotaxi-outline.svg" alt="" />
              </div>
              <div>
                <p className="eyebrow">Reference run</p>
                <h2>Start with the thesis scenario.</h2>
                <p>
                  The model runs entirely in this browser tab. Your first result
                  will include annual miles, revenue, fleet, impact and regional
                  uncertainty.
                </p>
                <button className="primary-button" type="button" onClick={run}>
                  Run reference model <span>↗</span>
                </button>
              </div>
            </div>
          ) : null}
          {result ? (
            <div className={`results-body ${running ? "is-running" : ""}`}>
              <div className="result-bar">
                <div>
                  <span className="eyebrow">Pinned year</span>
                  <input
                    type="range"
                    min={result.years[0]}
                    max={result.years.at(-1)}
                    value={selectedYear}
                    onChange={(event) =>
                      setTargetYear(Number(event.target.value))
                    }
                    aria-label="Pinned reporting year"
                  />
                  <strong>{selectedYear}</strong>
                </div>
                <span className="run-meta">
                  Run {result.sampleSize.toLocaleString()} draws · seed{" "}
                  {result.seed}
                </span>
              </div>
              <nav className="question-tabs" aria-label="Research question">
                {["Network", "Economics", "Impact"].map((category) => (
                  <button
                    key={category}
                    className={
                      metricItems.find((item) => item.key === activeMetric)
                        ?.category === category
                        ? "active"
                        : ""
                    }
                    onClick={() =>
                      setActiveMetric(
                        category === "Network"
                          ? "miles"
                          : category === "Economics"
                            ? "revenue"
                            : "co2",
                      )
                    }
                  >
                    {category}
                  </button>
                ))}
              </nav>
              <div className="metric-select">
                <label htmlFor="metric">Explore a measure</label>
                <select
                  id="metric"
                  value={activeMetric}
                  onChange={(e) => setActiveMetric(e.target.value as MetricKey)}
                >
                  {metricItems.map((item) => (
                    <option key={item.key} value={item.key}>
                      {item.category} / {item.label}
                    </option>
                  ))}
                </select>
              </div>
              {active?.series ? (
                <>
                  <div className="metric-grid">
                    <MetricCard
                      label={`${active.title} in ${selectedYear}`}
                      value={active.formatter(
                        active.series.average[selectedIndex],
                      )}
                      range={active.unit}
                    />
                    <MetricCard
                      label="Lower quartile · P25"
                      value={active.formatter(active.series.p25[selectedIndex])}
                      range="25% of draws fall below"
                    />
                    <MetricCard
                      label="Upper quartile · P75"
                      value={active.formatter(active.series.p75[selectedIndex])}
                      range="75% of draws fall below"
                    />
                  </div>
                  <section className="result-panel hero-panel">
                    <div className="panel-header">
                      <div>
                        <p className="eyebrow">
                          {running ? "Previous run" : "Completed scenario"}
                        </p>
                        <h2>{active.title}</h2>
                      </div>
                      <span className="unit">{active.unit}</span>
                    </div>
                    <ScenarioChart
                      key={activeMetric}
                      years={result.years}
                      series={active.series}
                      color="#cc0000"
                      formatter={active.formatter}
                      selectedIndex={selectedIndex}
                      onPin={setYearFromChart}
                    />
                    <p className="chart-definition">
                      {metricDescription(activeMetric)}
                    </p>
                  </section>
                  <section className="result-panel">
                    <div className="panel-header">
                      <h2>
                        {["cars", "pollution", "vmt"].includes(activeMetric)
                          ? "United States"
                          : "Regional breakdown"}
                      </h2>
                      <span className="unit">
                        {selectedYear} · {active.unit}
                      </span>
                    </div>
                    <RegionalBars
                      result={result}
                      selectedIndex={selectedIndex}
                      metric={activeMetric}
                      runConfig={lastRunConfig ?? config}
                    />
                  </section>
                  {activeMetric === "revenue" && (
                    <section className="result-panel">
                      <h2>Owner annual revenue</h2>
                      <OwnerLedger result={result} />
                    </section>
                  )}
                  {resultDepth === "explore" ? (
                    <DataTable result={result} metric={activeMetric} />
                  ) : (
                    <button
                      className="explore-prompt"
                      onClick={() => setResultDepth("explore")}
                    >
                      View annual data <span>Mean and both quartiles ↗</span>
                    </button>
                  )}
                </>
              ) : (
                <section className="result-panel unavailable">
                  <h2>{active?.title} is disabled</h2>
                  <p>Enable US VMT in Advanced assumptions and run again.</p>
                </section>
              )}
            </div>
          ) : null}
          <footer className="app-footer" id="method">
            <span>Thesis model · browser worker · reproducible seed</span>
            <span>Uncertainty shown as middle 50% unless stated</span>
          </footer>
        </section>
      </div>
      {advancedOpen ? (
        <AdvancedEditor
          configJson={configJson}
          setConfigJson={setConfigJson}
          jsonError={jsonError}
          onApply={applyJson}
          onClose={() => setAdvancedOpen(false)}
        />
      ) : null}
    </main>
  );
}

function metricDescription(metric: MetricKey) {
  if (metric === "fleet")
    return "Surviving Tesla vehicle stock. Participation and deployment availability are applied later when calculating network miles.";
  if (metric === "revenue")
    return "Modeled Tesla platform revenue from miles, fares and platform fees. Owner revenue is shown separately below.";
  if (metric === "co2")
    return "Annual avoided CO₂ covers USA, Europe and China. Other regions are not modeled.";
  if (["cars", "pollution", "vmt"].includes(metric))
    return "US measure only. Values describe the selected year under the thesis reference assumptions.";
  if (metric === "milesPerCar")
    return "Annual operating intensity per participating vehicle. This assumption is time-invariant, so the timeline is flat.";
  return "Mean across simulation draws. Dashed boundaries enclose the middle 50% of outcomes, not a confidence interval or a minimum and maximum.";
}
function RegionalBars({
  result,
  selectedIndex,
  metric,
  runConfig,
}: {
  result: SimulationResult;
  selectedIndex: number;
  metric: MetricKey;
  runConfig: SimulationConfig;
}) {
  const regional = (
    {
      miles: result.regionalMiles,
      fleet: result.regionalFleet,
      revenue: result.regionalRevenue,
      co2: result.regionalCo2Saved,
      hours: result.regionalHoursSaved,
      years: result.regionalYearsSaved,
      gdp: result.regionalExtraGdp,
    } as Record<string, SimulationResult["regionalFleet"]>
  )[metric];
  if (!regional)
    return (
      <p className="chart-definition">
        {["cars", "pollution", "vmt"].includes(metric)
          ? "This output covers the US only. Read its uncertainty in the chart above."
          : "The model returns this measure at the global level. A regional breakdown is not available."}
      </p>
    );
  const colors = ["#8ABEFF", "#77DFC3", "#F2C879", "#C1AAED", "#EDA9BC"];
  const max = Math.max(
    ...REGIONS.map((region) => Math.abs(regional[region].p75[selectedIndex])),
    1,
  );
  return (
    <div className="regional-bars">
      {REGIONS.map((region, index) => {
        const series = regional[region];
        const missing =
          (metric === "co2" && !["USA", "Europe", "China"].includes(region)) ||
          (metric === "gdp" &&
            runConfig.impact.productivityPerHour[region] === undefined);
        return (
          <div className="regional-row" key={region}>
            <div>
              <span>
                <i style={{ color: colors[index] }}>●</i> {region}
              </span>
              <strong>
                {missing
                  ? "Not modeled"
                  : getMetric(result, metric).formatter(
                      series.average[selectedIndex],
                    )}
              </strong>
            </div>
            {!missing && (
              <>
                <div className="regional-track">
                  <i
                    style={{
                      width: `${(Math.abs(series.average[selectedIndex]) / max) * 100}%`,
                      background: colors[index],
                    }}
                  />
                </div>
                <small>
                  Middle 50% ·{" "}
                  {getMetric(result, metric).formatter(
                    series.p25[selectedIndex],
                  )}{" "}
                  to{" "}
                  {getMetric(result, metric).formatter(
                    series.p75[selectedIndex],
                  )}
                </small>
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}

function MiniHistogram({
  label,
  values,
  color,
  domain,
}: {
  label: string;
  values: number[];
  color: string;
  domain: [number, number];
}) {
  const [min, max] = domain;
  const span = Math.max(max - min, 1);
  const bins = Array.from({ length: 12 }, () => 0);
  values.forEach((value) => {
    bins[
      Math.min(
        bins.length - 1,
        Math.floor(((value - min) / span) * bins.length),
      )
    ] += 1;
  });
  const peak = Math.max(...bins, 1);
  return (
    <div className="mini-histogram">
      <div className="histogram-heading">
        <span>{label}</span>
        <small>{formatDollars(quantile(values, 0.5))} median</small>
      </div>
      <div
        className="histogram-bars"
        aria-label={`${label} owner revenue distribution`}
      >
        {bins.map((bin, index) => (
          <i
            key={index}
            style={{ height: `${(bin / peak) * 100}%`, backgroundColor: color }}
          />
        ))}
      </div>
      <div className="histogram-axis">
        <span>{formatDollars(min)}</span>
        <span>{formatDollars(max)}</span>
      </div>
    </div>
  );
}

function OwnerLedger({ result }: { result: SimulationResult }) {
  const domain: [number, number] = [
    Math.min(...result.ownerRevenue.asia, ...result.ownerRevenue.nonAsia),
    Math.max(...result.ownerRevenue.asia, ...result.ownerRevenue.nonAsia),
  ];
  const nonAsia =
    result.ownerRevenue.nonAsia.reduce((sum, value) => sum + value, 0) /
    Math.max(result.ownerRevenue.nonAsia.length, 1);
  const asia =
    result.ownerRevenue.asia.reduce((sum, value) => sum + value, 0) /
    Math.max(result.ownerRevenue.asia.length, 1);
  return (
    <div className="owner-ledger">
      <div className="owner-histograms">
        <MiniHistogram
          domain={domain}
          label="Non-Asia"
          values={result.ownerRevenue.nonAsia}
          color="#7bc7a4"
        />
        <MiniHistogram
          domain={domain}
          label="Asia"
          values={result.ownerRevenue.asia}
          color="#77a8d7"
        />
      </div>
      <dl className="impact-ledger">
        <div>
          <dt>Mean owner revenue · non-Asia</dt>
          <dd>{formatDollars(nonAsia)}</dd>
        </div>
        <div>
          <dt>Mean owner revenue · Asia</dt>
          <dd>{formatDollars(asia)}</dd>
        </div>
        <div>
          <dt>Displacement coefficient</dt>
          <dd>
            {result.displacementCoefficient.length
              ? (
                  result.displacementCoefficient.reduce(
                    (sum, value) => sum + value,
                    0,
                  ) / result.displacementCoefficient.length
                ).toFixed(2)
              : "—"}
          </dd>
        </div>
      </dl>
      <p className="catalog-note">
        Owner values are annual distributions per participating vehicle. They do
        not use the reporting-year slider.
      </p>
    </div>
  );
}

function DataTable({
  result,
  metric,
}: {
  result: SimulationResult;
  metric: MetricKey;
}) {
  const active = getMetric(result, metric);
  if (!active.series) return null;
  const rows = result.years.map((year) => {
    const index = result.years.indexOf(year);
    return {
      year,
      mean: active.series!.average[index],
      p25: active.series!.p25[index],
      p75: active.series!.p75[index],
    };
  });
  return (
    <section className="result-panel data-table-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Selected measure</p>
          <h2>Annual data</h2>
        </div>
        <span className="unit">
          {active.unit}
          {metric === "vmt" ? " · raw fractions" : ""}
        </span>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Year</th>
              <th>Mean</th>
              <th>P25</th>
              <th>P75</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.year}>
                <th>{row.year}</th>
                <td>
                  {row.mean.toLocaleString("en-US", {
                    maximumFractionDigits: 4,
                  })}
                </td>
                <td>
                  {row.p25.toLocaleString("en-US", {
                    maximumFractionDigits: 4,
                  })}
                </td>
                <td>
                  {row.p75.toLocaleString("en-US", {
                    maximumFractionDigits: 4,
                  })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
