"""Configuration commune des tests.

- Profil Hypothesis reproductible (``derandomize=True``) : deux exécutions
  successives génèrent exactement les mêmes exemples.
- Fixture ``jenny_adapter`` : fournit l'adaptateur vers le **vrai** Jenny ou
  ignore (skip) explicitement le test si l'exécutable est indisponible.
"""

from __future__ import annotations

import os

import pytest
from hypothesis import settings

settings.register_profile(
    "projet",
    max_examples=200,
    derandomize=True,
    deadline=None,
    print_blob=True,
)
settings.register_profile("rapide", max_examples=30, derandomize=True, deadline=None)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "projet"))


@pytest.fixture(scope="session")
def jenny_adapter():
    """Adaptateur vérifié vers l'exécutable Jenny réel (sinon test ignoré)."""
    from quadratic_lab.jenny_adapter import JennyAdapter, JennyError

    try:
        adapter = JennyAdapter()
        adapter.verify()
    except JennyError as exc:  # pragma: no cover - dépend de l'environnement
        pytest.skip(f"Jenny indisponible : {exc}")
    return adapter
