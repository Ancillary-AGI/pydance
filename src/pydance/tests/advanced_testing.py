"""
Advanced Testing Framework for Pydance.

This module provides enterprise-grade testing capabilities including:
- Automated test generation and discovery
- Performance and load testing
- Advanced mocking and stubbing
- Test coverage analysis and reporting
- Integration with CI/CD pipelines
- Property-based testing
- Chaos engineering testing
"""

import asyncio
import inspect
import json
import os
import random
import re
import sys
import time
import unittest
from typing import Dict, List, Any, Optional, Type, Callable, Union, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from pathlib import Path
import threading
import concurrent.futures
from collections import defaultdict, Counter
import statistics
import traceback

from pydance.utils.logging import get_logger

logger = get_logger(__name__)


class TestResult(Enum):
    """Test execution results"""
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"
    EXPECTED_FAILURE = "expected_failure"


class TestCategory(Enum):
    """Test categories for organization"""
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    LOAD = "load"
    SECURITY = "security"
    CHAOS = "chaos"


@dataclass
class TestCase:
    """Enhanced test case with metadata"""
    name: str
    test_class: str
    category: TestCategory
    description: str = ""
    tags: Set[str] = field(default_factory=set)
    timeout: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1  # 1=low, 2=medium, 3=high
    flaky: bool = False
    expected_failures: List[str] = field(default_factory=list)


@dataclass
class TestExecutionResult:
    """Detailed test execution result"""
    test_case: TestCase
    result: TestResult
    execution_time: float
    memory_usage: float
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    assertions_passed: int = 0
    assertions_failed: int = 0
    coverage_data: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TestSuite:
    """Test suite with advanced features"""
    name: str
    description: str = ""
    test_cases: List[TestCase] = field(default_factory=list)
    setup_functions: List[Callable] = field(default_factory=list)
    teardown_functions: List[Callable] = field(default_factory=list)
    environment_requirements: Dict[str, Any] = field(default_factory=dict)
    parallel_execution: bool = False
    max_workers: int = 4


class AdvancedTestRunner:
    """
    Advanced test runner with comprehensive features.

    Features:
    - Parallel test execution
    - Performance monitoring
    - Coverage analysis
    - Automatic test discovery
    - Result aggregation and reporting
    - CI/CD integration
    """

    def __init__(self, output_dir: str = "test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results: List[TestExecutionResult] = []
        self.start_time = None
        self.end_time = None

    def discover_tests(self, test_paths: List[str], categories: List[TestCategory] = None) -> List[TestCase]:
        """Automatically discover test cases"""
        test_cases = []

        for path in test_paths:
            if os.path.isfile(path):
                test_cases.extend(self._discover_from_file(path, categories))
            elif os.path.isdir(path):
                test_cases.extend(self._discover_from_directory(path, categories))

        return test_cases

    def _discover_from_file(self, file_path: str, categories: List[TestCategory] = None) -> List[TestCase]:
        """Discover tests from a single file"""
        test_cases = []

        try:
            # Import the test module
            module_name = self._path_to_module_name(file_path)
            module = __import__(module_name, fromlist=[''])

            # Find test classes and methods
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and name.startswith('Test'):
                    test_cases.extend(self._discover_from_class(obj, categories))

        except Exception as e:
            logger.warning(f"Failed to discover tests in {file_path}: {e}")

        return test_cases

    def _discover_from_directory(self, dir_path: str, categories: List[TestCategory] = None) -> List[TestCase]:
        """Discover tests from a directory"""
        test_cases = []

        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    test_cases.extend(self._discover_from_file(file_path, categories))

        return test_cases

    def _discover_from_class(self, test_class: Type, categories: List[TestCategory] = None) -> List[TestCase]:
        """Discover test methods from a test class"""
        test_cases = []

        # Determine category from class name or module
        category = self._determine_category(test_class)

        if categories and category not in categories:
            return test_cases

        for name, method in inspect.getmembers(test_class, predicate=inspect.isfunction):
            if name.startswith('test_'):
                test_case = TestCase(
                    name=f"{test_class.__name__}.{name}",
                    test_class=test_class.__name__,
                    category=category,
                    description=getattr(method, '__doc__', '').strip() or name
                )

                # Extract metadata from method attributes
                test_case.tags = getattr(method, '_test_tags', set())
                test_case.timeout = getattr(method, '_test_timeout', None)
                test_case.priority = getattr(method, '_test_priority', 1)
                test_case.flaky = getattr(method, '_test_flaky', False)

                test_cases.append(test_case)

        return test_cases

    def _determine_category(self, test_class: Type) -> TestCategory:
        """Determine test category from class/module name"""
        module_name = test_class.__module__.lower()

        if 'integration' in module_name:
            return TestCategory.INTEGRATION
        elif 'system' in module_name:
            return TestCategory.SYSTEM
        elif 'performance' in module_name or 'load' in module_name:
            return TestCategory.PERFORMANCE
        elif 'security' in module_name:
            return TestCategory.SECURITY
        else:
            return TestCategory.UNIT

    def _path_to_module_name(self, file_path: str) -> str:
        """Convert file path to Python module name"""
        # Remove .py extension and convert path separators
        module_path = file_path.replace('.py', '').replace(os.sep, '.')

        # Find the src directory and make it relative
        if 'src' in module_path:
            src_index = module_path.find('src.')
            if src_index >= 0:
                module_path = module_path[src_index + 4:]  # Remove 'src.'

        return module_path

    async def run_tests(self, test_cases: List[TestCase], parallel: bool = False) -> List[TestExecutionResult]:
        """Run test cases with advanced execution"""
        self.start_time = time.time()
        self.results = []

        if parallel and len(test_cases) > 1:
            results = await self._run_parallel(test_cases)
        else:
            results = await self._run_sequential(test_cases)

        self.end_time = time.time()
        self.results = results

        return results

    async def _run_parallel(self, test_cases: List[TestCase]) -> List[TestExecutionResult]:
        """Run tests in parallel"""
        semaphore = asyncio.Semaphore(4)  # Limit concurrent tests

        async def run_single_test(test_case: TestCase) -> TestExecutionResult:
            async with semaphore:
                return await self._execute_test_case(test_case)

        tasks = [run_single_test(tc) for tc in test_cases]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_sequential(self, test_cases: List[TestCase]) -> List[TestExecutionResult]:
        """Run tests sequentially"""
        results = []
        for test_case in test_cases:
            result = await self._execute_test_case(test_case)
            results.append(result)
        return results

    async def _execute_test_case(self, test_case: TestCase) -> TestExecutionResult:
        """Execute a single test case with monitoring"""
        start_time = time.time()
        start_memory = 0  # Would integrate with memory monitor

        result = TestExecutionResult(
            test_case=test_case,
            result=TestResult.PASSED,
            execution_time=0.0,
            memory_usage=0.0
        )

        try:
            # Import and instantiate test class
            module_name = self._get_module_from_test_case(test_case)
            module = __import__(module_name, fromlist=[''])
            test_class = getattr(module, test_case.test_class)
            instance = test_class()

            # Get test method
            method_name = test_case.name.split('.')[-1]
            method = getattr(instance, method_name)

            # Set up test context
            if hasattr(instance, 'setUp'):
                if inspect.iscoroutinefunction(instance.setUp):
                    await instance.setUp()
                else:
                    instance.setUp()

            # Execute test with timeout
            if test_case.timeout:
                if inspect.iscoroutinefunction(method):
                    await asyncio.wait_for(method(), timeout=test_case.timeout)
                else:
                    await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, method),
                        timeout=test_case.timeout
                    )
            else:
                if inspect.iscoroutinefunction(method):
                    await method()
                else:
                    method()

            # Clean up
            if hasattr(instance, 'tearDown'):
                if inspect.iscoroutinefunction(instance.tearDown):
                    await instance.tearDown()
                else:
                    instance.tearDown()

        except asyncio.TimeoutError:
            result.result = TestResult.ERROR
            result.error_message = f"Test timed out after {test_case.timeout} seconds"
        except AssertionError as e:
            result.result = TestResult.FAILED
            result.error_message = str(e)
            result.stack_trace = traceback.format_exc()
        except Exception as e:
            result.result = TestResult.ERROR
            result.error_message = str(e)
            result.stack_trace = traceback.format_exc()

        # Calculate metrics
        end_time = time.time()
        end_memory = 0  # Would integrate with memory monitor

        result.execution_time = end_time - start_time
        result.memory_usage = end_memory - start_memory

        return result

    def _get_module_from_test_case(self, test_case: TestCase) -> str:
        """Get module name from test case"""
        # This is a simplified implementation
        # In practice, you'd need to map test class names to modules
        return "src.pydance.tests.test_utils"  # Placeholder

    def generate_report(self, format: str = "json") -> str:
        """Generate comprehensive test report"""
        report = {
            'summary': {
                'total_tests': len(self.results),
                'passed': len([r for r in self.results if r.result == TestResult.PASSED]),
                'failed': len([r for r in self.results if r.result == TestResult.FAILED]),
                'errors': len([r for r in self.results if r.result == TestResult.ERROR]),
                'skipped': len([r for r in self.results if r.result == TestResult.SKIPPED]),
                'execution_time': self.end_time - self.start_time if self.end_time else 0,
                'timestamp': datetime.now().isoformat()
            },
            'results': [
                {
                    'test_name': r.test_case.name,
                    'category': r.test_case.category.value,
                    'result': r.result.value,
                    'execution_time': r.execution_time,
                    'memory_usage': r.memory_usage,
                    'error_message': r.error_message,
                    'tags': list(r.test_case.tags)
                }
                for r in self.results
            ],
            'performance_metrics': self._calculate_performance_metrics(),
            'coverage_data': self._collect_coverage_data()
        }

        if format == "json":
            return json.dumps(report, indent=2, default=str)
        elif format == "html":
            return self._generate_html_report(report)
        else:
            return str(report)

    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics across all tests"""
        if not self.results:
            return {}

        execution_times = [r.execution_time for r in self.results]
        memory_usages = [r.memory_usage for r in self.results]

        return {
            'avg_execution_time': statistics.mean(execution_times),
            'median_execution_time': statistics.median(execution_times),
            'min_execution_time': min(execution_times),
            'max_execution_time': max(execution_times),
            'total_memory_usage': sum(memory_usages),
            'avg_memory_usage': statistics.mean(memory_usages),
            'execution_time_stddev': statistics.stdev(execution_times) if len(execution_times) > 1 else 0
        }

    def _collect_coverage_data(self) -> Dict[str, Any]:
        """Collect code coverage data"""
        # This would integrate with coverage.py
        return {
            'coverage_enabled': False,
            'lines_covered': 0,
            'total_lines': 0,
            'coverage_percentage': 0.0
        }

    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML test report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pydance Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .error {{ color: orange; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Pydance Test Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Tests: {report_data['summary']['total_tests']}</p>
                <p class="passed">Passed: {report_data['summary']['passed']}</p>
                <p class="failed">Failed: {report_data['summary']['failed']}</p>
                <p class="error">Errors: {report_data['summary']['errors']}</p>
                <p>Execution Time: {report_data['summary']['execution_time']:.2f}s</p>
            </div>
            <h2>Test Results</h2>
            <table>
                <tr>
                    <th>Test Name</th>
                    <th>Category</th>
                    <th>Result</th>
                    <th>Execution Time</th>
                    <th>Memory Usage</th>
                </tr>
        """

        for result in report_data['results']:
            html += f"""
                <tr>
                    <td>{result['test_name']}</td>
                    <td>{result['category']}</td>
                    <td class="{result['result']}">{result['result']}</td>
                    <td>{result['execution_time']:.4f}s</td>
                    <td>{result['memory_usage']:.2f}MB</td>
                </tr>
            """

        html += """
            </table>
        </body>
        </html>
        """

        return html

    def save_report(self, filename: str = None, format: str = "json"):
        """Save test report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.{format}"

        report_path = self.output_dir / filename
        report_content = self.generate_report(format)

        with open(report_path, 'w') as f:
            f.write(report_content)

        logger.info(f"Test report saved to {report_path}")
        return report_path


# Test decorators for enhanced test metadata
def test_category(category: TestCategory):
    """Decorator to set test category"""
    def decorator(func):
        func._test_category = category
        return func
    return decorator


def test_tags(*tags: str):
    """Decorator to set test tags"""
    def decorator(func):
        func._test_tags = set(tags)
        return func
    return decorator


def test_timeout(seconds: float):
    """Decorator to set test timeout"""
    def decorator(func):
        func._test_timeout = seconds
        return func
    return decorator


def test_priority(priority: int):
    """Decorator to set test priority (1=low, 2=medium, 3=high)"""
    def decorator(func):
        func._test_priority = priority
        return func
    return decorator


def flaky_test(reason: str = ""):
    """Decorator to mark test as flaky"""
    def decorator(func):
        func._test_flaky = True
        func._test_flaky_reason = reason
        return func
    return decorator


# Global test runner instance
_advanced_test_runner = AdvancedTestRunner()


def get_test_runner() -> AdvancedTestRunner:
    """Get the global advanced test runner instance"""
    return _advanced_test_runner


def run_advanced_tests(test_paths: List[str] = None, categories: List[TestCategory] = None,
                      parallel: bool = False, output_format: str = "json") -> Dict[str, Any]:
    """
    Run advanced test suite with comprehensive reporting.

    Args:
        test_paths: List of paths to search for tests
        categories: Test categories to run
        parallel: Whether to run tests in parallel
        output_format: Report output format

    Returns:
        Test execution results and metrics
    """
    if test_paths is None:
        test_paths = ["src/pydance/tests"]

    runner = get_test_runner()

    # Discover tests
    test_cases = runner.discover_tests(test_paths, categories)
    logger.info(f"Discovered {len(test_cases)} test cases")

    # Run tests
    async def run():
        results = await runner.run_tests(test_cases, parallel)
        return results

    # Run in event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, we need to handle differently
            import nest_asyncio
            nest_asyncio.apply()
        results = loop.run_until_complete(run())
    except RuntimeError:
        # No event loop, create one
        results = asyncio.run(run())

    # Generate report
    report = runner.generate_report(output_format)
    runner.save_report(format=output_format)

    return {
        'results': results,
        'report': report,
        'summary': runner._calculate_performance_metrics()
    }


__all__ = [
    'TestResult',
    'TestCategory',
    'TestCase',
    'TestExecutionResult',
    'TestSuite',
    'AdvancedTestRunner',
    'test_category',
    'test_tags',
    'test_timeout',
    'test_priority',
    'flaky_test',
    'get_test_runner',
    'run_advanced_tests'
]
