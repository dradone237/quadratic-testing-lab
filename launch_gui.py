"""Lance l'interface graphique : ``python launch_gui.py``.

Fonctionne même sans installation du paquet (ajoute ``src`` au chemin).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from quadratic_lab.gui.app import main  # noqa: E402

if __name__ == "__main__":
    main()
