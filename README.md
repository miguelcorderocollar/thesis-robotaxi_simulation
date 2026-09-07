# Robotaxi thesis lab

This project turns my master thesis into an interactive model of a possible Tesla Robotaxi network.

The thesis asks: if autonomous Tesla vehicles join a shared Robotaxi network, how large could the fleet become, and what might that mean for mobility, revenue, emissions, and the wider economy?

## What goes in

The model combines thesis assumptions with source data for:

- annual Tesla production growth;
- regional production shares;
- Robotaxi deployment dates by region;
- vehicle usage, pricing, costs, platform fees, participation, and lifespan;
- emissions, vehicle displacement, productivity, GDP, and US vehicle-miles-travelled assumptions.

Every input can be edited through the browser app's full configuration JSON.

## What comes out

Each Monte Carlo run produces uncertainty bands for:

- fleet size, production, and discontinued vehicles;
- Robotaxi miles and Tesla revenue;
- owner revenue and regional results;
- CO₂ savings, pollution savings, and cars displaced;
- hours and years saved, extra GDP, and US VMT share.

## Why it is useful

The model makes the assumptions visible and shows how uncertainty in deployment, production, usage, and economics changes the result. It is useful for exploring the thesis, checking which assumptions matter most, and presenting the research without requiring the original notebook environment.

## Development

The live application is in `web/`. The simulation runs in a browser Web Worker. The original notebook and Python implementation remain in the repository as research references.

```bash
cd web
npm install
npm run dev
```

Verify changes with:

```bash
npm run typecheck
npm test -- --run
npm run build
```

See [`docs/architecture.md`](docs/architecture.md) for the repository layout and [`web/README.md`](web/README.md) for the browser configuration contract.
