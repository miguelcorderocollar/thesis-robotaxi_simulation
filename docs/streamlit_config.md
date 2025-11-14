# Streamlit App Configuration Parameters

This document details all user-configurable parameters that will be exposed in the Streamlit application sidebar, organized by category.

## Configuration Categories

### 1. Simulation Settings

| Parameter | Type | Default | Range | Description | Model Variable |
|----------|------|---------|-------|-------------|----------------|
| `years_to_simulate` | Integer | 2039 | 2022-2050 | Final year of simulation | `years_to_simulate` |
| `num_simulations` | Integer | 5000 | 100-10000 | Number of Monte Carlo runs | `simulations` |

**Notes**:
- Lower simulation counts (500-1000) recommended for interactive exploration
- Higher counts (5000+) for final analysis and thesis documentation

---

### 2. Usage & Network Parameters

These parameters come from `general_inputs.csv` and control operational characteristics of the robotaxi network.

| Parameter | Type | Default | Range | Description | Model Variable |
|----------|------|---------|-------|-------------|----------------|
| `days_per_week` | Float | 7.0 | 1.0-7.0 | Days per week robotaxis operate | `Days/week` |
| `hours_per_day` | Float | 16.0 | 1.0-24.0 | Hours per day robotaxis operate | `Hours/day` |
| `miles_per_hour` | Float | 30.0 | 10.0-60.0 | Average miles per hour | `Miles/hour` |
| `occupancy_pct` | Float | 0.50 | 0.0-1.0 | Percentage of time vehicle is occupied | `% ocupacy` |
| `network_participation` | Float | 0.80 | 0.0-1.0 | Percentage of Tesla fleet participating in network | `Network Participation` |
| `car_lifespan` | Float | 15.0 | 5.0-30.0 | Expected car lifespan in years | `Car Lifespan` |

**Derived Calculation**:
- `Miles/car` = 52 × `days_per_week` × `hours_per_day` × `miles_per_hour` × `occupancy_pct`

**UI Implementation**:
- Use `st.slider()` for all parameters
- Display calculated `Miles/car` as read-only metric
- Add tooltips explaining each parameter's impact

---

### 3. Economics Parameters

Pricing, costs, and platform fees that determine revenue distribution.

| Parameter | Type | Default | Range | Description | Model Variable |
|----------|------|---------|-------|-------------|----------------|
| `price_per_mile` | Float | 1.50 | 0.50-5.00 | Price per mile (non-Asia regions) in USD | `Price/Mile` |
| `price_per_mile_asia` | Float | 1.20 | 0.50-5.00 | Price per mile (Asia regions) in USD | `Price/Mile Asia` |
| `platform_fee` | Float | 0.30 | 0.0-0.5 | Platform fee percentage (Tesla's cut) | `Platform fee` |
| `costs_per_mile` | Float | 0.20 | 0.0-1.0 | Operating costs per mile in USD | `Costs/Mile` |

**Revenue Formulas**:
- **Tesla Revenue** = `price_per_mile` × `robotaxi_miles` × `platform_fee`
- **Car Owner Revenue** = (`price_per_mile` × (1 - `platform_fee`) - `costs_per_mile`) × `miles_per_car`

**UI Implementation**:
- Use `st.number_input()` with step=0.01 for precision
- Display revenue formulas as help text
- Show calculated car owner revenue as preview metric

---

### 4. Production & Growth Parameters

Controls for Tesla vehicle production growth and regional distribution.

#### 4.1 Annual Production Growth

| Parameter | Type | Default | Range | Description | Model Variable |
|----------|------|---------|-------|-------------|----------------|
| `growth_min` | Float | 0.20 | -0.50-1.00 | Minimum annual growth rate | `Min` in `projected_production_growth.csv` |
| `growth_bear` | Float | 0.30 | -0.50-1.00 | Bear case annual growth rate | `Bear` |
| `growth_bull` | Float | 0.50 | -0.50-1.00 | Bull case annual growth rate | `Bull` |
| `growth_max` | Float | 0.80 | -0.50-1.00 | Maximum annual growth rate | `Max` |

**Initial Implementation**: Single set of growth parameters applied to all years
**Future Enhancement**: Per-year growth parameters via expandable table

#### 4.2 Regional Production Distribution

| Parameter | Type | Default | Range | Description | Model Variable |
|----------|------|---------|-------|-------------|----------------|
| `region_usa` | Float | 0.35 | 0.0-1.0 | USA production share | `USA` in `production_area_distribution.csv` |
| `region_europe` | Float | 0.25 | 0.0-1.0 | Europe production share | `Europe` |
| `region_china` | Float | 0.20 | 0.0-1.0 | China production share | `China` |
| `region_apac_excl_china` | Float | 0.15 | 0.0-1.0 | APAC (excl. China) production share | `APAC excl China` |
| `region_canada` | Float | 0.05 | 0.0-1.0 | Canada production share | `Canada` |

**Constraints**:
- All regional shares must sum to 1.0 (100%)
- UI will auto-normalize if sum ≠ 1.0
- Display warning if sum deviates significantly

**UI Implementation**:
- Use `st.slider()` for each region
- Display running total with color coding (green if sum=1.0, red if not)
- Auto-adjust option: "Normalize to 100%"

---

### 5. Robotaxi Deployment Timing

Deployment date scenarios by region. Each region has Min/Bear/Bull/Max deployment year estimates.

| Region | Parameter | Type | Default | Range | Description | Model Variable |
|--------|-----------|------|---------|-------|-------------|----------------|
| USA | `deploy_usa_min` | Integer | 2024 | 2022-2040 | Minimum deployment year | `Min` in `robotaxi_deployment_date.csv` |
| USA | `deploy_usa_bear` | Integer | 2025 | 2022-2040 | Bear case deployment year | `Bear` |
| USA | `deploy_usa_bull` | Integer | 2026 | 2022-2040 | Bull case deployment year | `Bull` |
| USA | `deploy_usa_max` | Integer | 2028 | 2022-2040 | Maximum deployment year | `Max` |
| Europe | `deploy_europe_min` | Integer | 2025 | 2022-2040 | Minimum deployment year | `Min` |
| Europe | `deploy_europe_bear` | Integer | 2026 | 2022-2040 | Bear case deployment year | `Bear` |
| Europe | `deploy_europe_bull` | Integer | 2027 | 2022-2040 | Bull case deployment year | `Bull` |
| Europe | `deploy_europe_max` | Integer | 2029 | 2022-2040 | Maximum deployment year | `Max` |
| China | `deploy_china_min` | Integer | 2024 | 2022-2040 | Minimum deployment year | `Min` |
| China | `deploy_china_bear` | Integer | 2025 | 2022-2040 | Bear case deployment year | `Bear` |
| China | `deploy_china_bull` | Integer | 2026 | 2022-2040 | Bull case deployment year | `Bull` |
| China | `deploy_china_max` | Integer | 2028 | 2022-2040 | Maximum deployment year | `Max` |
| APAC excl China | `deploy_apac_min` | Integer | 2026 | 2022-2040 | Minimum deployment year | `Min` |
| APAC excl China | `deploy_apac_bear` | Integer | 2027 | 2022-2040 | Bear case deployment year | `Bear` |
| APAC excl China | `deploy_apac_bull` | Integer | 2028 | 2022-2040 | Bull case deployment year | `Bull` |
| APAC excl China | `deploy_apac_max` | Integer | 2030 | 2022-2040 | Maximum deployment year | `Max` |
| Canada | `deploy_canada_min` | Integer | 2025 | 2022-2040 | Minimum deployment year | `Min` |
| Canada | `deploy_canada_bear` | Integer | 2026 | 2022-2040 | Bear case deployment year | `Bear` |
| Canada | `deploy_canada_bull` | Integer | 2027 | 2022-2040 | Bull case deployment year | `Bull` |
| Canada | `deploy_canada_max` | Integer | 2029 | 2022-2040 | Maximum deployment year | `Max` |

**UI Implementation**:
- Group by region in expandable sections
- Use `st.slider()` with step=1 for year selection
- Display deployment date distributions as histograms (preview)
- Validation: Ensure Min ≤ Bear ≤ Bull ≤ Max

---

### 6. Advanced Parameters (Optional)

Parameters that may be exposed for power users or kept as fixed defaults.

#### 6.1 VMT Forecast Parameters

| Parameter | Type | Default | Range | Description | Model Variable |
|----------|------|---------|-------|-------------|----------------|
| `enable_vmt_forecast` | Boolean | True | - | Enable VMT forecast calculations | - |
| `arima_order` | Tuple | (1,1,1) | - | ARIMA model order (p,d,q) | ARIMA order |
| `vmt_forecast_alpha` | Float | 0.05 | 0.01-0.10 | Confidence interval for forecast | `alpha` in forecast |

**Note**: VMT forecast is computationally expensive. Option to disable for faster runs.

#### 6.2 CO₂ Emission Factors

| Parameter | Type | Default | Range | Description | Model Variable |
|----------|------|---------|-------|-------------|----------------|
| `co2_ice_usa` | Float | 410.14 | 300-500 | CO₂ grams/mile for ICE (USA) | `ICE` in `g_co2_mile_2021` |
| `co2_ev_usa` | Float | 165.73 | 100-250 | CO₂ grams/mile for EV (USA) | `EV` |
| `co2_ice_europe` | Float | 395.72 | 300-500 | CO₂ grams/mile for ICE (Europe) | `ICE` |
| `co2_ev_europe` | Float | 133.90 | 100-250 | CO₂ grams/mile for EV (Europe) | `EV` |
| `co2_ice_china` | Float | 419.14 | 300-500 | CO₂ grams/mile for ICE (China) | `ICE` |
| `co2_ev_china` | Float | 265.41 | 100-250 | CO₂ grams/mile for EV (China) | `EV` |

**Source**: https://theicct.org/sites/default/files/Global-LCA-passenger-cars-fig1-jul2021_0.png

#### 6.3 Displacement Parameters

| Parameter | Type | Default | Range | Description | Model Variable |
|----------|------|---------|-------|-------------|----------------|
| `cars_usa_total` | Float | 282.8E6 | 200E6-350E6 | Total cars in USA | `cars_usa` |
| `avg_miles_per_car` | Float | 13476 | 10000-20000 | Average miles per car per year | `avg_miles_car` |

#### 6.4 GDP & Productivity Parameters

| Parameter | Type | Default | Range | Description | Model Variable |
|----------|------|---------|-------|-------------|----------------|
| `gdp_per_hour_usa` | Float | 74.19 | 50-100 | GDP per hour of work (USA) | `Productivity` |
| `gdp_per_hour_europe` | Float | 54.25 | 40-70 | GDP per hour of work (Europe) | `Productivity` |
| `gdp_per_hour_china` | Float | 15.00 | 10-30 | GDP per hour of work (China) | `Productivity` |
| `gdp_per_hour_canada` | Float | 56.61 | 40-70 | GDP per hour of work (Canada) | `Productivity` |

#### 6.5 Pollution Cost Parameters

| Parameter | Type | Default | Range | Description | Model Variable |
|----------|------|---------|-------|-------------|----------------|
| `ala_cost_per_gallon` | Float | 1.15 | 0.50-2.00 | Health cost per gallon (ALA) | `ALA_cost_gallon` |
| `usa_mpg` | Float | 25.4 | 20-35 | USA average miles per gallon | `usa_mpg` |

---

## Configuration Data Structure

### Python Implementation (Planned)

```python
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class SimulationConfig:
    # Simulation settings
    years_to_simulate: int = 2039
    num_simulations: int = 5000
    
    # Usage & Network
    days_per_week: float = 7.0
    hours_per_day: float = 16.0
    miles_per_hour: float = 30.0
    occupancy_pct: float = 0.50
    network_participation: float = 0.80
    car_lifespan: float = 15.0
    
    # Economics
    price_per_mile: float = 1.50
    price_per_mile_asia: float = 1.20
    platform_fee: float = 0.30
    costs_per_mile: float = 0.20
    
    # Production Growth (simplified - same for all years initially)
    growth_min: float = 0.20
    growth_bear: float = 0.30
    growth_bull: float = 0.50
    growth_max: float = 0.80
    
    # Regional Distribution
    region_usa: float = 0.35
    region_europe: float = 0.25
    region_china: float = 0.20
    region_apac_excl_china: float = 0.15
    region_canada: float = 0.05
    
    # Deployment Dates (by region)
    deployment_dates: Dict[str, Dict[str, int]] = None
    
    # Advanced (optional)
    enable_vmt_forecast: bool = True
    # ... other advanced params
    
    @classmethod
    def from_defaults(cls):
        """Load defaults from CSV files"""
        # Implementation to read from Data/*.csv
        pass
    
    def to_dict(self):
        """Convert to dictionary for caching key"""
        return asdict(self)
```

---

## Default Values Source

Default values are loaded from existing CSV files:

1. **`general_inputs.csv`**: Usage, network, and economics parameters
2. **`projected_production_growth.csv`**: Production growth scenarios (per year)
3. **`production_area_distribution.csv`**: Regional production distribution
4. **`robotaxi_deployment_date.csv`**: Deployment timing by region
5. **`tesla_production_history.csv`**: Historical production data (read-only)
6. **`VMT_US.csv`**: Historical VMT data for ARIMA forecast (read-only)

**Note**: Historical data files are read-only and not user-configurable. They serve as baseline inputs for the simulation.

---

## Validation Rules

1. **Regional Distribution**: Sum must equal 1.0 (100%)
2. **Deployment Dates**: Min ≤ Bear ≤ Bull ≤ Max for each region
3. **Growth Rates**: Min ≤ Bear ≤ Bull ≤ Max
4. **Percentages**: All percentage values must be between 0.0 and 1.0
5. **Years**: `years_to_simulate` must be >= 2022
6. **Simulations**: `num_simulations` must be >= 100 for meaningful results

---

## UI Control Recommendations

### Input Types by Parameter

- **Sliders** (`st.slider`): Continuous values with clear ranges (e.g., percentages, prices)
- **Number Inputs** (`st.number_input`): Values requiring precision (e.g., prices with decimals)
- **Select Boxes** (`st.selectbox`): Discrete choices (e.g., ARIMA order)
- **Checkboxes** (`st.checkbox`): Boolean flags (e.g., enable/disable features)
- **Date Inputs** (`st.date_input`): For deployment dates (if converted from years)
- **Expanders** (`st.expander`): Group related parameters, especially for advanced options

### Help Text & Tooltips

Each parameter should include:
- **Description**: What the parameter controls
- **Impact**: How changing it affects results
- **Source**: Where the default value comes from (if applicable)
- **Units**: Clear unit labels (USD, %, years, etc.)

---

## Configuration Presets

Planned preset configurations for quick scenario switching:

1. **Conservative**: Lower growth, later deployment, lower participation
2. **Base Case**: Default values from CSV files
3. **Aggressive**: Higher growth, earlier deployment, higher participation
4. **Custom**: User-defined (future: save/load)

