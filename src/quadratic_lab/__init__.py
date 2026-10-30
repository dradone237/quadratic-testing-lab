"""QUADRATIC TESTING LAB.

Résolution et vérification robuste des équations du second degré avec
Jenny, Uniwise et Pairwise Testing.
"""

from .models import Category, QuadraticCase, SolveResult, Status
from .solver import solve

__all__ = ["Category", "QuadraticCase", "SolveResult", "Status", "solve", "__version__"]
__version__ = "1.0.0"
