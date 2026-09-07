import { describe, expect, it } from "vitest";
import { DEFAULT_CONFIG, REGIONS } from "./data";
import { runSimulation, validateConfig } from "./simulation";
import type { SimulationConfig } from "./types";

function testConfig(overrides: Partial<SimulationConfig> = {}): SimulationConfig {
  const generalInputs = { ...DEFAULT_CONFIG.generalInputs, ...(overrides.generalInputs ?? {}) };
  if (overrides.networkParticipation !== undefined) generalInputs["Network Participation"] = { ...generalInputs["Network Participation"], bear: overrides.networkParticipation };
  if (overrides.hoursPerDay !== undefined) generalInputs["Hours/day"] = { ...generalInputs["Hours/day"], bear: overrides.hoursPerDay };
  if (overrides.milesPerHour !== undefined) generalInputs["Miles/hour"] = { ...generalInputs["Miles/hour"], bear: overrides.milesPerHour };
  if (overrides.occupancyPct !== undefined) generalInputs["% ocupacy"] = { ...generalInputs["% ocupacy"], bear: overrides.occupancyPct };
  if (overrides.carLifespan !== undefined) generalInputs["Car Lifespan"] = { ...generalInputs["Car Lifespan"], bear: overrides.carLifespan };
  if (overrides.pricePerMile !== undefined) generalInputs["Price/Mile"] = { ...generalInputs["Price/Mile"], bear: overrides.pricePerMile };
  if (overrides.platformFee !== undefined) generalInputs["Platform fee"] = { ...generalInputs["Platform fee"], bear: overrides.platformFee };
  return {
    ...DEFAULT_CONFIG,
    ...overrides,
    numSimulations: overrides.numSimulations ?? 120,
    yearsToSimulate: overrides.yearsToSimulate ?? 2032,
    seed: overrides.seed ?? 42,
    growth: { ...DEFAULT_CONFIG.growth, ...(overrides.growth ?? {}) },
    generalInputs,
    growthByYear: { ...DEFAULT_CONFIG.growthByYear, ...(overrides.growthByYear ?? {}) },
    regionalDistribution: { ...DEFAULT_CONFIG.regionalDistribution, ...(overrides.regionalDistribution ?? {}) },
    regionalShares: { ...DEFAULT_CONFIG.regionalShares, ...(overrides.regionalShares ?? {}) },
    deploymentDates: { ...DEFAULT_CONFIG.deploymentDates, ...(overrides.deploymentDates ?? {}) },
    impact: { ...DEFAULT_CONFIG.impact, ...(overrides.impact ?? {}) },
    vmt: { ...DEFAULT_CONFIG.vmt, ...(overrides.vmt ?? {}) },
  };
}

describe("browser simulation engine", () => {
  it("accepts the reference configuration", () => {
    expect(validateConfig(testConfig())).toEqual([]);
  });

  it("keeps every notebook input range and impact output available", () => {
    expect(Object.keys(DEFAULT_CONFIG.generalInputs)).toHaveLength(10);
    expect(Object.keys(DEFAULT_CONFIG.growthByYear)).toContain("2039");
    expect(Object.keys(DEFAULT_CONFIG.regionalDistribution)).toEqual(expect.arrayContaining([...REGIONS]));
    expect(DEFAULT_CONFIG.impact.co2PerMile.USA.ice).toBe(410.141318);
    const result = runSimulation(testConfig({ yearsToSimulate: 2024, vmt: { enabled: true, arimaOrder: [1, 1, 1] } }));
    expect(result.usPercentageVmt).not.toBeNull();
    expect(result.regionalCo2SavedPercentage.USA.average).toHaveLength(3);
    expect(result.regionalExtraGdpPercentage.Canada.average).toHaveLength(3);
  });

  it("rejects invalid regional shares and deployment order", () => {
    const invalid = testConfig({
      regionalShares: { ...DEFAULT_CONFIG.regionalShares, USA: 0.99 },
      deploymentDates: {
        ...DEFAULT_CONFIG.deploymentDates,
        USA: { min: "01/01/2025", bull: "01/01/2024", bear: "01/01/2026", max: "01/01/2029" },
      },
    });
    expect(validateConfig(invalid)).toHaveLength(2);
  });

  it("is deterministic for a fixed seed", () => {
    const first = runSimulation(testConfig({ seed: 123 }));
    const second = runSimulation(testConfig({ seed: 123 }));
    expect(first.robotaxiMiles).toEqual(second.robotaxiMiles);
    expect(first.revenue).toEqual(second.revenue);
    expect(first.ownerRevenue).toEqual(second.ownerRevenue);
  });

  it("changes the operational result when network participation changes", () => {
    const lower = runSimulation(testConfig({ seed: 7, networkParticipation: 0.2 }));
    const higher = runSimulation(testConfig({ seed: 7, networkParticipation: 0.4 }));
    expect(higher.robotaxiMiles.average.at(-1)!).toBeGreaterThan(lower.robotaxiMiles.average.at(-1)!);
    expect(higher.revenue.average.at(-1)!).toBeGreaterThan(lower.revenue.average.at(-1)!);
  });

  it("keeps region summaries and impact metrics finite", () => {
    const result = runSimulation(testConfig({ seed: 9 }));
    expect(result.years).toEqual([2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032]);
    for (const series of [result.fleet, result.robotaxiMiles, result.revenue, result.co2Saved, result.carsDisplaced, result.hoursSaved]) {
      for (const value of [...series.average, ...series.p25, ...series.p75]) expect(Number.isFinite(value)).toBe(true);
    }
    for (const region of REGIONS) {
      expect(result.regionalFleet[region].average).toHaveLength(result.years.length);
      expect(result.regionalMiles[region].average.every((value) => value >= 0)).toBe(true);
    }
    expect(result.ownerRevenue.nonAsia).toHaveLength(120);
    expect(result.displacementCoefficient.every((value) => Number.isFinite(value))).toBe(true);
    expect(result.pollutionSavings.average.every((value) => value >= 0)).toBe(true);
    expect(result.yearsSaved.average.every((value) => value >= 0)).toBe(true);
  });

  it("uses the same miles-per-car relationship as the thesis model", () => {
    const result = runSimulation(testConfig({ seed: 11, numSimulations: 500 }));
    const mean = result.milesPerCar.average[0];
    const expectedCenter = 52 * 5.6 * 8 * 13 * 0.45;
    expect(mean).toBeGreaterThan(expectedCenter * 0.5);
    expect(mean).toBeLessThan(expectedCenter * 2.5);
  });

  it("matches the Python reference distribution within Monte Carlo tolerance", () => {
    const result = runSimulation({ ...DEFAULT_CONFIG, numSimulations: 1000, seed: 123 });
    const index = result.years.indexOf(2030);
    const mean = (values: number[]) => values.reduce((sum, value) => sum + value, 0) / values.length;
    const closeToPython = (actual: number, reference: number, tolerance = 0.03) => {
      expect(Math.abs(actual - reference) / Math.abs(reference)).toBeLessThan(tolerance);
    };

    // Reference values come from a notebook-faithful Python run with the CSV
    // ranges, 1,000 draws, and np.random.seed(123). The browser uses a
    // separate seeded generator, so a small Monte Carlo difference is expected.
    closeToPython(result.robotaxiMiles.average[index], 557299911409.619);
    closeToPython(result.robotaxiMiles.p25[index], 420727855714.0623);
    closeToPython(result.robotaxiMiles.p75[index], 671122697143.5015);
    closeToPython(result.revenue.average[index], 153140414696.39993);
    closeToPython(result.fleet.average[index], 69474592.88682076);
    closeToPython(result.co2Saved.average[index], 115607331.76332165);
    closeToPython(mean(result.ownerRevenue.nonAsia), 13978.79740012576);
    closeToPython(mean(result.ownerRevenue.asia), 8415.74823054287);
  });

  it("keeps the 5,000-draw engine bounded in the optimized runtime", () => {
    const started = performance.now();
    const result = runSimulation({ ...DEFAULT_CONFIG, numSimulations: 5000, seed: 321 });
    const elapsed = performance.now() - started;
    expect(result.sampleSize).toBe(5000);
    expect(result.robotaxiMiles.average).toHaveLength(18);
    expect(elapsed).toBeLessThan(5000);
  });
});
