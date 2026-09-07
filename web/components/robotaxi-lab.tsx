"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { DEFAULT_CONFIG, PRESETS, REGIONS } from "../lib/data";
import { runSimulation, validateConfig } from "../lib/simulation";
import type { Region, ScenarioSeries, SimulationConfig, SimulationResult, WorkerMessage } from "../lib/types";

function cloneConfig(config: SimulationConfig): SimulationConfig {
  return {
    ...config,
    growth: { ...config.growth },
    generalInputs: Object.fromEntries(
      Object.entries(config.generalInputs).map(([key, range]) => [key, { ...range }]),
    ) as SimulationConfig["generalInputs"],
    growthByYear: Object.fromEntries(
      Object.entries(config.growthByYear).map(([year, range]) => [year, { ...range }]),
    ),
    regionalDistribution: Object.fromEntries(
      Object.entries(config.regionalDistribution).map(([region, range]) => [region, { ...range }]),
    ) as SimulationConfig["regionalDistribution"],
    regionalShares: { ...config.regionalShares },
    deploymentDates: Object.fromEntries(
      Object.entries(config.deploymentDates).map(([region, dates]) => [region, { ...dates }]),
    ) as SimulationConfig["deploymentDates"],
    impact: {
      ...config.impact,
      co2PerMile: Object.fromEntries(Object.entries(config.impact.co2PerMile).map(([region, values]) => [region, { ...values }])) as SimulationConfig["impact"]["co2PerMile"],
      co2Produced: { ...config.impact.co2Produced },
      productivityPerHour: { ...config.impact.productivityPerHour },
      gdpByRegion: { ...config.impact.gdpByRegion },
    },
    vmt: { ...config.vmt, arimaOrder: [...config.vmt.arimaOrder] as [number, number, number] },
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

function yearIndex(result: SimulationResult, year: number): number {
  return Math.max(0, result.years.indexOf(year));
}

function ScenarioChart({
  years,
  series,
  color,
  formatter = formatCompact,
}: {
  years: number[];
  series: ScenarioSeries;
  color: string;
  formatter?: (value: number) => string;
}) {
  const width = 760;
  const height = 250;
  const padding = { top: 18, right: 20, bottom: 28, left: 56 };
  const values = [...series.p25, ...series.p75, ...series.average];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(max - min, Math.abs(max) * 0.03, 1);
  const yMin = min >= 0 ? 0 : min - span * 0.08;
  const yMax = max + span * 0.08;
  const x = (index: number) => padding.left + (index / Math.max(years.length - 1, 1)) * (width - padding.left - padding.right);
  const y = (value: number) => height - padding.bottom - ((value - yMin) / (yMax - yMin)) * (height - padding.top - padding.bottom);
  const path = (line: number[]) => line.map((value, index) => `${index === 0 ? "M" : "L"}${x(index).toFixed(1)},${y(value).toFixed(1)}`).join(" ");
  const band = `${path(series.p75)} ${series.p25.map((value, index) => `L${x(series.p25.length - 1 - index).toFixed(1)},${y(value).toFixed(1)}`).join(" ")} Z`;
  const ticks = [0, 0.5, 1].map((fraction) => yMin + (yMax - yMin) * fraction);

  return (
    <div className="chart-wrap">
      <svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Average with 25th to 75th percentile band">
        {ticks.map((tick) => (
          <g key={tick}>
            <line x1={padding.left} x2={width - padding.right} y1={y(tick)} y2={y(tick)} className="chart-grid" />
            <text x={padding.left - 9} y={y(tick) + 4} textAnchor="end" className="chart-label">{formatter(tick)}</text>
          </g>
        ))}
        <path d={band} fill={color} opacity="0.13" />
        <path d={path(series.p75)} fill="none" stroke={color} strokeWidth="1.4" opacity="0.55" strokeDasharray="4 4" />
        <path d={path(series.p25)} fill="none" stroke={color} strokeWidth="1.4" opacity="0.55" strokeDasharray="4 4" />
        <path d={path(series.average)} fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        {years.map((year, index) => (index % 3 === 0 || index === years.length - 1) ? (
          <text key={year} x={x(index)} y={height - 7} textAnchor="middle" className="chart-label">{year}</text>
        ) : null)}
      </svg>
      <div className="chart-legend"><span className="legend-line" style={{ backgroundColor: color }} /> average <span className="legend-band" style={{ backgroundColor: color }} /> 25th–75th percentile</div>
    </div>
  );
}

function StatCard({ label, value, note }: { label: string; value: string; note: string }) {
  return <article className="stat-card"><p>{label}</p><strong>{value}</strong><span>{note}</span></article>;
}

function NumberField({ label, value, min, max, step, suffix, onChange }: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  suffix?: string;
  onChange: (value: number) => void;
}) {
  return <label className="field"><span>{label}<em>{suffix ?? ""}</em></span><input type="number" value={value} min={min} max={max} step={step} onChange={(event) => onChange(Number(event.target.value))} /></label>;
}

export function RobotaxiLab() {
  const [config, setConfig] = useState<SimulationConfig>(() => cloneConfig(DEFAULT_CONFIG));
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [targetYear, setTargetYear] = useState(2030);
  const [status, setStatus] = useState("Ready to run");
  const [progress, setProgress] = useState(0);
  const [configJson, setConfigJson] = useState(() => JSON.stringify(DEFAULT_CONFIG, null, 2));
  const [jsonError, setJsonError] = useState("");
  const workerRef = useRef<Worker | null>(null);

  const errors = useMemo(() => validateConfig(config), [config]);
  const selectedYear = result?.years.includes(targetYear) ? targetYear : result?.years.at(-1) ?? 2030;
  const selectedIndex = result ? yearIndex(result, selectedYear) : 0;

  useEffect(() => () => workerRef.current?.terminate(), []);
  useEffect(() => setConfigJson(JSON.stringify(config, null, 2)), [config]);

  const run = () => {
    if (errors.length > 0) return;
    workerRef.current?.terminate();
    const worker = new Worker(new URL("../lib/simulation.worker.ts", import.meta.url));
    workerRef.current = worker;
    setResult(null);
    setProgress(0.01);
    setStatus(`Running ${config.numSimulations.toLocaleString()} Monte Carlo draws in a browser worker`);
    worker.onmessage = (event: MessageEvent<WorkerMessage>) => {
      const message = event.data;
      if (message.type === "progress") {
        setProgress(message.value);
        setStatus(message.label);
      } else if (message.type === "success") {
        setResult(message.result);
        setProgress(1);
        setStatus(`Complete in ${(message.result.runtimeMs / 1000).toFixed(2)}s`);
        worker.terminate();
      } else {
        setStatus(message.message);
        setProgress(0);
        worker.terminate();
      }
    };
    worker.postMessage({ config });
  };

  const update = (changes: Partial<SimulationConfig>) => setConfig((current) => {
    const next = { ...current, ...changes };
    if (changes.networkParticipation !== undefined) next.generalInputs = { ...current.generalInputs, "Network Participation": { ...current.generalInputs["Network Participation"], bear: changes.networkParticipation } };
    if (changes.hoursPerDay !== undefined) next.generalInputs = { ...next.generalInputs, "Hours/day": { ...next.generalInputs["Hours/day"], bear: changes.hoursPerDay } };
    if (changes.milesPerHour !== undefined) next.generalInputs = { ...next.generalInputs, "Miles/hour": { ...next.generalInputs["Miles/hour"], bear: changes.milesPerHour } };
    if (changes.occupancyPct !== undefined) next.generalInputs = { ...next.generalInputs, "% ocupacy": { ...next.generalInputs["% ocupacy"], bear: changes.occupancyPct } };
    if (changes.carLifespan !== undefined) next.generalInputs = { ...next.generalInputs, "Car Lifespan": { ...next.generalInputs["Car Lifespan"], bear: changes.carLifespan } };
    if (changes.pricePerMile !== undefined) next.generalInputs = { ...next.generalInputs, "Price/Mile": { ...next.generalInputs["Price/Mile"], bear: changes.pricePerMile } };
    if (changes.platformFee !== undefined) next.generalInputs = { ...next.generalInputs, "Platform fee": { ...next.generalInputs["Platform fee"], bear: changes.platformFee } };
    return cloneConfig(next);
  });
  const applyPreset = (preset: "base" | "conservative" | "aggressive") => {
    setConfig((current) => {
      const next = { ...cloneConfig(DEFAULT_CONFIG), ...current, ...PRESETS[preset] };
      if (next.growth !== current.growth) next.growthByYear = Object.fromEntries(Object.keys(next.growthByYear).map((year) => [year, { ...next.growth }])) as SimulationConfig["growthByYear"];
      return cloneConfig(next);
    });
  };
  const applyJson = () => {
    try {
      const parsed = JSON.parse(configJson) as Partial<SimulationConfig>;
      const defaults = cloneConfig(DEFAULT_CONFIG);
      const next = cloneConfig({
        ...defaults,
        ...parsed,
        generalInputs: { ...defaults.generalInputs, ...(parsed.generalInputs ?? {}) },
        growthByYear: { ...defaults.growthByYear, ...(parsed.growthByYear ?? {}) },
        regionalDistribution: { ...defaults.regionalDistribution, ...(parsed.regionalDistribution ?? {}) },
        regionalShares: { ...defaults.regionalShares, ...(parsed.regionalShares ?? {}) },
        deploymentDates: { ...defaults.deploymentDates, ...(parsed.deploymentDates ?? {}) },
        impact: {
          ...defaults.impact,
          ...(parsed.impact ?? {}),
          co2PerMile: { ...defaults.impact.co2PerMile, ...(parsed.impact?.co2PerMile ?? {}) },
          co2Produced: { ...defaults.impact.co2Produced, ...(parsed.impact?.co2Produced ?? {}) },
          productivityPerHour: { ...defaults.impact.productivityPerHour, ...(parsed.impact?.productivityPerHour ?? {}) },
          gdpByRegion: { ...defaults.impact.gdpByRegion, ...(parsed.impact?.gdpByRegion ?? {}) },
        },
        vmt: { ...defaults.vmt, ...(parsed.vmt ?? {}) },
      });
      const nextErrors = validateConfig(next);
      if (nextErrors.length > 0) {
        setJsonError(nextErrors.join(" "));
        return;
      }
      setConfig(next);
      setJsonError("");
      setStatus("Configuration applied");
    } catch (error) {
      setJsonError(error instanceof Error ? error.message : "Configuration JSON is invalid.");
    }
  };

  return (
    <main className="shell">
      <header className="topbar"><div><span className="mark">RT</span><span className="topline">Robotaxi thesis lab</span></div><span className="runtime-pill">browser worker / v0.1</span></header>
      <div className="layout">
        <aside className="controls">
          <div className="control-heading"><p className="eyebrow">Model controls</p><h2>Assumptions</h2></div>
          <div className="preset-row"><button onClick={() => applyPreset("conservative")}>Conservative</button><button className="active" onClick={() => applyPreset("base")}>Base</button><button onClick={() => applyPreset("aggressive")}>Aggressive</button></div>
          <NumberField label="Monte Carlo draws" value={config.numSimulations} min={100} max={5000} step={100} onChange={(value) => update({ numSimulations: value })} />
          <NumberField label="End year" value={config.yearsToSimulate} min={2022} max={2050} step={1} onChange={(value) => update({ yearsToSimulate: value })} />
          <NumberField label="Network participation" value={config.networkParticipation} min={0.05} max={0.8} step={0.01} suffix=" share" onChange={(value) => update({ networkParticipation: value })} />
          <NumberField label="Hours per day" value={config.hoursPerDay} min={1} max={24} step={0.5} onChange={(value) => update({ hoursPerDay: value })} />
          <NumberField label="Miles per hour" value={config.milesPerHour} min={5} max={60} step={1} onChange={(value) => update({ milesPerHour: value })} />
          <NumberField label="Price per mile" value={config.pricePerMile} min={0.1} max={5} step={0.05} suffix=" USD" onChange={(value) => update({ pricePerMile: value })} />
          <NumberField label="Platform fee" value={config.platformFee} min={0} max={0.8} step={0.01} suffix=" share" onChange={(value) => update({ platformFee: value })} />
          <details><summary>Advanced model inputs</summary><div className="advanced-fields"><NumberField label="Occupancy" value={config.occupancyPct} min={0.05} max={1} step={0.01} suffix=" share" onChange={(value) => update({ occupancyPct: value })} /><NumberField label="Car lifespan" value={config.carLifespan} min={3} max={30} step={0.5} suffix=" years" onChange={(value) => update({ carLifespan: value })} /></div></details>
          <details><summary>Full notebook configuration</summary><p className="json-help">Edit every range, deployment date, impact constant, and VMT setting as JSON.</p><textarea className="config-json" value={configJson} onChange={(event) => setConfigJson(event.target.value)} spellCheck={false} /><button className="json-button" onClick={applyJson}>Apply full config</button>{jsonError ? <p className="validation">{jsonError}</p> : null}</details>
          {errors.length > 0 ? <div className="validation">{errors.map((error) => <p key={error}>{error}</p>)}</div> : null}
          <button className="run-button" disabled={errors.length > 0} onClick={run}>Run simulation <span>↗</span></button>
          <div className="progress-track"><span style={{ width: `${progress * 100}%` }} /></div><p className="status">{status}</p>
        </aside>

        <section className="workspace">
          <div className="intro"><p className="eyebrow">Monte Carlo scenario analysis / 2022–{config.yearsToSimulate}</p><h1>How much road can an autonomous fleet absorb?</h1><p className="intro-copy">A browser-based reconstruction of the thesis model. Adjust the operating assumptions, run the draws locally, and inspect the uncertainty band rather than a single forecast.</p></div>
          {result ? <>
            <div className="result-toolbar"><div><span className="eyebrow">Reporting year</span><input type="range" min={result.years[0]} max={result.years.at(-1)} value={selectedYear} onChange={(event) => setTargetYear(Number(event.target.value))} /><strong>{selectedYear}</strong></div><span className="seed-note">seed {result.seed} / {result.sampleSize.toLocaleString()} draws</span></div>
            <div className="stats-grid">
              <StatCard label="Tesla revenue / year" value={formatDollars(result.revenue.average[selectedIndex])} note={`${formatDollars(result.revenue.p25[selectedIndex])} to ${formatDollars(result.revenue.p75[selectedIndex])}`} />
              <StatCard label="Robotaxi miles" value={formatCompact(result.robotaxiMiles.average[selectedIndex])} note="annual global miles" />
              <StatCard label="Cumulative fleet" value={formatCompact(result.fleet.average[selectedIndex])} note="vehicles in service" />
              <StatCard label="CO₂ avoided" value={`${formatCompact(result.co2Saved.average[selectedIndex])} t`} note="ICE displacement basis" />
            </div>
            <div className="panel-grid"><section className="panel wide"><div className="panel-heading"><div><p className="eyebrow">Network output</p><h2>Robotaxi miles</h2></div><span className="unit">global / annual</span></div><ScenarioChart years={result.years} series={result.robotaxiMiles} color="#dd5d35" /></section><section className="panel"><div className="panel-heading"><div><p className="eyebrow">Economics</p><h2>Tesla revenue</h2></div><span className="unit">USD / annual</span></div><ScenarioChart years={result.years} series={result.revenue} color="#1c8a73" formatter={formatDollars} /></section></div>
            <div className="panel-grid"><section className="panel"><div className="panel-heading"><div><p className="eyebrow">Fleet geography</p><h2>Vehicles by region</h2></div><span className="unit">{selectedYear}</span></div><div className="bars">{REGIONS.map((region) => { const value = result.regionalFleet[region].average[selectedIndex]; const max = Math.max(...REGIONS.map((item) => result.regionalFleet[item].average[selectedIndex])); return <div className="bar-row" key={region}><div><span>{region}</span><strong>{formatCompact(value)}</strong></div><div className="bar-track"><i style={{ width: `${(value / max) * 100}%` }} /></div></div>; })}</div></section><section className="panel"><div className="panel-heading"><div><p className="eyebrow">Impact ledger</p><h2>What changes on the ground</h2></div><span className="unit">{selectedYear}</span></div><dl className="ledger"><div><dt>Cars displaced</dt><dd>{formatCompact(result.carsDisplaced.average[selectedIndex])}</dd></div><div><dt>Hours unlocked</dt><dd>{formatCompact(result.hoursSaved.average[selectedIndex])}</dd></div><div><dt>Potential GDP</dt><dd>{formatDollars(result.extraGdp.average[selectedIndex])}</dd></div><div><dt>Owner revenue</dt><dd>{formatDollars(result.ownerRevenue.nonAsia.reduce((sum, value) => sum + value, 0) / result.ownerRevenue.nonAsia.length)}</dd></div></dl></section></div>
          </> : <div className="empty-state"><span className="empty-number">01</span><div><h2>Run the reference model in your browser.</h2><p>The first run creates the same scenario summaries as the thesis model, but keeps the work off the server and out of the UI thread.</p><button className="run-button" onClick={run}>Run base case <span>↗</span></button></div></div>}
          <footer className="footer"><span>Reference model: Tesla Robotaxi Simulation</span><span>Local execution / reproducible seed / research prototype</span></footer>
        </section>
      </div>
    </main>
  );
}
