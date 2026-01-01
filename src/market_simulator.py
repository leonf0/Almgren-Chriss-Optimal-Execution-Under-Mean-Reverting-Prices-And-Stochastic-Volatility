import numpy as np
from src.data_structures import MarketState
from src.market_components import HestonVolatility, RegimeDetector

class MarketSimulator:   
    def __init__(self, S0=100.0, base_vol=0.02, base_spread=0.02, base_depth=10000, 
                 base_adv=1000000, impact_gamma=0.1, impact_alpha=0.65, seed=None):
        if seed is not None:
            np.random.seed(seed)
        
        self.S0 = S0
        self.price = S0
        self.base_vol = base_vol
        self.base_spread = base_spread
        self.base_depth = base_depth
        self.base_adv = base_adv
        self.impact_gamma = impact_gamma
        self.impact_alpha = impact_alpha
        
        self.vol_per_minute = base_vol / np.sqrt(390)
        
        self.vol_model = HestonVolatility(
            v0=(self.vol_per_minute)**2,
            kappa=3.0,
            theta=(self.vol_per_minute)**2,
            sigma_v=0.3,
            rho=-0.7
        )
        
        self.regime_detector = RegimeDetector()
        self.current_time = 0
        self.current_minute = 0
        self.scenario = None
        self.scenario_duration = 0
        
        self.cumulative_perm_impact = 0.0
        
    def _intraday_volume_pattern(self, minute_of_day):
        t = minute_of_day / 390
        u_shape = 1.0 + abs(t - 0.5)
        return self.base_adv / 390 * u_shape
    
    def _intraday_spread_pattern(self, minute_of_day):
        t = minute_of_day / 390
        spread_multiplier = 1.2 - 0.4 * abs(t - 0.5)
        return self.base_spread * spread_multiplier
    
    def step(self, dt=1/390, external_order_size=0) -> MarketState:
        self.current_time += dt
        self.current_minute += 1
        
        expected_volume = self._intraday_volume_pattern(self.current_minute % 390)
        base_spread = self._intraday_spread_pattern(self.current_minute % 390)
        current_vol = self.vol_model.step(dt)
        
        if self.scenario and self.scenario_duration > 0:
            current_vol *= self.scenario.get('vol_multiplier', 1.0)
            base_spread *= self.scenario.get('spread_multiplier', 1.0)
            expected_volume *= self.scenario.get('volume_multiplier', 1.0)
            self.scenario_duration -= 1
        
        kappa = 0.5
        theta = self.S0
        dW = np.random.normal(0, np.sqrt(dt))
        
        drift = 0
        if self.scenario and self.scenario.get('type') == 'momentum':
            drift = self.scenario.get('drift_rate', 0) * self.price * dt
        
        dP = kappa * (theta - self.price) * dt + current_vol * self.price * dW + drift
        self.price += dP
        
        impact = 0
        if external_order_size != 0:
            participation = abs(external_order_size) / max(expected_volume, 1)
            impact = self.impact_gamma * (participation ** self.impact_alpha) * current_vol * self.price
            self.price += np.sign(external_order_size) * impact
        
        spread = base_spread * (1 + 1.5 * current_vol / self.vol_per_minute)
        if abs(external_order_size) > 0:
            spread *= (1 + 0.5 * participation)
        
        depth = self.base_depth / (1 + 0.5 * abs(external_order_size) / max(expected_volume, 1))
        
        regime = self.regime_detector.classify(current_vol, spread / self.price, expected_volume)
        
        state = MarketState(
            time=self.current_time,
            mid_price=self.price,
            bid=self.price - spread / 2,
            ask=self.price + spread / 2,
            bid_depth=depth,
            ask_depth=depth,
            volume=expected_volume,
            volatility=current_vol,
            regime=regime.composite
        )
        
        return state
    
    def inject_scenario(self, scenario_type: str):
        if scenario_type == 'flash_crash':
            self.scenario = {
                'type': 'flash_crash',
                'vol_multiplier': 10.0,
                'spread_multiplier': 5.0,
                'volume_multiplier': 0.3,
                'duration': 10
            }
            self.scenario_duration = 10
        elif scenario_type == 'momentum':
            self.scenario = {
                'type': 'momentum',
                'drift_rate': 0.0005,
                'duration': 9999
            }
            self.scenario_duration = 9999
        elif scenario_type == 'liquidity_drought':
            self.scenario = {
                'type': 'liquidity_drought',
                'volume_multiplier': 0.1,
                'spread_multiplier': 2.0,
                'duration': 30
            }
            self.scenario_duration = 30
    
    def reset(self):
        self.price = self.S0
        self.vol_model = HestonVolatility(
            v0=(self.vol_per_minute)**2,
            kappa=3.0,
            theta=(self.vol_per_minute)**2,
            sigma_v=0.3,
            rho=-0.7
        )
        self.regime_detector = RegimeDetector()
        self.current_time = 0
        self.current_minute = 0
        self.scenario = None
        self.scenario_duration = 0
        self.cumulative_perm_impact = 0.0
