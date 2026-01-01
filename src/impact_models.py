import numpy as np
from typing import List
from src.data_structures import MarketState, CostBreakdown

class ImpactModel:
    def __init__(self, temp_gamma=0.1, temp_alpha=0.65, perm_eta=0.03, perm_beta=0.42,
                 temp_half_life=10.0):
        self.temp_gamma = temp_gamma
        self.temp_alpha = temp_alpha
        self.perm_eta = perm_eta
        self.perm_beta = perm_beta
        
        self.temp_decay_rate = np.log(2) / temp_half_life if temp_half_life > 0 else float('inf')
    
    def temporary_impact_instantaneous(self, trade_size: float, volume: float, 
                                        volatility: float, price: float) -> float:
        if trade_size == 0 or volume == 0:
            return 0.0
        
        participation = abs(trade_size) / volume

        impact_per_share = self.temp_gamma * (participation ** self.temp_alpha) * volatility * price

        return impact_per_share * abs(trade_size)
    
    def temporary_impact_with_decay(self, trade_sizes: List[float], volumes: List[float],
                                     volatilities: List[float], prices: List[float]) -> float:

        if not trade_sizes:
            return 0.0
        
        T = len(trade_sizes)
        total_impact = 0.0
        
        for t in range(T):
            if trade_sizes[t] == 0:
                continue
            
            inst_impact = self.temporary_impact_instantaneous(
                trade_sizes[t], volumes[t], volatilities[t], prices[t]
            )
            
            remaining = T - t
            if self.temp_decay_rate < float('inf') and remaining > 0:
                decay_factor = (1 - np.exp(-self.temp_decay_rate * remaining)) / (
                    self.temp_decay_rate * remaining)
            else:
                decay_factor = 1.0
            
            total_impact += inst_impact * decay_factor
        
        return total_impact
    
    def permanent_impact(self, total_size: float, daily_volume: float, price: float) -> float:
        if total_size == 0 or daily_volume == 0:
            return 0.0
        
        participation = abs(total_size) / daily_volume
        impact_per_share = self.perm_eta * (participation ** self.perm_beta) * price
        return impact_per_share * abs(total_size)

class CostModel:
    def __init__(self, impact_model: ImpactModel):
        self.impact = impact_model
    
    def compute_costs(self, trajectory: List[float], states: List[MarketState], 
                     arrival_price: float) -> CostBreakdown:
        total_shares = sum(trajectory)
        if total_shares == 0:
            return CostBreakdown(0, 0, 0, 0, 0)
        
        spread_cost = sum([
            0.5 * state.spread * abs(n_t) 
            for n_t, state in zip(trajectory, states)
        ])
        
        temp_impact = self.impact.temporary_impact_with_decay(
            trajectory,
            [s.volume for s in states],
            [s.volatility for s in states],
            [s.mid_price for s in states]
        )
        
        avg_daily_volume = np.mean([s.volume for s in states]) * len(states)
        perm_impact = self.impact.permanent_impact(
            total_shares, avg_daily_volume, arrival_price
        )
        
        exec_prices = []
        for n_t, state in zip(trajectory, states):
            if n_t > 0:  # Buy
                exec_prices.extend([state.ask] * int(abs(n_t)))
            elif n_t < 0:  # Sell
                exec_prices.extend([state.bid] * int(abs(n_t)))
        
        if exec_prices:
            vwap = np.mean(exec_prices)  
        else:
            vwap = arrival_price

        #Implementation Shortfall (opportunity cost)
        implementation_shortfall = (vwap - arrival_price) * total_shares
        opportunity_cost = max(0, implementation_shortfall)
        
        final_price = states[-1].mid_price if states else arrival_price

        # For simplicity measure drift from VWAP to final price
        post_trade_drift = (final_price - vwap) * total_shares

        # For a buy the adverse selection is negative drift 
        adverse_selection = max(0, -post_trade_drift) if total_shares > 0 else max(0, post_trade_drift)
        
        return CostBreakdown(
            spread=spread_cost,
            temporary=temp_impact,
            permanent=perm_impact,
            opportunity=opportunity_cost,
            adverse_selection=adverse_selection
        )
