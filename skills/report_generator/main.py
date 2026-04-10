"""
Report Generator Skill - Main implementation.
Generates comprehensive reports with visualizations from benchmark results.
"""
import os
import sys
import time
from typing import Dict, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.result_types import BenchmarkSuiteResult
from src.templates import TemplateLoader
from src.report_generator import ReportGenerator as CoreReportGenerator


class ReportGeneratorSkill:
    """
    Skill wrapper for report generation operations.
    """
    def __init__(self, reports_dir: str = "reports", do_visualize: bool = True,
                 slo_ttft_max: float = 1e8, slo_tpot_max: float = 1e8,
                 data_watch_policy: str = "remove_min_max",
                 template_loader: Optional[TemplateLoader] = None):
        """
        Initialize the report generator.

        Args:
            reports_dir: Directory to save reports
            do_visualize: Whether to generate visualizations
            slo_ttft_max: Maximum TTFT for SLO filtering
            slo_tpot_max: Maximum TPOT for SLO filtering
            data_watch_policy: Policy for outlier removal
            template_loader: Optional template loader for OPT explanations
        """
        self.reports_dir = reports_dir
        self.do_visualize = do_visualize

        self.core_generator = CoreReportGenerator(
            reports_dir=reports_dir,
            do_visualize=do_visualize,
            slo_ttft_max=slo_ttft_max,
            slo_tpot_max=slo_tpot_max,
            data_watch_policy=data_watch_policy,
            template_loader=template_loader
        )

    def generate_report(self, suite_result: BenchmarkSuiteResult,
                       report_name: Optional[str] = None) -> str:
        """
        Generate a complete report from benchmark results.

        Args:
            suite_result: The benchmark suite result to report on
            report_name: Optional name for the report (without extension)

        Returns:
            Path to the generated markdown report
        """
        return self.core_generator.generate_report(suite_result, report_name)


# Convenience function
def generate_report(suite_result: BenchmarkSuiteResult, reports_dir: str = "reports",
                   do_visualize: bool = True, slo_ttft_max: float = 1e8,
                   slo_tpot_max: float = 1e8, data_watch_policy: str = "remove_min_max",
                   template_loader: Optional[TemplateLoader] = None,
                   report_name: Optional[str] = None) -> str:
    """
    Generate a report from benchmark results (convenience function).

    Args:
        suite_result: Benchmark results to report
        reports_dir: Directory to save reports
        do_visualize: Whether to create plots
        slo_ttft_max: SLO TTFT threshold
        slo_tpot_max: SLO TPOT threshold
        data_watch_policy: How to handle outliers
        template_loader: Template loader for OPT explanations
        report_name: Optional report name

    Returns:
        Path to generated report
    """
    skill = ReportGeneratorSkill(
        reports_dir=reports_dir,
        do_visualize=do_visualize,
        slo_ttft_max=slo_ttft_max,
        slo_tpot_max=slo_tpot_max,
        data_watch_policy=data_watch_policy,
        template_loader=template_loader
    )
    return skill.generate_report(suite_result, report_name)
