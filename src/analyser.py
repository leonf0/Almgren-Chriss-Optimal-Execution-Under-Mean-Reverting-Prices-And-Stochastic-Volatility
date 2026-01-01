import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict
from src.data_structures import MonteCarloResults

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class MonteCarloAnalyzer:
    @staticmethod
    def create_summary_table(mc_results: Dict[str, MonteCarloResults]) -> pd.DataFrame:
        rows = []
        
        for name, result in mc_results.items():
            rows.append({
                'Strategy': name,
                'Mean (bp)': result.mean_cost,
                'Std (bp)': result.std_cost,
                'Median (bp)': result.median_cost,
                '5th Pct (bp)': result.percentile_5,
                '95th Pct (bp)': result.percentile_95,
                'VaR 95% (bp)': result.value_at_risk_95,
                'Risk-Adjusted Savings': result.risk_adjusted_savings,
                'N Sims': result.n_simulations
            })
        
        return pd.DataFrame(rows)
    
    @staticmethod
    def create_component_table(mc_results: Dict[str, MonteCarloResults]) -> pd.DataFrame:
        rows = []
        
        for name, result in mc_results.items():
            rows.append({
                'Strategy': name,
                'Spread (bp)': result.mean_spread,
                'Temp Impact (bp)': result.mean_temp_impact,
                'Perm Impact (bp)': result.mean_perm_impact,
                'Impl Shortfall (bp)': result.mean_opportunity,
                'Adverse Sel (bp)': result.mean_adverse,
                'Total (bp)': result.mean_cost
            })
        
        return pd.DataFrame(rows)
    
    @staticmethod
    def plot_distributions(mc_results: Dict[str, MonteCarloResults], save_path: str = None):
        fig, axes = plt.subplots(2, 1, figsize=(12, 10))
        
        data_for_violin = []
        labels = []
        for name, result in mc_results.items():
            data_for_violin.append(result.costs_bps)
            labels.append(name)
        
        parts = axes[0].violinplot(data_for_violin, positions=range(len(labels)), 
                                    showmeans=True, showmedians=True, widths=0.7)
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        for i, pc in enumerate(parts['bodies']):
            pc.set_facecolor(colors[i])
            pc.set_alpha(0.7)
        
        axes[0].set_xticks(range(len(labels)))
        axes[0].set_xticklabels(labels, rotation=45, ha='right')
        axes[0].set_ylabel('Cost (basis points)', fontsize=11)
        axes[0].set_title('Cost Distribution by Strategy (Violin Plot)', fontsize=12, fontweight='bold')
        axes[0].grid(axis='y', alpha=0.3)
        
        bp = axes[1].boxplot(data_for_violin, labels=labels, patch_artist=True, showfliers=False)
        
        for i, patch in enumerate(bp['boxes']):
            patch.set_facecolor(colors[i])
            patch.set_alpha(0.7)
        
        for i, (name, result) in enumerate(mc_results.items()):
            y = result.costs_bps
            if len(y) > 100:
                indices = np.random.choice(len(y), 100, replace=False)
                y = [y[idx] for idx in indices]
            
            x = np.random.normal(i + 1, 0.04, size=len(y))
            axes[1].scatter(x, y, alpha=0.3, s=10, color=colors[i])
        
        axes[1].set_xticklabels(labels, rotation=45, ha='right')
        axes[1].set_ylabel('Cost (basis points)', fontsize=11)
        axes[1].set_title('Cost Distribution by Strategy (Box Plot + Sample Points)', fontsize=12, fontweight='bold')
        axes[1].grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.show()
        plt.close(fig)
        
        return fig
    
    @staticmethod
    def plot_cost_decomposition_with_ci(mc_results: Dict[str, MonteCarloResults]):
        strategies = list(mc_results.keys())
        
        fig, ax = plt.subplots(figsize=(12, 7))
        
        x = np.arange(len(strategies))
        
        component_data = {
            'Spread': [mc_results[s].mean_spread for s in strategies],
            'Temp Impact': [mc_results[s].mean_temp_impact for s in strategies],
            'Perm Impact': [mc_results[s].mean_perm_impact for s in strategies],
            'Impl Shortfall': [mc_results[s].mean_opportunity for s in strategies],
            'Adverse Sel': [mc_results[s].mean_adverse for s in strategies],
        }
        
        bottom = np.zeros(len(strategies))
        colors = plt.cm.Set2(np.linspace(0, 1, len(component_data)))
        
        for i, (comp, values) in enumerate(component_data.items()):
            ax.bar(x, values, width=0.7, bottom=bottom, label=comp, 
                   color=colors[i], alpha=0.8, edgecolor='black', linewidth=0.5)
            bottom += values
        
        total_means = [mc_results[s].mean_cost for s in strategies]
        ci_lower = [mc_results[s].percentile_5 for s in strategies]
        ci_upper = [mc_results[s].percentile_95 for s in strategies]
        
        errors_lower = [mean - lower for mean, lower in zip(total_means, ci_lower)]
        errors_upper = [upper - mean for mean, upper in zip(total_means, ci_upper)]
        
        ax.errorbar(x, total_means, yerr=[errors_lower, errors_upper],
                    fmt='none', ecolor='black', capsize=5, capthick=2, 
                    linewidth=2, label='95% CI')
        
        ax.set_ylabel('Cost (basis points)', fontsize=11)
        ax.set_xlabel('Strategy', fontsize=11)
        ax.set_title('Mean Cost Decomposition with 95% Confidence Intervals', 
                     fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(strategies, rotation=45, ha='right')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
  
        return fig
    
    @staticmethod
    def plot_performance_comparison(mc_results: Dict[str, MonteCarloResults]):
        strategies = list(mc_results.keys())
        means = [mc_results[s].mean_cost for s in strategies]
        stds = [mc_results[s].std_cost for s in strategies]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(len(strategies))
        bars = ax.bar(x, means, yerr=stds, capsize=10, alpha=0.7, 
                      edgecolor='black', linewidth=1.5, error_kw={'linewidth': 2})
        
        colors = plt.cm.RdYlGn_r(np.linspace(0.3, 0.9, len(strategies)))
        sorted_indices = np.argsort(means)
        for i, bar in enumerate(bars):
            bar.set_color(colors[np.where(sorted_indices == i)[0][0]])
        
        ax.set_ylabel('Mean Cost (basis points)', fontsize=11)
        ax.set_xlabel('Strategy', fontsize=11)
        ax.set_title('Strategy Performance Comparison (Mean ± 1 Std Dev)', 
                     fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(strategies, rotation=45, ha='right')
        ax.grid(axis='y', alpha=0.3)
        
        for i, (mean, std) in enumerate(zip(means, stds)):
            ax.text(i, mean + std + 0.5, f'{mean:.1f}', 
                   ha='center', va='bottom', fontweight='bold', fontsize=9)
        
        plt.tight_layout()
        
        return fig
    
    @staticmethod
    def plot_sharpe_ratios(mc_results: Dict[str, MonteCarloResults]):
        strategies = [s for s in mc_results.keys() if s != 'TWAP' and mc_results[s].risk_adjusted_savings != 0]
        sharpes = [mc_results[s].risk_adjusted_savings for s in strategies]
        
        if not strategies:
            print("  [INFO] No Sharpe ratios to plot (need TWAP baseline)")
            return None
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(len(strategies))
        bars = ax.bar(x, sharpes, alpha=0.7, edgecolor='black', linewidth=1.5)
        
        for i, (bar, sharpe) in enumerate(zip(bars, sharpes)):
            if sharpe > 0:
                bar.set_color('green')
            else:
                bar.set_color('red')
        
        ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
        ax.set_ylabel('Risk-Adjusted Savings vs TWAP', fontsize=11)
        ax.set_xlabel('Strategy', fontsize=11)
        ax.set_title('Risk-Adjusted Performance', 
                     fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(strategies, rotation=45, ha='right')
        ax.grid(axis='y', alpha=0.3)
        
        for i, sharpe in enumerate(sharpes):
            ax.text(i, sharpe + 0.05, f'{sharpe:.2f}', 
                   ha='center', va='bottom' if sharpe > 0 else 'top', 
                   fontweight='bold', fontsize=9)
        
        plt.tight_layout()
        
        return fig
    
    @staticmethod
    def plot_stress_comparison(normal_results: Dict[str, MonteCarloResults],
                               stress_results: Dict[str, MonteCarloResults],
                               scenario_name: str):

        strategies = list(normal_results.keys())
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        x = np.arange(len(strategies))
        width = 0.35
        
        normal_means = [normal_results[s].mean_cost for s in strategies]
        stress_means = [stress_results[s].mean_cost for s in strategies]
        
        axes[0].bar(x - width/2, normal_means, width, label='Normal', 
                   alpha=0.7, edgecolor='black')
        axes[0].bar(x + width/2, stress_means, width, label=scenario_name, 
                   alpha=0.7, edgecolor='black')
        
        axes[0].set_ylabel('Mean Cost (bp)', fontsize=11)
        axes[0].set_xlabel('Strategy', fontsize=11)
        axes[0].set_title('Mean Cost: Normal vs Stress', fontsize=12, fontweight='bold')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(strategies, rotation=45, ha='right')
        axes[0].legend()
        axes[0].grid(axis='y', alpha=0.3)
        
        relative_increase = [(stress - normal) / normal * 100 
                            for normal, stress in zip(normal_means, stress_means)]
        
        bars = axes[1].bar(x, relative_increase, alpha=0.7, edgecolor='black', linewidth=1.5)
        
        for i, (bar, val) in enumerate(zip(bars, relative_increase)):
            if val < 50:
                bar.set_color('green')
            elif val < 150:
                bar.set_color('orange')
            else:
                bar.set_color('red')
        
        axes[1].axhline(y=0, color='black', linestyle='--', linewidth=1)
        axes[1].set_ylabel('Cost Increase (%)', fontsize=11)
        axes[1].set_xlabel('Strategy', fontsize=11)
        axes[1].set_title(f'Relative Cost Increase in {scenario_name}', 
                         fontsize=12, fontweight='bold')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(strategies, rotation=45, ha='right')
        axes[1].grid(axis='y', alpha=0.3)
        
        for i, val in enumerate(relative_increase):
            axes[1].text(i, val + 5, f'{val:.0f}%', 
                        ha='center', va='bottom', fontweight='bold', fontsize=9)
        
        plt.tight_layout()
        
        return fig
    
    @staticmethod
    def plot_trajectory_comparison(mc_results: Dict[str, MonteCarloResults]):
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for name, result in mc_results.items():

            if result.all_results:
                trajectories = [r.trajectory for r in result.all_results]
                T = len(trajectories[0])
                avg_trajectory = np.mean(trajectories, axis=0)
                std_trajectory = np.std(trajectories, axis=0)
                
                #normalize to cumulative percentage
                cumsum = np.cumsum(avg_trajectory)
                total = cumsum[-1]
                pct_complete = cumsum / total * 100
                
                ax.plot(range(T), pct_complete, label=name, linewidth=2)
        
        ax.set_xlabel('Period', fontsize=11)
        ax.set_ylabel('Cumulative % Executed', fontsize=11)
        ax.set_title('Average Execution Trajectory by Strategy', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)
        ax.set_ylim([0, 105])
        
        plt.tight_layout()
        
        return fig
