"""
Tesla Robotaxi Simulation - Streamlit Application

Milestone 3: Core Configuration Controls
Add sidebar controls for the most impactful parameters and wire them up to update simulation results.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from model.config import SimulationConfig
from model.core import run_simulation
from model.plots import plot_global_series
from app.sidebar import render_sidebar

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
        
        # Plots
        st.subheader("Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Global Robotaxi Miles")
            try:
                fig1 = plot_global_series(
                    results.robotaxi_miles,
                    "Global Robotaxi Miles",
                    results.years,
                    12  # trillions
                )
                st.pyplot(fig1, use_container_width=True)
                plt.close(fig1)  # Close figure to free memory
            except Exception as e:
                st.error(f"Error plotting robotaxi miles: {e}")
        
        with col2:
            st.markdown("#### Global Tesla Revenue")
            try:
                fig2 = plot_global_series(
                    results.revenue_tesla_global,
                    "Global Revenue Tesla",
                    results.years,
                    9  # billions
                )
                st.pyplot(fig2, use_container_width=True)
                plt.close(fig2)  # Close figure to free memory
            except Exception as e:
                st.error(f"Error plotting revenue: {e}")
        
        # Simulation info
        with st.expander("Simulation Details"):
            st.write(f"**Configuration Hash**: `{current_config_hash}`")
            st.write(f"**Number of Simulations**: {user_config.num_simulations}")
            st.write(f"**Years Simulated**: {results.years[0]} - {results.years[-1]}")
            st.write(f"**Total Years**: {len(results.years)}")
            st.write(f"**Miles per Car**: {user_config.miles_per_car:,.0f}")
            st.write(f"**Network Participation**: {user_config.network_participation:.1%}")
            st.write(f"**Platform Fee**: {user_config.platform_fee:.1%}")
            
            st.markdown("---")
            st.markdown("### Validation Data")
            st.caption("Use this data to verify that cumulative cars and robotaxi miles increase over time")
            
            # Select key years for validation (2025, 2030, 2035, or closest available)
            validation_years = []
            for year in [2025, 2030, 2035]:
                if year in results.years:
                    validation_years.append(year)
            # If none of those exist, use first, middle, and last year
            if not validation_years:
                validation_years = [
                    results.years[0],
                    results.years[len(results.years)//2],
                    results.years[-1]
                ]
            
            # Cumulative Cars by Region
            st.markdown("#### Cumulative Cars by Region (Average)")
            cum_cars_data = []
            for region in sorted(results.cum_cars_by_area.keys()):
                row = {"Region": region}
                for year in validation_years:
                    if year in results.cum_cars_by_area[region].columns:
                        avg_cars = results.cum_cars_by_area[region][year].mean()
                        row[f"{year}"] = f"{avg_cars:,.0f}"
                    else:
                        row[f"{year}"] = "N/A"
                cum_cars_data.append(row)
            
            cum_cars_df = pd.DataFrame(cum_cars_data)
            st.dataframe(cum_cars_df, use_container_width=True, hide_index=True)
            
            # Global Cumulative Cars (sum across all regions)
            st.markdown("#### Global Cumulative Cars (Average)")
            global_cum_cars_data = []
            for year in validation_years:
                total_cars = 0
                for region in results.cum_cars_by_area.keys():
                    if year in results.cum_cars_by_area[region].columns:
                        total_cars += results.cum_cars_by_area[region][year].mean()
                global_cum_cars_data.append({"Year": year, "Cumulative Cars": f"{total_cars:,.0f}"})
            
            global_cum_cars_df = pd.DataFrame(global_cum_cars_data)
            st.dataframe(global_cum_cars_df, use_container_width=True, hide_index=True)
            
            # Robotaxi Miles (Global)
            st.markdown("#### Global Robotaxi Miles (Average)")
            robotaxi_miles_data = []
            for year in validation_years:
                if year in results.robotaxi_miles.columns:
                    avg_miles = results.robotaxi_miles[year].mean()
                    robotaxi_miles_data.append({
                        "Year": year,
                        "Robotaxi Miles (trillions)": f"{avg_miles / 1e12:.2f}"
                    })
            
            robotaxi_miles_df = pd.DataFrame(robotaxi_miles_data)
            st.dataframe(robotaxi_miles_df, use_container_width=True, hide_index=True)
            
            # Robotaxi Miles by Region
            st.markdown("#### Robotaxi Miles by Region (Average)")
            robotaxi_miles_region_data = []
            for region in sorted(results.robotaxi_miles_per_region.keys()):
                row = {"Region": region}
                for year in validation_years:
                    if year in results.robotaxi_miles_per_region[region].columns:
                        avg_miles = results.robotaxi_miles_per_region[region][year].mean()
                        row[f"{year} (billions)"] = f"{avg_miles / 1e9:.2f}"
                    else:
                        row[f"{year} (billions)"] = "N/A"
                robotaxi_miles_region_data.append(row)
            
            robotaxi_miles_region_df = pd.DataFrame(robotaxi_miles_region_data)
            st.dataframe(robotaxi_miles_region_df, use_container_width=True, hide_index=True)
    
    else:
        st.info("👆 Click 'Run Simulation' to start. Adjust parameters in the sidebar and click the button to run with your settings.")

except FileNotFoundError as e:
    st.error(f"Data files not found: {e}")
    st.info("Please ensure the Data/ directory exists with required CSV files.")
except Exception as e:
    st.error(f"Error loading configuration: {e}")
    st.exception(e)

