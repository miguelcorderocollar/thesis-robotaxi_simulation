import { runSimulation } from "./simulation";
import type { SimulationConfig, WorkerMessage } from "./types";

const worker = self as unknown as {
  postMessage: (message: WorkerMessage) => void;
  onmessage: ((event: MessageEvent<{ config: SimulationConfig }>) => void) | null;
};

worker.onmessage = (event) => {
  try {
    const result = runSimulation(event.data.config, (value, label) => {
      worker.postMessage({ type: "progress", value, label });
    });
    worker.postMessage({ type: "success", result });
  } catch (error) {
    worker.postMessage({
      type: "error",
      message: error instanceof Error ? error.message : "Simulation failed.",
    });
  }
};

export {};
