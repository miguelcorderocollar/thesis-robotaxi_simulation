# 🚗 Tesla Robotaxi Simulation

A Monte Carlo simulation model for analyzing the economic and environmental impact of Tesla's Robotaxi network. This project includes both a Python simulation engine and an interactive Streamlit web application.

## 📋 Overview

This simulation models the deployment and operation of Tesla's autonomous robotaxi fleet, providing insights into:
- **Economic Impact**: Revenue projections, fleet size, and network participation
- **Environmental Impact**: CO₂ emissions reduction through vehicle electrification and shared mobility
- **Regional Analysis**: Geographic distribution of vehicles and miles traveled
- **Scenario Analysis**: Bear, average, and bull case projections using Monte Carlo methods

## ✨ Features

- **Interactive Web Interface**: Streamlit-based UI with real-time parameter adjustment
- **Monte Carlo Simulation**: 5,000+ simulation runs with probabilistic modeling
- **Comprehensive Metrics**: Revenue, fleet size, miles traveled, and CO₂ savings
- **Regional Analysis**: Breakdown by geographic areas (USA, Europe, China, etc.)
- **Visualization**: Interactive charts and graphs for key metrics
- **Configurable Parameters**: Adjust deployment dates, usage patterns, pricing, and more

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/thesis-robotaxi_simulation.git
   cd thesis-robotaxi_simulation
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Streamlit application**:
   ```bash
   streamlit run app.py
   ```

4. **Open your browser** to the URL shown in the terminal (typically `http://localhost:8501`)

### Using the Application

1. **Adjust Parameters**: Use the sidebar to modify simulation parameters:
   - Deployment dates and production growth
   - Usage patterns (days per week, hours per day, miles per hour)
   - Network participation and platform fees
   - Pricing and cost assumptions
   - Environmental factors

2. **Run Simulation**: Click the "🚀 Run Simulation" button to execute the Monte Carlo simulation

3. **View Results**: Explore the results including:
   - Key metrics (Bear/Average/Bull scenarios)
   - Visualizations of global trends
   - Regional breakdowns
   - Detailed validation data

## 📁 Project Structure

```
thesis-robotaxi_simulation/
├── app.py                 # Main Streamlit application
├── app/
│   ├── __init__.py
│   └── sidebar.py         # Sidebar configuration controls
├── model/
│   ├── __init__.py
│   ├── config.py          # Simulation configuration and defaults
│   ├── core.py            # Core simulation engine
│   └── plots.py           # Visualization functions
├── Data/                  # Input data files (CSV)
│   ├── general_inputs.csv
│   ├── production_area_distribution.csv
│   ├── projected_production_growth.csv
│   ├── robotaxi_deployment_date.csv
│   ├── tesla_production_history.csv
│   └── VMT_US.csv
├── docs/                  # Documentation
│   ├── README.md          # Documentation index
│   ├── architecture.md    # Technical architecture
│   ├── implementation_milestones.md
│   └── streamlit_config.md
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🔧 Configuration

The simulation uses configuration files in the `Data/` directory:
- **general_inputs.csv**: Default parameters for usage patterns, pricing, and costs
- **production_area_distribution.csv**: Geographic distribution of production
- **projected_production_growth.csv**: Production growth projections
- **robotaxi_deployment_date.csv**: Deployment timeline by region
- **tesla_production_history.csv**: Historical production data
- **VMT_US.csv**: Vehicle miles traveled data for the USA

Parameters can be adjusted through the Streamlit UI sidebar or by modifying the CSV files.

## 📊 Key Metrics

The simulation outputs several key metrics:

- **Global Robotaxi Miles**: Total miles traveled by the robotaxi fleet
- **Tesla Revenue**: Revenue from robotaxi operations
- **CO₂ Saved**: Environmental impact in tons of CO₂ saved
- **Cumulative Cars**: Fleet size over time by region
- **Regional Breakdown**: Geographic distribution of operations

## 🧪 Running Simulations Programmatically

You can also use the simulation engine directly in Python:

```python
from model.config import SimulationConfig
from model.core import run_simulation

# Load default configuration
config = SimulationConfig.from_defaults()

# Or create a custom configuration
config = SimulationConfig(
    num_simulations=1000,
    years_to_simulate=2035,
    miles_per_car=50000,
    # ... other parameters
)

# Run simulation
results = run_simulation(config)

# Access results
print(f"Average revenue in 2030: ${results.revenue_tesla_global[2030].mean() / 1e9:.2f}B")
```

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Documentation Index](docs/README.md)**: Overview of all documentation
- **[Architecture](docs/architecture.md)**: Technical architecture and data structures
- **[Configuration Parameters](docs/streamlit_config.md)**: Detailed parameter specifications
- **[Implementation Milestones](docs/implementation_milestones.md)**: Development roadmap

## 🛠️ Development

### Running Tests

(Add test instructions when tests are implemented)

### Code Structure

- **`model/config.py`**: Configuration management and validation
- **`model/core.py`**: Monte Carlo simulation engine
- **`model/plots.py`**: Visualization utilities
- **`app.py`**: Streamlit application entry point
- **`app/sidebar.py`**: UI controls and parameter management

## 📝 License

[Add your license here - e.g., MIT, Apache 2.0, etc.]

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

[Add your contact information or GitHub profile]

## 🙏 Acknowledgments

- Tesla production and deployment data
- Vehicle miles traveled (VMT) data sources
- Environmental impact calculations based on life cycle assessment data

---

**Note**: This is a research simulation model. Results are projections based on assumptions and should not be considered financial or investment advice.

