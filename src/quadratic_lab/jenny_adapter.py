"""Adaptateur vers l'exécutable Jenny réel (S-42, S-43).

Jenny (Bob Jenkins, domaine public) est un programme C ; il est compilé
localement par ``tools/jenny/build_jenny.ps1``. Cet adaptateur :

- localise l'exécutable (variable d'environnement, dossier du projet, PATH) ;
- construit les arguments de façon sûre (liste, entiers validés, sans shell) ;
- l'exécute avec ``subprocess.run`` et un délai maximal ;
- conserve la sortie brute et contrôle code de retour ET contenu : Jenny
  écrit ses messages d'erreur sur la sortie standard avec le code 0 ;
- lève une exception explicite en cas de problème. Il n'existe AUCUN mode de
  simulation : sans Jenny, la génération est déclarée indisponible.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

#: Variable d'environnement permettant d'imposer un exécutable Jenny.
ENV_VAR = "QUADRATIC_LAB_JENNY"
#: Délai maximal d'exécution (secondes).
DEFAULT_TIMEOUT = 20.0
#: Limites de Jenny : 2 à 52 valeurs par dimension (lettres a..z, A..Z).
MIN_FEATURES, MAX_FEATURES = 2, 52
_TOKEN_RE = re.compile(r"([0-9]+)([a-zA-Z])")
_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


class JennyError(Exception):
    """Classe de base des erreurs liées à Jenny."""


class JennyNotFoundError(JennyError):
    """Exécutable Jenny introuvable."""


class JennyInvalidExecutableError(JennyError):
    """Le fichier existe mais n'est pas un Jenny fonctionnel."""


class JennyExecutionError(JennyError):
    """Jenny a signalé une erreur (code de retour ou message ``jenny:``)."""


class JennyTimeoutError(JennyError):
    """Jenny a dépassé le délai maximal."""


class JennyOutputError(JennyError):
    """Sortie de Jenny vide ou mal formée."""


class JennyCombinationError(JennyError):
    """Combinaison générée incohérente avec les dimensions demandées."""


def project_root() -> Path:
    """Racine du projet (``src/quadratic_lab/`` -> deux niveaux au-dessus)."""
    return Path(__file__).resolve().parents[2]


def default_locations() -> list[Path]:
    bin_dir = project_root() / "tools" / "jenny" / "bin"
    return [bin_dir / "jenny.exe", bin_dir / "jenny"]


BUILD_HINT = (
    "Compilez Jenny avec : powershell -ExecutionPolicy Bypass -File tools\\jenny\\build_jenny.ps1 "
    "(voir docs/GUIDE_JENNY.md)."
)


def _check_file(path: Path) -> Path:
    if not path.exists():
        raise JennyNotFoundError(f"Exécutable Jenny introuvable : {path}. {BUILD_HINT}")
    if not path.is_file():
        raise JennyInvalidExecutableError(f"{path} n'est pas un fichier exécutable.")
    return path.resolve()


def find_jenny(explicit: str | os.PathLike | None = None) -> Path:
    """Localise Jenny : chemin explicite, puis ``QUADRATIC_LAB_JENNY``,
    puis ``tools/jenny/bin``, puis le PATH.

    Une configuration explicite erronée est signalée (pas de repli silencieux).
    """
    if explicit is not None:
        return _check_file(Path(explicit))
    env_value = os.environ.get(ENV_VAR)
    if env_value:
        path = Path(env_value)
        if not path.exists():
            raise JennyNotFoundError(f"{ENV_VAR}={env_value} : fichier introuvable. {BUILD_HINT}")
        return _check_file(path)
    for candidate in default_locations():
        if candidate.is_file():
            return candidate.resolve()
    on_path = shutil.which("jenny")
    if on_path:
        return Path(on_path).resolve()
    raise JennyNotFoundError(f"Jenny est indisponible (ni {ENV_VAR}, ni tools/jenny/bin, ni PATH). {BUILD_HINT}")


def is_jenny_available() -> bool:
    try:
        JennyAdapter().verify()
    except JennyError:
        return False
    return True


@dataclass(frozen=True)
class JennyRun:
    """Trace complète d'une exécution de Jenny (preuve d'utilisation)."""

    command: tuple[str, ...]
    dimensions: tuple[int, ...]
    strength: int
    seed: int | None
    stdout: str
    stderr: str
    returncode: int
    rows: tuple[tuple[str, ...], ...]
    duration_s: float

    @property
    def command_line(self) -> str:
        """Commande sous forme lisible : ``jenny -n2 5 5 5``."""
        return " ".join(["jenny", *self.command[1:]])


def _strict_int(value: object, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} doit être un entier, reçu {value!r}.")
    return value


def parse_output(stdout: str, dimensions: Sequence[int]) -> tuple[tuple[str, ...], ...]:
    """Analyse la sortie standard de Jenny et valide chaque combinaison."""
    rows: list[tuple[str, ...]] = []
    for line_no, raw_line in enumerate(stdout.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("jenny:"):
            raise JennyExecutionError(f"Jenny a signalé une erreur : {line}")
        if line.lower().startswith("could not cover"):
            raise JennyCombinationError(f"Jenny n'a pas pu couvrir toutes les combinaisons : {line}")
        tokens = line.split()
        parsed = []
        for token in tokens:
            match = _TOKEN_RE.fullmatch(token)
            if not match:
                raise JennyOutputError(f"Ligne {line_no} mal formée : {raw_line!r} (élément {token!r}).")
            parsed.append((int(match.group(1)), match.group(2)))
        if len(parsed) != len(dimensions):
            raise JennyCombinationError(
                f"Ligne {line_no} : {len(dimensions)} dimensions attendues, {len(parsed)} trouvées ({line!r})."
            )
        for position, ((dim_number, letter), size) in enumerate(zip(parsed, dimensions), start=1):
            if dim_number != position:
                raise JennyCombinationError(f"Ligne {line_no} : dimension {position} attendue, {dim_number} trouvée.")
            if letter not in _LETTERS[:size]:
                raise JennyCombinationError(
                    f"Ligne {line_no} : valeur {letter!r} inexistante pour la dimension {position} ({size} valeurs)."
                )
        rows.append(tuple(tokens))
    if not rows:
        raise JennyOutputError("Jenny n'a produit aucune combinaison.")
    return tuple(rows)


Runner = Callable[..., subprocess.CompletedProcess]


class JennyAdapter:
    """Exécute le vrai Jenny et renvoie des combinaisons validées."""

    def __init__(
        self,
        executable: str | os.PathLike | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        runner: Runner = subprocess.run,
    ) -> None:
        if not timeout or timeout <= 0:
            raise ValueError("Le délai maximal doit être strictement positif.")
        self.executable = find_jenny(executable)
        self.timeout = timeout
        self._runner = runner
        self._verified = False

    # -- construction des arguments ------------------------------------------------
    def build_command(self, dimensions: Sequence[int], strength: int, seed: int | None = None) -> list[str]:
        dims = [_strict_int(d, "Chaque dimension") for d in dimensions]
        strength = _strict_int(strength, "La force d'interaction (n)")
        if not dims:
            raise ValueError("Au moins une dimension est nécessaire.")
        for size in dims:
            if not MIN_FEATURES <= size <= MAX_FEATURES:
                raise ValueError(f"Une dimension doit avoir entre {MIN_FEATURES} et {MAX_FEATURES} valeurs ({size}).")
        if not 1 <= strength <= len(dims):
            raise ValueError(f"La force n doit être comprise entre 1 et {len(dims)} (reçu {strength}).")
        command = [str(self.executable), f"-n{strength}", *(str(d) for d in dims)]
        if seed is not None:
            seed = _strict_int(seed, "La graine")
            if not 0 <= seed <= 0xFFFFFFFF:
                raise ValueError("La graine doit être comprise entre 0 et 2^32 - 1.")
            command.append(f"-s{seed}")
        return command

    # -- exécution -------------------------------------------------------------
    def run_raw(self, args: Sequence[str]) -> subprocess.CompletedProcess:
        """Exécute Jenny avec des arguments bruts (chaînes), sans shell."""
        command = [str(self.executable), *(str(arg) for arg in args)]
        try:
            return self._runner(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise JennyTimeoutError(f"Jenny a dépassé le délai maximal de {self.timeout} s.") from exc
        except OSError as exc:
            raise JennyInvalidExecutableError(f"Impossible d'exécuter {self.executable} : {exc}") from exc

    def run(self, dimensions: Sequence[int], strength: int, seed: int | None = None) -> JennyRun:
        command = self.build_command(dimensions, strength, seed)
        start = time.perf_counter()
        completed = self.run_raw(command[1:])
        duration = time.perf_counter() - start
        if completed.returncode != 0:
            raise JennyExecutionError(
                f"Jenny s'est terminé avec le code {completed.returncode}. "
                f"Sortie d'erreur : {completed.stderr.strip() or '(vide)'}"
            )
        rows = parse_output(completed.stdout, dimensions)
        return JennyRun(
            command=tuple(command),
            dimensions=tuple(dimensions),
            strength=strength,
            seed=seed,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
            rows=rows,
            duration_s=duration,
        )

    def verify(self) -> None:
        """Auto-test : ``jenny -n1 2`` doit produire exactement « 1a » puis « 1b »."""
        if self._verified:
            return
        try:
            completed = self.run_raw(["-n1", "2"])
            rows = parse_output(completed.stdout, [2]) if completed.returncode == 0 else None
        except JennyError as exc:
            raise JennyInvalidExecutableError(
                f"{self.executable} ne se comporte pas comme Jenny : {exc}"
            ) from exc
        if rows != (("1a",), ("1b",)):
            raise JennyInvalidExecutableError(
                f"{self.executable} ne se comporte pas comme Jenny (auto-test « -n1 2 » inattendu)."
            )
        self._verified = True
