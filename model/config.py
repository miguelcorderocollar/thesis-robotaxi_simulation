"""
Configuration module for Tesla Robotaxi Simulation.

Defines SimulationConfig dataclass and methods for loading defaults from CSV files.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import pandas as pd
import os
import hashlib
import json


@dataclass
class SimulationConfig:
    """
    Configuration for Tesla Robotaxi Simulation.
    
    Contains all user-configurable parameters for a simulation run.
    """
    # Simulation settings
    years_to_simulate: int = 2039
    num_simulations: int = 5000
    
    # Usage & Network (from general_inputs.csv)
    days_per_week: float = 7.0
    hours_per_day: float = 16.0
    miles_per_hour: float = 30.0
    occupancy_pct: float = 0.50
    network_participation: float = 0.80
    car_lifespan: float = 15.0
    
    # Economics (from general_inputs.csv)
    price_per_mile: float = 1.50
    price_per_mile_asia: float = 1.20
    platform_fee: float = 0.30
    costs_per_mile: float = 0.20
    
    # Production Growth (from projected_production_growth.csv)
    # Simplified: single set of growth parameters for all years
    growth_min: float = 0.20
    growth_bear: float = 0.30
    growth_bull: float = 0.50
    growth_max: float = 0.80
    
    # Regional Distribution (from production_area_distribution.csv)
    region_usa: float = 0.35
    region_europe: float = 0.25
    region_china: float = 0.20
    region_apac_excl_china: float = 0.15
    region_canada: float = 0.05
    
    # Deployment Dates (from robotaxi_deployment_date.csv)
    # Format: {'USA': {'Min': 2024, 'Bear': 2025, 'Bull': 2026, 'Max': 2028}, ...}
    deployment_dates: Optional[Dict[str, Dict[str, int]]] = None
    
    # Advanced parameters
    enable_vmt_forecast: bool = True
    
    # Data file paths
    data_dir: str = './Data'
    
    def __post_init__(self):
        """Initialize deployment_dates if None."""
        if self.deployment_dates is None:
            self.deployment_dates = {
                'USA': {'Min': 2024, 'Bull': 2025, 'Bear': 2026, 'Max': 2028},
                'Europe': {'Min': 2025, 'Bull': 2026, 'Bear': 2027, 'Max': 2029},
                'China': {'Min': 2024, 'Bull': 2025, 'Bear': 2026, 'Max': 2028},
                'APAC excl China': {'Min': 2026, 'Bull': 2027, 'Bear': 2028, 'Max': 2030},
                'Canada': {'Min': 2025, 'Bull': 2026, 'Bear': 2027, 'Max': 2029},
            }
    
    @classmethod
    def from_defaults(cls, data_dir: str = './Data') -> 'SimulationConfig':
        """
        Load default values from CSV files.
        
        Args:
            data_dir: Directory containing CSV data files
            
        Returns:
            SimulationConfig with defaults loaded from CSV files
        """
        config = cls(data_dir=data_dir)
        
        # Load general_inputs.csv
        general_inputs_path = os.path.join(data_dir, 'general_inputs.csv')
        if os.path.exists(general_inputs_path):
            general_inputs = pd.read_csv(general_inputs_path, index_col=0)
            
            # Map CSV column names to config attributes
            mapping = {
                'Days/week': 'days_per_week',
                'Hours/day': 'hours_per_day',
                'Miles/hour': 'miles_per_hour',
                '% ocupacy': 'occupancy_pct',
                'Network Participation': 'network_participation',
                'Car Lifespan': 'car_lifespan',
                'Price/Mile': 'price_per_mile',
                'Price/Mile Asia': 'price_per_mile_asia',
                'Platform fee': 'platform_fee',
                'Costs/Mile': 'costs_per_mile',
            }
            
            for csv_key, attr_name in mapping.items():
                if csv_key in general_inputs.index:
                    # Use Bear value as default (middle of distribution)
                    if 'Bear' in general_inputs.columns:
                        setattr(config, attr_name, float(general_inputs.loc[csv_key, 'Bear']))
                    elif 'Average' in general_inputs.columns:
                        setattr(config, attr_name, float(general_inputs.loc[csv_key, 'Average']))
                    else:
                        # Use first numeric column
                        numeric_cols = general_inputs.select_dtypes(include=['float64', 'int64']).columns
                        if len(numeric_cols) > 0:
                            setattr(config, attr_name, float(general_inputs.loc[csv_key, numeric_cols[0]]))
        
        # Load production_area_distribution.csv
        prod_dist_path = os.path.join(data_dir, 'production_area_distribution.csv')
        if os.path.exists(prod_dist_path):
            prod_dist = pd.read_csv(prod_dist_path, index_col=0)
            
            region_mapping = {
                'USA': 'region_usa',
                'Europe': 'region_europe',
                'China': 'region_china',
                'APAC excl China': 'region_apac_excl_china',
                'Canada': 'region_canada',
            }
            
            # Load Bear values (or Average if Bear not available)
            region_values = {}
            for region_name, attr_name in region_mapping.items():
                if region_name in prod_dist.index:
                    if 'Bear' in prod_dist.columns:
                        region_values[attr_name] = float(prod_dist.loc[region_name, 'Bear'])
                    elif 'Average' in prod_dist.columns:
                        region_values[attr_name] = float(prod_dist.loc[region_name, 'Average'])
            
            # Normalize regional distribution to sum to 1.0
            total = sum(region_values.values())
            if total > 0:
                for attr_name, value in region_values.items():
                    setattr(config, attr_name, value / total)
        
        # Load projected_production_growth.csv
        growth_path = os.path.join(data_dir, 'projected_production_growth.csv')
        if os.path.exists(growth_path):
            growth = pd.read_csv(growth_path, index_col=0)
            # Use first year's values as defaults (simplified)
            if len(growth) > 0:
                first_year = growth.index[0]
                if 'Min' in growth.columns:
                    config.growth_min = float(growth.loc[first_year, 'Min'])
                if 'Bear' in growth.columns:
                    config.growth_bear = float(growth.loc[first_year, 'Bear'])
                if 'Bull' in growth.columns:
                    config.growth_bull = float(growth.loc[first_year, 'Bull'])
                if 'Max' in growth.columns:
                    config.growth_max = float(growth.loc[first_year, 'Max'])
        
        # Load robotaxi_deployment_date.csv
        # Note: CSV has Bear/Bull columns, but we need Bull (optimistic/earlier) ≤ Bear (pessimistic/later)
        # The CSV appears to have them swapped, so we swap them when loading
        deployment_path = os.path.join(data_dir, 'robotaxi_deployment_date.csv')
        if os.path.exists(deployment_path):
            deployment = pd.read_csv(deployment_path, index_col=0, parse_dates=['Min', 'Bear', 'Bull', 'Max'])
            deployment_dates = {}
            for region in deployment.index:
                # CSV has Bear/Bull, but semantically: Bull = optimistic (earlier), Bear = pessimistic (later)
                # If CSV Bear < Bull, they're swapped and we need to fix it
                csv_bear = deployment.loc[region, 'Bear'].year
                csv_bull = deployment.loc[region, 'Bull'].year
                
                # If Bear is earlier than Bull in CSV, they're swapped - swap them
                if csv_bear < csv_bull:
                    # CSV has them backwards, swap them
                    bull_year = csv_bear  # CSV's "Bear" is actually the optimistic (earlier) = Bull
                    bear_year = csv_bull  # CSV's "Bull" is actually the pessimistic (later) = Bear
                else:
                    # CSV has them correct
                    bull_year = csv_bull
                    bear_year = csv_bear
                
                deployment_dates[region] = {
                    'Min': deployment.loc[region, 'Min'].year,
                    'Bull': bull_year,  # Optimistic (earlier)
                    'Bear': bear_year,  # Pessimistic (later)
                    'Max': deployment.loc[region, 'Max'].year,
                }
            config.deployment_dates = deployment_dates
        
        return config
    
    def validate(self) -> List[str]:
        """
        Validate configuration and return list of errors.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Regional distribution must sum to 1.0
        region_sum = (
            self.region_usa + self.region_europe + self.region_china +
            self.region_apac_excl_china + self.region_canada
        )
        if abs(region_sum - 1.0) > 0.01:
            errors.append(f"Regional distribution sums to {region_sum:.3f}, must equal 1.0")
        
        # Deployment dates: Min <= Bull <= Bear <= Max (earlier = more optimistic)
        if self.deployment_dates:
            for region, dates in self.deployment_dates.items():
                if not (dates['Min'] <= dates['Bull'] <= dates['Bear'] <= dates['Max']):
                    errors.append(
                        f"Deployment dates for {region} are invalid: "
                        f"Min ({dates['Min']}) <= Bull ({dates['Bull']}) <= "
                        f"Bear ({dates['Bear']}) <= Max ({dates['Max']}). Earlier years = more optimistic."
                    )
        
        # Growth rates: Min <= Bear <= Bull <= Max
        if not (self.growth_min <= self.growth_bear <= self.growth_bull <= self.growth_max):
            errors.append(
                f"Growth rates are invalid: "
                f"Min ({self.growth_min}) <= Bear ({self.growth_bear}) <= "
                f"Bull ({self.growth_bull}) <= Max ({self.growth_max})"
            )
        
        # Percentages must be between 0 and 1
        pct_params = [
            ('occupancy_pct', self.occupancy_pct),
            ('network_participation', self.network_participation),
            ('platform_fee', self.platform_fee),
        ]
        for name, value in pct_params:
            if not (0.0 <= value <= 1.0):
                errors.append(f"{name} must be between 0.0 and 1.0, got {value}")
        
        # Years must be valid
        if self.years_to_simulate < 2022:
            errors.append(f"years_to_simulate must be >= 2022, got {self.years_to_simulate}")
        
        # Simulations must be reasonable
        if self.num_simulations < 100:
            errors.append(f"num_simulations must be >= 100, got {self.num_simulations}")
        
        return errors
    
    def to_dict(self) -> dict:
        """Convert to dictionary for caching."""
        return asdict(self)
    
    def to_hash(self) -> str:
        """Generate hash for caching."""
        config_dict = self.to_dict()
        # Remove data_dir from hash (doesn't affect simulation)
        config_dict.pop('data_dir', None)
        config_str = json.dumps(config_dict, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    @property
    def miles_per_car(self) -> float:
        """Calculate miles per car per year."""
        return (
            52 * self.days_per_week * self.hours_per_day *
            self.miles_per_hour * self.occupancy_pct
        )
    
    @property
    def years(self) -> List[int]:
        """Get list of years to simulate."""
        return list(range(2022, self.years_to_simulate + 1))
    
    @property
    def simulation_list(self) -> List[int]:
        """Get list of simulation indices."""
        return list(range(0, self.num_simulations))

