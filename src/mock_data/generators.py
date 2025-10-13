"""
Mock Data Generators
Simple utilities for generating mock data for testing and development
"""

import random
from typing import Union


def random_int(min_val: int, max_val: int) -> int:
    """Generate random integer between min and max (inclusive)"""
    return random.randint(min_val, max_val)


def random_float(min_val: float, max_val: float, decimals: int = 2) -> float:
    """Generate random float between min and max"""
    value = random.uniform(min_val, max_val)
    return round(value, decimals)


def random_choice(choices: list) -> any:
    """Select random item from list"""
    return random.choice(choices)


def random_bool(probability: float = 0.5) -> bool:
    """Generate random boolean with given probability of True"""
    return random.random() < probability
