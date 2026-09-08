import type {
  DeploymentRange,
  DistributionRange,
  GeneralInputKey,
  ImpactConfig,
  Region,
  SimulationConfig,
} from "./types";

export { REGIONS } from "./types";

export const YEARS = Array.from({ length: 29 }, (_, index) => 2022 + index);

export const INPUT_RANGES: Record<GeneralInputKey, DistributionRange> = {
  "Price/Mile": { min: 0.7, bear: 0.8, bull: 1.2, max: 1.7 },
  "Price/Mile Asia": { min: 0.5, bear: 0.66, bull: 0.8, max: 1.1 },
  "Costs/Mile": { min: 0.1, bear: 0.15, bull: 0.25, max: 0.3 },
  "Platform fee": { min: 0.15, bear: 0.25, bull: 0.35, max: 0.45 },
  "Hours/day": { min: 6, bear: 8, bull: 13, max: 16 },
  "Days/week": { min: 4.5, bear: 5.6, bull: 6.5, max: 7 },
  "Miles/hour": { min: 10, bear: 13, bull: 17, max: 20 },
  "% ocupacy": { min: 0.35, bear: 0.45, bull: 0.65, max: 0.69 },
  "Network Participation": { min: 0.2, bear: 0.25, bull: 0.35, max: 0.4 },
  "Car Lifespan": { min: 8.5, bear: 9, bull: 11.5, max: 13 },
};

export const GROWTH_BY_YEAR: Record<number, DistributionRange> = {
  2022: { min: 0.4, bear: 0.55, bull: 0.7, max: 0.8 },
  2023: { min: 0.39, bear: 0.5, bull: 0.66, max: 0.75 },
  2024: { min: 0.37, bear: 0.43, bull: 0.6, max: 0.65 },
  2025: { min: 0.35, bear: 0.4, bull: 0.55, max: 0.62 },
  2026: { min: 0.3, bear: 0.38, bull: 0.49, max: 0.55 },
  2027: { min: 0.18, bear: 0.25, bull: 0.4, max: 0.4 },
  2028: { min: 0.11, bear: 0.18, bull: 0.31, max: 0.35 },
  2029: { min: 0.07, bear: 0.12, bull: 0.17, max: 0.22 },
  2030: { min: 0.05, bear: 0.09, bull: 0.15, max: 0.2 },
  2031: { min: 0.04, bear: 0.08, bull: 0.13, max: 0.17 },
  2032: { min: 0.035, bear: 0.075, bull: 0.1, max: 0.15 },
  2033: { min: 0.03, bear: 0.07, bull: 0.09, max: 0.13 },
  2034: { min: 0.025, bear: 0.06, bull: 0.08, max: 0.1 },
  2035: { min: 0.02, bear: 0.05, bull: 0.07, max: 0.09 },
  2036: { min: 0.015, bear: 0.04, bull: 0.06, max: 0.08 },
  2037: { min: 0.01, bear: 0.03, bull: 0.05, max: 0.07 },
  2038: { min: 0.005, bear: 0.02, bull: 0.04, max: 0.06 },
  2039: { min: 0.005, bear: 0.01, bull: 0.03, max: 0.05 },
};

export const REGIONAL_DISTRIBUTION: Record<Region, DistributionRange> = {
  USA: { min: 0.27, bear: 0.3, bull: 0.35, max: 0.38 },
  Canada: { min: 0.005, bear: 0.008, bull: 0.012, max: 0.016 },
  Europe: { min: 0.22, bear: 0.25, bull: 0.35, max: 0.38 },
  China: { min: 0.23, bear: 0.265, bull: 0.373, max: 0.38 },
  "APAC excl China": { min: 0.01, bear: 0.03, bull: 0.065, max: 0.072 },
};

export const DEPLOYMENT_DATES: Record<Region, DeploymentRange> = {
  USA: {
    min: "01/01/2027",
    bear: "01/01/2027",
    bull: "01/01/2027",
    max: "01/01/2027",
  },
  Canada: {
    min: "01/01/2027",
    bear: "01/01/2027",
    bull: "01/01/2027",
    max: "01/01/2027",
  },
  Europe: {
    min: "01/01/2027",
    bear: "01/01/2027",
    bull: "01/01/2027",
    max: "01/01/2027",
  },
  China: {
    min: "01/01/2027",
    bear: "01/01/2027",
    bull: "01/01/2027",
    max: "01/01/2027",
  },
  "APAC excl China": {
    min: "01/01/2027",
    bear: "01/01/2027",
    bull: "01/01/2027",
    max: "01/01/2027",
  },
};

export const HISTORICAL_PRODUCTION: Record<Region, number> = {
  USA: 915338,
  Canada: 86040,
  Europe: 471849,
  China: 511293,
  "APAC excl China": 99470,
};

export const PRODUCTION_2021_TOTAL = 858000;

// June rolling-12-month values from the notebook's ARIMA(1,1,1) forecast of
// legacy/data/VMT_US.csv. The workbook only consumes this June series for the US VMT
// percentage output, so shipping the compact derived series keeps the client
// free of a statistics runtime.
export const VMT_JUNE_ROLLING_MEAN: Record<number, number> = {
  2020: 3266762.2711381386,
  2021: 3275914.0905888528,
  2022: 3282974.38244351,
  2023: 3286560.8015685845,
  2024: 3288381.0852244277,
  2025: 3289304.579755584,
  2026: 3289773.0013353694,
  2027: 3290010.5718036783,
  2028: 3290131.054360302,
  2029: 3290192.1547255605,
  2030: 3290223.140139883,
  2031: 3290238.853450654,
  2032: 3290246.821949538,
  2033: 3290250.862909358,
  2034: 3290252.912146153,
  2035: 3290253.951347135,
  2036: 3290254.4783425634,
  2037: 3290254.7455903366,
  2038: 3290254.8811159264,
  2039: 3290254.949843101,
  2040: 3290254.9846957377,
  2041: 3290255.002370063,
  2042: 3290255.0113330004,
  2043: 3290255.0158782485,
  2044: 3290255.018183216,
  2045: 3290255.019352101,
  2046: 3290255.0199448583,
  2047: 3290255.0202454473,
  2048: 3290255.0203978866,
  2049: 3290255.020475196,
  2050: 3290255.020514397,
};

const normalizedRegionalShares = Object.fromEntries(
  Object.entries(REGIONAL_DISTRIBUTION).map(([region, values]) => [
    region,
    values.bear,
  ]),
) as Record<Region, number>;
const shareTotal = Object.values(normalizedRegionalShares).reduce(
  (sum, value) => sum + value,
  0,
);

export const IMPACT_CONFIG: ImpactConfig = {
  co2PerMile: {
    Europe: { ice: 395.721596, ev: 133.897421 },
    USA: { ice: 410.141318, ev: 165.730245 },
    China: { ice: 419.137551, ev: 265.413012 },
  },
  co2Produced: {
    USA: 4712770573,
    Europe: 4946034489,
    China: 10667887453,
  },
  alaCostPerGallon: 1.15,
  usaMpg: 25.4,
  carsUsa: 282.8e6,
  avgMilesCar: 13476,
  hoursInYear: 8760,
  productivityPerHour: {
    USA: 74.19,
    Europe: 54.25,
    China: 15,
    Canada: 56.61,
  },
  gdpByRegion: {
    USA: 20936600 * 1e6,
    Europe: 15276468.99 * 1e6,
    China: 14722730.7 * 1e6,
    Canada: 1644037.29 * 1e6,
  },
};

export const DEFAULT_CONFIG: SimulationConfig = {
  yearsToSimulate: 2039,
  numSimulations: 5000,
  seed: 20300907,
  daysPerWeek: INPUT_RANGES["Days/week"].bear,
  hoursPerDay: INPUT_RANGES["Hours/day"].bear,
  milesPerHour: INPUT_RANGES["Miles/hour"].bear,
  occupancyPct: INPUT_RANGES["% ocupacy"].bear,
  networkParticipation: INPUT_RANGES["Network Participation"].bear,
  carLifespan: INPUT_RANGES["Car Lifespan"].bear,
  pricePerMile: INPUT_RANGES["Price/Mile"].bear,
  pricePerMileAsia: INPUT_RANGES["Price/Mile Asia"].bear,
  platformFee: INPUT_RANGES["Platform fee"].bear,
  costsPerMile: INPUT_RANGES["Costs/Mile"].bear,
  growth: GROWTH_BY_YEAR[2022],
  generalInputs: { ...INPUT_RANGES },
  growthByYear: Object.fromEntries(
    Object.entries(GROWTH_BY_YEAR).map(([year, range]) => [
      String(year),
      { ...range },
    ]),
  ),
  regionalDistribution: Object.fromEntries(
    Object.entries(REGIONAL_DISTRIBUTION).map(([region, range]) => [
      region,
      { ...range },
    ]),
  ) as Record<Region, DistributionRange>,
  regionalShares: Object.fromEntries(
    Object.entries(normalizedRegionalShares).map(([region, value]) => [
      region,
      value / shareTotal,
    ]),
  ) as Record<Region, number>,
  deploymentDates: DEPLOYMENT_DATES,
  impact: IMPACT_CONFIG,
  vmt: { enabled: true, arimaOrder: [1, 1, 1] },
};

export const PRESETS: Record<
  "base" | "conservative" | "aggressive",
  Partial<SimulationConfig>
> = {
  base: {},
  conservative: {
    networkParticipation: 0.2,
    growth: { min: 0.2, bear: 0.3, bull: 0.5, max: 0.65 },
    generalInputs: {
      ...INPUT_RANGES,
      "Network Participation": { min: 0.15, bear: 0.2, bull: 0.28, max: 0.35 },
    },
  },
  aggressive: {
    networkParticipation: 0.4,
    growth: { min: 0.45, bear: 0.6, bull: 0.8, max: 1.0 },
    generalInputs: {
      ...INPUT_RANGES,
      "Network Participation": { min: 0.3, bear: 0.4, bull: 0.5, max: 0.6 },
    },
  },
};
