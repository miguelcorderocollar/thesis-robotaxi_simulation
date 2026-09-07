"""
Core simulation engine for Tesla Robotaxi Simulation.

Contains helper functions and the main run_simulation() function.
"""

import numpy as np
import pandas as pd
import math
import scipy.stats as stats
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import warnings
import os

# ARIMA forecast (optional)
try:
    from statsmodels.tsa.arima.model import ARIMA
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False
    warnings.warn("statsmodels not available, VMT forecast will be disabled")

from .config import SimulationConfig

warnings.filterwarnings('ignore')


# Helper Functions (extracted from notebook)

def simulate_norm_dist(mini: float, bear: float, bull: float, maxi: float, num_simulations: int) -> np.ndarray:
    """
    Returns random simulations based on truncated normal distribution.
    
    Args:
        mini: Minimum value
        bear: Bear case (25th percentile target)
        bull: Bull case (75th percentile target)
        maxi: Maximum value
        num_simulations: Number of simulations to generate
        
    Returns:
        Array of simulated values
    """
    mu = (bear + bull) / 2
    # Calculate sigma as the distance from mu to bull (or bear, they should be symmetric)
    # Use absolute value to handle both cases: bull > bear (growth rates) and bull < bear (deployment dates)
    sigma = abs(bull - mu)
    
    # Handle edge case where bull == bear (no uncertainty)
    if sigma < 1e-10:
        # If sigma is too small, try fallback based on the range
        sigma = abs(maxi - mini) / 4.0
        if sigma < 1e-10:
            # If range is also zero, return constant value
            return np.full(num_simulations, mu)
    
    # Calculate truncation bounds
    a = (mini - mu) / sigma
    b = (maxi - mu) / sigma
    
    # Handle case where bounds are invalid (a >= b)
    if a >= b:
        # If bounds are invalid, return constant value at the midpoint
        return np.full(num_simulations, (mini + maxi) / 2)
    
    try:
        list_return = stats.truncnorm(a, b, loc=mu, scale=sigma)
        x = list_return.rvs(num_simulations)
        return x
    except (ValueError, RuntimeError) as e:
        # Fallback: if distribution creation fails, return uniform distribution between mini and maxi
        warnings.warn(f"truncnorm failed ({e}), using uniform distribution between {mini} and {maxi}")
        return np.random.uniform(mini, maxi, num_simulations)


def simulate_normal_dist_row(row: pd.Series, num_simulations: int) -> pd.Series:
    """
    Given a row with a distribution, returns the simulations.
    
    Args:
        row: Series with 'Min', 'Bear', 'Bull', 'Max' keys
        num_simulations: Number of simulations
        
    Returns:
        Series of simulated values
    """
    return pd.Series(simulate_norm_dist(
        row['Min'], row['Bear'], row['Bull'], row['Max'], num_simulations
    ))


def get_sims_robo_deployment(table: pd.DataFrame, num_simulations: int) -> pd.DataFrame:
    """
    Returns simulation of Robotaxi Deployment dates.
    
    Args:
        table: DataFrame with 'Min', 'Bear', 'Bull', 'Max' columns (as timestamps)
        num_simulations: Number of simulations
        
    Returns:
        DataFrame with simulations (rows=simulations, columns=areas)
    """
    areas = table.index
    robo_deployment_simulations = []
    for area in areas:
        sim_result = simulate_norm_dist(
            table['Min'][area], table['Bear'][area],
            table['Bull'][area], table['Max'][area],
            num_simulations
        )
        robo_deployment_simulations.append(sim_result)
    robo_deployment_simulations_df = pd.DataFrame(
        robo_deployment_simulations, index=table.index
    ).T
    return robo_deployment_simulations_df


def datetime_to_timestamp(table: pd.DataFrame) -> pd.DataFrame:
    """
    Transform a dataframe from datetime to timestamp.
    
    Args:
        table: DataFrame with datetime values
        
    Returns:
        DataFrame with timestamp values
    """
    table_timestamp = pd.DataFrame(index=table.index, columns=table.columns)
    for row in table.index:
        for column in table.columns:
            table_timestamp.loc[row, column] = datetime.timestamp(table.loc[row, column])
    return table_timestamp


def timestamp_to_datetime(table: pd.DataFrame) -> pd.DataFrame:
    """
    Transform a dataframe from timestamp to datetime.
    
    Args:
        table: DataFrame with timestamp values
        
    Returns:
        DataFrame with datetime values
    """
    table_datetime = pd.DataFrame(index=table.index, columns=table.columns)
    for row in table.index:
        for column in table.columns:
            table_datetime.loc[row, column] = datetime.fromtimestamp(table.loc[row, column])
    return table_datetime


def get_years_regions_future_production(
    row: pd.Series, years: List[int], num_simulations: int
) -> pd.DataFrame:
    """
    Creates simulation of future production growth for a region.
    
    Args:
        row: Series with 'Min', 'Bear', 'Bull', 'Max' keys
        years: List of years to simulate
        num_simulations: Number of simulations
        
    Returns:
        DataFrame with simulations per year (rows=simulations, columns=years)
    """
    years_simulations = pd.DataFrame()
    for year in years:
        sim_result = simulate_norm_dist(
            row['Min'], row['Bear'], row['Bull'], row['Max'],
            num_simulations
        )
        years_simulations[year] = sim_result
    return years_simulations


def get_standarise_percentages(
    dictionary: Dict[str, pd.DataFrame], years: List[int], simulation_list: List[int]
) -> Dict[str, pd.DataFrame]:
    """
    Standardizes simulation percentages so they add up to 100%.
    
    Args:
        dictionary: Dictionary of DataFrames (one per area)
        years: List of years
        simulation_list: List of simulation indices
        
    Returns:
        Dictionary with normalized percentages
    """
    for year in years:
        for i in simulation_list:
            total_sum = 0
            for area in dictionary.keys():
                total_sum += dictionary[area].loc[i, year]
            for area in dictionary.keys():
                dictionary[area].loc[i, year] = dictionary[area].loc[i, year] / total_sum
    return dictionary


def get_percentage_year_left(date: datetime) -> float:
    """
    Return percentage of a year left based on a date.
    
    Args:
        date: Datetime object
        
    Returns:
        Float between 0 and 1
    """
    return (365 - date.timetuple().tm_yday) / 365


def get_all_percentage_years_robo(
    dates_by_area: pd.DataFrame, years: List[int], simulation_list: List[int]
) -> Dict[str, pd.DataFrame]:
    """
    Percentage of Robotaxi network availability per year per region.
    
    Args:
        dates_by_area: DataFrame with deployment dates (rows=simulations, columns=areas)
        years: List of years
        simulation_list: List of simulation indices
        
    Returns:
        Dictionary of DataFrames with percentage availability per year
    """
    result = {}
    for area in dates_by_area.columns:
        result_temp = pd.DataFrame(columns=years, index=simulation_list)
        for i in simulation_list:
            initial_year = dates_by_area.loc[i, area].year
            years_to_change = [year_no_robo for year_no_robo in years if year_no_robo <= initial_year]
            for year in years_to_change:
                if year == initial_year:
                    result_temp.loc[i, year] = get_percentage_year_left(dates_by_area.loc[i, area])
                else:
                    result_temp.loc[i, year] = 0
        result_temp.fillna(1, inplace=True)
        result[area] = result_temp
    return result


def get_revenue_tesla_per_region(
    gen_inp: pd.DataFrame, robo_miles: Dict[str, pd.DataFrame],
    years: List[int], simulation_list: List[int]
) -> Dict[str, pd.DataFrame]:
    """
    Get expected revenue by Tesla based on Robotaxi miles and price.
    
    Args:
        gen_inp: DataFrame with general inputs (rows=simulations)
        robo_miles: Dictionary of DataFrames with robotaxi miles per region
        years: List of years
        simulation_list: List of simulation indices
        
    Returns:
        Dictionary of DataFrames with revenue per region
    """
    ppm = gen_inp['Price/Mile']
    ppma = gen_inp['Price/Mile Asia']
    pf = gen_inp['Platform fee']
    result = {}
    for area in robo_miles:
        if area == 'China' or area == 'APAC excl China':
            ppm_aux = ppma
        else:
            ppm_aux = ppm
        result_area = pd.DataFrame(index=simulation_list, columns=years)
        for i in simulation_list:
            for year in years:
                result_area.loc[i, year] = (
                    ppm_aux.iloc[i] * robo_miles[area].loc[i, year] * pf.iloc[i]
                )
        result[area] = result_area
    return result


def get_average_per_year(dataframe: pd.DataFrame, years: List[int]) -> pd.DataFrame:
    """
    Returns the average for dataframe by years.
    
    Args:
        dataframe: DataFrame with years as columns
        years: List of years
        
    Returns:
        DataFrame with 'average' column and years as index
    """
    result = pd.DataFrame(columns=['average'], index=years)
    for year in years:
        result.loc[year] = dataframe[year].mean()
    return result


def get_quantile_per_year(dataframe: pd.DataFrame, q: float, years: List[int]) -> pd.DataFrame:
    """
    Returns the quantile of a series per year.
    
    Args:
        dataframe: DataFrame with years as columns
        q: Quantile (0.0 to 1.0)
        years: List of years
        
    Returns:
        DataFrame with 'Q' column and years as index
    """
    result = pd.DataFrame(columns=['Q'], index=years)
    for year in years:
        result.loc[year] = dataframe[year].quantile(q)
    return result


def get_global_from_areas(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Given dictionary with areas, get the global dataframe.
    
    Args:
        data: Dictionary of DataFrames (one per area)
        
    Returns:
        DataFrame with global totals
    """
    result = pd.DataFrame(0, columns=data[list(data.keys())[0]].columns,
                         index=data[list(data.keys())[0]].index)
    for area in data:
        result += data[area]
    return result


def get_discontinued_by_calculation(
    area: str, year: int, i: int, ls: int, ls_dec: float,
    glob_del_hist: pd.DataFrame, temp_result_prod: pd.DataFrame
) -> float:
    """
    Calculate discontinued cars for a given area, year, and simulation.
    
    Args:
        area: Region name
        year: Year to calculate
        i: Simulation index
        ls: Lifespan (integer part)
        ls_dec: Lifespan (decimal part)
        glob_del_hist: Historical production data
        temp_result_prod: Projected production data
        
    Returns:
        Number of discontinued cars
    """
    result = 0
    if (year - ls) in glob_del_hist.columns:
        result += glob_del_hist.loc[area, year - ls] * (1 - ls_dec)
    elif (year - ls) in temp_result_prod.columns:
        result += temp_result_prod.loc[i, year - ls] * (1 - ls_dec)
    
    if (year - ls - 1) in glob_del_hist.columns:
        result += glob_del_hist.loc[area, year - ls - 1] * ls_dec
    elif (year - ls - 1) in temp_result_prod.columns:
        result += temp_result_prod.loc[i, year - ls - 1] * ls_dec
    
    return result


@dataclass
class SimulationResults:
    """
    Results from a simulation run.
    
    Contains all computed metrics and data structures.
    """
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


def run_simulation(config: SimulationConfig) -> SimulationResults:
    """
    Execute Monte Carlo simulation with given configuration.
    
    Args:
        config: SimulationConfig object with all parameters
        
    Returns:
        SimulationResults object with all computed metrics
    """
    years = config.years
    simulation_list = config.simulation_list
    num_simulations = config.num_simulations
    
    # Load historical data
    data_dir = config.data_dir
    glob_del_hist_path = os.path.join(data_dir, 'tesla_production_history.csv')
    
    if not os.path.exists(glob_del_hist_path):
        raise FileNotFoundError(
            f"Historical production data not found at {glob_del_hist_path}. "
            "Please ensure legacy/data/ exists with required CSV files."
        )
    
    glob_del_hist = pd.read_csv(glob_del_hist_path, index_col=0)
    glob_del_hist.loc['Total'] = glob_del_hist.sum(axis=0)
    
    # Starting point - matches notebook: get 'Total' row, excluding last column
    start_by_area_2021 = glob_del_hist.loc['Total'][:-1]
    # Get 2021 total production from 'Total' column (matches notebook)
    production_2021_pred = glob_del_hist['Total'][2021]
    
    # Generate general inputs simulations
    general_inputs_sims = pd.DataFrame(index=simulation_list)
    
    # Simulate general inputs
    general_inputs_sims['Days/week'] = simulate_norm_dist(
        config.days_per_week * 0.8, config.days_per_week * 0.9,
        config.days_per_week * 1.1, config.days_per_week * 1.2,
        num_simulations
    )
    general_inputs_sims['Hours/day'] = simulate_norm_dist(
        config.hours_per_day * 0.8, config.hours_per_day * 0.9,
        config.hours_per_day * 1.1, config.hours_per_day * 1.2,
        num_simulations
    )
    general_inputs_sims['Miles/hour'] = simulate_norm_dist(
        config.miles_per_hour * 0.8, config.miles_per_hour * 0.9,
        config.miles_per_hour * 1.1, config.miles_per_hour * 1.2,
        num_simulations
    )
    general_inputs_sims['% ocupacy'] = simulate_norm_dist(
        config.occupancy_pct * 0.8, config.occupancy_pct * 0.9,
        config.occupancy_pct * 1.1, config.occupancy_pct * 1.2,
        num_simulations
    )
    general_inputs_sims['Network Participation'] = simulate_norm_dist(
        config.network_participation * 0.8, config.network_participation * 0.9,
        config.network_participation * 1.1, config.network_participation * 1.2,
        num_simulations
    )
    general_inputs_sims['Price/Mile'] = simulate_norm_dist(
        config.price_per_mile * 0.8, config.price_per_mile * 0.9,
        config.price_per_mile * 1.1, config.price_per_mile * 1.2,
        num_simulations
    )
    general_inputs_sims['Price/Mile Asia'] = simulate_norm_dist(
        config.price_per_mile_asia * 0.8, config.price_per_mile_asia * 0.9,
        config.price_per_mile_asia * 1.1, config.price_per_mile_asia * 1.2,
        num_simulations
    )
    general_inputs_sims['Platform fee'] = simulate_norm_dist(
        config.platform_fee * 0.8, config.platform_fee * 0.9,
        config.platform_fee * 1.1, config.platform_fee * 1.2,
        num_simulations
    )
    general_inputs_sims['Costs/Mile'] = simulate_norm_dist(
        config.costs_per_mile * 0.8, config.costs_per_mile * 0.9,
        config.costs_per_mile * 1.1, config.costs_per_mile * 1.2,
        num_simulations
    )
    
    # Calculate miles per car
    general_inputs_sims['Miles/car'] = (
        52 * general_inputs_sims['Days/week'] * general_inputs_sims['Hours/day'] *
        general_inputs_sims['Miles/hour'] * general_inputs_sims['% ocupacy']
    )
    
    # Simulate discontinued cars lifespan
    discontinued_sims = simulate_norm_dist(
        config.car_lifespan * 0.8, config.car_lifespan * 0.9,
        config.car_lifespan * 1.1, config.car_lifespan * 1.2,
        num_simulations
    )
    
    # Generate production growth simulations
    growth_percentage = pd.DataFrame(columns=years, index=simulation_list)
    for year in years:
        growth_percentage[year] = simulate_norm_dist(
            config.growth_min, config.growth_bear,
            config.growth_bull, config.growth_max,
            num_simulations
        )
    
    # Generate regional distribution simulations
    region_names = ['USA', 'Europe', 'China', 'APAC excl China', 'Canada']
    region_values = [
        config.region_usa, config.region_europe, config.region_china,
        config.region_apac_excl_china, config.region_canada
    ]
    
    percent_region_future_sims = {}
    for area, base_value in zip(region_names, region_values):
        percent_region_future_sims[area] = pd.DataFrame(columns=years, index=simulation_list)
        for year in years:
            # Add some variation around base value
            percent_region_future_sims[area][year] = simulate_norm_dist(
                max(0, base_value * 0.8), base_value * 0.9,
                base_value * 1.1, min(1, base_value * 1.2),
                num_simulations
            )
    
    # Normalize percentages
    percent_region_future_sims = get_standarise_percentages(
        percent_region_future_sims, years, simulation_list
    )
    
    # Simulate robotaxi deployment dates
    deployment_dates_df = pd.DataFrame(config.deployment_dates).T
    # Convert years to datetime (use Jan 1st of each year)
    deployment_dates_datetime = pd.DataFrame(index=deployment_dates_df.index)
    for col in ['Min', 'Bear', 'Bull', 'Max']:
        deployment_dates_datetime[col] = pd.to_datetime(
            deployment_dates_df[col].astype(str) + '-01-01'
        )
    
    deployment_dates_timestamp = datetime_to_timestamp(deployment_dates_datetime)
    sims_robo_deployment = get_sims_robo_deployment(deployment_dates_timestamp, num_simulations)
    sims_robo_deployment_datetime = timestamp_to_datetime(sims_robo_deployment)
    
    # Calculate cumulative cars per area
    cum_cars_by_area = {}
    prod_cars_by_area = {}
    prod_disc_by_area = {}
    
    for area in start_by_area_2021.index:
        temp_result_cum = pd.DataFrame(columns=years, index=simulation_list)
        temp_result_prod = pd.DataFrame(columns=years, index=simulation_list)
        temp_result_disc = pd.DataFrame(columns=years, index=simulation_list)
        
        for i in simulation_list:
            lifespan_sim = math.floor(discontinued_sims[i])
            decimal_lifespan_sim = discontinued_sims[i] % 1
            
            for year in years:
                if year == 2022:
                    temp_result_prod.loc[i, year] = (
                        production_2021_pred * (1 + growth_percentage.loc[i, year]) *
                        percent_region_future_sims[area].loc[i, year]
                    )
                    temp_result_disc.loc[i, year] = get_discontinued_by_calculation(
                        area, year, i, lifespan_sim, decimal_lifespan_sim,
                        glob_del_hist, temp_result_prod
                    )
                    temp_result_cum.loc[i, year] = (
                        start_by_area_2021[area] + temp_result_prod.loc[i, year]
                    )
                else:
                    temp_result_prod.loc[i, year] = (
                        temp_result_prod.loc[i, year - 1] /
                        percent_region_future_sims[area].loc[i, year - 1] *
                        (1 + growth_percentage.loc[i, year]) *
                        percent_region_future_sims[area].loc[i, year]
                    )
                    temp_result_disc.loc[i, year] = get_discontinued_by_calculation(
                        area, year, i, lifespan_sim, decimal_lifespan_sim,
                        glob_del_hist, temp_result_prod
                    )
                    temp_result_cum.loc[i, year] = (
                        temp_result_cum.loc[i, year - 1] +
                        temp_result_prod.loc[i, year] -
                        temp_result_disc.loc[i, year]
                    )
        
        prod_cars_by_area[area] = temp_result_prod
        prod_disc_by_area[area] = temp_result_disc
        cum_cars_by_area[area] = temp_result_cum
    
    # Calculate robotaxi miles
    percentage_years_robo = get_all_percentage_years_robo(
        sims_robo_deployment_datetime, years, simulation_list
    )
    
    robotaxi_miles_per_region = {}
    for area in cum_cars_by_area:
        aux = pd.DataFrame(columns=years, index=simulation_list)
        for i in simulation_list:
            for year in years:
                aux.loc[i, year] = (
                    cum_cars_by_area[area].loc[i, year] *
                    general_inputs_sims.loc[i, 'Miles/car'] *
                    general_inputs_sims.loc[i, 'Network Participation'] *
                    percentage_years_robo[area].loc[i, year]
                )
        robotaxi_miles_per_region[area] = aux
    
    robotaxi_miles = get_global_from_areas(robotaxi_miles_per_region)
    
    # Calculate revenue
    revenue_tesla_per_region = get_revenue_tesla_per_region(
        general_inputs_sims, robotaxi_miles_per_region, years, simulation_list
    )
    revenue_tesla_global = get_global_from_areas(revenue_tesla_per_region)
    
    # Car owner revenue
    car_owner_revenue = (
        general_inputs_sims['Price/Mile'] * (1 - general_inputs_sims['Platform fee']) -
        general_inputs_sims['Costs/Mile']
    ) * general_inputs_sims['Miles/car']
    
    car_owner_revenue_asia = (
        general_inputs_sims['Price/Mile Asia'] * (1 - general_inputs_sims['Platform fee']) -
        general_inputs_sims['Costs/Mile']
    ) * general_inputs_sims['Miles/car']
    
    # CO2 saved
    g_co2_mile_2021 = pd.DataFrame(
        [[395.721596, 133.897421], [410.141318, 165.730245], [419.137551, 265.413012]],
        index=['Europe', 'USA', 'China'],
        columns=['ICE', 'EV']
    )
    
    tons_co2_saved = {}
    for area in g_co2_mile_2021.index:
        temp_result = pd.DataFrame(columns=years, index=simulation_list)
        for year in years:
            for i in simulation_list:
                temp_result.loc[i, year] = (
                    robotaxi_miles_per_region[area].loc[i, year] *
                    (g_co2_mile_2021.loc[area, 'ICE'] - g_co2_mile_2021.loc[area, 'EV']) /
                    1000000
                )
        tons_co2_saved[area] = temp_result
    
    # Percentage of CO2 saved
    tons_co2_produced = pd.DataFrame(
        [4712770573, 4946034489, 10667887453],
        index=['USA', 'Europe', 'China'],
        columns=['CO2 Tons/year']
    ).T
    
    percentage_tons_co2_saved_per_region = {}
    for area in g_co2_mile_2021.index:
        temp_result = pd.DataFrame(columns=years, index=simulation_list)
        for year in years:
            for i in simulation_list:
                temp_result.loc[i, year] = (
                    tons_co2_saved[area].loc[i, year] /
                    tons_co2_produced.loc['CO2 Tons/year', area]
                )
        percentage_tons_co2_saved_per_region[area] = temp_result
    
    # Savings in pollution (ALA)
    ALA_cost_gallon = 1.15
    usa_mpg = 25.4
    savings_pollution_ALA = (
        robotaxi_miles_per_region['USA'] * ALA_cost_gallon / usa_mpg *
        (g_co2_mile_2021.loc['USA', 'ICE'] - g_co2_mile_2021.loc['USA', 'EV']) /
        g_co2_mile_2021.loc['USA', 'ICE']
    )
    
    # Cars displaced
    cars_usa = 282.8E6
    avg_miles_car = 13476
    cars_displaced = robotaxi_miles_per_region['USA'] / avg_miles_car
    
    # Displacement coefficient
    s_robo_cars = pd.DataFrame(index=simulation_list, columns=years)
    for i in simulation_list:
        s_robo_cars.loc[i] = (
            cum_cars_by_area['USA'].loc[i] *
            general_inputs_sims.loc[i, 'Network Participation']
        )
    
    displacement_coefficient_all = cars_displaced / s_robo_cars
    displacement_coefficient = displacement_coefficient_all[2030] if 2030 in displacement_coefficient_all.columns else displacement_coefficient_all.iloc[:, -1]
    
    # Hours and years saved
    hours_in_year = 8760
    hours_saved_per_region = {}
    for area in robotaxi_miles_per_region.keys():
        temp_hours_saved_per_region = pd.DataFrame(index=simulation_list, columns=years)
        for i in simulation_list:
            for year in years:
                temp_hours_saved_per_region.loc[i, year] = (
                    robotaxi_miles_per_region[area].loc[i, year] /
                    general_inputs_sims.loc[i, 'Miles/hour']
                )
        hours_saved_per_region[area] = temp_hours_saved_per_region
    
    years_saved_per_region = {}
    for area in hours_saved_per_region:
        years_saved_per_region[area] = hours_saved_per_region[area] / hours_in_year
    
    # GDP impact
    gdp_per_hour_work = pd.DataFrame(
        [74.19, 54.25, 15, 56.61],
        index=['USA', 'Europe', 'China', 'Canada'],
        columns=['Productivity']
    ).T
    
    gdp_per_area = pd.DataFrame(
        [20936600 * 1000000, 15276468.99 * 1000000, 14722730.70 * 1000000, 1644037.29 * 1000000],
        index=['USA', 'Europe', 'China', 'Canada'],
        columns=['GDP']
    ).T
    
    extra_gdp = {}
    percentage_extra_gdp = {}
    for area in gdp_per_hour_work.columns:
        if area in hours_saved_per_region:
            extra_gdp[area] = (
                hours_saved_per_region[area] *
                gdp_per_hour_work.loc['Productivity', area]
            )
            percentage_extra_gdp[area] = (
                extra_gdp[area] / gdp_per_area.loc['GDP', area]
            )
    
    # VMT forecast (optional)
    vmt_forecast = None
    us_percentage_vmt = None
    
    if config.enable_vmt_forecast and ARIMA_AVAILABLE:
        try:
            vmt_history_path = os.path.join(data_dir, 'VMT_US.csv')
            if os.path.exists(vmt_history_path):
                vmt_history = pd.read_csv(
                    vmt_history_path, parse_dates=['DATE'],
                    index_col=['DATE'], dayfirst=True
                )
                
                vmt_history_log = np.log(vmt_history)
                vmt_model = ARIMA(vmt_history_log, order=(1, 1, 1))
                vmt_model_fit = vmt_model.fit()
                
                vmt_months_sim = 12 * (config.years_to_simulate - 2019)
                vmt_forecast_result = vmt_model_fit.forecast(steps=vmt_months_sim, alpha=0.05)
                
                result_list = []
                for i in range(2020, config.years_to_simulate + 1):
                    for j in range(1, 13):
                        result_list.append('1/' + str(j) + '/' + str(i))
                vmt_forecast_dates = pd.to_datetime(result_list, dayfirst=True)
                vmt_predicted = pd.DataFrame(columns=['DATE', 'VMT'])
                vmt_predicted['DATE'] = vmt_forecast_dates
                vmt_predicted['VMT'] = np.exp(vmt_forecast_result[0])
                vmt_predicted = vmt_predicted.set_index('DATE')
                
                VMT_MA = vmt_predicted.rolling(12, min_periods=1).mean()
                
                us_percentage_vmt = pd.DataFrame(columns=years, index=simulation_list)
                for year in years:
                    year_date = pd.Timestamp(f'{year}-06-01')
                    if year_date in VMT_MA.index:
                        us_percentage_vmt[year] = (
                            robotaxi_miles_per_region['USA'][year] /
                            VMT_MA.loc[year_date, 'VMT'] / 1000000
                        )
                
                vmt_forecast = vmt_predicted
        except Exception as e:
            warnings.warn(f"VMT forecast failed: {e}")
    
    return SimulationResults(
        config=config,
        years=years,
        simulation_list=simulation_list,
        cum_cars_by_area=cum_cars_by_area,
        prod_cars_by_area=prod_cars_by_area,
        prod_disc_by_area=prod_disc_by_area,
        robotaxi_miles_per_region=robotaxi_miles_per_region,
        robotaxi_miles=robotaxi_miles,
        revenue_tesla_per_region=revenue_tesla_per_region,
        revenue_tesla_global=revenue_tesla_global,
        car_owner_revenue=car_owner_revenue,
        car_owner_revenue_asia=car_owner_revenue_asia,
        tons_co2_saved=tons_co2_saved,
        percentage_tons_co2_saved_per_region=percentage_tons_co2_saved_per_region,
        savings_pollution_ALA=savings_pollution_ALA,
        cars_displaced=cars_displaced,
        displacement_coefficient=displacement_coefficient,
        hours_saved_per_region=hours_saved_per_region,
        years_saved_per_region=years_saved_per_region,
        extra_gdp=extra_gdp,
        percentage_extra_gdp=percentage_extra_gdp,
        vmt_forecast=vmt_forecast,
        us_percentage_vmt=us_percentage_vmt,
    )
