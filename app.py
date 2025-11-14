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
        
        # Get 2030 values (or last available year)
        target_year = 2030 if 2030 in results.years else results.years[-1]
        
        # Summary KPIs with Bear/Average/Bull scenarios
        st.subheader(f"Key Metrics ({target_year})")
        
        if target_year in results.robotaxi_miles.columns:
            # Calculate metrics with quantiles
            robotaxi_miles_bear = results.robotaxi_miles[target_year].quantile(0.25)
            robotaxi_miles_avg = results.robotaxi_miles[target_year].mean()
            robotaxi_miles_bull = results.robotaxi_miles[target_year].quantile(0.75)
            
            revenue_bear = results.revenue_tesla_global[target_year].quantile(0.25)
            revenue_avg = results.revenue_tesla_global[target_year].mean()
            revenue_bull = results.revenue_tesla_global[target_year].quantile(0.75)
            
            # CO2 saved (USA)
            co2_bear = 0
            co2_avg = 0
            co2_bull = 0
            if 'USA' in results.tons_co2_saved and target_year in results.tons_co2_saved['USA'].columns:
                co2_bear = results.tons_co2_saved['USA'][target_year].quantile(0.25)
                co2_avg = results.tons_co2_saved['USA'][target_year].mean()
                co2_bull = results.tons_co2_saved['USA'][target_year].quantile(0.75)
            
            # Display KPIs in columns (3 metrics × 3 scenarios = 9 columns, use 3 rows)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### Global Robotaxi Miles")
                st.metric(
                    label="Bear (25th percentile)",
                    value=f"{robotaxi_miles_bear / 1e12:.2f}T",
                    help="25th percentile of simulations"
                )
                st.metric(
                    label="Average",
                    value=f"{robotaxi_miles_avg / 1e12:.2f}T",
                    help="Mean of all simulations"
                )
                st.metric(
                    label="Bull (75th percentile)",
                    value=f"{robotaxi_miles_bull / 1e12:.2f}T",
                    delta=(robotaxi_miles_bull - robotaxi_miles_avg) / 1e12,
                    delta_color="normal",
                    help="75th percentile of simulations"
                )
            
            with col2:
                st.markdown("#### Tesla Revenue")
                st.metric(
                    label="Bear (25th percentile)",
                    value=f"${revenue_bear / 1e9:.2f}B",
                    help="25th percentile of simulations"
                )
                st.metric(
                    label="Average",
                    value=f"${revenue_avg / 1e9:.2f}B",
                    help="Mean of all simulations"
                )
                st.metric(
                    label="Bull (75th percentile)",
                    value=f"${revenue_bull / 1e9:.2f}B",
                    delta=(revenue_bull - revenue_avg) / 1e9,
                    delta_color="normal",
                    help="75th percentile of simulations"
                )
            
            with col3:
                st.markdown("#### CO₂ Saved (USA)")
                st.metric(
                    label="Bear (25th percentile)",
                    value=f"{co2_bear / 1e6:.2f}M tons",
                    help="25th percentile of simulations"
                )
                st.metric(
                    label="Average",
                    value=f"{co2_avg / 1e6:.2f}M tons",
                    help="Mean of all simulations"
                )
                st.metric(
                    label="Bull (75th percentile)",
                    value=f"{co2_bull / 1e6:.2f}M tons",
                    delta=(co2_bull - co2_avg) / 1e6,
                    delta_color="normal",
                    help="75th percentile of simulations"
                )
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

