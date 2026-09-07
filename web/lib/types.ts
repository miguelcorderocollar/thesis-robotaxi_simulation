export const REGIONS = [
  "USA",
  "Europe",
  "China",
  "APAC excl China",
  "Canada",
] as const;

export type Region = (typeof REGIONS)[number];

export interface DistributionRange {
  min: number;
  bear: number;
  bull: number;
  max: number;
}

export interface DeploymentRange {
  min: string;
  bull: string;
  bear: string;
  max: string;
}

export type GeneralInputKey =
  | "Price/Mile"
  | "Price/Mile Asia"
  | "Costs/Mile"
  | "Platform fee"
  | "Hours/day"
  | "Days/week"
  | "Miles/hour"
  | "% ocupacy"
  | "Network Participation"
  | "Car Lifespan";

export interface ImpactConfig {
  co2PerMile: Record<"USA" | "Europe" | "China", { ice: number; ev: number }>;
  co2Produced: Record<"USA" | "Europe" | "China", number>;
  alaCostPerGallon: number;
  usaMpg: number;
  carsUsa: number;
  avgMilesCar: number;
  hoursInYear: number;
  productivityPerHour: Partial<Record<Region, number>>;
  gdpByRegion: Partial<Record<Region, number>>;
}

export interface VmtConfig {
  enabled: boolean;
  arimaOrder: [number, number, number];
}

export interface SimulationConfig {
  yearsToSimulate: number;
  numSimulations: number;
  seed: number;

  daysPerWeek: number;
  hoursPerDay: number;
  milesPerHour: number;
  occupancyPct: number;
  networkParticipation: number;
  carLifespan: number;

  pricePerMile: number;
  pricePerMileAsia: number;
  platformFee: number;
  costsPerMile: number;

  growth: DistributionRange;
  generalInputs: Record<GeneralInputKey, DistributionRange>;
  growthByYear: Record<string, DistributionRange>;
  regionalDistribution: Record<Region, DistributionRange>;
  regionalShares: Record<Region, number>;
  deploymentDates: Record<Region, DeploymentRange>;
  impact: ImpactConfig;
  vmt: VmtConfig;
}

export interface ScenarioSeries {
  average: number[];
  p25: number[];
  p75: number[];
}

export interface RegionalScenarioSeries {
  [region: string]: ScenarioSeries;
}

export interface SimulationResult {
  years: number[];
  sampleSize: number;
  seed: number;
  runtimeMs: number;
  milesPerCar: ScenarioSeries;
  fleet: ScenarioSeries;
  production: ScenarioSeries;
  discontinued: ScenarioSeries;
  robotaxiMiles: ScenarioSeries;
  revenue: ScenarioSeries;
  co2Saved: ScenarioSeries;
  carsDisplaced: ScenarioSeries;
  hoursSaved: ScenarioSeries;
  extraGdp: ScenarioSeries;
  regionalFleet: RegionalScenarioSeries;
  regionalMiles: RegionalScenarioSeries;
  regionalRevenue: RegionalScenarioSeries;
  regionalCo2Saved: RegionalScenarioSeries;
  regionalCo2SavedPercentage: RegionalScenarioSeries;
  pollutionSavings: ScenarioSeries;
  yearsSaved: ScenarioSeries;
  regionalHoursSaved: RegionalScenarioSeries;
  regionalYearsSaved: RegionalScenarioSeries;
  regionalExtraGdp: RegionalScenarioSeries;
  regionalExtraGdpPercentage: RegionalScenarioSeries;
  ownerRevenue: { nonAsia: number[]; asia: number[] };
  displacementCoefficient: number[];
  usPercentageVmt: ScenarioSeries | null;
  regionShares: Record<Region, number>;
}

export interface WorkerProgress {
  type: "progress";
  value: number;
  label: string;
}

export interface WorkerSuccess {
  type: "success";
  result: SimulationResult;
}

export interface WorkerFailure {
  type: "error";
  message: string;
}

export type WorkerMessage = WorkerProgress | WorkerSuccess | WorkerFailure;
