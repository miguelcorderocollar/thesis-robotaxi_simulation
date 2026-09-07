# Browser model

This is the browser version of the thesis model. It runs the Monte Carlo engine in a Web Worker so the page stays responsive and no simulation request reaches a server.

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

## Deployment

Deploy this directory as the Vercel project root:

```bash
vercel --cwd web
vercel --cwd web --prod
```
