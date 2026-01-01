import matplotlib.pyplot as plt
from src.config import config
from src.monte_carlo import MonteCarloSimulator
from src.strategies import NaiveStrategy, TWAPStrategy, VWAPStrategy, AlmgrenChrissStrategy
from src.analyser import MonteCarloAnalyzer

def run_experiment_1_monte_carlo_validation():
    print("Experiment 1: Validation")
    print(f"Running {config.n_simulations} simulations per strategy...")
    
    mc_sim = MonteCarloSimulator(config)
    
    strategies = [
        NaiveStrategy(),
        TWAPStrategy(),
        VWAPStrategy(),
        AlmgrenChrissStrategy()
    ]
    
    def progress(msg):
        print(f"  {msg}")
    
    mc_results = mc_sim.run_monte_carlo(strategies, config.n_simulations, 
                                        scenario=None, progress_callback=progress)
    
    print("Summary:")
    summary_df = MonteCarloAnalyzer.create_summary_table(mc_results)
    print(summary_df.to_string(index=False))
    
    print("\nCost Component Breakdown")
    
    component_df = MonteCarloAnalyzer.create_component_table(mc_results)
    print(component_df.to_string(index=False))
    
    print("\nGenerating visualizations...")
    
    MonteCarloAnalyzer.plot_distributions(
        mc_results
    )
    
    MonteCarloAnalyzer.plot_cost_decomposition_with_ci(
        mc_results
    )
    
    MonteCarloAnalyzer.plot_performance_comparison(
        mc_results
    )
    
    MonteCarloAnalyzer.plot_sharpe_ratios(
        mc_results
    )
    
    MonteCarloAnalyzer.plot_trajectory_comparison(
        mc_results
    )
    
    print("\nExperiment 1 complete")

    
    return mc_results

def run_experiment_2_stress_scenarios():   
    print("Experiment 2: Stress Test")
    print(f"Running {config.n_simulations_quick} simulations per strategy per scenario...")
    
    mc_sim = MonteCarloSimulator(config)
    
    strategies = [
        NaiveStrategy(),
        TWAPStrategy(),
        VWAPStrategy(),
        AlmgrenChrissStrategy()
    ]
    
    scenarios = {
        'normal': None,
        'flash_crash': 'flash_crash',
        'momentum': 'momentum',
        'liquidity_drought': 'liquidity_drought'
    }
    
    all_scenario_results = {}
    
    for scenario_name, scenario_type in scenarios.items():
        print(f"Scenario: {scenario_name.upper()}")
        
        def progress(msg):
            print(f"  {msg}")
        
        mc_results = mc_sim.run_monte_carlo(
            strategies, 
            config.n_simulations_quick, 
            scenario=scenario_type,
            progress_callback=progress
        )
        
        all_scenario_results[scenario_name] = mc_results
        
        print(f"\n  Mean costs:")
        for name, result in mc_results.items():
            print(f"    {name}: {result.mean_cost:.2f} bp (±{result.std_cost:.2f})")
    
    print("Stress Scenario Analysis")
    
    for scenario_name in ['flash_crash', 'momentum', 'liquidity_drought']:
        print(f"\n{scenario_name.upper()} vs NORMAL:")
        
        normal_results = all_scenario_results['normal']
        stress_results = all_scenario_results[scenario_name]
        
        for strat in strategies:
            normal_mean = normal_results[strat.name].mean_cost
            stress_mean = stress_results[strat.name].mean_cost
            increase_pct = (stress_mean - normal_mean) / normal_mean * 100
            
            print(f"  {strat.name}: {normal_mean:.1f} → {stress_mean:.1f} bp (+{increase_pct:.0f}%)")
    
    print("\nGenerating comparative visualizations...")
    
    for scenario_name in ['flash_crash', 'momentum', 'liquidity_drought']:
        MonteCarloAnalyzer.plot_stress_comparison(
            all_scenario_results['normal'],
            all_scenario_results[scenario_name],
            scenario_name
        )
    
    for scenario_name, mc_results in all_scenario_results.items():
        summary_df = MonteCarloAnalyzer.create_summary_table(mc_results)
    
    print("\nExperiment 2 complete!")
    
    return all_scenario_results

def run_experiment_3_robustness_analysis():

    print("Experiment 3: Robustness Analysis")
    print("\nTesting sensitivity to order size...")
    
    mc_sim = MonteCarloSimulator(config)
    
    strategies = [
        TWAPStrategy(),
        VWAPStrategy(),
        AlmgrenChrissStrategy()
    ]
    
    order_sizes = [50000, 100000, 200000]
    
    results_by_size = {}
    
    for size in order_sizes:
        print(f"\nTesting order size: {size:,} ({size/config.base_adv*100:.0f}% of ADV)")
        
        original_size = config.order_size
        config.order_size = size
        
        def progress(msg):
            print(f"  {msg}")
        
        mc_results = mc_sim.run_monte_carlo(
            strategies,
            config.n_simulations_quick,
            scenario=None,
            progress_callback=progress
        )
        
        results_by_size[size] = mc_results
        
        config.order_size = original_size
        
        print(f"  Mean costs:")
        for name, result in mc_results.items():
            print(f"    {name}: {result.mean_cost:.2f} bp")
    fig, ax = plt.subplots(figsize=(10, 6))
 
    for strat in strategies:
        sizes = list(order_sizes)
        costs = [results_by_size[s][strat.name].mean_cost for s in sizes]
        ax.plot(sizes, costs, marker='o', markersize=8, linewidth=2, label=strat.name)

    ax.set_xlabel('Order Size (shares)', fontsize=11)
    ax.set_ylabel('Mean Cost (bp)', fontsize=11)
    ax.set_title('Cost vs Order Size (Robustness Analysis)', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    plt.close(fig)
    
    print("\nExperiment 3 complete!")
    
    return results_by_size
