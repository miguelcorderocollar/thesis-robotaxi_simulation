# Browser model

This is the browser version of the thesis model. It runs the Monte Carlo engine in a Web Worker so the page stays responsive and no simulation request reaches a server. The UI is intentionally thin; the model and configuration contract are the important parts.

## Local development

```bash
npm install
npm run dev
```

## Verification

```bash
npm run typecheck
npm test
npm run build
```

The cross-language regression test compares the browser engine with the existing Python engine using the same defaults and a fixed 1,000-draw reference run. The two engines use different seeded random-number generators, so the test uses a 3% Monte Carlo tolerance for means and percentile bands.

The reference fixture is derived from the thesis notebook and its CSV ranges. The browser engine supports the notebook's operating ranges, year-by-year production growth, year-by-year regional production distribution, exact deployment-date ranges, environmental constants, GDP/productivity assumptions, owner economics, and the ARIMA(1,1,1)-based US VMT output. The VMT forecast is shipped as the notebook's compact June rolling-12-month denominator rather than loading a statistics runtime in the browser.

Every model input is available in the `Full notebook configuration` JSON editor. The visible controls are convenience fields; the JSON object is the complete configuration contract sent to the worker.

## Deployment

Deploy this directory as the Vercel project root:

```bash
vercel --cwd web
vercel --cwd web --prod
```
