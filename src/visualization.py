"""
Visualization - Generates plots and charts for benchmark results.
"""
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import matplotlib, but make it optional
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    logger.warning("matplotlib not available - visualization will be skipped")
    MATPLOTLIB_AVAILABLE = False


class Visualizer:
    """
    Generates visualizations for benchmark results.
    """

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = reports_dir
        self._ensure_reports_dir()

    def _ensure_reports_dir(self):
        """Ensure the reports directory exists."""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
            logger.info(f"Created reports directory: {self.reports_dir}")

    def is_available(self) -> bool:
        """Check if visualization is available."""
        return MATPLOTLIB_AVAILABLE

    def plot_throughput_comparison(
        self,
        aggregated_results: Dict,
        title: str = "Total Token Throughput Comparison",
        filename: str = "throughput_comparison.png",
    ) -> Optional[str]:
        """
        Create a bar chart comparing total token throughput across configurations.

        Args:
            aggregated_results: Dictionary of AggregatedResult objects
            title: Plot title
            filename: Output filename

        Returns:
            Path to the saved plot, or None if visualization failed
        """
        if not self.is_available():
            logger.warning("Cannot create plot - matplotlib not available")
            return None

        if not aggregated_results:
            logger.warning("No aggregated results to plot")
            return None

        try:
            # Prepare data
            results_list = list(aggregated_results.values())

            # Create labels (model + concurrency + image info)
            labels = []
            for agg in results_list:
                model_name = os.path.basename(agg.model_path) if agg.model_path else "unknown"
                img_info = f", {agg.image_size or '-'}, {agg.image_count or '-'}"
                label = f"{model_name}\nconc={agg.max_concurrency or '?'}{img_info}"
                labels.append(label)

            x_pos = np.arange(len(labels))
            throughputs = [agg.avg_total_token_throughput for agg in results_list]
            std_devs = [agg.std_total_token_throughput for agg in results_list]

            # Create figure - slimmer width
            plt.figure(figsize=(max(6, len(labels) * 1.2), 6))

            # Plot bars with error bars
            bars = plt.bar(
                x_pos,
                throughputs,
                yerr=std_devs,
                capsize=8,
                alpha=0.7,
                color='steelblue',
                edgecolor='navy',
            )

            # Add value labels on top of bars
            for i, bar in enumerate(bars):
                height = bar.get_height()
                plt.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height + (max(throughputs) * 0.01 if throughputs else 1),
                    f'{height:.1f}',
                    ha='center',
                    va='bottom',
                    fontweight='bold',
                )

            # Customize plot
            plt.xlabel('Configuration', fontsize=12, fontweight='bold')
            plt.ylabel('Total Token Throughput (tok/s)', fontsize=12, fontweight='bold')
            plt.title(title, fontsize=14, fontweight='bold', pad=20)
            plt.xticks(x_pos, labels, fontsize=9, rotation=45, ha='right')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.ylim(bottom=0, top=max(throughputs) * 1.15 if throughputs else None)

            # Adjust layout
            plt.tight_layout()

            # Save figure
            filepath = os.path.join(self.reports_dir, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()

            logger.info(f"Saved throughput comparison plot to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to create throughput plot: {e}")
            plt.close()
            return None

    def plot_group_individual_results(
        self,
        group_result,
        group_idx: int,
        title: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a plot showing (service, case) results within a single group.

        Args:
            group_result: GroupResult object with service_case_results
            group_idx: Index of this group (for filename)
            title: Optional plot title
            filename: Optional output filename

        Returns:
            Path to the saved plot, or None if visualization failed
        """
        if not self.is_available():
            logger.warning("Cannot create plot - matplotlib not available")
            return None

        if not group_result or not group_result.service_case_results:
            logger.warning("No service case results to plot")
            return None

        try:
            results = group_result.service_case_results

            # Prepare data
            x_pos = np.arange(len(results))
            throughputs = [r.avg_total_token_throughput for r in results]
            labels = [f"{i}" for i in range(len(results))]

            # Create figure - slimmer width
            plt.figure(figsize=(max(6, len(results) * 0.8), 5))

            # Plot bars
            bars = plt.bar(
                x_pos,
                throughputs,
                alpha=0.7,
                color='coral',
                edgecolor='darkred',
            )

            # Add value labels on top of bars
            for i, bar in enumerate(bars):
                height = bar.get_height()
                plt.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height + (max(throughputs) * 0.01 if throughputs else 1),
                    f'{height:.1f}',
                    ha='center',
                    va='bottom',
                    fontweight='bold',
                    fontsize=9,
                )

            # Customize plot
            if title is None:
                model_name = os.path.basename(group_result.group_key.model_path) if group_result.group_key.model_path else "unknown"
                title = (f"Group {group_idx}: {model_name}\n"
                        f"TP={group_result.group_key.deploy_method}, "
                        f"In={group_result.group_key.input_len}, "
                        f"Out={group_result.group_key.output_len}, "
                        f"Conc={group_result.group_key.max_concurrency}")

            plt.xlabel('Configuration Index (idx)', fontsize=11, fontweight='bold')
            plt.ylabel('Total Token Throughput (tok/s)', fontsize=11, fontweight='bold')
            plt.title(title, fontsize=12, fontweight='bold', pad=15)
            plt.xticks(x_pos, labels, fontsize=9, rotation=30, ha='right')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.ylim(bottom=0, top=max(throughputs) * 1.12 if throughputs else None)

            # Adjust layout
            plt.tight_layout()

            # Save figure
            if filename is None:
                filename = f"group_{group_idx}_results.png"

            filepath = os.path.join(self.reports_dir, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()

            logger.info(f"Saved group results plot to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to create group results plot: {e}")
            plt.close()
            return None

    def plot_latency_metrics(
        self,
        aggregated_results: Dict,
        title: str = "Latency Metrics",
        filename: str = "latency_metrics.png",
    ) -> Optional[str]:
        """
        Create a plot showing TTFT and TPOT latency metrics.

        Args:
            aggregated_results: Dictionary of AggregatedResult objects
            title: Plot title
            filename: Output filename

        Returns:
            Path to the saved plot, or None if visualization failed
        """
        if not self.is_available():
            logger.warning("Cannot create plot - matplotlib not available")
            return None

        if not aggregated_results:
            logger.warning("No aggregated results to plot")
            return None

        try:
            results_list = list(aggregated_results.values())

            # Create labels
            labels = []
            for agg in results_list:
                model_name = os.path.basename(agg.model_path) if agg.model_path else "unknown"
                label = f"{model_name}\nconc={agg.max_concurrency or '?'}"
                labels.append(label)

            x_pos = np.arange(len(labels))
            ttfts = [agg.avg_mean_ttft_ms for agg in results_list]
            tpots = [agg.avg_mean_tpot_ms for agg in results_list]

            width = 0.35

            # Create figure - slimmer width
            plt.figure(figsize=(max(6, len(labels) * 1.0), 6))

            # Plot both metrics
            bars1 = plt.bar(x_pos - width/2, ttfts, width, label='TTFT (ms)', alpha=0.7, color='coral')
            bars2 = plt.bar(x_pos + width/2, tpots, width, label='TPOT (ms)', alpha=0.7, color='seagreen')

            # Add value labels
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    max_val = max(ttfts + tpots) if (ttfts + tpots) else 100
                    plt.text(
                        bar.get_x() + bar.get_width() / 2.,
                        height + (max_val * 0.01),
                        f'{height:.1f}',
                        ha='center',
                        va='bottom',
                        fontsize=9,
                    )

            # Customize plot
            plt.xlabel('Configuration', fontsize=12, fontweight='bold')
            plt.ylabel('Latency (ms)', fontsize=12, fontweight='bold')
            plt.title(title, fontsize=14, fontweight='bold', pad=20)
            plt.xticks(x_pos, labels, fontsize=10, rotation=45, ha='right')
            plt.legend(fontsize=11)
            plt.grid(axis='y', linestyle='--', alpha=0.7)

            max_val = max(ttfts + tpots) if (ttfts + tpots) else 100
            plt.ylim(bottom=0, top=max_val * 1.15)

            plt.tight_layout()

            filepath = os.path.join(self.reports_dir, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()

            logger.info(f"Saved latency metrics plot to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to create latency plot: {e}")
            plt.close()
            return None
