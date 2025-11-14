"""
Tesla Robotaxi Simulation - Streamlit Application

Milestone 5: Complete Result Tabs
Add all remaining analysis tabs to match notebook functionality.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from model.config import SimulationConfig
from model.core import run_simulation
from model.plots import plot_global_series
from app.sidebar import render_sidebar
from app.tabs import (
    render_production_fleet_tab,
    render_robotaxi_miles_tab,
    render_tesla_revenue_tab,
    render_car_owner_economics_tab,
    render_co2_pollution_tab,
    render_displacement_tab,
    render_time_gdp_tab,
    render_diagnostics_tab
)

# Page configuration
st.set_page_config(
    page_title="Tesla Robotaxi Simulation",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header
st.title("🚗 Tesla Robotaxi Simulation")
st.markdown("""
This application simulates the economic and environmental impact of Tesla's Robotaxi network
using Monte Carlo methods. Adjust parameters in the sidebar and run simulations to explore
different scenarios.
""")

# Load default config (cached)
@st.cache_data
def load_default_config():
    """Load default configuration (cached)."""
    return SimulationConfig.from_defaults()

default_config = load_default_config()

# Sidebar - render configuration controls
with st.sidebar:
    user_config = render_sidebar(default_config)

# Caching function for simulation results
@st.cache_data
def cached_run_simulation(config_hash: str, config_dict: dict):
    """
    Cache simulation results keyed by configuration hash.
    
    Args:
        config_hash: Hash of the configuration
        config_dict: Dictionary representation of configuration
        
    Returns:
        SimulationResults object
    """
    # Reconstruct config from dict
    config = SimulationConfig(**config_dict)
    return run_simulation(config)

# Main content area
st.header("Simulation Results")

# Session state management
if 'last_config_hash' not in st.session_state:
    st.session_state['last_config_hash'] = None
if 'run_simulation' not in st.session_state:
    st.session_state['run_simulation'] = False

# Get current config hash
current_config_hash = user_config.to_hash()
current_config_dict = user_config.to_dict()

# Check if config has changed (but don't act on it yet - only when button is clicked)
config_changed = (
    st.session_state['last_config_hash'] is not None and 
    st.session_state['last_config_hash'] != current_config_hash
)

# Show config change indicator
if config_changed:
    st.warning("⚠️ Configuration has changed. Click 'Run Simulation' to update results with new parameters.")

# Run Simulation button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🚀 Run Simulation", type="primary", use_container_width=True):
        st.session_state['run_simulation'] = True

# Run simulation only if button was clicked
if st.session_state.get('run_simulation', False):
    # Always run when button is clicked (caching will handle if config is same)
    with st.spinner("Running simulation... This may take a minute."):
        try:
            # Run simulation (cached if config hasn't changed)
            results = cached_run_simulation(current_config_hash, current_config_dict)
            
            # Store results in session state
            st.session_state['results'] = results
            st.session_state['last_config_hash'] = current_config_hash
            st.session_state['config'] = user_config
            
        except Exception as e:
            st.error(f"Simulation failed: {str(e)}")
            st.exception(e)
            st.session_state['results'] = None
            st.session_state['last_config_hash'] = None
    
    # Reset the run flag after processing
    st.session_state['run_simulation'] = False

try:
    # Display results if available (only show if simulation has been run)
    if 'results' in st.session_state and st.session_state['results'] is not None:
        results = st.session_state['results']
        # Use the config that was used for this simulation
        user_config = st.session_state.get('config', user_config)
        
        # Year selector for Key Metrics
        default_year = 2030 if 2030 in results.years else results.years[-1]
        target_year = st.select_slider(
            "Select Year",
            options=results.years,
            value=default_year,
            help="Choose a year to view metrics for that specific year"
        )
        
        # Summary KPIs with improved visual hierarchy
        st.subheader(f"📊 Key Metrics ({target_year})")
        
        if target_year in results.robotaxi_miles.columns:
            # Calculate primary metrics with quantiles
            revenue_bear = results.revenue_tesla_global[target_year].quantile(0.25)
            revenue_avg = results.revenue_tesla_global[target_year].mean()
            revenue_bull = results.revenue_tesla_global[target_year].quantile(0.75)
            
            # Cumulative revenue (sum from start year to target year)
            cumulative_revenue = results.revenue_tesla_global[results.years].sum(axis=1)
            cum_revenue_bear = cumulative_revenue.quantile(0.25)
            cum_revenue_avg = cumulative_revenue.mean()
            cum_revenue_bull = cumulative_revenue.quantile(0.75)
            
            # Global fleet size (cumulative cars) - calculate only for target year
            global_cum_cars_target = pd.Series(index=results.simulation_list, dtype=float)
            for sim in results.simulation_list:
                total = 0
                for region in results.cum_cars_by_area.keys():
                    if target_year in results.cum_cars_by_area[region].columns:
                        total += results.cum_cars_by_area[region].loc[sim, target_year]
                global_cum_cars_target.loc[sim] = total
            
            fleet_bear = global_cum_cars_target.quantile(0.25)
            fleet_avg = global_cum_cars_target.mean()
            fleet_bull = global_cum_cars_target.quantile(0.75)
            
            # Global CO2 saved (sum across all regions) - calculate only for target year
            global_co2_target = pd.Series(index=results.simulation_list, dtype=float)
            for sim in results.simulation_list:
                total = 0
                for region in results.tons_co2_saved.keys():
                    if target_year in results.tons_co2_saved[region].columns:
                        total += results.tons_co2_saved[region].loc[sim, target_year]
                global_co2_target.loc[sim] = total
            
            co2_bear = global_co2_target.quantile(0.25) if len(global_co2_target) > 0 else 0.0
            co2_avg = global_co2_target.mean() if len(global_co2_target) > 0 else 0.0
            co2_bull = global_co2_target.quantile(0.75) if len(global_co2_target) > 0 else 0.0
            
            # Primary metrics in 2x2 grid
            col1, col2 = st.columns(2)
            
            with col1:
                # Tesla Revenue (Annual)
                st.markdown("#### 💰 Tesla Revenue (Annual)")
                st.metric(
                    label="Average",
                    value=f"${revenue_avg / 1e9:.2f}B",
                    delta=f"Range: ${revenue_bear / 1e9:.1f}B - ${revenue_bull / 1e9:.1f}B",
                    delta_color="off",
                    help=f"25th percentile: ${revenue_bear / 1e9:.2f}B | 75th percentile: ${revenue_bull / 1e9:.2f}B"
                )
                
                # Global Fleet Size
                st.markdown("#### 🚗 Global Fleet Size")
                st.metric(
                    label="Cumulative Cars",
                    value=f"{fleet_avg / 1e6:.2f}M",
                    delta=f"Range: {fleet_bear / 1e6:.1f}M - {fleet_bull / 1e6:.1f}M",
                    delta_color="off",
                    help=f"25th percentile: {fleet_bear / 1e6:.2f}M | 75th percentile: {fleet_bull / 1e6:.2f}M"
                )
            
            with col2:
                # Cumulative Revenue
                st.markdown("#### 📈 Cumulative Revenue")
                st.metric(
                    label=f"Total ({results.years[0]}-{target_year})",
                    value=f"${cum_revenue_avg / 1e9:.2f}B",
                    delta=f"Range: ${cum_revenue_bear / 1e9:.1f}B - ${cum_revenue_bull / 1e9:.1f}B",
                    delta_color="off",
                    help=f"25th percentile: ${cum_revenue_bear / 1e9:.2f}B | 75th percentile: ${cum_revenue_bull / 1e9:.2f}B"
                )
                
                # Global CO2 Saved
                st.markdown("#### 🌍 Global CO₂ Saved")
                st.metric(
                    label="Tons Saved",
                    value=f"{co2_avg / 1e6:.2f}M",
                    delta=f"Range: {co2_bear / 1e6:.1f}M - {co2_bull / 1e6:.1f}M",
                    delta_color="off",
                    help=f"25th percentile: {co2_bear / 1e6:.2f}M | 75th percentile: {co2_bull / 1e6:.2f}M"
                )
            
            # Secondary metrics in expandable section
            with st.expander("📋 Additional Metrics", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Robotaxi Miles
                    robotaxi_miles_bear = results.robotaxi_miles[target_year].quantile(0.25)
                    robotaxi_miles_avg = results.robotaxi_miles[target_year].mean()
                    robotaxi_miles_bull = results.robotaxi_miles[target_year].quantile(0.75)
                    
                    st.markdown("**🛣️ Global Robotaxi Miles**")
                    st.metric(
                        label="Average",
                        value=f"{robotaxi_miles_avg / 1e12:.2f}T",
                        delta=f"Range: {robotaxi_miles_bear / 1e12:.2f}T - {robotaxi_miles_bull / 1e12:.2f}T",
                        delta_color="off"
                    )
                
                with col2:
                    # Cars Displaced
                    if target_year in results.cars_displaced.columns:
                        displaced_bear = results.cars_displaced[target_year].quantile(0.25)
                        displaced_avg = results.cars_displaced[target_year].mean()
                        displaced_bull = results.cars_displaced[target_year].quantile(0.75)
                        
                        st.markdown("**🔄 Cars Displaced**")
                        st.metric(
                            label="Average",
                            value=f"{displaced_avg / 1e6:.2f}M",
                            delta=f"Range: {displaced_bear / 1e6:.2f}M - {displaced_bull / 1e6:.2f}M",
                            delta_color="off"
                        )
                    else:
                        st.markdown("**🔄 Cars Displaced**")
                        st.info("Data not available")
                
                with col3:
                    # Car Owner Revenue (Non-Asia)
                    if len(results.car_owner_revenue) > 0:
                        owner_rev_mean = results.car_owner_revenue.mean()
                        owner_rev_p25 = results.car_owner_revenue.quantile(0.25)
                        owner_rev_p75 = results.car_owner_revenue.quantile(0.75)
                        
                        st.markdown("**👤 Car Owner Revenue**")
                        st.metric(
                            label="Average (Non-Asia)",
                            value=f"${owner_rev_mean:,.0f}",
                            delta=f"Range: ${owner_rev_p25:,.0f} - ${owner_rev_p75:,.0f}",
                            delta_color="off"
                        )
                    else:
                        st.markdown("**👤 Car Owner Revenue**")
                        st.info("Data not available")
        else:
            st.warning(f"Target year {target_year} not available in results.")
        
        # Create tabs for detailed results
        st.markdown("---")
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "Production & Fleet",
            "Robotaxi Miles",
            "Tesla Revenue",
            "Car Owner Economics",
            "CO₂ & Pollution",
            "Displacement & S-Curves",
            "Time Saved & GDP",
            "Diagnostics"
        ])
        
        with tab1:
            render_production_fleet_tab(results)
        
        with tab2:
            render_robotaxi_miles_tab(results)
        
        with tab3:
            render_tesla_revenue_tab(results)
        
        with tab4:
            render_car_owner_economics_tab(results)
        
        with tab5:
            render_co2_pollution_tab(results)
        
        with tab6:
            render_displacement_tab(results)
        
        with tab7:
            render_time_gdp_tab(results)
        
        with tab8:
            render_diagnostics_tab(results, current_config_hash, user_config)
    
    else:
        st.info("👆 Click 'Run Simulation' to start. Adjust parameters in the sidebar and click the button to run with your settings.")

except FileNotFoundError as e:
    st.error(f"Data files not found: {e}")
    st.info("Please ensure the Data/ directory exists with required CSV files.")
except Exception as e:
    st.error(f"Error loading configuration: {e}")
    st.exception(e)

