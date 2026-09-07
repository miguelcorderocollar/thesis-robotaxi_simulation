import {
  GROWTH_BY_YEAR,
  HISTORICAL_PRODUCTION,
  PRODUCTION_2021_TOTAL,
  REGIONS,
  VMT_JUNE_ROLLING_MEAN,
  YEARS,
} from "./data";
import type {
  DistributionRange,
  Region,
  ScenarioSeries,
  SimulationConfig,
  SimulationResult,
} from "./types";

type Matrix = Float64Array[];
type ProgressCallback = (value: number, label: string) => void;
type Co2Region = "USA" | "Europe" | "China";

function createMatrix(rows: number, columns: number): Matrix {
  return Array.from({ length: rows }, () => new Float64Array(columns));
}

function addMatrices(...matrices: Matrix[]): Matrix {
  if (matrices.length === 0) return [];
  const result = createMatrix(matrices[0].length, matrices[0][0].length);
  for (const matrix of matrices) {
    for (let simulation = 0; simulation < matrix.length; simulation += 1) {
      for (let year = 0; year < matrix[simulation].length; year += 1) {
        result[simulation][year] += matrix[simulation][year];
      }
    }
  }
  return result;
}

function scaledMatrix(matrix: Matrix, scalar: number): Matrix {
  return matrix.map((row) => Float64Array.from(row, (value) => value * scalar));
}

function createSeededRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state += 0x6d2b79f5;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

function normalCdf(value: number): number {
  const sign = value < 0 ? -1 : 1;
  const absolute = Math.abs(value) / Math.sqrt(2);
  const t = 1 / (1 + 0.3275911 * absolute);
  const polynomial =
    1 -
    (((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t -
      0.284496736) *
      t +
      0.254829592) *
      t) *
      Math.exp(-absolute * absolute);
  return 0.5 * (1 + sign * polynomial);
}

// Acklam's rational approximation avoids rejection loops in the browser.
function inverseNormalCdf(probability: number): number {
  const p = Math.min(1 - 1e-12, Math.max(1e-12, probability));
  const low = 0.02425;
  const high = 1 - low;
  const a = [-39.6968302866538, 220.946098424521, -275.928510446969, 138.357751867269, -30.6647980661472, 2.50662827745924];
  const b = [-54.4760987982241, 161.585836858041, -155.698979859887, 66.8013118877197, -13.2806815528857];
  const c = [-0.00778489400243029, -0.322396458041136, -2.40075827716184, -2.54973253934373, 4.37466414146497, 2.93816398269878];
  const d = [0.00778469570904146, 0.32246712907004, 2.445134137143, 3.75440866190742];
  if (p < low) {
    const q = Math.sqrt(-2 * Math.log(p));
    const numerator = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]);
    const denominator = ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    return numerator / denominator;
  }
  if (p > high) {
    const q = Math.sqrt(-2 * Math.log(1 - p));
    const numerator = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]);
    const denominator = ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    return -numerator / denominator;
  }
  const q = p - 0.5;
  const r = q * q;
  const numerator = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q;
  const denominator = (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  return numerator / denominator;
}

export function sampleTruncatedNormal(range: DistributionRange, count: number, random: () => number): Float64Array {
  const mean = (range.bear + range.bull) / 2;
  let sigma = Math.abs(range.bull - mean);
  if (sigma < 1e-10) sigma = Math.abs(range.max - range.min) / 4;
  if (sigma < 1e-10) return new Float64Array(count).fill(mean);
  const a = (range.min - mean) / sigma;
  const b = (range.max - mean) / sigma;
  if (a >= b) return new Float64Array(count).fill((range.min + range.max) / 2);
  const lower = normalCdf(a);
  const upper = normalCdf(b);
  const result = new Float64Array(count);
  for (let index = 0; index < count; index += 1) {
    const probability = lower + random() * (upper - lower);
    result[index] = Math.min(range.max, Math.max(range.min, mean + sigma * inverseNormalCdf(probability)));
  }
  return result;
}

function rangeAround(value: number): DistributionRange {
  return { min: value * 0.8, bear: value * 0.9, bull: value * 1.1, max: value * 1.2 };
}

function quantile(values: Float64Array | number[], probability: number): number {
  const sorted = Array.from(values).sort((left, right) => left - right);
  if (sorted.length === 0) return 0;
  const position = (sorted.length - 1) * probability;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  if (lower === upper) return sorted[lower];
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower);
}

function summarize(matrix: Matrix): ScenarioSeries {
  if (matrix.length === 0) return { average: [], p25: [], p75: [] };
  const columns = matrix[0].length;
  const average = new Array<number>(columns).fill(0);
  const p25 = new Array<number>(columns).fill(0);
  const p75 = new Array<number>(columns).fill(0);
  for (let column = 0; column < columns; column += 1) {
    const values = new Float64Array(matrix.length);
    for (let row = 0; row < matrix.length; row += 1) {
      values[row] = matrix[row][column];
      average[column] += values[row];
    }
    average[column] /= matrix.length;
    p25[column] = quantile(values, 0.25);
    p75[column] = quantile(values, 0.75);
  }
  return { average, p25, p75 };
}

function summarizeRegions(matrices: Record<Region, Matrix>): Record<string, ScenarioSeries> {
  return Object.fromEntries(REGIONS.map((region) => [region, summarize(matrices[region])])) as Record<string, ScenarioSeries>;
}

function constantSeries(values: Float64Array, years: number[]): ScenarioSeries {
  const average = values.reduce((sum, value) => sum + value, 0) / values.length;
  const p25 = quantile(values, 0.25);
  const p75 = quantile(values, 0.75);
  return { average: years.map(() => average), p25: years.map(() => p25), p75: years.map(() => p75) };
}

function parseNotebookDate(value: string): number {
  const match = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(value.trim());
  if (match) return Date.UTC(Number(match[3]), Number(match[2]) - 1, Number(match[1]));
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) throw new Error(`Invalid deployment date: ${value}`);
  return timestamp;
}

function dayOfYear(timestamp: number): number {
  const date = new Date(timestamp);
  const start = Date.UTC(date.getUTCFullYear(), 0, 1);
  return Math.floor((Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()) - start) / 86400000) + 1;
}

function deploymentAvailability(config: SimulationConfig, years: number[], random: () => number): Record<Region, Matrix> {
  const result = {} as Record<Region, Matrix>;
  for (const region of REGIONS) {
    const range = config.deploymentDates[region];
    const sampledDates = sampleTruncatedNormal(
      { min: parseNotebookDate(range.min), bear: parseNotebookDate(range.bear), bull: parseNotebookDate(range.bull), max: parseNotebookDate(range.max) },
      config.numSimulations,
      random,
    );
    const availability = createMatrix(config.numSimulations, years.length);
    for (let simulation = 0; simulation < config.numSimulations; simulation += 1) {
      const date = new Date(sampledDates[simulation]);
      const initialYear = date.getUTCFullYear();
      const firstYearAvailability = (365 - dayOfYear(sampledDates[simulation])) / 365;
      for (let year = 0; year < years.length; year += 1) {
        if (years[year] < initialYear) availability[simulation][year] = 0;
        else if (years[year] === initialYear) availability[simulation][year] = firstYearAvailability;
        else availability[simulation][year] = 1;
      }
    }
    result[region] = availability;
  }
  return result;
}

function operatingRange(config: SimulationConfig, key: keyof SimulationConfig["generalInputs"], fallback: number): DistributionRange {
  return config.generalInputs?.[key] ?? rangeAround(fallback);
}

function forecastUsVmt(year: number): number {
  return VMT_JUNE_ROLLING_MEAN[year] ?? VMT_JUNE_ROLLING_MEAN[2050];
}

export function runSimulation(config: SimulationConfig, onProgress?: ProgressCallback): SimulationResult {
  const started = Date.now();
  const years = YEARS.filter((year) => year <= config.yearsToSimulate);
  const yearCount = years.length;
  const simulations = config.numSimulations;
  const random = createSeededRandom(config.seed);
  const progress = (value: number, label: string) => onProgress?.(value, label);

  const daysPerWeek = sampleTruncatedNormal(operatingRange(config, "Days/week", config.daysPerWeek), simulations, random);
  const hoursPerDay = sampleTruncatedNormal(operatingRange(config, "Hours/day", config.hoursPerDay), simulations, random);
  const milesPerHour = sampleTruncatedNormal(operatingRange(config, "Miles/hour", config.milesPerHour), simulations, random);
  const occupancy = sampleTruncatedNormal(operatingRange(config, "% ocupacy", config.occupancyPct), simulations, random);
  const networkParticipation = sampleTruncatedNormal(operatingRange(config, "Network Participation", config.networkParticipation), simulations, random);
  const prices = sampleTruncatedNormal(operatingRange(config, "Price/Mile", config.pricePerMile), simulations, random);
  const pricesAsia = sampleTruncatedNormal(operatingRange(config, "Price/Mile Asia", config.pricePerMileAsia), simulations, random);
  const platformFees = sampleTruncatedNormal(operatingRange(config, "Platform fee", config.platformFee), simulations, random);
  const costs = sampleTruncatedNormal(operatingRange(config, "Costs/Mile", config.costsPerMile), simulations, random);
  const lifespan = sampleTruncatedNormal(operatingRange(config, "Car Lifespan", config.carLifespan), simulations, random);
  const milesPerCar = new Float64Array(simulations);
  for (let simulation = 0; simulation < simulations; simulation += 1) milesPerCar[simulation] = 52 * daysPerWeek[simulation] * hoursPerDay[simulation] * milesPerHour[simulation] * occupancy[simulation];
  progress(0.12, "Sampling operating assumptions");

  const growthByYear = createMatrix(simulations, yearCount);
  for (let year = 0; year < yearCount; year += 1) {
    const range = config.growthByYear?.[String(years[year])] ?? config.growth ?? GROWTH_BY_YEAR[years[year]] ?? GROWTH_BY_YEAR[2039];
    const sampled = sampleTruncatedNormal(range, simulations, random);
    for (let simulation = 0; simulation < simulations; simulation += 1) growthByYear[simulation][year] = sampled[simulation];
  }

  const regionalDistribution = {} as Record<Region, Matrix>;
  for (const region of REGIONS) {
    regionalDistribution[region] = createMatrix(simulations, yearCount);
    const range = config.regionalDistribution?.[region] ?? rangeAround(config.regionalShares[region]);
    for (let year = 0; year < yearCount; year += 1) {
      const sampled = sampleTruncatedNormal(range, simulations, random);
      for (let simulation = 0; simulation < simulations; simulation += 1) regionalDistribution[region][simulation][year] = sampled[simulation];
    }
  }
  for (let simulation = 0; simulation < simulations; simulation += 1) {
    for (let year = 0; year < yearCount; year += 1) {
      let total = 0;
      for (const region of REGIONS) total += regionalDistribution[region][simulation][year];
      for (const region of REGIONS) regionalDistribution[region][simulation][year] /= total;
    }
  }
  progress(0.26, "Sampling production scenarios");

  const availability = deploymentAvailability(config, years, random);
  const production = {} as Record<Region, Matrix>;
  const discontinued = {} as Record<Region, Matrix>;
  const fleet = {} as Record<Region, Matrix>;
  for (const region of REGIONS) {
    production[region] = createMatrix(simulations, yearCount);
    discontinued[region] = createMatrix(simulations, yearCount);
    fleet[region] = createMatrix(simulations, yearCount);
    for (let simulation = 0; simulation < simulations; simulation += 1) {
      const lifespanInteger = Math.floor(lifespan[simulation]);
      const lifespanFraction = lifespan[simulation] % 1;
      for (let year = 0; year < yearCount; year += 1) {
        const currentYear = years[year];
        const currentDistribution = regionalDistribution[region][simulation][year];
        if (currentYear === 2022) {
          production[region][simulation][year] = PRODUCTION_2021_TOTAL * (1 + growthByYear[simulation][year]) * currentDistribution;
          fleet[region][simulation][year] = HISTORICAL_PRODUCTION[region] + production[region][simulation][year];
        } else {
          const previousDistribution = regionalDistribution[region][simulation][year - 1];
          production[region][simulation][year] = (production[region][simulation][year - 1] / previousDistribution) * (1 + growthByYear[simulation][year]) * currentDistribution;
          const productionYear = currentYear - lifespanInteger;
          const previousProductionYear = productionYear - 1;
          let retired = 0;
          if (productionYear >= 2022 && productionYear <= config.yearsToSimulate) retired += production[region][simulation][productionYear - 2022] * (1 - lifespanFraction);
          if (previousProductionYear >= 2022 && previousProductionYear <= config.yearsToSimulate) retired += production[region][simulation][previousProductionYear - 2022] * lifespanFraction;
          discontinued[region][simulation][year] = retired;
          fleet[region][simulation][year] = fleet[region][simulation][year - 1] + production[region][simulation][year] - retired;
        }
      }
    }
  }
  progress(0.49, "Building the fleet timeline");

  const robotaxiMilesByRegion = {} as Record<Region, Matrix>;
  const revenueByRegion = {} as Record<Region, Matrix>;
  const hoursByRegion = {} as Record<Region, Matrix>;
  for (const region of REGIONS) {
    robotaxiMilesByRegion[region] = createMatrix(simulations, yearCount);
    revenueByRegion[region] = createMatrix(simulations, yearCount);
    hoursByRegion[region] = createMatrix(simulations, yearCount);
    for (let simulation = 0; simulation < simulations; simulation += 1) {
      for (let year = 0; year < yearCount; year += 1) {
        const miles = fleet[region][simulation][year] * milesPerCar[simulation] * networkParticipation[simulation] * availability[region][simulation][year];
        robotaxiMilesByRegion[region][simulation][year] = miles;
        const price = region === "China" || region === "APAC excl China" ? pricesAsia[simulation] : prices[simulation];
        revenueByRegion[region][simulation][year] = miles * price * platformFees[simulation];
        hoursByRegion[region][simulation][year] = miles / milesPerHour[simulation];
      }
    }
  }
  const robotaxiMiles = addMatrices(...REGIONS.map((region) => robotaxiMilesByRegion[region]));
  const revenue = addMatrices(...REGIONS.map((region) => revenueByRegion[region]));
  const hoursSaved = addMatrices(...REGIONS.map((region) => hoursByRegion[region]));
  progress(0.68, "Calculating network operations");

  const co2ByRegion = {} as Record<Region, Matrix>;
  const co2PercentageByRegion = {} as Record<Region, Matrix>;
  for (const region of REGIONS) {
    co2ByRegion[region] = createMatrix(simulations, yearCount);
    co2PercentageByRegion[region] = createMatrix(simulations, yearCount);
    if (!(region in config.impact.co2PerMile)) continue;
    const regionKey = region as Co2Region;
    const factor = (config.impact.co2PerMile[regionKey].ice - config.impact.co2PerMile[regionKey].ev) / 1_000_000;
    for (let simulation = 0; simulation < simulations; simulation += 1) {
      for (let year = 0; year < yearCount; year += 1) {
        const saved = robotaxiMilesByRegion[region][simulation][year] * factor;
        co2ByRegion[region][simulation][year] = saved;
        co2PercentageByRegion[region][simulation][year] = saved / config.impact.co2Produced[regionKey];
      }
    }
  }
  const co2Saved = addMatrices(...REGIONS.map((region) => co2ByRegion[region]));
  const carsDisplaced = scaledMatrix(robotaxiMilesByRegion.USA, 1 / config.impact.avgMilesCar);
  const yearsSaved = scaledMatrix(hoursSaved, 1 / config.impact.hoursInYear);
  const extraGdpByRegion = {} as Record<Region, Matrix>;
  const extraGdpPercentageByRegion = {} as Record<Region, Matrix>;
  const pollutionSavings = scaledMatrix(
    robotaxiMilesByRegion.USA,
    (config.impact.alaCostPerGallon / config.impact.usaMpg) *
      (config.impact.co2PerMile.USA.ice - config.impact.co2PerMile.USA.ev) /
      config.impact.co2PerMile.USA.ice,
  );
  for (const region of REGIONS) {
    const productivity = config.impact.productivityPerHour[region] ?? 0;
    const gdp = config.impact.gdpByRegion[region] ?? 0;
    extraGdpByRegion[region] = scaledMatrix(hoursByRegion[region], productivity);
    extraGdpPercentageByRegion[region] = gdp === 0 ? createMatrix(simulations, yearCount) : scaledMatrix(extraGdpByRegion[region], 1 / gdp);
  }
  const extraGdp = addMatrices(...REGIONS.map((region) => extraGdpByRegion[region]));

  const ownerRevenue = { nonAsia: new Float64Array(simulations), asia: new Float64Array(simulations) };
  for (let simulation = 0; simulation < simulations; simulation += 1) {
    ownerRevenue.nonAsia[simulation] = (prices[simulation] * (1 - platformFees[simulation]) - costs[simulation]) * milesPerCar[simulation];
    ownerRevenue.asia[simulation] = (pricesAsia[simulation] * (1 - platformFees[simulation]) - costs[simulation]) * milesPerCar[simulation];
  }
  const targetYearIndex = Math.max(0, Math.min(yearCount - 1, 2030 - 2022));
  const displacementCoefficient = new Float64Array(simulations);
  for (let simulation = 0; simulation < simulations; simulation += 1) {
    const networkCars = fleet.USA[simulation][targetYearIndex] * networkParticipation[simulation];
    displacementCoefficient[simulation] = networkCars === 0 ? 0 : carsDisplaced[simulation][targetYearIndex] / networkCars;
  }

  let usPercentageVmt: Matrix | null = null;
  if (config.vmt?.enabled) {
    usPercentageVmt = createMatrix(simulations, yearCount);
    for (let simulation = 0; simulation < simulations; simulation += 1) {
      for (let year = 0; year < yearCount; year += 1) usPercentageVmt[simulation][year] = robotaxiMilesByRegion.USA[simulation][year] / forecastUsVmt(years[year]) / 1_000_000;
    }
  }
  progress(0.9, "Summarizing uncertainty bands");

  const regionalYearsSaved = Object.fromEntries(REGIONS.map((region) => [region, scaledMatrix(hoursByRegion[region], 1 / config.impact.hoursInYear)])) as Record<Region, Matrix>;
  return {
    years,
    sampleSize: simulations,
    seed: config.seed,
    runtimeMs: Date.now() - started,
    milesPerCar: constantSeries(milesPerCar, years),
    fleet: summarize(addMatrices(...REGIONS.map((region) => fleet[region]))),
    production: summarize(addMatrices(...REGIONS.map((region) => production[region]))),
    discontinued: summarize(addMatrices(...REGIONS.map((region) => discontinued[region]))),
    robotaxiMiles: summarize(robotaxiMiles),
    revenue: summarize(revenue),
    co2Saved: summarize(co2Saved),
    carsDisplaced: summarize(carsDisplaced),
    hoursSaved: summarize(hoursSaved),
    extraGdp: summarize(extraGdp),
    regionalFleet: summarizeRegions(fleet),
    regionalMiles: summarizeRegions(robotaxiMilesByRegion),
    regionalRevenue: summarizeRegions(revenueByRegion),
    regionalCo2Saved: summarizeRegions(co2ByRegion),
    regionalCo2SavedPercentage: summarizeRegions(co2PercentageByRegion),
    pollutionSavings: summarize(pollutionSavings),
    yearsSaved: summarize(yearsSaved),
    regionalHoursSaved: summarizeRegions(hoursByRegion),
    regionalYearsSaved: summarizeRegions(regionalYearsSaved),
    regionalExtraGdp: summarizeRegions(extraGdpByRegion),
    regionalExtraGdpPercentage: summarizeRegions(extraGdpPercentageByRegion),
    ownerRevenue: { nonAsia: Array.from(ownerRevenue.nonAsia), asia: Array.from(ownerRevenue.asia) },
    displacementCoefficient: Array.from(displacementCoefficient),
    usPercentageVmt: usPercentageVmt ? summarize(usPercentageVmt) : null,
    regionShares: config.regionalShares,
  };
}

function dateIsOrdered(range: SimulationConfig["deploymentDates"][Region]): boolean {
  const values = [range.min, range.bear, range.bull, range.max].map(parseNotebookDate);
  return values.every((value, index) => index === 0 || values[index - 1] <= value);
}

function rangeIsOrdered(range: DistributionRange): boolean {
  return range.min <= range.bear && range.bear <= range.bull && range.bull <= range.max;
}

export function validateConfig(config: SimulationConfig): string[] {
  const errors: string[] = [];
  const regionalTotal = Object.values(config.regionalShares).reduce((sum, value) => sum + value, 0);
  if (Math.abs(regionalTotal - 1) > 0.01) errors.push("Regional shares must sum to 100%.");
  if (config.numSimulations < 50) errors.push("Use at least 50 Monte Carlo draws.");
  if (config.numSimulations > 5000) errors.push("Use no more than 5,000 Monte Carlo draws in the browser.");
  if (config.yearsToSimulate < 2022 || config.yearsToSimulate > 2050) errors.push("Simulation end year must be between 2022 and 2050.");
  if (!rangeIsOrdered(config.growth)) errors.push("Growth assumptions must be ordered from minimum to maximum.");
  for (const [key, range] of Object.entries(config.generalInputs ?? {})) if (!rangeIsOrdered(range)) errors.push(`${key} assumptions are not ordered.`);
  for (const [year, range] of Object.entries(config.growthByYear ?? {})) if (!rangeIsOrdered(range)) errors.push(`Growth assumptions for ${year} are not ordered.`);
  for (const region of REGIONS) {
    try {
      if (!dateIsOrdered(config.deploymentDates[region])) errors.push(`${region} deployment dates are not ordered.`);
    } catch {
      errors.push(`${region} deployment dates are invalid.`);
    }
    if (!rangeIsOrdered(config.regionalDistribution[region])) errors.push(`${region} production distribution is not ordered.`);
  }
  if (config.vmt?.arimaOrder.join(",") !== "1,1,1") errors.push("The notebook VMT forecast supports ARIMA order [1, 1, 1].");
  return errors;
}
