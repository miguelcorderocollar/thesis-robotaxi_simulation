# Technical Architecture - Streamlit App

This document describes the technical architecture, data structures, and implementation details for the Tesla Robotaxi Simulation Streamlit application.

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                    │
│  (app.py - Sidebar, Tabs, Visualizations, KPIs)         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  Configuration Layer                     │
│  (model/config.py - SimulationConfig, Validation)       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  Simulation Engine                        │
│  (model/core.py - run_simulation(), Helper Functions)    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  Visualization Layer                      │
│  (model/plots.py - Plotting Functions)                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                    Data Layer                            │
│  (Data/*.csv - Historical Data, Defaults)               │
└─────────────────────────────────────────────────────────┘
```

## Data Structures

### SimulationConfig

**Purpose**: Encapsulates all user-configurable parameters for a simulation run.

**Location**: `model/config.py`

**Structure**:
```python
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class SimulationConfig:
    # Simulation settings
    years_to_simulate: int
    num_simulations: int
    
    # Usage & Network
    days_per_week: float
    hours_per_day: float
    miles_per_hour: float
    occupancy_pct: float
    network_participation: float
    car_lifespan: float
    
    # Economics
    price_per_mile: float
    price_per_mile_asia: float
    platform_fee: float
    costs_per_mile: float
    
    # Production Growth (simplified - per year in future)
    growth_min: float
    growth_bear: float
    growth_bull: float
    growth_max: float
    
    # Regional Distribution
    region_usa: float
    region_europe: float
    region_china: float
    region_apac_excl_china: float
    region_canada: float
    
    # Deployment Dates
    deployment_dates: Dict[str, Dict[str, int]]
    # Format: {'USA': {'Min': 2024, 'Bear': 2025, 'Bull': 2026, 'Max': 2028}, ...}
    
    # Advanced (optional)
    enable_vmt_forecast: bool = True
    # ... other advanced params
    
    @classmethod
    def from_defaults(cls) -> 'SimulationConfig':
        """Load default values from CSV files"""
        pass
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        pass
    
    def to_hash(self) -> str:
        """Generate hash for caching"""
        pass
```

**Key Methods**:
- `from_defaults()`: Load defaults from `Data/*.csv` files
- `validate()`: Check constraints (e.g., regional distribution sums to 1.0)
- `to_hash()`: Generate unique identifier for caching

---

### SimulationResults

**Purpose**: Contains all computed results from a simulation run.

**Location**: `model/core.py`

**Structure**:
```python
from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd

@dataclass
class SimulationResults:
    # Configuration used
    config: SimulationConfig
    
    # Years and simulation list
    years: List[int]
    simulation_list: List[int]
    
    # Fleet metrics
    cum_cars_by_area: Dict[str, pd.DataFrame]  # [simulation][year]
    prod_cars_by_area: Dict[str, pd.DataFrame]
    prod_disc_by_area: Dict[str, pd.DataFrame]
    
    # Robotaxi metrics
    robotaxi_miles_per_region: Dict[str, pd.DataFrame]
    robotaxi_miles: pd.DataFrame  # Global
    
    # Revenue metrics
    revenue_tesla_per_region: Dict[str, pd.DataFrame]
    revenue_tesla_global: pd.DataFrame
    car_owner_revenue: pd.Series  # Non-Asia
    car_owner_revenue_asia: pd.Series
    
    # Environmental metrics
    tons_co2_saved: Dict[str, pd.DataFrame]
    percentage_tons_co2_saved_per_region: Dict[str, pd.DataFrame]
    savings_pollution_ALA: pd.DataFrame
    
    # Displacement metrics
    cars_displaced: pd.DataFrame
    displacement_coefficient: pd.Series
    
    # Time & GDP metrics
    hours_saved_per_region: Dict[str, pd.DataFrame]
    years_saved_per_region: Dict[str, pd.DataFrame]
    extra_gdp: Dict[str, pd.DataFrame]
    percentage_extra_gdp: Dict[str, pd.DataFrame]
    
    # VMT forecast (optional)
    vmt_forecast: Optional[pd.DataFrame] = None
    us_percentage_vmt: Optional[pd.DataFrame] = None
```

**DataFrame Structure**:
- **Rows**: Simulation index (0 to num_simulations-1)
- **Columns**: Years (2022 to years_to_simulate)
- **Values**: Computed metrics (miles, revenue, cars, etc.)

**Example**:
```python
# robotaxi_miles_per_region['USA']
#          2022    2023    2024    2025    ...
# 0      1.2e12  2.5e12  4.1e12  6.8e12   ...
# 1      1.1e12  2.3e12  3.9e12  6.5e12   ...
# ...
# 4999   1.3e12  2.7e12  4.3e12  7.1e12   ...
```

---

## Core Functions

### Simulation Engine

**Location**: `model/core.py`

**Main Function**:
```python
def run_simulation(config: SimulationConfig) -> SimulationResults:
    """
    Execute Monte Carlo simulation with given configuration.
    
    Steps:
    1. Generate random distributions for general inputs
    2. Calculate production growth and regional distribution
    3. Compute cumulative cars per region (with discontinuation)
    4. Simulate robotaxi deployment dates
    5. Calculate robotaxi miles
    6. Forecast VMT (if enabled)
    7. Calculate revenue, CO₂, displacement, time saved, GDP
    8. Return SimulationResults object
    """
    pass
```

**Helper Functions** (extracted from notebook):
- `simulate_norm_dist(mini, bear, bull, maxi) -> np.array`
- `simulate_normal_dist_row(row) -> pd.Series`
- `get_sims_robo_deployment(table) -> pd.DataFrame`
- `datetime_to_timestamp(table) -> pd.DataFrame`
- `timestamp_to_datetime(table) -> pd.DataFrame`
- `get_years_regions_future_production(row) -> pd.DataFrame`
- `get_standarise_percentages(dictionary) -> dict`
- `get_all_percentage_years_robo(dates_by_area) -> dict`
- `get_revenue_tesla_per_region(gen_inp, robo_miles) -> dict`
- `get_percentage_year_left(date) -> float`
- `get_average_per_year(dataframe) -> pd.DataFrame`
- `get_quantile_per_year(dataframe, q) -> pd.DataFrame`
- `get_global_from_areas(data) -> pd.DataFrame`
- `get_discontinued_by_calculation(area, year, i, ls, ls_dec) -> float`

---

### Plotting Functions

**Location**: `model/plots.py`

**Functions**:
```python
def plot_area_series(
    data: Dict[str, pd.DataFrame],
    legend: str,
    magnitude: int = 0
) -> matplotlib.figure.Figure:
    """
    Plot average, bear, and bull cases for multiple areas.
    Returns matplotlib Figure for Streamlit display.
    """
    pass

def plot_global_series(
    data: pd.DataFrame,
    legend: str,
    magnitude: int = 0
) -> matplotlib.figure.Figure:
    """
    Plot global series with bear/average/bull scenarios.
    Returns matplotlib Figure for Streamlit display.
    """
    pass

def plot_3_areas(
    data: Dict[str, pd.DataFrame],
    legend: str,
    magnitude: int = 0
) -> matplotlib.figure.Figure:
    """
    Plot three areas side-by-side with bear/average/bull.
    Returns matplotlib Figure for Streamlit display.
    """
    pass

def plot_percentage_graph(
    data: pd.DataFrame,
    title: str
) -> matplotlib.figure.Figure:
    """
    Plot percentage bar chart with error bars.
    Returns matplotlib Figure for Streamlit display.
    """
    pass
```

**Key Changes from Notebook**:
- Return `matplotlib.figure.Figure` instead of calling `plt.show()`
- Remove notebook-specific code (`%matplotlib inline`, magic commands)
- Ensure figures are properly closed/returned for Streamlit

---

## Streamlit Application Structure

### Main Application File

**Location**: `app.py`

**Structure**:
```python
import streamlit as st
from model.config import SimulationConfig
from model.core import run_simulation
from model.plots import plot_global_series, plot_area_series, ...

# Page configuration
st.set_page_config(...)

# Sidebar
def render_sidebar() -> SimulationConfig:
    """Render sidebar controls and return user configuration"""
    with st.sidebar:
        # Simulation settings
        # Usage & Network
        # Economics
        # Production & Growth
        # Deployment Timing
        # Advanced Options
    return config

# Main content
def render_main_content(results: SimulationResults):
    """Render main content area with tabs and visualizations"""
    # Summary KPIs
    # Tabs
    # Visualizations

# Main execution
if __name__ == "__main__":
    config = render_sidebar()
    results = run_simulation(config)
    render_main_content(results)
```

---

### Caching Strategy

**Purpose**: Improve performance by caching expensive computations.

**Implementation**:

1. **Static Data Caching**:
```python
@st.cache_data
def load_csv_data(filepath: str) -> pd.DataFrame:
    """Load CSV file (cached)"""
    return pd.read_csv(filepath, ...)
```

2. **ARIMA Model Caching**:
```python
@st.cache_resource
def train_arima_model(vmt_history: pd.DataFrame) -> ARIMAResults:
    """Train ARIMA model (cached as resource)"""
    model = ARIMA(...)
    return model.fit()
```

3. **Simulation Results Caching**:
```python
@st.cache_data
def cached_run_simulation(config_hash: str, config_dict: dict) -> SimulationResults:
    """Cache simulation results keyed by configuration hash"""
    config = SimulationConfig.from_dict(config_dict)
    return run_simulation(config)
```

**Cache Invalidation**:
- Static data: Never invalidated (read-only CSV files)
- ARIMA model: Invalidated if VMT data changes
- Simulation results: Invalidated when config changes (detected via hash)

---

### Session State Management

**Purpose**: Manage application state and avoid unnecessary recomputations.

**Usage**:
```python
# Initialize session state
if 'last_config_hash' not in st.session_state:
    st.session_state.last_config_hash = None
if 'results' not in st.session_state:
    st.session_state.results = None

# Check if config changed
current_config = render_sidebar()
current_hash = current_config.to_hash()

if current_hash != st.session_state.last_config_hash:
    # Config changed, rerun simulation
    st.session_state.results = run_simulation(current_config)
    st.session_state.last_config_hash = current_hash
else:
    # Use cached results
    results = st.session_state.results
```

---

## Data Flow

### Simulation Execution Flow

```
User Inputs (Sidebar)
    ↓
SimulationConfig Object
    ↓
[Cache Check] → If cached, return cached results
    ↓
Generate Random Distributions
    ├─ General Inputs (usage, economics)
    ├─ Production Growth (per year)
    ├─ Regional Distribution
    └─ Deployment Dates (per region)
    ↓
Calculate Fleet Metrics
    ├─ Production by Region
    ├─ Discontinued Cars
    └─ Cumulative Cars
    ↓
Calculate Robotaxi Metrics
    ├─ Deployment Availability (%)
    ├─ Robotaxi Miles
    └─ Revenue
    ↓
Calculate Environmental Metrics
    ├─ CO₂ Saved
    ├─ Pollution Savings
    └─ Displacement
    ↓
Calculate Economic Metrics
    ├─ Time Saved
    ├─ GDP Impact
    └─ Car Owner Revenue
    ↓
[Cache Results]
    ↓
SimulationResults Object
    ↓
Visualization & Display
```

---

## File Structure

```
thesis-robotaxi_simulation/
├── app.py                    # Main Streamlit application
├── model/
│   ├── __init__.py
│   ├── config.py            # SimulationConfig class
│   ├── core.py              # Simulation engine and helper functions
│   └── plots.py             # Plotting functions
├── Data/                     # Static CSV data files
│   ├── general_inputs.csv
│   ├── tesla_production_history.csv
│   ├── production_area_distribution.csv
│   ├── projected_production_growth.csv
│   ├── robotaxi_deployment_date.csv
│   └── VMT_US.csv
├── docs/
│   ├── streamlit_app_overview.md
│   ├── streamlit_config.md
│   ├── implementation_milestones.md
│   └── architecture.md
├── tests/
│   ├── test_model_api.py
│   └── test_integration.py
├── requirements.txt
├── README.md
└── .streamlit/
    └── config.toml
```

---

## Performance Considerations

### Optimization Strategies

1. **Caching**:
   - Cache static data (CSV files)
   - Cache expensive computations (ARIMA, simulations)
   - Use appropriate cache decorators (`@st.cache_data` vs `@st.cache_resource`)

2. **Simulation Count**:
   - Default to 1,000 simulations for interactive use
   - Allow increase to 5,000+ for final analysis
   - Warn users about performance impact

3. **Lazy Loading**:
   - Only compute tab data when tab is selected
   - Defer heavy computations (ARIMA diagnostics) until needed

4. **Progress Indicators**:
   - Show progress bars for long-running computations
   - Display estimated time remaining

5. **Memory Management**:
   - Clear large DataFrames when not needed
   - Use efficient data types (e.g., `float32` instead of `float64` if precision allows)

---

## Error Handling

### Error Types

1. **Configuration Errors**:
   - Invalid parameter ranges
   - Regional distribution doesn't sum to 1.0
   - Deployment dates out of order

2. **Data Loading Errors**:
   - Missing CSV files
   - Corrupted data
   - Incorrect data format

3. **Computation Errors**:
   - Numerical errors (division by zero, etc.)
   - ARIMA model convergence issues
   - Memory errors for large simulations

### Error Handling Strategy

```python
try:
    config = render_sidebar()
    config.validate()  # Raises ValidationError if invalid
    results = run_simulation(config)
except ValidationError as e:
    st.error(f"Configuration error: {e}")
except FileNotFoundError as e:
    st.error(f"Data file not found: {e}")
except Exception as e:
    st.error(f"Unexpected error: {e}")
    st.exception(e)  # Show full traceback in expander
```

---

## Testing Strategy

### Unit Tests

- Test individual functions (e.g., `simulate_norm_dist()`)
- Test configuration validation
- Test data loading

### Integration Tests

- Test `run_simulation()` with various configs
- Test plotting functions
- Test Streamlit components

### Validation Tests

- Compare outputs with notebook results
- Verify numerical accuracy
- Check plot formatting

---

## Future Enhancements

1. **Export Functionality**: Download results as CSV/PDF
2. **Comparison Mode**: Side-by-side scenario comparison
3. **Sensitivity Analysis**: Automated parameter sweep
4. **Scenario Presets**: Save/load custom configurations
5. **Advanced Distributions**: Non-normal distributions
6. **Real-time Collaboration**: Share scenarios via URL parameters
7. **Database Backend**: Store results and configurations
8. **API Endpoints**: REST API for programmatic access

