"""
Plotting functions for Tesla Robotaxi Simulation.

All functions return matplotlib.figure.Figure objects for research and notebook use.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, List
from matplotlib.ticker import MaxNLocator
import seaborn as sns

# Import helper functions from core
from .core import get_average_per_year, get_quantile_per_year

# Set style defaults (matching notebook)
sns.set_style('darkgrid')
plt.rc('axes', titlesize=18)
plt.rc('axes', labelsize=14)
plt.rc('xtick', labelsize=13)
plt.rc('ytick', labelsize=13)
plt.rc('legend', fontsize=13)
plt.rc('font', size=13)


def plot_area_series(
    data: Dict[str, pd.DataFrame],
    legend: str,
    years: List[int],
    magnitude: int = 0
) -> plt.Figure:
    """
    Plot average, bear, and bull cases for multiple areas.
    
    Args:
        data: Dictionary of DataFrames (one per area)
        legend: Title/legend for the plot
        years: List of years
        magnitude: Power of 10 for scaling (6=million, 9=billion, 12=trillion)
        
    Returns:
        matplotlib Figure object
    """
    fig, axes = plt.subplots(figsize=(19, 8), nrows=1, ncols=3)
    
    if magnitude == 6:
        magnitude_label = 'in millions'
    elif magnitude == 9:
        magnitude_label = 'in billions'
    elif magnitude == 12:
        magnitude_label = 'in trillions'
    else:
        magnitude_label = ''
        magnitude = 0
    
    magnitude = pow(10, magnitude)
    
    i = 0
    for graph in axes:
        graph.set_xlabel('Years')
        graph.set_ylabel(magnitude_label)
        if i == 0:
            graph.set_title(legend + "\nAverage case")
            for area in data:
                avg_data = get_average_per_year(data[area], years)
                graph.plot(avg_data / magnitude, label=area, marker='o', markersize=2)
        elif i == 1:
            graph.set_title(legend + "\nBull case")
            for area in data:
                bull_data = get_quantile_per_year(data[area] / magnitude, 0.75, years)
                graph.plot(bull_data, label=area, marker='o', markersize=2)
        else:
            graph.set_title(legend + "\nBear case")
            for area in data:
                bear_data = get_quantile_per_year(data[area] / magnitude, 0.25, years)
                graph.plot(bear_data, label=area, marker='o', markersize=2)
        graph.legend(loc=2)
        i += 1
        graph.xaxis.set_major_locator(MaxNLocator(integer=True))
    
    plt.tight_layout()
    return fig


def plot_global_series(
    data: pd.DataFrame,
    legend: str,
    years: List[int],
    magnitude: int = 0
) -> plt.Figure:
    """
    Plot global series with bear/average/bull scenarios.
    
    Args:
        data: DataFrame with years as columns
        legend: Title for the plot
        years: List of years
        magnitude: Power of 10 for scaling (6=million, 9=billion, 12=trillion)
        
    Returns:
        matplotlib Figure object
    """
    if magnitude == 6:
        magnitude_label = 'in millions'
    elif magnitude == 9:
        magnitude_label = 'in billions'
    elif magnitude == 12:
        magnitude_label = 'in trillions'
    else:
        magnitude_label = ''
        magnitude = 0
    
    magnitude = pow(10, magnitude)
    
    fig, axes = plt.subplots(figsize=(19, 8))
    axes.set_xlabel('Years')
    axes.set_ylabel(magnitude_label)
    axes.set_title(legend)
    
    bull_data = get_quantile_per_year(data, 0.75, years)
    avg_data = get_average_per_year(data, years)
    bear_data = get_quantile_per_year(data, 0.25, years)
    
    axes.plot(bull_data / magnitude, marker='o', markersize=3, label='Bull', color='#e67070')
    axes.plot(avg_data / magnitude, marker='o', markersize=3, label='Average', color='#cc0000')
    axes.plot(bear_data / magnitude, marker='o', markersize=3, label='Bear', color='#e67070')
    
    sup = (pd.DataFrame(bull_data['Q'].tolist()) / magnitude)[0].tolist()
    bot = (pd.DataFrame(bear_data['Q'].tolist()) / magnitude)[0].tolist()
    axes.fill_between(years, sup, bot, color='#e67070', alpha=.1)
    axes.xaxis.set_major_locator(MaxNLocator(integer=True))
    axes.legend(loc=2)
    plt.xticks(years)
    plt.tight_layout()
    return fig


def plot_3_areas(
    data: Dict[str, pd.DataFrame],
    legend: str,
    years: List[int],
    magnitude: int = 0
) -> plt.Figure:
    """
    Plot three areas side-by-side with bear/average/bull.
    
    Args:
        data: Dictionary of DataFrames (one per area)
        legend: Title for the plot
        years: List of years
        magnitude: Power of 10 for scaling (6=million, 9=billion, 12=trillion)
        
    Returns:
        matplotlib Figure object
    """
    areas = list(data.keys())
    
    if magnitude == 6:
        magnitude_label = 'in millions'
    elif magnitude == 9:
        magnitude_label = 'in billions'
    elif magnitude == 12:
        magnitude_label = 'in trillions'
    else:
        magnitude_label = ''
        magnitude = 0
    
    magnitude = pow(10, magnitude)
    
    fig, axes = plt.subplots(figsize=(19, 8), nrows=1, ncols=3)
    i = 0
    for graph in axes:
        graph.set_xlabel('Years')
        graph.set_ylabel(magnitude_label)
        graph.set_title(legend + '\n' + areas[i])
        
        bull_data = get_quantile_per_year(data[areas[i]], 0.75, years)
        avg_data = get_average_per_year(data[areas[i]], years)
        bear_data = get_quantile_per_year(data[areas[i]], 0.25, years)
        
        graph.plot(bull_data / magnitude, marker='o', markersize=2, label='Bull', color='#e67070')
        graph.plot(avg_data / magnitude, marker='o', markersize=2, label='Average', color='#cc0000')
        graph.plot(bear_data / magnitude, marker='o', markersize=2, label='Bear', color='#e67070')
        graph.legend(loc=2)
        
        sup = (pd.DataFrame(bull_data['Q'].tolist()) / magnitude)[0].tolist()
        bot = (pd.DataFrame(bear_data['Q'].tolist()) / magnitude)[0].tolist()
        graph.fill_between(years, sup, bot, color='#e67070', alpha=.1)
        graph.xaxis.set_major_locator(MaxNLocator(integer=True))
        i += 1
    
    plt.tight_layout()
    return fig


def plot_percentage_graph(
    data: pd.DataFrame,
    title: str,
    years: List[int]
) -> plt.Figure:
    """
    Plot percentage bar chart with error bars.
    
    Args:
        data: DataFrame with years as columns
        title: Title for the plot
        years: List of years
        
    Returns:
        matplotlib Figure object
    """
    percentage_avg = get_average_per_year(data, years)
    percentage_bear = get_quantile_per_year(data, 0.25, years)
    percentage_bull = get_quantile_per_year(data, 0.75, years)
    percentage_bull_bear_diff = percentage_bull['Q'] * 100 - percentage_bear['Q'] * 100
    
    fig, axes = plt.subplots(figsize=(16, 6))
    axes.set_xlabel('Years')
    axes.set_ylabel('%')
    axes.set_title(title)
    axes.bar(
        percentage_avg.index, percentage_avg['average'] * 100,
        color='#cc0000', yerr=percentage_bull_bear_diff, capsize=5
    )
    axes.xaxis.set_major_locator(MaxNLocator(integer=True))
    plt.xticks(years)
    plt.tight_layout()
    return fig
