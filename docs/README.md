# Project documentation

The public application lives in `web/`. It is a Next.js app whose Monte Carlo engine runs in a Web Worker, so simulation work stays in the browser and does not require a Python service.

- [Architecture](architecture.md): repository layout and runtime data flow.
- [Browser app guide](../web/README.md): local development, configuration, tests, and deployment.
- [Thesis notebook](../Tesla%20Robotaxi%20Model-checkpoint.ipynb): the original research model.

The Python code under `model/` remains as a reference implementation for research comparisons. It is not part of the deployed application.
