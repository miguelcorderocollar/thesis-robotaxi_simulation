# Tesla Robotaxi Simulation - Streamlit App Overview

## Purpose

This document describes the design and architecture of the Streamlit web application that provides an interactive interface for the Tesla Robotaxi economic and environmental impact simulation model.

## Main Use Cases

1. **Interactive Scenario Analysis**: Users can adjust key assumptions (pricing, network participation, deployment timing) and immediately see the impact on revenue, CO₂ savings, and other metrics.

2. **Sensitivity Analysis**: Explore how different parameter combinations affect outcomes without modifying code or CSV files.

3. **Thesis Documentation**: Generate reproducible results with documented assumptions for academic presentation.

4. **Stakeholder Presentations**: Visualize key metrics and trends through an accessible web interface.

## High-Level Architecture

### Data Flow

```
User Inputs (Sidebar Controls)
    ↓
SimulationConfig Object
    ↓
Monte Carlo Simulation Engine
    ↓
SimulationResults Object
    ↓
Visualization & Metrics Display
```

### Component Structure

```
thesis-robotaxi_simulation/
├── app.py                    # Main Streamlit application entry point
├── model/
│   ├── __init__.py
│   ├── config.py            # Configuration data structures
│   ├── core.py              # Core simulation logic (extracted from notebook)
│   └── plots.py             # Plotting functions adapted for Streamlit
├── Data/                     # Static CSV data files (historical data)
│   ├── general_inputs.csv
│   ├── tesla_production_history.csv
│   ├── production_area_distribution.csv
│   ├── projected_production_growth.csv
│   ├── robotaxi_deployment_date.csv
│   └── VMT_US.csv
└── docs/                     # Documentation
    ├── streamlit_app_overview.md
    ├── streamlit_config.md
    ├── implementation_milestones.md
    └── architecture.md
```

## User Interface Design

### Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  Header: Title + Description                            │
├──────────────┬──────────────────────────────────────────┤
│              │  Summary KPI Cards (4-6 metrics)        │
│   SIDEBAR    │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│              │  │ KPI1 │ │ KPI2 │ │ KPI3 │ │ KPI4 │   │
│  Config      │  └──────┘ └──────┘ └──────┘ └──────┘   │
│  Controls    │                                          │
│              │  ┌────────────────────────────────────┐  │
│  - Sim       │  │  Tab 1 │ Tab 2 │ Tab 3 │ ...     │  │
│  Settings    │  └────────────────────────────────────┘  │
│              │                                          │
│  - Usage &   │  [Chart/Plot Area]                      │
│  Network     │                                          │
│              │                                          │
│  - Economics │  [Additional visualizations]           │
│              │                                          │
│  - Production│                                          │
│              │                                          │
│  - Deployment│                                          │
└──────────────┴──────────────────────────────────────────┘
```

### Key UI Components

#### 1. Sidebar Configuration Panel

All user inputs are organized in collapsible sections:

- **Simulation Settings**: Years to simulate, number of Monte Carlo runs
- **Usage & Network**: Operational parameters (days/week, hours/day, miles/hour, occupancy, participation)
- **Economics**: Pricing, costs, platform fees
- **Production & Growth**: Annual growth rates, regional distribution
- **Robotaxi Deployment**: Deployment timing by region (Min/Bear/Bull/Max scenarios)
- **Advanced Options**: Optional parameters for power users

#### 2. Main Content Area

**Top Section - Summary KPIs**:
- 2030 Global Robotaxi Miles (Average/Bear/Bull)
- 2030 Tesla Revenue (Average/Bear/Bull)
- 2030 CO₂ Saved (tons)
- 2030 Cars Displaced (USA)
- Average Car Owner Revenue (non-Asia/Asia)

**Tabbed Results Sections**:
1. **Production & Fleet**: Production, discontinued cars, cumulative fleet by region
2. **Robotaxi Miles**: Miles traveled by region and globally
3. **Tesla Revenue**: Revenue breakdown by region and globally
4. **Car Owner Economics**: Revenue distribution histograms
5. **CO₂ & Pollution**: Environmental impact metrics
6. **Displacement & S-Curves**: Vehicle displacement analysis
7. **Time Saved & GDP**: Productivity and economic impact
8. **Diagnostics**: Model validation and reproducibility info

## Key Design Decisions

### 1. No File Uploads
- All configuration is entered via UI controls
- Default values loaded from existing CSV files
- Ensures reproducibility and ease of use

### 2. Caching Strategy
- Cache static data (CSV files) using `st.cache_data`
- Cache heavy computations (ARIMA model, VMT forecast) using `st.cache_resource`
- Cache simulation results keyed by configuration hash
- Allow users to adjust simulation count for performance vs. accuracy tradeoff

### 3. Progressive Disclosure
- Basic parameters visible by default
- Advanced options hidden in expanders
- Preset configurations (Conservative, Base Case, Aggressive) for quick scenario switching

### 4. Performance Optimization
- Default to fewer simulations (e.g., 1,000) for interactive use
- Option to increase to 5,000+ for final analysis
- Toggle heavy computations (ARIMA diagnostics) on/off
- Lazy loading of tabs (compute on demand)

## Integration with Existing Model

The Streamlit app wraps the existing simulation logic from:
- `Tesla Robotaxi Model-checkpoint.ipynb` (Jupyter notebook)
- `original_model.py` (Python script)

**Key Functions Preserved**:
- `simulate_norm_dist()`: Truncated normal distribution simulation
- `get_years_regions_future_production()`: Regional production growth
- `get_sims_robo_deployment()`: Robotaxi deployment date simulation
- `get_revenue_tesla_per_region()`: Revenue calculations
- All plotting functions adapted for Streamlit display

**Model Logic Flow** (from notebook):
1. Load historical data (production, VMT)
2. Generate Monte Carlo simulations for general inputs
3. Calculate production growth and regional distribution
4. Compute cumulative cars per region (accounting for discontinuation)
5. Simulate robotaxi deployment dates by region
6. Calculate robotaxi miles (cars × miles/car × participation × availability)
7. Forecast VMT using ARIMA
8. Calculate revenue, CO₂ savings, displacement, time saved, GDP impact

## Output Metrics

### Primary Metrics
- **Robotaxi Miles**: Total miles driven by Tesla robotaxis globally and by region
- **Tesla Revenue**: Platform revenue from robotaxi operations
- **Car Owner Revenue**: Annual revenue for Tesla owners participating in network
- **CO₂ Saved**: Tons of CO₂ emissions avoided vs. ICE vehicles
- **Cars Displaced**: Number of traditional vehicles replaced by robotaxis
- **Time Saved**: Hours/years of productivity unlocked
- **GDP Impact**: Potential additional GDP from productivity gains

### Visualization Types
- **Time Series Plots**: Average, Bear (25th percentile), Bull (75th percentile) scenarios
- **Histograms**: Distribution of outcomes (e.g., car owner revenue)
- **Bar Charts**: Percentage metrics (e.g., % of VMT, % of CO₂ saved)
- **Multi-line Plots**: Regional comparisons and S-curves

## Future Enhancements (Post-MVP)

1. **Export Functionality**: Download results as CSV/PDF
2. **Comparison Mode**: Side-by-side comparison of two scenarios
3. **Sensitivity Analysis**: Automated parameter sweep visualization
4. **Scenario Presets**: Save and load custom configurations
5. **Advanced Distributions**: Support for non-normal distributions
6. **Real-time Collaboration**: Share scenarios via URL parameters

