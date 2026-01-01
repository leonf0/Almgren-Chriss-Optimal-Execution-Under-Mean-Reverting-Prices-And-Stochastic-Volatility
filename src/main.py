from src.config import config
from src.experiments import run_experiment_1_monte_carlo_validation, run_experiment_2_stress_scenarios, run_experiment_3_robustness_analysis
from src.analyser import MonteCarloAnalyzer

def run_all_monte_carlo_experiments():
    
    print(f"  Simulations per experiment: {config.n_simulations}")
    print(f"  Quick simulations: {config.n_simulations_quick}")
    print(f"  Order size: {config.order_size:,} shares")
    print(f"  Execution window: {config.execution_periods} periods (2 hours)")
    print(f"  Temp impact half-life: {config.temp_impact_half_life} periods")
    
    exp1_results = run_experiment_1_monte_carlo_validation()
    exp2_results = run_experiment_2_stress_scenarios()
    exp3_results = run_experiment_3_robustness_analysis()
    
    summary_df = MonteCarloAnalyzer.create_summary_table(exp1_results)
    best_idx = summary_df['Mean (bp)'].idxmin()
    worst_idx = summary_df['Mean (bp)'].idxmax()
    
    best_strat = summary_df.loc[best_idx, 'Strategy']
    best_mean = summary_df.loc[best_idx, 'Mean (bp)']
    best_std = summary_df.loc[best_idx, 'Std (bp)']
    
    worst_strat = summary_df.loc[worst_idx, 'Strategy']
    worst_mean = summary_df.loc[worst_idx, 'Mean (bp)']
    worst_std = summary_df.loc[worst_idx, 'Std (bp)']
    
    print(f"\nBest Strategy (Normal Market):")
    print(f"   {best_strat}: {best_mean:.2f} ± {best_std:.2f} bp")
    print(f"   Worst: {worst_strat}: {worst_mean:.2f} ± {worst_std:.2f} bp")
    print(f"   Improvement: {((worst_mean - best_mean) / worst_mean * 100):.1f}%")
    
    most_robust_idx = summary_df['Std (bp)'].idxmin()
    robust_strat = summary_df.loc[most_robust_idx, 'Strategy']
    robust_std = summary_df.loc[most_robust_idx, 'Std (bp)']
    
    print(f"\nMost Robust Strategy (Lowest Variance):")
    print(f"   {robust_strat}: Std = {robust_std:.2f} bp")
    
    flash_results = exp2_results['flash_crash']
    flash_summary = MonteCarloAnalyzer.create_summary_table(flash_results)
    best_flash_idx = flash_summary['Mean (bp)'].idxmin()
    best_flash = flash_summary.loc[best_flash_idx, 'Strategy']
    best_flash_cost = flash_summary.loc[best_flash_idx, 'Mean (bp)']
    
    print(f"\nBest in Flash Crash:")
    print(f"   {best_flash}: {best_flash_cost:.2f} bp")
    
    return {
        'exp1': exp1_results,
        'exp2': exp2_results,
        'exp3': exp3_results
    }

if __name__ == "__main__":
    all_results = run_all_monte_carlo_experiments()
