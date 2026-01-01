import numpy as np
from typing import List, Dict, Optional
from src.config import MonteCarloConfig, base_seed
from src.data_structures import MonteCarloResults, ExecutionResult
from src.market_simulator import MarketSimulator
from src.impact_models import ImpactModel, CostModel
from src.strategies import BaseStrategy

class MonteCarloSimulator:
    
    def __init__(self, config: MonteCarloConfig):
        self.config = config
    
    def perturb_market_params(self, seed: int) -> Dict:
        rng = np.random.RandomState(seed)
        
        vol_mult = 1.0 + rng.uniform(-self.config.vol_perturbation, self.config.vol_perturbation)
        spread_mult = 1.0 + rng.uniform(-self.config.spread_perturbation, self.config.spread_perturbation)
        depth_mult = 1.0 + rng.uniform(-self.config.depth_perturbation, self.config.depth_perturbation)
        
        return {
            'S0': self.config.base_price,
            'base_vol': self.config.base_vol * vol_mult,
            'base_spread': self.config.base_spread * spread_mult,
            'base_depth': self.config.base_depth * depth_mult,
            'base_adv': self.config.base_adv,
            'impact_gamma': self.config.temp_gamma,
            'impact_alpha': self.config.temp_alpha,
            'seed': seed
        }
    
    def run_single_simulation(self, strategy: BaseStrategy, simulation_id: int,
                             scenario: Optional[str] = None) -> ExecutionResult:

        market_params = self.perturb_market_params(base_seed + simulation_id)
        market_sim = MarketSimulator(**market_params)
        
        if scenario:
            market_sim.inject_scenario(scenario)
        
        impact_model = ImpactModel(
            temp_gamma=self.config.temp_gamma,
            temp_alpha=self.config.temp_alpha,
            perm_eta=self.config.perm_eta,
            perm_beta=self.config.perm_beta,
            temp_half_life=self.config.temp_impact_half_life
        )
        cost_model = CostModel(impact_model)
        
        result = strategy.execute(
            total_size=self.config.order_size,
            T=self.config.execution_periods,
            market_sim=market_sim,
            cost_model=cost_model,
            simulation_id=simulation_id
        )
        
        return result
    
    def run_monte_carlo(self, strategies: List[BaseStrategy], n_simulations: int,
                       scenario: Optional[str] = None, 
                       progress_callback=None) -> Dict[str, MonteCarloResults]:

        results_by_strategy = {}
        
        for strategy in strategies:
            if progress_callback:
                progress_callback(f"Running {strategy.name}...")
            
            all_results = []
            costs_bps = []
            
            for sim_id in range(n_simulations):
                result = self.run_single_simulation(strategy, sim_id, scenario)
                all_results.append(result)
                
                notional = result.arrival_price * self.config.order_size
                costs_bps.append(result.costs.total_bps(notional))
            
            costs_array = np.array(costs_bps)
            
            mean_spread = np.mean([
                (r.costs.spread / (r.arrival_price * self.config.order_size)) * 10000
                for r in all_results
            ])
            mean_temp = np.mean([
                (r.costs.temporary / (r.arrival_price * self.config.order_size)) * 10000
                for r in all_results
            ])
            mean_perm = np.mean([
                (r.costs.permanent / (r.arrival_price * self.config.order_size)) * 10000
                for r in all_results
            ])
            mean_opp = np.mean([
                (r.costs.opportunity / (r.arrival_price * self.config.order_size)) * 10000
                for r in all_results
            ])
            mean_adv = np.mean([
                (r.costs.adverse_selection / (r.arrival_price * self.config.order_size)) * 10000
                for r in all_results
            ])
            
            risk_adjusted_savings = 0.0
            
            results_by_strategy[strategy.name] = MonteCarloResults(
                strategy=strategy.name,
                n_simulations=n_simulations,
                costs_bps=costs_bps,
                mean_cost=np.mean(costs_array),
                std_cost=np.std(costs_array),
                median_cost=np.median(costs_array),
                percentile_5=np.percentile(costs_array, 5),
                percentile_95=np.percentile(costs_array, 95),
                risk_adjusted_savings=risk_adjusted_savings,
                value_at_risk_95=np.percentile(costs_array, 95),
                mean_spread=mean_spread,
                mean_temp_impact=mean_temp,
                mean_perm_impact=mean_perm,
                mean_opportunity=mean_opp,
                mean_adverse=mean_adv,
                all_results=all_results
            )
        
        # Compute risk adjusted returns against TWAP benchmark
        if 'TWAP' in results_by_strategy:
            twap_mean = results_by_strategy['TWAP'].mean_cost
            for name, mc_result in results_by_strategy.items():
                if name != 'TWAP':
                    cost_savings = twap_mean - mc_result.mean_cost
                    if mc_result.std_cost > 0:
                        mc_result.risk_adjusted_savings = cost_savings / mc_result.std_cost
        
        return results_by_strategy
