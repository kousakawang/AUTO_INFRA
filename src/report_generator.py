"""
Report Generator - Creates markdown and HTML reports from benchmark results.
"""
import os
import time
import logging
from typing import Dict, List, Optional

from .result_types import BenchmarkSuiteResult
from .data_processor import (
    DataProcessor, ServiceCaseAggregatedResult, GroupResult, GroupKey
)
from .visualization import Visualizer
from .templates import TemplateLoader

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates comprehensive reports from benchmark results.

    Groups results by model, config, template_id, and deploy_method.
    Shows one data point per (service, case), after aggregating per_config_benchmark_times runs.
    """

    def __init__(
        self,
        reports_dir: str = "reports",
        do_visualize: bool = True,
        slo_ttft_max: float = 1e8,
        slo_tpot_max: float = 1e8,
        data_watch_policy: str = "remove_min_max",
        template_loader: Optional[TemplateLoader] = None,
    ):
        self.reports_dir = reports_dir
        self.do_visualize = do_visualize
        self.slo_ttft_max = slo_ttft_max
        self.slo_tpot_max = slo_tpot_max
        self.data_watch_policy = data_watch_policy

        self._ensure_reports_dir()
        self.visualizer = Visualizer(reports_dir)
        self.data_processor = DataProcessor(
            data_watch_policy=data_watch_policy,
            slo_ttft_max=slo_ttft_max,
            slo_tpot_max=slo_tpot_max,
        )

        # Load OPT files for option explanations
        self.template_loader = template_loader or TemplateLoader()
        if not self.template_loader.env_opts or not self.template_loader.server_args_opts:
            self.template_loader.load_all()

    def _ensure_reports_dir(self):
        """Ensure the reports directory exists."""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
            logger.info(f"Created reports directory: {self.reports_dir}")

    def generate_report(
        self,
        suite_result: BenchmarkSuiteResult,
        report_name: Optional[str] = None,
    ) -> str:
        """
        Generate a complete report from benchmark results.

        Args:
            suite_result: The benchmark suite result to report on
            report_name: Optional name for the report (without extension)

        Returns:
            Path to the generated markdown report
        """
        if report_name is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            report_name = f"benchmark_report_{timestamp}"

        logger.info(f"Generating report: {report_name}")

        # Aggregate results per (service, case)
        aggregated_results = self.data_processor.aggregate_per_service_case(suite_result)

        # Group results
        group_results = self.data_processor.group_results(aggregated_results)

        # Generate visualizations
        plot_paths = {}
        if self.do_visualize:
            for idx, group in enumerate(group_results):
                plot_path = self.visualizer.plot_group_individual_results(
                    group,
                    idx
                )
                plot_paths[idx] = plot_path

        # Generate markdown report
        markdown_content = self._generate_markdown(
            suite_result,
            group_results,
            plot_paths,
            report_name,
        )

        markdown_path = os.path.join(self.reports_dir, f"{report_name}.md")
        with open(markdown_path, "w") as f:
            f.write(markdown_content)

        logger.info(f"Generated report at: {markdown_path}")
        return markdown_path

    def _generate_markdown(
        self,
        suite_result: BenchmarkSuiteResult,
        group_results: List[GroupResult],
        plot_paths: Dict[int, str],
        report_name: str,
    ) -> str:
        """Generate markdown report content."""
        lines = []

        # Header
        lines.append("# Benchmark Results Report")
        lines.append("")
        lines.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # SLO information
        lines.append("## SLO Criteria")
        lines.append("")
        if self.slo_ttft_max < 1e8 or self.slo_tpot_max < 1e8:
            lines.append(f"- TTFT Max: {self.slo_ttft_max} ms")
            lines.append(f"- TPOT Max: {self.slo_tpot_max} ms")
        else:
            lines.append("- No SLO thresholds applied")
        lines.append(f"- Data Policy: {self.data_watch_policy}")
        lines.append("")

        # Group results
        lines.append("## Group Results")
        lines.append("")

        for group_idx, group in enumerate(group_results):
            lines.append(f"### Group {group_idx}")
            lines.append("")

            # Group header
            lines.append(self._generate_group_header(group.group_key))
            lines.append("")

            # Plot
            if self.do_visualize and group_idx in plot_paths:
                plot_filename = os.path.basename(plot_paths[group_idx])
                lines.append(f"![Group {group_idx} Plot]({plot_filename})")
                lines.append("")

            # Results table with idx
            lines.append("#### Results")
            lines.append("")
            lines.append(self._generate_results_table(group))
            lines.append("")

            # Configuration details table
            lines.append("#### Configuration Details")
            lines.append("")
            lines.append(self._generate_config_details_table(group))
            lines.append("")

        return "\n".join(lines)

    def _generate_group_header(self, group_key: GroupKey) -> str:
        """Generate header for a group."""
        model_name = os.path.basename(group_key.model_path) if group_key.model_path else "unknown"
        img_info = f"{group_key.image_size or '-'}/{group_key.image_count or '-'}"

        lines = []
        lines.append("| Attribute | Value |")
        lines.append("|-----------|-------|")
        lines.append(f"| **Model** | {model_name} |")
        lines.append(f"| **Deploy Method** | {group_key.deploy_method or '-'} |")
        lines.append(f"| **Template ID** | {group_key.template_id or '-'} |")
        lines.append(f"| **Input Length** | {group_key.input_len or '-'} |")
        lines.append(f"| **Output Length** | {group_key.output_len or '-'} |")
        lines.append(f"| **Max Concurrency** | {group_key.max_concurrency or '-'} |")
        lines.append(f"| **Image Size/Count** | {img_info} |")

        return "\n".join(lines)

    def _generate_results_table(
        self,
        group: GroupResult,
    ) -> str:
        """Generate results table with idx for each item in the group."""
        if not group.service_case_results:
            return "No results available."

        lines = []

        # Header
        headers = [
            "idx",
            "Throughput (tok/s)",
            "TTFT (ms)",
            "TPOT (ms)",
        ]

        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        # Rows
        for idx, agg in enumerate(group.service_case_results):
            throughput_label = f"{agg.avg_total_token_throughput:.1f}"
            if agg.is_per_device_throughput:
                throughput_label += f" (per-device)"

            row = [
                str(idx),
                throughput_label,
                f"{agg.avg_mean_ttft_ms:.1f}",
                f"{agg.avg_mean_tpot_ms:.1f}",
            ]
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)

    def _generate_config_details_table(
        self,
        group: GroupResult,
    ) -> str:
        """Generate table explaining configuration for each idx in the group."""
        if not group.service_case_results:
            return "No configurations available."

        lines = []

        # Header
        headers = [
            "idx",
            "Env Opt",
            "Server Args Opt",
            "Additional Options",
        ]

        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        # Rows
        for idx, agg in enumerate(group.service_case_results):
            # Format env opts
            env_opt_ids_str = ",".join(str(x) for x in agg.env_opt_ids) if agg.env_opt_ids else "-"
            env_opt_values = []
            if agg.env_opt_ids:
                for opt_id in agg.env_opt_ids:
                    if opt_id >= 0 and opt_id < len(self.template_loader.env_opts):
                        env_opt_values.append(self.template_loader.env_opts[opt_id])
                    elif opt_id == -1:
                        env_opt_values.append("(none)")
                    else:
                        env_opt_values.append(f"(invalid id: {opt_id})")
            env_opt_str = "<br>".join(env_opt_values) if env_opt_values else "(none)"

            # Format server args opts
            server_args_opt_ids_str = ",".join(str(x) for x in agg.server_args_opt_ids) if agg.server_args_opt_ids else "-"
            server_args_opt_values = []
            if agg.server_args_opt_ids:
                for opt_id in agg.server_args_opt_ids:
                    if opt_id >= 0 and opt_id < len(self.template_loader.server_args_opts):
                        server_args_opt_values.append(self.template_loader.server_args_opts[opt_id])
                    elif opt_id == -1:
                        server_args_opt_values.append("(none)")
                    else:
                        server_args_opt_values.append(f"(invalid id: {opt_id})")
            server_args_opt_str = "<br>".join(server_args_opt_values) if server_args_opt_values else "(none)"

            # Format additional options
            add_opts_str = "<br>".join(agg.additional_options) if agg.additional_options else "(none)"

            row = [
                str(idx),
                env_opt_str,
                server_args_opt_str,
                add_opts_str,
            ]
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)
