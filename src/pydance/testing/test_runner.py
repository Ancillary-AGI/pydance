"""
Test runner and suite utilities for Pydance testing framework.
"""

import unittest
from typing import Type, List, Dict, Any

# TestRunner is an alias for unittest.TextTestRunner
TestRunner = unittest.TextTestRunner

class TestSuite:
    """Custom test suite with additional features"""

    def __init__(self, name: str = "Pydance  Test Suite"):
        self.name = name
        self.tests = []
        self.results = {}

    def add_test(self, test_case: Type[unittest.TestCase]):
        """Add test case to suite"""
        self.tests.append(test_case)

    def run(self, verbosity: int = 1) -> unittest.TestResult:
        """Run test suite"""
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()

        for test_case in self.tests:
            suite.addTests(loader.loadTestsFromTestCase(test_case))

        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)

        self.results = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped),
            'success': result.wasSuccessful()
        }

        return result

    def get_coverage_report(self):
        """Get test coverage report"""
        try:
            import coverage
            cov = coverage.Coverage()
            cov.start()

            # Run tests
            self.run(verbosity=0)

            cov.stop()
            cov.save()

            return cov.report()
        except ImportError:
            return "Coverage not available (install coverage package)"

__all__ = ['TestRunner', 'TestSuite']
