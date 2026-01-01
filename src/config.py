import numpy as np
import pandas as pd

base_seed = 42

class MonteCarloConfig:
    
    n_simulations = 1000  
    n_simulations_quick = 300
    
    base_price = 100.0
    base_vol = 0.02  
    base_spread = 0.02  
    base_depth = 10000  
    base_adv = 1000000 
    
    
    
    temp_gamma = 0.1      # dimensionless scaling
    temp_alpha = 0.65     # concavity 
    
    perm_eta = 0.03       
    perm_beta = 0.42      
    
    temp_impact_half_life = 10.0  
    
    order_size = 100000   
    execution_periods = 120  

    vol_perturbation = 0.3    
    spread_perturbation = 0.5  
    depth_perturbation = 0.4   
    
    confidence_level = 0.95  
    percentiles = [5, 25, 50, 75, 95] 

config = MonteCarloConfig()
