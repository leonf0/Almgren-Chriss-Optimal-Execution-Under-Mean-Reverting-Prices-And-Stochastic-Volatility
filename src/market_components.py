import numpy as np
from collections import deque
from scipy import stats
from src.data_structures import Regime

class HestonVolatility:
    def __init__(self, v0=0.0004, kappa=3.0, theta=0.0004, sigma_v=0.3, rho=-0.7):
        self.v = v0
        self.kappa = kappa
        self.theta = theta
        self.sigma_v = sigma_v
        self.rho = rho
        
    def step(self, dt=1/390):
        dW = np.random.normal(0, np.sqrt(dt))
        v_plus = max(self.v, 0)
        dv = self.kappa * (self.theta - v_plus) * dt + self.sigma_v * np.sqrt(v_plus) * dW
        self.v = max(self.v + dv, 0)
        return np.sqrt(self.v)
    
    def get_volatility(self):
        return np.sqrt(max(self.v, 0))

class RegimeDetector: 
    def __init__(self, window_size=20, vol_thresholds=(25, 75), 
                 spread_thresholds=(25, 75), volume_thresholds=(25, 75)):
        self.window_size = window_size
        self.vol_thresholds = vol_thresholds
        self.spread_thresholds = spread_thresholds
        self.volume_thresholds = volume_thresholds
        
        self.vol_history = deque(maxlen=window_size)
        self.spread_history = deque(maxlen=window_size)
        self.volume_history = deque(maxlen=window_size)
        
    def classify(self, volatility: float, spread: float, volume: float) -> Regime:
        self.vol_history.append(volatility)
        self.spread_history.append(spread)
        self.volume_history.append(volume)
        
        if len(self.vol_history) < 5:
            return Regime('medium', 'normal', 'normal')
        
        vol_pct = self._percentile(volatility, self.vol_history)
        spread_pct = self._percentile(spread, self.spread_history)
        volume_pct = self._percentile(volume, self.volume_history)
        
        vol_regime = self._bin(vol_pct, self.vol_thresholds)
        spread_regime = self._bin(spread_pct, self.spread_thresholds)
        volume_regime = self._bin(volume_pct, self.volume_thresholds)
        
        return Regime(vol_regime, spread_regime, volume_regime)
    
    def _percentile(self, value, history):
        if len(history) < 2:
            return 50.0
        return stats.percentileofscore(list(history), value)
    
    def _bin(self, percentile, thresholds):
        if percentile < thresholds[0]:
            return 'low' if thresholds == self.vol_thresholds else 'tight' if thresholds == self.spread_thresholds else 'thin'
        elif percentile > thresholds[1]:
            return 'high' if thresholds == self.vol_thresholds else 'wide' if thresholds == self.spread_thresholds else 'heavy'
        else:
            return 'medium' if thresholds == self.vol_thresholds else 'normal'
