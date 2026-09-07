# Architecture

## Repository layout

```text
legacy/                       Original thesis artifacts
  robotaxi-thesis-model.ipynb Original research notebook
  data/                        Source CSVs used by the thesis model
model/                        Python reference implementation
web/
  app/                        Next.js App Router entry points and styles
  components/                 Browser UI
  lib/data.ts                 Typed defaults and compact derived data
  lib/simulation.ts           Monte Carlo engine
  lib/simulation.worker.ts    Worker boundary for simulation runs
  lib/simulation.test.ts      Regression and behavior tests
```

## Runtime flow

1. The page builds a typed `SimulationConfig` from the visible controls or the full JSON editor.
2. The page sends that config to `simulation.worker.ts`.
3. The worker samples the configured distributions, builds the regional fleet timeline, and calculates revenue, miles, emissions, displacement, time, GDP, and VMT outputs.
4. The worker returns compact averages and percentile bands to the page.

The deployed app is static Next.js output plus a browser worker. Vercel serves the page and does not run the Monte Carlo loop on the server.

## Configuration contract

`web/lib/types.ts` defines the complete browser input and output contract. The JSON editor exposes:

- operating input ranges from `legacy/data/general_inputs.csv`;
- year-specific production growth ranges;
- regional production distribution ranges;
- exact deployment-date ranges;
- environmental, displacement, productivity, and GDP assumptions;
- the notebook's ARIMA(1,1,1) VMT switch.

The browser tests compare a fixed run with notebook-derived Python values. They allow a small tolerance because the implementations use different random-number generators.
