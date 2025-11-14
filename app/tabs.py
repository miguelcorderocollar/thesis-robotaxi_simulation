"""
Tab implementations for Tesla Robotaxi Simulation app.

Each function renders a specific results tab with visualizations and KPIs.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict
from model.core import SimulationResults
from model.plots import (
    plot_area_series,
    plot_global_series,
    plot_3_areas,
    plot_percentage_graph
)


def render_production_fleet_tab(results: SimulationResults):
    """Tab 1: Production & Fleet"""
    st.header("Production & Fleet")
    
    # Summary KPIs
    st.subheader("Key Metrics")
    target_years = [2025, 2030, 2035]
    available_years = [y for y in target_years if y in results.years]
    if not available_years:
        available_years = [results.years[0], results.years[len(results.years)//2], results.years[-1]]
    
    # Create summary table
    summary_data = []
    for region in sorted(results.cum_cars_by_area.keys()):
        row = {"Region": region}
        for year in available_years:
            if year in results.cum_cars_by_area[region].columns:
                avg_cars = results.cum_cars_by_area[region][year].mean()
                row[f"{year} Cumulative"] = f"{avg_cars:,.0f}"
                
                # Production
                if year in results.prod_cars_by_area[region].columns:
                    avg_prod = results.prod_cars_by_area[region][year].mean()
                    row[f"{year} Production"] = f"{avg_prod:,.0f}"
                else:
                    row[f"{year} Production"] = "N/A"
            else:
                row[f"{year} Cumulative"] = "N/A"
                row[f"{year} Production"] = "N/A"
        summary_data.append(row)
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    # Plots
    st.subheader("Cumulative Cars by Region")
    try:
        fig1 = plot_area_series(
            results.cum_cars_by_area,
            "Cumulative Cars",
            results.years,
            magnitude=6  # millions
        )
        st.pyplot(fig1, use_container_width=True)
        plt.close(fig1)
    except Exception as e:
        st.error(f"Error plotting cumulative cars: {e}")
    
    st.subheader("Production Cars by Region")
    try:
        fig2 = plot_area_series(
            results.prod_cars_by_area,
            "Production Cars",
            results.years,
            magnitude=6  # millions
        )
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)
    except Exception as e:
        st.error(f"Error plotting production cars: {e}")
    
    st.subheader("Discontinued Cars by Region")
    try:
        fig3 = plot_area_series(
            results.prod_disc_by_area,
            "Discontinued Cars",
            results.years,
            magnitude=6  # millions
        )
        st.pyplot(fig3, use_container_width=True)
        plt.close(fig3)
    except Exception as e:
        st.error(f"Error plotting discontinued cars: {e}")
    
    # Global totals
    st.subheader("Global Totals")
    col1, col2 = st.columns(2)
    
    with col1:
        # Calculate global cumulative cars
        global_cum_cars = pd.DataFrame(index=results.simulation_list, columns=results.years)
        for year in results.years:
            for sim in results.simulation_list:
                total = 0
                for region in results.cum_cars_by_area.keys():
                    if year in results.cum_cars_by_area[region].columns:
                        total += results.cum_cars_by_area[region].loc[sim, year]
                global_cum_cars.loc[sim, year] = total
        
        try:
            fig4 = plot_global_series(
                global_cum_cars,
                "Global Cumulative Cars",
                results.years,
                magnitude=6  # millions
            )
            st.pyplot(fig4, use_container_width=True)
            plt.close(fig4)
        except Exception as e:
            st.error(f"Error plotting global cumulative cars: {e}")
    
    with col2:
        # Calculate global production
        global_prod_cars = pd.DataFrame(index=results.simulation_list, columns=results.years)
        for year in results.years:
            for sim in results.simulation_list:
                total = 0
                for region in results.prod_cars_by_area.keys():
                    if year in results.prod_cars_by_area[region].columns:
                        total += results.prod_cars_by_area[region].loc[sim, year]
                global_prod_cars.loc[sim, year] = total
        
        try:
            fig5 = plot_global_series(
                global_prod_cars,
                "Global Production Cars",
                results.years,
                magnitude=6  # millions
            )
            st.pyplot(fig5, use_container_width=True)
            plt.close(fig5)
        except Exception as e:
            st.error(f"Error plotting global production cars: {e}")


def render_robotaxi_miles_tab(results: SimulationResults):
    """Tab 2: Robotaxi Miles"""
    st.header("Robotaxi Miles")
    
    # KPI cards
    st.subheader("Key Metrics")
    target_years = [2030, 2035]
    available_years = [y for y in target_years if y in results.years]
    if not available_years:
        available_years = [results.years[-1]]
    
    cols = st.columns(len(available_years))
    for idx, year in enumerate(available_years):
        with cols[idx]:
            if year in results.robotaxi_miles.columns:
                miles_bear = results.robotaxi_miles[year].quantile(0.25)
                miles_avg = results.robotaxi_miles[year].mean()
                miles_bull = results.robotaxi_miles[year].quantile(0.75)
                
                st.metric(
                    label=f"{year} Global Robotaxi Miles (Average)",
                    value=f"{miles_avg / 1e12:.2f}T"
                )
                st.metric(
                    label=f"{year} Bear (25th percentile)",
                    value=f"{miles_bear / 1e12:.2f}T"
                )
                st.metric(
                    label=f"{year} Bull (75th percentile)",
                    value=f"{miles_bull / 1e12:.2f}T"
                )
    
    # Regional plots
    st.subheader("Robotaxi Miles by Region")
    try:
        fig1 = plot_area_series(
            results.robotaxi_miles_per_region,
            "Robotaxi Miles",
            results.years,
            magnitude=9  # billions
        )
        st.pyplot(fig1, use_container_width=True)
        plt.close(fig1)
    except Exception as e:
        st.error(f"Error plotting regional robotaxi miles: {e}")
    
    # Global plot
    st.subheader("Global Robotaxi Miles")
    try:
        fig2 = plot_global_series(
            results.robotaxi_miles,
            "Global Robotaxi Miles",
            results.years,
            magnitude=12  # trillions
        )
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)
    except Exception as e:
        st.error(f"Error plotting global robotaxi miles: {e}")


def render_tesla_revenue_tab(results: SimulationResults):
    """Tab 3: Tesla Revenue"""
    st.header("Tesla Revenue")
    
    # KPI cards
    st.subheader("Key Metrics")
    target_year = 2030 if 2030 in results.years else results.years[-1]
    
    if target_year in results.revenue_tesla_global.columns:
        revenue_bear = results.revenue_tesla_global[target_year].quantile(0.25)
        revenue_avg = results.revenue_tesla_global[target_year].mean()
        revenue_bull = results.revenue_tesla_global[target_year].quantile(0.75)
        
        # Cumulative revenue to target year
        cumulative_revenue = results.revenue_tesla_global[results.years].sum(axis=1)
        cum_revenue_bear = cumulative_revenue.quantile(0.25)
        cum_revenue_avg = cumulative_revenue.mean()
        cum_revenue_bull = cumulative_revenue.quantile(0.75)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### {target_year} Revenue")
            st.metric("Bear (25th percentile)", f"${revenue_bear / 1e9:.2f}B")
            st.metric("Average", f"${revenue_avg / 1e9:.2f}B")
            st.metric("Bull (75th percentile)", f"${revenue_bull / 1e9:.2f}B")
        
        with col2:
            st.markdown(f"#### Cumulative Revenue ({results.years[0]}-{target_year})")
            st.metric("Bear (25th percentile)", f"${cum_revenue_bear / 1e9:.2f}B")
            st.metric("Average", f"${cum_revenue_avg / 1e9:.2f}B")
            st.metric("Bull (75th percentile)", f"${cum_revenue_bull / 1e9:.2f}B")
    
    # Regional plots
    st.subheader("Tesla Revenue by Region")
    try:
        fig1 = plot_area_series(
            results.revenue_tesla_per_region,
            "Tesla Revenue",
            results.years,
            magnitude=9  # billions
        )
        st.pyplot(fig1, use_container_width=True)
        plt.close(fig1)
    except Exception as e:
        st.error(f"Error plotting regional revenue: {e}")
    
    # Global plot
    st.subheader("Global Tesla Revenue")
    try:
        fig2 = plot_global_series(
            results.revenue_tesla_global,
            "Global Revenue Tesla",
            results.years,
            magnitude=9  # billions
        )
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)
    except Exception as e:
        st.error(f"Error plotting global revenue: {e}")


def render_car_owner_economics_tab(results: SimulationResults):
    """Tab 4: Car Owner Economics"""
    st.header("Car Owner Economics")
    
    # KPI cards
    st.subheader("Key Metrics")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Non-Asia Car Owner Revenue")
        if len(results.car_owner_revenue) > 0:
            mean_rev = results.car_owner_revenue.mean()
            p25_rev = results.car_owner_revenue.quantile(0.25)
            p75_rev = results.car_owner_revenue.quantile(0.75)
            
            st.metric("Mean", f"${mean_rev:,.0f}")
            st.metric("25th percentile", f"${p25_rev:,.0f}")
            st.metric("75th percentile", f"${p75_rev:,.0f}")
        else:
            st.info("No data available")
    
    with col2:
        st.markdown("#### Asia Car Owner Revenue")
        if len(results.car_owner_revenue_asia) > 0:
            mean_rev = results.car_owner_revenue_asia.mean()
            p25_rev = results.car_owner_revenue_asia.quantile(0.25)
            p75_rev = results.car_owner_revenue_asia.quantile(0.75)
            
            st.metric("Mean", f"${mean_rev:,.0f}")
            st.metric("25th percentile", f"${p25_rev:,.0f}")
            st.metric("75th percentile", f"${p75_rev:,.0f}")
        else:
            st.info("No data available")
    
    # Histograms
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Car Owner Revenue (Non-Asia)")
        if len(results.car_owner_revenue) > 0:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(results.car_owner_revenue, bins=50, edgecolor='black', alpha=0.7)
            ax.set_xlabel('Revenue ($)')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of Car Owner Revenue (Non-Asia)')
            ax.axvline(results.car_owner_revenue.mean(), color='r', linestyle='--', label='Mean')
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        else:
            st.info("No data available")
    
    with col2:
        st.subheader("Car Owner Revenue (Asia)")
        if len(results.car_owner_revenue_asia) > 0:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(results.car_owner_revenue_asia, bins=50, edgecolor='black', alpha=0.7)
            ax.set_xlabel('Revenue ($)')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of Car Owner Revenue (Asia)')
            ax.axvline(results.car_owner_revenue_asia.mean(), color='r', linestyle='--', label='Mean')
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        else:
            st.info("No data available")


def render_co2_pollution_tab(results: SimulationResults):
    """Tab 5: CO₂ & Pollution"""
    st.header("CO₂ & Pollution")
    
    # KPI cards
    st.subheader("Key Metrics")
    target_year = 2030 if 2030 in results.years else results.years[-1]
    
    # CO2 saved (USA)
    if 'USA' in results.tons_co2_saved and target_year in results.tons_co2_saved['USA'].columns:
        co2_bear = results.tons_co2_saved['USA'][target_year].quantile(0.25)
        co2_avg = results.tons_co2_saved['USA'][target_year].mean()
        co2_bull = results.tons_co2_saved['USA'][target_year].quantile(0.75)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### CO₂ Saved - USA ({target_year})")
            st.metric("Bear (25th percentile)", f"{co2_bear / 1e6:.2f}M tons")
            st.metric("Average", f"{co2_avg / 1e6:.2f}M tons")
            st.metric("Bull (75th percentile)", f"{co2_bull / 1e6:.2f}M tons")
        
        with col2:
            # Health cost savings
            if target_year in results.savings_pollution_ALA.columns:
                health_bear = results.savings_pollution_ALA[target_year].quantile(0.25)
                health_avg = results.savings_pollution_ALA[target_year].mean()
                health_bull = results.savings_pollution_ALA[target_year].quantile(0.75)
                
                st.markdown(f"#### Health Cost Savings ({target_year})")
                st.metric("Bear (25th percentile)", f"${health_bear / 1e9:.2f}B")
                st.metric("Average", f"${health_avg / 1e9:.2f}B")
                st.metric("Bull (75th percentile)", f"${health_bull / 1e9:.2f}B")
    
    # CO2 saved plots (3 areas)
    st.subheader("CO₂ Saved by Region")
    try:
        fig1 = plot_3_areas(
            results.tons_co2_saved,
            "Tons CO₂ Saved",
            results.years,
            magnitude=6  # millions
        )
        st.pyplot(fig1, use_container_width=True)
        plt.close(fig1)
    except Exception as e:
        st.error(f"Error plotting CO₂ saved: {e}")
    
    # Percentage CO2 saved per region
    st.subheader("Percentage of Emissions Saved per Region")
    try:
        # Plot first region as example (or create combined plot)
        if len(results.percentage_tons_co2_saved_per_region) > 0:
            first_region = list(results.percentage_tons_co2_saved_per_region.keys())[0]
            fig2 = plot_percentage_graph(
                results.percentage_tons_co2_saved_per_region[first_region],
                f"Percentage CO₂ Saved - {first_region}",
                results.years
            )
            st.pyplot(fig2, use_container_width=True)
            plt.close(fig2)
            
            # Show other regions if available
            for region in list(results.percentage_tons_co2_saved_per_region.keys())[1:]:
                fig = plot_percentage_graph(
                    results.percentage_tons_co2_saved_per_region[region],
                    f"Percentage CO₂ Saved - {region}",
                    results.years
                )
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
    except Exception as e:
        st.error(f"Error plotting percentage CO₂ saved: {e}")
    
    # Health cost savings
    st.subheader("Health Cost Savings (Pollution)")
    try:
        fig3 = plot_global_series(
            results.savings_pollution_ALA,
            "Health Cost Savings from Pollution Reduction",
            results.years,
            magnitude=9  # billions
        )
        st.pyplot(fig3, use_container_width=True)
        plt.close(fig3)
    except Exception as e:
        st.error(f"Error plotting health cost savings: {e}")


def render_displacement_tab(results: SimulationResults):
    """Tab 6: Displacement & S-Curves"""
    st.header("Displacement & S-Curves")
    
    # KPI cards
    st.subheader("Key Metrics")
    target_year = 2030 if 2030 in results.years else results.years[-1]
    
    if target_year in results.cars_displaced.columns:
        displaced_bear = results.cars_displaced[target_year].quantile(0.25)
        displaced_avg = results.cars_displaced[target_year].mean()
        displaced_bull = results.cars_displaced[target_year].quantile(0.75)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### Cars Displaced ({target_year})")
            st.metric("Bear (25th percentile)", f"{displaced_bear / 1e6:.2f}M")
            st.metric("Average", f"{displaced_avg / 1e6:.2f}M")
            st.metric("Bull (75th percentile)", f"{displaced_bull / 1e6:.2f}M")
        
        with col2:
            if len(results.displacement_coefficient) > 0:
                disp_coef_mean = results.displacement_coefficient.mean()
                disp_coef_p25 = results.displacement_coefficient.quantile(0.25)
                disp_coef_p75 = results.displacement_coefficient.quantile(0.75)
                
                st.markdown("#### Displacement Coefficient")
                st.metric("Mean", f"{disp_coef_mean:.3f}")
                st.metric("25th percentile", f"{disp_coef_p25:.3f}")
                st.metric("75th percentile", f"{disp_coef_p75:.3f}")
    
    # Multi-line plot: Cars displaced, Tesla cars, robotaxis, remaining
    st.subheader("Fleet Composition Over Time")
    try:
        # Calculate global cumulative cars
        global_cum_cars = pd.DataFrame(index=results.simulation_list, columns=results.years)
        for year in results.years:
            for sim in results.simulation_list:
                total = 0
                for region in results.cum_cars_by_area.keys():
                    if year in results.cum_cars_by_area[region].columns:
                        total += results.cum_cars_by_area[region].loc[sim, year]
                global_cum_cars.loc[sim, year] = total
        
        # Calculate average for each year
        avg_cum_cars = global_cum_cars.mean(axis=0)
        avg_displaced = results.cars_displaced.mean(axis=0)
        
        fig, ax = plt.subplots(figsize=(14, 8))
        ax.plot(results.years, avg_cum_cars / 1e6, marker='o', label='Tesla Cumulative Cars', linewidth=2)
        ax.plot(results.years, avg_displaced / 1e6, marker='s', label='Cars Displaced', linewidth=2)
        
        # Calculate robotaxis (assuming cumulative cars are robotaxis)
        ax.plot(results.years, avg_cum_cars / 1e6, marker='^', label='Robotaxis', linewidth=2, linestyle='--')
        
        ax.set_xlabel('Years')
        ax.set_ylabel('Cars (millions)')
        ax.set_title('Fleet Composition: Tesla Cars, Robotaxis, and Displaced Cars')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(results.years)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    except Exception as e:
        st.error(f"Error plotting fleet composition: {e}")
    
    # Displacement coefficient histogram
    st.subheader("Displacement Coefficient Distribution")
    if len(results.displacement_coefficient) > 0:
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(results.displacement_coefficient, bins=50, edgecolor='black', alpha=0.7)
            ax.set_xlabel('Displacement Coefficient')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of Displacement Coefficient')
            ax.axvline(results.displacement_coefficient.mean(), color='r', linestyle='--', label='Mean')
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except Exception as e:
            st.error(f"Error plotting displacement coefficient: {e}")
    else:
        st.info("No displacement coefficient data available")


def render_time_gdp_tab(results: SimulationResults):
    """Tab 7: Time Saved & GDP"""
    st.header("Time Saved & GDP Impact")
    
    # KPI cards
    st.subheader("Key Metrics")
    target_year = 2030 if 2030 in results.years else results.years[-1]
    
    # Years saved (global)
    if len(results.years_saved_per_region) > 0:
        # Calculate global years saved
        global_years_saved = pd.DataFrame(index=results.simulation_list, columns=results.years)
        for year in results.years:
            for sim in results.simulation_list:
                total = 0
                for region in results.years_saved_per_region.keys():
                    if year in results.years_saved_per_region[region].columns:
                        total += results.years_saved_per_region[region].loc[sim, year]
                global_years_saved.loc[sim, year] = total
        
        if target_year in global_years_saved.columns:
            years_bear = global_years_saved[target_year].quantile(0.25)
            years_avg = global_years_saved[target_year].mean()
            years_bull = global_years_saved[target_year].quantile(0.75)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"#### Years Saved ({target_year})")
                st.metric("Bear (25th percentile)", f"{years_bear / 1e6:.2f}M years")
                st.metric("Average", f"{years_avg / 1e6:.2f}M years")
                st.metric("Bull (75th percentile)", f"{years_bull / 1e6:.2f}M years")
            
            with col2:
                # GDP impact
                if len(results.extra_gdp) > 0:
                    # Calculate global extra GDP
                    global_extra_gdp = pd.DataFrame(index=results.simulation_list, columns=results.years)
                    for year in results.years:
                        for sim in results.simulation_list:
                            total = 0
                            for region in results.extra_gdp.keys():
                                if year in results.extra_gdp[region].columns:
                                    total += results.extra_gdp[region].loc[sim, year]
                            global_extra_gdp.loc[sim, year] = total
                    
                    if target_year in global_extra_gdp.columns:
                        gdp_bear = global_extra_gdp[target_year].quantile(0.25)
                        gdp_avg = global_extra_gdp[target_year].mean()
                        gdp_bull = global_extra_gdp[target_year].quantile(0.75)
                        
                        st.markdown(f"#### Extra GDP ({target_year})")
                        st.metric("Bear (25th percentile)", f"${gdp_bear / 1e12:.2f}T")
                        st.metric("Average", f"${gdp_avg / 1e12:.2f}T")
                        st.metric("Bull (75th percentile)", f"${gdp_bull / 1e12:.2f}T")
    
    # Years saved by region
    st.subheader("Years Saved by Region")
    try:
        fig1 = plot_area_series(
            results.years_saved_per_region,
            "Years Saved",
            results.years,
            magnitude=6  # millions
        )
        st.pyplot(fig1, use_container_width=True)
        plt.close(fig1)
    except Exception as e:
        st.error(f"Error plotting years saved: {e}")
    
    # Global years saved
    if len(results.years_saved_per_region) > 0:
        st.subheader("Global Years Saved")
        try:
            global_years_saved = pd.DataFrame(index=results.simulation_list, columns=results.years)
            for year in results.years:
                for sim in results.simulation_list:
                    total = 0
                    for region in results.years_saved_per_region.keys():
                        if year in results.years_saved_per_region[region].columns:
                            total += results.years_saved_per_region[region].loc[sim, year]
                    global_years_saved.loc[sim, year] = total
            
            fig2 = plot_global_series(
                global_years_saved,
                "Global Years Saved",
                results.years,
                magnitude=6  # millions
            )
            st.pyplot(fig2, use_container_width=True)
            plt.close(fig2)
        except Exception as e:
            st.error(f"Error plotting global years saved: {e}")
    
    # Percentage extra GDP per region
    st.subheader("Percentage Extra GDP per Region")
    try:
        if len(results.percentage_extra_gdp) > 0:
            for region in results.percentage_extra_gdp.keys():
                fig = plot_percentage_graph(
                    results.percentage_extra_gdp[region],
                    f"Percentage Extra GDP - {region}",
                    results.years
                )
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
    except Exception as e:
        st.error(f"Error plotting percentage extra GDP: {e}")


def render_diagnostics_tab(results: SimulationResults, config_hash: str, config):
    """Tab 8: Diagnostics"""
    st.header("Diagnostics")
    
    # Configuration summary
    st.subheader("Configuration Summary")
    config_dict = config.to_dict()
    
    # Organize config into sections
    st.markdown("#### Simulation Settings")
    config_table_data = [
        {"Parameter": "Years to Simulate", "Value": f"{config.years[0]} - {config.years[-1]}"},
        {"Parameter": "Number of Simulations", "Value": config.num_simulations},
        {"Parameter": "Miles per Car", "Value": f"{config.miles_per_car:,.0f}"},
    ]
    st.dataframe(pd.DataFrame(config_table_data), use_container_width=True, hide_index=True)
    
    st.markdown("#### Usage & Network")
    network_table_data = [
        {"Parameter": "Days per Week", "Value": f"{config.days_per_week:.1f}"},
        {"Parameter": "Hours per Day", "Value": f"{config.hours_per_day:.1f}"},
        {"Parameter": "Miles per Hour", "Value": f"{config.miles_per_hour:.1f}"},
        {"Parameter": "Occupancy %", "Value": f"{config.occupancy_pct:.1%}"},
        {"Parameter": "Network Participation", "Value": f"{config.network_participation:.1%}"},
        {"Parameter": "Car Lifespan", "Value": f"{config.car_lifespan:.1f} years"},
    ]
    st.dataframe(pd.DataFrame(network_table_data), use_container_width=True, hide_index=True)
    
    st.markdown("#### Economics")
    economics_table_data = [
        {"Parameter": "Price per Mile", "Value": f"${config.price_per_mile:.2f}"},
        {"Parameter": "Price per Mile (Asia)", "Value": f"${config.price_per_mile_asia:.2f}"},
        {"Parameter": "Platform Fee", "Value": f"{config.platform_fee:.1%}"},
        {"Parameter": "Costs per Mile", "Value": f"${config.costs_per_mile:.2f}"},
    ]
    st.dataframe(pd.DataFrame(economics_table_data), use_container_width=True, hide_index=True)
    
    st.markdown("#### Production Growth")
    growth_table_data = [
        {"Parameter": "Growth Min", "Value": f"{config.growth_min:.1%}"},
        {"Parameter": "Growth Bear", "Value": f"{config.growth_bear:.1%}"},
        {"Parameter": "Growth Bull", "Value": f"{config.growth_bull:.1%}"},
        {"Parameter": "Growth Max", "Value": f"{config.growth_max:.1%}"},
    ]
    st.dataframe(pd.DataFrame(growth_table_data), use_container_width=True, hide_index=True)
    
    st.markdown("#### Regional Distribution")
    region_mapping = {
        'USA': 'region_usa',
        'Europe': 'region_europe',
        'China': 'region_china',
        'APAC excl China': 'region_apac_excl_china',
        'Canada': 'region_canada',
    }
    regional_table_data = []
    for region in sorted(results.cum_cars_by_area.keys()):
        attr_name = region_mapping.get(region, None)
        if attr_name:
            share = getattr(config, attr_name, 0)
            regional_table_data.append({"Region": region, "Share": f"{share:.1%}"})
    st.dataframe(pd.DataFrame(regional_table_data), use_container_width=True, hide_index=True)
    
    # Reproducibility info
    st.subheader("Reproducibility")
    st.code(f"Configuration Hash: {config_hash}", language=None)
    st.caption("Use this hash to reproduce this exact simulation configuration.")
    
    # ARIMA diagnostics (if available)
    if results.vmt_forecast is not None:
        st.subheader("ARIMA Model Diagnostics")
        st.info("VMT forecast was enabled for this simulation.")
        st.dataframe(results.vmt_forecast.head(20), use_container_width=True)
    else:
        st.info("VMT forecast was not enabled for this simulation.")
    
    # Data summary
    st.subheader("Results Summary")
    summary_data = [
        {"Metric": "Total Years", "Value": len(results.years)},
        {"Metric": "Total Simulations", "Value": len(results.simulation_list)},
        {"Metric": "Regions", "Value": len(results.cum_cars_by_area)},
    ]
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

