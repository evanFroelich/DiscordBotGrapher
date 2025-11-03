"""Utility functions for the Discord bot."""
import numpy as np
from datetime import datetime


def sigmoid(x):
    """Calculate sigmoid function."""
    return 1 / (1 + np.exp(-x))


async def numToGrade(percentage):
    """Converts a percentage to a letter grade."""
    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 60:
        return "D"
    else:
        return "F"

