"""
Sidebar configuration controls for Tesla Robotaxi Simulation.

Milestone 4: Production, Distribution, and Deployment Controls
"""

import streamlit as st
from model.config import SimulationConfig
import copy


def _apply_conservative_preset(config: SimulationConfig):
    """Apply conservative preset: lower growth, later deployment."""
    # Lower growth rates
    st.session_state['growth_min'] = 0.10
    st.session_state['growth_bear'] = 0.20
    st.session_state['growth_bull'] = 0.35
    st.session_state['growth_max'] = 0.50
    
    # Later deployment (add 2 years)
    if 'deployment_dates' not in st.session_state:
        st.session_state['deployment_dates'] = copy.deepcopy(config.deployment_dates)
    
    deployment_dates = copy.deepcopy(st.session_state['deployment_dates'])
    for region in deployment_dates:
        deployment_dates[region] = {
            'Min': min(2050, deployment_dates[region]['Min'] + 2),
            'Bear': min(2050, deployment_dates[region]['Bear'] + 2),
            'Bull': min(2050, deployment_dates[region]['Bull'] + 2),
            'Max': min(2050, deployment_dates[region]['Max'] + 2),
        }
    st.session_state['deployment_dates'] = deployment_dates


def _apply_base_case_preset(config: SimulationConfig, default_config: SimulationConfig):
    """Apply base case preset: reset to defaults."""
    # Reset to default values
    st.session_state['growth_min'] = default_config.growth_min
    st.session_state['growth_bear'] = default_config.growth_bear
    st.session_state['growth_bull'] = default_config.growth_bull
    st.session_state['growth_max'] = default_config.growth_max
    
    # Reset regional distribution
    st.session_state['region_usa'] = default_config.region_usa
    st.session_state['region_europe'] = default_config.region_europe
    st.session_state['region_china'] = default_config.region_china
    st.session_state['region_apac_excl_china'] = default_config.region_apac_excl_china
    st.session_state['region_canada'] = default_config.region_canada
    
    # Reset deployment dates
    st.session_state['deployment_dates'] = copy.deepcopy(default_config.deployment_dates)


def _apply_aggressive_preset(config: SimulationConfig):
    """Apply aggressive preset: higher growth, earlier deployment."""
    # Higher growth rates
    st.session_state['growth_min'] = 0.30
    st.session_state['growth_bear'] = 0.45
    st.session_state['growth_bull'] = 0.65
    st.session_state['growth_max'] = 0.90
    
    # Earlier deployment (subtract 1 year)
    if 'deployment_dates' not in st.session_state:
        st.session_state['deployment_dates'] = copy.deepcopy(config.deployment_dates)
    
    deployment_dates = copy.deepcopy(st.session_state['deployment_dates'])
    for region in deployment_dates:
        deployment_dates[region] = {
            'Min': max(2022, deployment_dates[region]['Min'] - 1),
            'Bear': max(2022, deployment_dates[region]['Bear'] - 1),
            'Bull': max(2022, deployment_dates[region]['Bull'] - 1),
            'Max': max(2022, deployment_dates[region]['Max'] - 1),
        }
    st.session_state['deployment_dates'] = deployment_dates


def render_sidebar(default_config: SimulationConfig) -> SimulationConfig:
    """
    Render sidebar with configuration controls and return updated config.
    
    Args:
        default_config: Default configuration to use as starting point
        
    Returns:
        SimulationConfig with user-selected values
    """
    st.header("Configuration")
    
    # Use default config as base (will be updated from user inputs)
    config = default_config
    
    # === Simulation Settings ===
    st.subheader("Simulation Settings")
    
    years_to_simulate = st.slider(
        "Years to Simulate",
        min_value=2022,
        max_value=2050,
        value=config.years_to_simulate,
        help="Final year of simulation (starts from 2022)"
    )
    
    num_simulations = st.slider(
        "Number of Simulations",
        min_value=100,
        max_value=10000,
        value=config.num_simulations,
        step=100,
        help="Number of Monte Carlo runs. Higher values = more accurate but slower."
    )
    
    st.markdown("---")
    
    # === Usage & Network ===
    st.subheader("Usage & Network")
    
    days_per_week = st.slider(
        "Days per Week",
        min_value=1.0,
        max_value=7.0,
        value=config.days_per_week,
        step=0.5,
        help="Days per week robotaxis operate"
    )
    
    hours_per_day = st.slider(
        "Hours per Day",
        min_value=1.0,
        max_value=24.0,
        value=config.hours_per_day,
        step=0.5,
        help="Hours per day robotaxis operate"
    )
    
    miles_per_hour = st.slider(
        "Miles per Hour",
        min_value=10.0,
        max_value=60.0,
        value=config.miles_per_hour,
        step=1.0,
        help="Average miles per hour"
    )
    
    occupancy_pct = st.slider(
        "Occupancy Percentage",
        min_value=0.0,
        max_value=1.0,
        value=config.occupancy_pct,
        step=0.01,
        format="%.2f",
        help="Percentage of time vehicle is occupied (0.0 = 0%, 1.0 = 100%)"
    )
    
    network_participation = st.slider(
        "Network Participation",
        min_value=0.0,
        max_value=1.0,
        value=config.network_participation,
        step=0.01,
        format="%.2f",
        help="Percentage of Tesla fleet participating in network (0.0 = 0%, 1.0 = 100%)"
    )
    
    car_lifespan = st.slider(
        "Car Lifespan (years)",
        min_value=5.0,
        max_value=30.0,
        value=config.car_lifespan,
        step=0.5,
        help="Expected car lifespan in years"
    )
    
    # Calculate and display miles per car
    miles_per_car = (
        52 * days_per_week * hours_per_day *
        miles_per_hour * occupancy_pct
    )
    st.metric(
        "Miles per Car (calculated)",
        value=f"{miles_per_car:,.0f}",
        help="Calculated: 52 × days/week × hours/day × miles/hour × occupancy"
    )
    
    st.markdown("---")
    
    # === Economics ===
    st.subheader("Economics")
    
    price_per_mile = st.number_input(
        "Price per Mile (USD)",
        min_value=0.50,
        max_value=5.00,
        value=config.price_per_mile,
        step=0.01,
        format="%.2f",
        help="Price per mile for non-Asia regions"
    )
    
    price_per_mile_asia = st.number_input(
        "Price per Mile - Asia (USD)",
        min_value=0.50,
        max_value=5.00,
        value=config.price_per_mile_asia,
        step=0.01,
        format="%.2f",
        help="Price per mile for Asia regions"
    )
    
    platform_fee = st.slider(
        "Platform Fee",
        min_value=0.0,
        max_value=0.5,
        value=config.platform_fee,
        step=0.01,
        format="%.2f",
        help="Platform fee percentage (Tesla's cut) (0.0 = 0%, 0.5 = 50%)"
    )
    
    costs_per_mile = st.number_input(
        "Costs per Mile (USD)",
        min_value=0.0,
        max_value=1.0,
        value=config.costs_per_mile,
        step=0.01,
        format="%.2f",
        help="Operating costs per mile"
    )
    
    # Calculate car owner revenue preview
    car_owner_revenue_per_car = (
        (price_per_mile * (1 - platform_fee) - costs_per_mile) * miles_per_car
    )
    st.metric(
        "Car Owner Revenue per Car (preview)",
        value=f"${car_owner_revenue_per_car:,.0f}",
        help="Estimated annual revenue per car owner"
    )
    
    st.markdown("---")
    
    # === Preset Configurations ===
    st.subheader("Preset Configurations")
    
    preset_col1, preset_col2, preset_col3 = st.columns(3)
    
    with preset_col1:
        if st.button("📉 Conservative", use_container_width=True, help="Conservative assumptions: lower growth, later deployment"):
            _apply_conservative_preset(config)
            st.rerun()
    
    with preset_col2:
        if st.button("📊 Base Case", use_container_width=True, help="Reset to default/base case assumptions"):
            _apply_base_case_preset(config, default_config)
            st.rerun()
    
    with preset_col3:
        if st.button("📈 Aggressive", use_container_width=True, help="Aggressive assumptions: higher growth, earlier deployment"):
            _apply_aggressive_preset(config)
            st.rerun()
    
    st.markdown("---")
    
    # === Production & Growth ===
    st.subheader("Production & Growth")
    st.caption("Annual production growth rates (simplified: same for all years)")
    
    # Initialize session state for growth rates if not present
    if 'growth_min' not in st.session_state:
        st.session_state['growth_min'] = config.growth_min
    if 'growth_bear' not in st.session_state:
        st.session_state['growth_bear'] = config.growth_bear
    if 'growth_bull' not in st.session_state:
        st.session_state['growth_bull'] = config.growth_bull
    if 'growth_max' not in st.session_state:
        st.session_state['growth_max'] = config.growth_max
    
    growth_min = st.slider(
        "Growth Min",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state['growth_min'],
        step=0.01,
        format="%.2f",
        help="Minimum annual production growth rate"
    )
    st.session_state['growth_min'] = growth_min
    
    growth_bear = st.slider(
        "Growth Bear (25th percentile)",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state['growth_bear'],
        step=0.01,
        format="%.2f",
        help="Bear case (25th percentile) growth rate"
    )
    st.session_state['growth_bear'] = growth_bear
    
    growth_bull = st.slider(
        "Growth Bull (75th percentile)",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state['growth_bull'],
        step=0.01,
        format="%.2f",
        help="Bull case (75th percentile) growth rate"
    )
    st.session_state['growth_bull'] = growth_bull
    
    growth_max = st.slider(
        "Growth Max",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state['growth_max'],
        step=0.01,
        format="%.2f",
        help="Maximum annual production growth rate"
    )
    st.session_state['growth_max'] = growth_max
    
    # Validate growth rates
    if not (growth_min <= growth_bear <= growth_bull <= growth_max):
        st.warning("⚠️ Growth rates must satisfy: Min ≤ Bear ≤ Bull ≤ Max")
    
    st.markdown("---")
    
    # === Regional Distribution ===
    st.subheader("Regional Distribution")
    st.caption("Production share by region (must sum to 100%)")
    
    # Initialize session state for regional distribution if not present
    if 'region_usa' not in st.session_state:
        st.session_state['region_usa'] = config.region_usa
    if 'region_europe' not in st.session_state:
        st.session_state['region_europe'] = config.region_europe
    if 'region_china' not in st.session_state:
        st.session_state['region_china'] = config.region_china
    if 'region_apac_excl_china' not in st.session_state:
        st.session_state['region_apac_excl_china'] = config.region_apac_excl_china
    if 'region_canada' not in st.session_state:
        st.session_state['region_canada'] = config.region_canada
    
    region_usa = st.slider(
        "USA",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state['region_usa'],
        step=0.01,
        format="%.2f",
        help="USA production share"
    )
    st.session_state['region_usa'] = region_usa
    
    region_europe = st.slider(
        "Europe",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state['region_europe'],
        step=0.01,
        format="%.2f",
        help="Europe production share"
    )
    st.session_state['region_europe'] = region_europe
    
    region_china = st.slider(
        "China",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state['region_china'],
        step=0.01,
        format="%.2f",
        help="China production share"
    )
    st.session_state['region_china'] = region_china
    
    region_apac_excl_china = st.slider(
        "APAC excl China",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state['region_apac_excl_china'],
        step=0.01,
        format="%.2f",
        help="APAC excluding China production share"
    )
    st.session_state['region_apac_excl_china'] = region_apac_excl_china
    
    region_canada = st.slider(
        "Canada",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state['region_canada'],
        step=0.01,
        format="%.2f",
        help="Canada production share"
    )
    st.session_state['region_canada'] = region_canada
    
    # Calculate and display running total
    region_sum = region_usa + region_europe + region_china + region_apac_excl_china + region_canada
    
    # Color code the total
    if abs(region_sum - 1.0) < 0.01:
        total_color = "green"
        total_icon = "✅"
    else:
        total_color = "red"
        total_icon = "⚠️"
    
    st.markdown(f"**Total: {total_icon} {region_sum:.1%}**")
    
    if abs(region_sum - 1.0) > 0.01:
        st.warning(f"⚠️ Regional distribution sums to {region_sum:.1%}, should equal 100%")
    
    # Normalize button
    if st.button("🔧 Normalize to 100%", use_container_width=True):
        if region_sum > 0:
            st.session_state['region_usa'] = region_usa / region_sum
            st.session_state['region_europe'] = region_europe / region_sum
            st.session_state['region_china'] = region_china / region_sum
            st.session_state['region_apac_excl_china'] = region_apac_excl_china / region_sum
            st.session_state['region_canada'] = region_canada / region_sum
            st.rerun()
    
    # Normalize if sum is not close to 1.0
    if abs(region_sum - 1.0) < 0.01:
        # Already normalized
        region_usa_final = region_usa
        region_europe_final = region_europe
        region_china_final = region_china
        region_apac_excl_china_final = region_apac_excl_china
        region_canada_final = region_canada
    elif region_sum > 0:
        # Normalize to sum to 1.0
        region_usa_final = region_usa / region_sum
        region_europe_final = region_europe / region_sum
        region_china_final = region_china / region_sum
        region_apac_excl_china_final = region_apac_excl_china / region_sum
        region_canada_final = region_canada / region_sum
    else:
        # Fallback: use session state values (shouldn't happen)
        region_usa_final = st.session_state['region_usa']
        region_europe_final = st.session_state['region_europe']
        region_china_final = st.session_state['region_china']
        region_apac_excl_china_final = st.session_state['region_apac_excl_china']
        region_canada_final = st.session_state['region_canada']
    
    st.markdown("---")
    
    # === Deployment Timing ===
    st.subheader("Deployment Timing")
    st.caption("Robotaxi deployment year by region (Min ≤ Bull ≤ Bear ≤ Max). Earlier = more optimistic.")
    
    # Initialize deployment dates in session state if not present
    if 'deployment_dates' not in st.session_state:
        st.session_state['deployment_dates'] = copy.deepcopy(config.deployment_dates)
    
    deployment_dates = st.session_state['deployment_dates']
    
    # Regions to display
    regions = ['USA', 'Europe', 'China', 'APAC excl China', 'Canada']
    
    for region in regions:
        if region not in deployment_dates:
            deployment_dates[region] = {'Min': 2024, 'Bull': 2025, 'Bear': 2026, 'Max': 2028}
        
        with st.expander(f"📍 {region} Deployment"):
            col1, col2 = st.columns(2)
            
            with col1:
                min_year = st.number_input(
                    f"{region} Min Year",
                    min_value=2022,
                    max_value=2050,
                    value=deployment_dates[region]['Min'],
                    step=1,
                    key=f"{region}_min"
                )
                
                bear_year = st.number_input(
                    f"{region} Bear Year",
                    min_value=2022,
                    max_value=2050,
                    value=deployment_dates[region]['Bear'],
                    step=1,
                    key=f"{region}_bear"
                )
            
            with col2:
                bull_year = st.number_input(
                    f"{region} Bull Year",
                    min_value=2022,
                    max_value=2050,
                    value=deployment_dates[region]['Bull'],
                    step=1,
                    key=f"{region}_bull"
                )
                
                max_year = st.number_input(
                    f"{region} Max Year",
                    min_value=2022,
                    max_value=2050,
                    value=deployment_dates[region]['Max'],
                    step=1,
                    key=f"{region}_max"
                )
            
            # Validate deployment dates (Bull should be earlier than Bear - earlier = more optimistic)
            if not (min_year <= bull_year <= bear_year <= max_year):
                st.warning(f"⚠️ {region}: Min ({min_year}) ≤ Bull ({bull_year}) ≤ Bear ({bear_year}) ≤ Max ({max_year}). Earlier years = more optimistic.")
            
            # Update session state
            deployment_dates[region] = {
                'Min': min_year,
                'Bear': bear_year,
                'Bull': bull_year,
                'Max': max_year
            }
    
    st.session_state['deployment_dates'] = deployment_dates
    
    st.markdown("---")
    
    # === Reset to Defaults Button ===
    if st.button("🔄 Reset to Defaults", use_container_width=True):
        # Clear cached results to force recomputation with defaults
        if 'last_config_hash' in st.session_state:
            del st.session_state['last_config_hash']
        if 'results' in st.session_state:
            del st.session_state['results']
        # Reset regional distribution in session state
        if 'region_usa' in st.session_state:
            del st.session_state['region_usa']
        if 'region_europe' in st.session_state:
            del st.session_state['region_europe']
        if 'region_china' in st.session_state:
            del st.session_state['region_china']
        if 'region_apac_excl_china' in st.session_state:
            del st.session_state['region_apac_excl_china']
        if 'region_canada' in st.session_state:
            del st.session_state['region_canada']
        if 'deployment_dates' in st.session_state:
            del st.session_state['deployment_dates']
        # Reset growth rates
        if 'growth_min' in st.session_state:
            del st.session_state['growth_min']
        if 'growth_bear' in st.session_state:
            del st.session_state['growth_bear']
        if 'growth_bull' in st.session_state:
            del st.session_state['growth_bull']
        if 'growth_max' in st.session_state:
            del st.session_state['growth_max']
        st.rerun()
    
    # Create updated config object
    updated_config = SimulationConfig(
        years_to_simulate=years_to_simulate,
        num_simulations=num_simulations,
        days_per_week=days_per_week,
        hours_per_day=hours_per_day,
        miles_per_hour=miles_per_hour,
        occupancy_pct=occupancy_pct,
        network_participation=network_participation,
        car_lifespan=car_lifespan,
        price_per_mile=price_per_mile,
        price_per_mile_asia=price_per_mile_asia,
        platform_fee=platform_fee,
        costs_per_mile=costs_per_mile,
        # Production growth parameters
        growth_min=growth_min,
        growth_bear=growth_bear,
        growth_bull=growth_bull,
        growth_max=growth_max,
        # Regional distribution parameters
        region_usa=region_usa_final,
        region_europe=region_europe_final,
        region_china=region_china_final,
        region_apac_excl_china=region_apac_excl_china_final,
        region_canada=region_canada_final,
        # Deployment dates
        deployment_dates=deployment_dates,
        enable_vmt_forecast=config.enable_vmt_forecast,
        data_dir=config.data_dir,
    )
    
    # Validate config
    validation_errors = updated_config.validate()
    if validation_errors:
        st.error("⚠️ Configuration Validation Errors:")
        for error in validation_errors:
            st.error(f"  • {error}")
    
    return updated_config

