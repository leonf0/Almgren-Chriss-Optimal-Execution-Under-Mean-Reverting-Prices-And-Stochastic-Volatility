from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional

@dataclass
class MarketState:
    time: float
    mid_price: float
    bid: float
    ask: float
    bid_depth: float
    ask_depth: float
    volume: float
    volatility: float
    regime: str = "normal"
    
    @property
    def spread(self):
        return self.ask - self.bid

@dataclass
class Regime:
    volatility: str  # 'low', 'medium', 'high'
    spread: str      # 'tight', 'normal', 'wide'
    volume: str      # 'thin', 'normal', 'heavy'
    
    @property
    def composite(self):
        return f"{self.volatility}_{self.spread}_{self.volume}"

@dataclass
class CostBreakdown:
    spread: float
    temporary: float
    permanent: float
    opportunity: float       
    adverse_selection: float
    
    @property
    def total(self):
        return self.spread + self.temporary + self.permanent + self.adverse_selection
    
    def total_bps(self, notional: float):
        return (self.total / notional) * 10000 if notional > 0 else 0

@dataclass
class ExecutionResult:
    strategy: str
    trajectory: List[float]
    market_states: List[MarketState]
    costs: CostBreakdown
    metrics: Dict
    simulation_id: int = 0
    arrival_price: float = 0.0  

@dataclass
class MonteCarloResults:
    strategy: str
    n_simulations: int
    costs_bps: List[float]  
    
    mean_cost: float
    std_cost: float
    median_cost: float
    percentile_5: float
    percentile_95: float
    
    risk_adjusted_savings: float  # (Expected savings vs TWAP) / std
    value_at_risk_95: float  # 95th percentile cost
    
    mean_spread: float
    mean_temp_impact: float
    mean_perm_impact: float
    mean_opportunity: float  
    mean_adverse: float    
    
    all_results: List[ExecutionResult]
