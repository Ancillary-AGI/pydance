"""
Mathematical Operations and Algorithms for Pydance Framework.

This module provides pure mathematical functions, algorithms, and computations.
Focused on numerical methods, matrix operations, and mathematical utilities.
"""

import math
import cmath
import statistics
from typing import List, Tuple, Union, Optional
from decimal import Decimal, getcontext
from functools import lru_cache
import operator


class MathOperations:
    """Pure mathematical operations and algorithms"""

    @staticmethod
    @lru_cache(maxsize=1000)
    def fibonacci(n: int) -> int:
        """Calculate nth Fibonacci number using matrix exponentiation"""
        if n < 0:
            raise ValueError("Negative Fibonacci numbers not supported")
        if n == 0:
            return 0
        if n == 1 or n == 2:
            return 1

        # Use closed-form solution (Binet's formula) for better performance
        phi = (1 + math.sqrt(5)) / 2
        psi = (1 - math.sqrt(5)) / 2
        return round((phi ** n - psi ** n) / math.sqrt(5))

    @staticmethod
    def prime_factors(n: int) -> List[Tuple[int, int]]:
        """Get prime factors with their exponents"""
        if n <= 1:
            return []

        factors = []
        # Check for factor 2
        count = 0
        while n % 2 == 0:
            count += 1
            n //= 2
        if count > 0:
            factors.append((2, count))

        # Check for odd factors
        for i in range(3, int(math.sqrt(n)) + 1, 2):
            count = 0
            while n % i == 0:
                count += 1
                n //= i
            if count > 0:
                factors.append((i, count))

        # If n is a prime number greater than 2
        if n > 2:
            factors.append((n, 1))

        return factors

    @staticmethod
    def gcd(a: int, b: int) -> int:
        """Calculate greatest common divisor using Euclidean algorithm"""
        while b:
            a, b = b, a % b
        return a

    @staticmethod
    def lcm(a: int, b: int) -> int:
        """Calculate least common multiple"""
        return abs(a * b) // MathOperations.gcd(a, b)

    @staticmethod
    def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
        """Extended Euclidean algorithm - returns gcd and coefficients"""
        if a == 0:
            return b, 0, 1

        gcd, x1, y1 = MathOperations.extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1

        return gcd, x, y

    @staticmethod
    def modular_inverse(a: int, m: int) -> int:
        """Calculate modular inverse using extended Euclidean algorithm"""
        gcd, x, y = MathOperations.extended_gcd(a, m)
        if gcd != 1:
            raise ValueError(f"Modular inverse does not exist for {a} mod {m}")
        return (x % m + m) % m

    @staticmethod
    def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
        """Matrix multiplication with input validation"""
        if not a or not b or not a[0] or not b[0]:
            raise ValueError("Empty matrices not allowed")

        if len(a[0]) != len(b):
            raise ValueError("Matrix dimensions don't match for multiplication")

        result = [[0.0 for _ in range(len(b[0]))] for _ in range(len(a))]

        for i in range(len(a)):
            for j in range(len(b[0])):
                for k in range(len(b)):
                    result[i][j] += a[i][k] * b[k][j]

        return result

    @staticmethod
    def matrix_determinant(matrix: List[List[float]]) -> float:
        """Calculate matrix determinant using Gaussian elimination"""
        if not matrix or not matrix[0]:
            raise ValueError("Empty matrix")

        n = len(matrix)
        if n != len(matrix[0]):
            raise ValueError("Matrix must be square")

        if n == 1:
            return matrix[0][0]
        if n == 2:
            return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]

        # Make a copy to avoid modifying the original
        mat = [row[:] for row in matrix]
        det = 1.0
        sign = 1

        # Gaussian elimination
        for i in range(n):
            # Find pivot
            pivot_row = i
            for j in range(i + 1, n):
                if abs(mat[j][i]) > abs(mat[pivot_row][i]):
                    pivot_row = j

            if abs(mat[pivot_row][i]) < 1e-10:
                return 0.0  # Matrix is singular

            # Swap rows
            if pivot_row != i:
                mat[i], mat[pivot_row] = mat[pivot_row], mat[i]
                sign = -sign

            # Eliminate
            for j in range(i + 1, n):
                factor = mat[j][i] / mat[i][i]
                for k in range(i, n):
                    mat[j][k] -= factor * mat[i][k]

        # Calculate determinant
        for i in range(n):
            det *= mat[i][i]

        return det * sign

    @staticmethod
    def solve_linear_system(a: List[List[float]], b: List[float]) -> List[float]:
        """Solve linear system Ax = b using Gaussian elimination"""
        if not a or not b:
            raise ValueError("Empty matrices not allowed")

        n = len(a)
        if len(a[0]) != n or len(b) != n:
            raise ValueError("Invalid matrix dimensions")

        # Create augmented matrix
        augmented = [row[:] + [b[i]] for i, row in enumerate(a)]

        # Forward elimination
        for i in range(n):
            # Find pivot
            pivot_row = i
            for j in range(i + 1, n):
                if abs(augmented[j][i]) > abs(augmented[pivot_row][i]):
                    pivot_row = j

            # Swap rows
            augmented[i], augmented[pivot_row] = augmented[pivot_row], augmented[i]

            # Check for singular matrix
            if abs(augmented[i][i]) < 1e-10:
                raise ValueError("Matrix is singular")

            # Eliminate
            for j in range(i + 1, n):
                factor = augmented[j][i] / augmented[i][i]
                for k in range(i, n + 1):
                    augmented[j][k] -= factor * augmented[i][k]

        # Back substitution
        x = [0.0] * n
        for i in range(n - 1, -1, -1):
            x[i] = augmented[i][n]
            for j in range(i + 1, n):
                x[i] -= augmented[i][j] * x[j]
            x[i] /= augmented[i][i]

        return x

    @staticmethod
    def numerical_integration(func: callable, a: float, b: float, n: int = 1000) -> float:
        """Numerical integration using Simpson's rule"""
        if a >= b:
            raise ValueError("Integration limits must satisfy a < b")
        if n <= 0:
            raise ValueError("Number of intervals must be positive")

        if n % 2 != 0:
            n += 1  # Simpson's rule requires even number of intervals

        h = (b - a) / n
        integral = func(a) + func(b)

        for i in range(1, n):
            x = a + i * h
            if i % 2 == 0:
                integral += 2 * func(x)
            else:
                integral += 4 * func(x)

        return integral * h / 3

    @staticmethod
    def newton_method(func: callable, derivative: callable, initial_guess: float,
                     tolerance: float = 1e-10, max_iterations: int = 100) -> float:
        """Newton-Raphson method for finding roots"""
        if tolerance <= 0:
            raise ValueError("Tolerance must be positive")
        if max_iterations <= 0:
            raise ValueError("Max iterations must be positive")

        x = initial_guess
        for iteration in range(max_iterations):
            try:
                fx = func(x)
                if abs(fx) < tolerance:
                    return x
                dfx = derivative(x)
                if abs(dfx) < 1e-10:
                    raise ValueError("Derivative too close to zero")
                x = x - fx / dfx
            except (ZeroDivisionError, OverflowError) as e:
                raise ValueError(f"Numerical instability at iteration {iteration}: {e}")

        raise ValueError(f"Maximum iterations ({max_iterations}) reached")

    @staticmethod
    def statistical_analysis(data: List[float]) -> dict:
        """Perform basic statistical analysis"""
        if not data:
            raise ValueError("Data cannot be empty")

        return {
            'mean': statistics.mean(data),
            'median': statistics.median(data),
            'mode': statistics.mode(data) if len(set(data)) < len(data) else None,
            'stdev': statistics.stdev(data) if len(data) > 1 else 0,
            'variance': statistics.variance(data) if len(data) > 1 else 0,
            'min': min(data),
            'max': max(data),
            'range': max(data) - min(data)
        }


# Create a singleton instance for convenience
_math_operations = MathOperations()

# Convenience functions
def fibonacci(n: int) -> int:
    """Calculate nth Fibonacci number"""
    return _math_operations.fibonacci(n)

def prime_factors(n: int) -> List[Tuple[int, int]]:
    """Get prime factors"""
    return _math_operations.prime_factors(n)

def gcd(a: int, b: int) -> int:
    """Calculate GCD"""
    return _math_operations.gcd(a, b)

def lcm(a: int, b: int) -> int:
    """Calculate LCM"""
    return _math_operations.lcm(a, b)

def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication"""
    return _math_operations.matrix_multiply(a, b)

def solve_linear_system(a: List[List[float]], b: List[float]) -> List[float]:
    """Solve linear system"""
    return _math_operations.solve_linear_system(a, b)
