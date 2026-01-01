import numpy as np
from typing import List
from src.data_structures import MarketState, ExecutionResult
from src.market_simulator import MarketSimulator
from src.impact_models import CostModel

class BaseStrategy:
    def __init__(self, name: str):
        self.name = name
    
    def generate_trajectory(self, total_size: float, T: int, states: List[MarketState] = None) -> List[float]:
        raise NotImplementedError
    
    def execute(self, total_size: float, T: int, market_sim: MarketSimulator, 
                cost_model: CostModel, simulation_id: int = 0) -> ExecutionResult:
        arrival_price = market_sim.price 
        
        trajectory = self.generate_trajectory(total_size, T)
        states = []
        for n_t in trajectory:
            state = market_sim.step(dt=1/390, external_order_size=n_t)
            states.append(state)
        
        costs = cost_model.compute_costs(trajectory, states, arrival_price)
        
        notional = arrival_price * total_size
        metrics = {
            'total_cost_bps': costs.total_bps(notional),
            'avg_participation': np.mean([
                abs(n)/s.volume for n, s in zip(trajectory, states) if s.volume > 0
            ]),
            'execution_periods': len([n for n in trajectory if n != 0]),
            'arrival_price': arrival_price,
            'final_price': states[-1].mid_price if states else arrival_price,
        }
        
        return ExecutionResult(
            strategy=self.name,
            trajectory=trajectory,
            market_states=states,
            costs=costs,
            metrics=metrics,
            simulation_id=simulation_id,
            arrival_price=arrival_price
        )

class NaiveStrategy(BaseStrategy):
    #Executes entire order immediately
    def __init__(self):
        super().__init__("Naive")
    
    def generate_trajectory(self, total_size: float, T: int, states=None) -> List[float]:
        trajectory = [0.0] * T
        trajectory[0] = total_size
        return trajectory

class TWAPStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("TWAP")
    
    def generate_trajectory(self, total_size: float, T: int, states=None) -> List[float]:
        per_period = total_size / T
        return [per_period] * T

class VWAPStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("VWAP")
    
    def _forecast_volume_profile(self, T):
        t = np.linspace(0, 1, T)

        # U-shape: high (1) at open/close, low (2) mid-day.
        u_shape = 1.0 + np.abs(t - 0.5)
        return u_shape
    
    def generate_trajectory(self, total_size: float, T: int, states=None) -> List[float]:
        profile = self._forecast_volume_profile(T)
        weights = profile / np.sum(profile)
        trajectory = (total_size * weights).tolist()
        
        # Ensure exact sum
        actual_sum = sum(trajectory)
        if abs(actual_sum - total_size) > 1e-6:
            trajectory = [n * total_size / actual_sum for n in trajectory]
        
        return trajectory

class AlmgrenChrissStrategy(BaseStrategy):
    def __init__(self, urgency=3.0):
        super().__init__("Almgren-Chriss")
        self.urgency = urgency  # kappa * T 
        
    def generate_trajectory(self, total_size: float, T: int, states=None) -> List[float]:

        urgency = max(0.1, min(self.urgency, 10.0))
        kappa = urgency / T
        
        trajectory = []
        sinh_kappa_T = np.sinh(urgency)  
        
        for t in range(T):
            if t == T - 1:
                remaining = total_size - sum(trajectory)
                trajectory.append(remaining)
            else:
                X_t = total_size * np.sinh(kappa * (T - t)) / sinh_kappa_T
                X_t_plus_1 = total_size * np.sinh(kappa * (T - t - 1)) / sinh_kappa_T
                
                n_t = X_t - X_t_plus_1
                trajectory.append(max(0, n_t))  
        
        actual_sum = sum(trajectory)
        if abs(actual_sum - total_size) > 1e-6 and actual_sum > 0:
            trajectory = [n * total_size / actual_sum for n in trajectory]
        
        return trajectory
