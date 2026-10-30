"""Interface en ligne de commande : ``python -m quadratic_lab`` (S-60).

Codes de sortie : 0 succès, 1 échec de tests, 2 erreur d'utilisation ou
saisie invalide, 3 Jenny indisponible.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections.abc import Sequence
from pathlib import Path

from .combinatorial import GeneratedSuite, Method, generate
from .jenny_adapter import BUILD_HINT, JennyAdapter, JennyError, project_root
from .mapping import mapping_rows
from .models import Category, Status
from .mutation import run_mutation_analysis
from .reporting import REPORTS_DIR, export_campaign, export_comparison, export_suite
from .runner import COMPARISON_ORDER, CampaignResult, compare_strategies, run_suite
from .solver import format_complex, format_exact, format_roots, solve
from .validation import DISPLAY_DIGITS, INTERNAL_PRECISION, InvalidCoefficientError, parse_user_input

EXIT_OK = 0
EXIT_TEST_FAILURE = 1
EXIT_INVALID = 2
EXIT_JENNY_UNAVAILABLE = 3

METHOD_CHOICES = [m.value for m in Method]

EPILOG = """Exemples :
  python -m quadratic_lab solve --a 1 --b -3 --c 2
  python -m quadratic_lab solve --a 1,5 --b 0 --c -6        (virgule décimale acceptée)
  python -m quadratic_lab generate --method uniwise
  python -m quadratic_lab generate --method pairwise
  python -m quadratic_lab generate --method exhaustive
  python -m quadratic_lab test --method uniwise
  python -m quadratic_lab test --method pairwise
  python -m quadratic_lab compare
  python -m quadratic_lab gui

Codes de sortie : 0 succès, 1 échec de tests, 2 saisie invalide, 3 Jenny indisponible."""


class FrenchHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        return super().add_usage(usage, actions, groups, prefix or "usage : ")


def _parser(prog: str | None = None, **kwargs) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=prog, add_help=False, formatter_class=FrenchHelpFormatter, **kwargs)
    parser._optionals.title = "options"
    parser.add_argument("-h", "--help", action="help", help="afficher cette aide et quitter")
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = _parser(
        "python -m quadratic_lab",
        description="QUADRATIC TESTING LAB — résolution et vérification robuste des équations du second degré "
        "avec Jenny, Uniwise et Pairwise Testing.",
        epilog=EPILOG,
    )
    sub = parser.add_subparsers(dest="command", title="commandes", metavar="COMMANDE")

    def add(name: str, help_text: str) -> argparse.ArgumentParser:
        return sub.add_parser(
            name, help=help_text, description=help_text, add_help=False, formatter_class=FrenchHelpFormatter
        )

    def with_help(p: argparse.ArgumentParser) -> argparse.ArgumentParser:
        p._optionals.title = "options"
        p.add_argument("-h", "--help", action="help", help="afficher cette aide et quitter")
        return p

    p = with_help(add("solve", "Résoudre a·x² + b·x + c = 0."))
    p.add_argument("--a", required=True, help="coefficient a (ex. 1, -2.5, 1,5, 1e-3)")
    p.add_argument("--b", required=True, help="coefficient b")
    p.add_argument("--c", required=True, help="coefficient c")
    p.add_argument(
        "--chiffres",
        type=int,
        default=DISPLAY_DIGITS,
        help=f"chiffres significatifs affichés (1 à {INTERNAL_PRECISION}, défaut {DISPLAY_DIGITS})",
    )
    p.add_argument("--complexe", action="store_true", help="afficher les racines complexes si Delta < 0")

    for name, text in (
        ("generate", "Générer un jeu de cas (Jenny pour uniwise/pairwise/triplewise)."),
        ("test", "Générer puis exécuter une campagne et la juger avec l'oracle."),
    ):
        p = with_help(add(name, text))
        p.add_argument("--method", required=True, choices=METHOD_CHOICES, help="méthode : " + ", ".join(METHOD_CHOICES))
        p.add_argument("--seed", type=int, default=None, help="graine de Jenny (option -s), facultative")
        p.add_argument("--output-dir", type=Path, default=REPORTS_DIR, help="dossier des rapports (défaut : reports)")

    p = with_help(add("compare", "Comparer toutes les stratégies et produire le rapport de validation."))
    p.add_argument("--output-dir", type=Path, default=REPORTS_DIR, help="dossier des rapports (défaut : reports)")
    p.add_argument("--sans-mutation", action="store_true", help="ne pas exécuter l'analyse de mutation")

    with_help(add("mutation", "Mesurer la détection de défauts injectés (mutants) par chaque stratégie."))
    with_help(add("mapping", "Afficher la table de correspondance étiquettes Jenny -> coefficients."))
    with_help(add("jenny", "Vérifier l'exécutable Jenny (chemin, empreinte, auto-test)."))
    with_help(add("gui", "Lancer l'interface graphique pédagogique."))
    return parser


# ---------------------------------------------------------------------------
# Utilitaires d'affichage
# ---------------------------------------------------------------------------
def _print_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> None:
    text_rows = [[str(cell) for cell in row] for row in rows]
    widths = [max(len(h), *(len(r[i]) for r in text_rows)) if text_rows else len(h) for i, h in enumerate(headers)]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("  ".join("-" * w for w in widths))
    for row in text_rows:
        print("  ".join(cell.ljust(w) for cell, w in zip(row, widths)))


def _error(message: str) -> None:
    print(f"Erreur : {message}", file=sys.stderr)


def _signed(value) -> str:
    text = format_exact(value)
    return f"({text})" if text.startswith("-") else text


# ---------------------------------------------------------------------------
# Commandes
# ---------------------------------------------------------------------------
def cmd_solve(args: argparse.Namespace) -> int:
    if not 1 <= args.chiffres <= INTERNAL_PRECISION:
        _error(f"--chiffres doit être compris entre 1 et {INTERNAL_PRECISION}.")
        return EXIT_INVALID
    try:
        a = parse_user_input(args.a, "a")
        b = parse_user_input(args.b, "b")
        c = parse_user_input(args.c, "c")
    except InvalidCoefficientError as exc:
        _error(str(exc))
        return EXIT_INVALID
    result = solve(a, b, c)
    print("QUADRATIC TESTING LAB — Résolution")
    print(f"Équation      : {_signed(a)}·x² + {_signed(b)}·x + {_signed(c)} = 0")
    print(f"Catégorie     : {result.category.label} ({result.category.value})")
    if result.discriminant is not None:
        print(f"Discriminant  : Delta = {format_exact(result.discriminant)}")
    roots = format_roots(result.roots, args.chiffres)
    if result.category is Category.TWO_REAL_ROOTS:
        print("Solutions     :")
        print(f"  x1 = {roots[0]}")
        print(f"  x2 = {roots[1]}")
    elif result.category in (Category.DOUBLE_REAL_ROOT, Category.LINEAR_ROOT):
        print(f"Solution      : x = {roots[0]}")
    elif result.category is Category.NO_REAL_ROOT:
        print("Solutions     : Aucune racine réelle.")
        if args.complexe:
            for index, (re, im) in enumerate(result.complex_roots, start=1):
                print(f"  z{index} = {format_complex(re, im, args.chiffres)}  (extension complexe, informative)")
    elif result.category is Category.INFINITE_SOLUTIONS:
        print("Solutions     : une infinité (tout réel x est solution).")
    else:
        print("Solutions     : Aucune solution.")
    print(f"Explication   : {result.explanation()}")
    print(f"Précision     : calcul interne {INTERNAL_PRECISION} chiffres, affichage {args.chiffres} chiffres.")
    return EXIT_OK


def _generate_or_report(method: str, seed: int | None) -> GeneratedSuite | None:
    try:
        return generate(method, seed=seed)
    except JennyError as exc:
        _error(f"Jenny indisponible — génération impossible, aucune simulation n'est faite.\n{exc}")
        return None


def _print_suite(suite: GeneratedSuite) -> None:
    print(f"Méthode       : {suite.method.label} ({suite.method.value})")
    print(f"Générateur    : {suite.generator}")
    if suite.command:
        print(f"Commande      : {suite.command}")
        print(f"Exécutable    : {suite.executable}")
        print("Sortie brute de Jenny :")
        for line in suite.raw_output.splitlines():
            print(f"  |{line}")
    print(f"Nombre de cas : {len(suite.cases)}")


def cmd_generate(args: argparse.Namespace) -> int:
    suite = _generate_or_report(args.method, args.seed)
    if suite is None:
        return EXIT_JENNY_UNAVAILABLE
    _print_suite(suite)
    _print_table(
        ["ID", "Combinaison", "a", "b", "c"],
        [[c.case_id, c.jenny_combination or "-", format_exact(c.a), format_exact(c.b), format_exact(c.c)] for c in suite.cases],
    )
    for path in export_suite(suite, args.output_dir):
        print(f"Fichier écrit : {path}")
    return EXIT_OK


def _print_campaign(campaign: CampaignResult) -> None:
    rows = []
    for outcome in campaign.outcomes:
        case = outcome.case
        rows.append(
            [
                case.case_id,
                case.jenny_combination or "-",
                format_exact(case.a),
                format_exact(case.b),
                format_exact(case.c),
                outcome.expected.category.value,
                outcome.actual.category.value if outcome.actual else "-",
                " | ".join(format_roots(outcome.actual.roots)) if outcome.actual else "-",
                outcome.status.label,
            ]
        )
    _print_table(["ID", "Jenny", "a", "b", "c", "Attendu", "Obtenu", "Racines", "Statut"], rows)
    print()
    print(
        f"Résultats     : {campaign.passed} réussis, {campaign.failed} échecs, {campaign.errors} erreurs "
        f"(sur {campaign.total}) en {campaign.duration_s * 1000:.1f} ms"
    )
    for strength, report in campaign.coverage.items():
        print(f"Couverture {strength}-way : {report.summary()}" + (" — COMPLÈTE" if report.is_complete else ""))
    missing = ", ".join(c.value for c in campaign.categories.missing) or "aucune"
    print(f"Catégories    : {len(campaign.categories.covered)}/{campaign.categories.total} atteintes ; manquantes : {missing}")
    for outcome in campaign.outcomes:
        if outcome.status is not Status.PASS:
            print(f"  {outcome.status.label} {outcome.case.case_id} : {outcome.error}")


def cmd_test(args: argparse.Namespace) -> int:
    suite = _generate_or_report(args.method, args.seed)
    if suite is None:
        return EXIT_JENNY_UNAVAILABLE
    _print_suite(suite)
    campaign = run_suite(suite)
    _print_campaign(campaign)
    for path in export_campaign(campaign, args.output_dir):
        print(f"Fichier écrit : {path}")
    return EXIT_OK if campaign.all_passed else EXIT_TEST_FAILURE


def cmd_compare(args: argparse.Namespace) -> int:
    comparison = compare_strategies(include_mutation=not args.sans_mutation)
    rows = []
    for method in COMPARISON_ORDER:
        if method in comparison.campaigns:
            c = comparison.campaigns[method]
            score = (
                f"{comparison.mutation.score(method):.0f} %" if comparison.mutation is not None else "-"
            )
            rows.append(
                [
                    method.label,
                    c.total,
                    f"{c.suite.duration_s * 1000:.1f}",
                    f"{c.duration_s * 1000:.1f}",
                    c.coverage[1].summary(),
                    c.coverage[2].summary(),
                    c.coverage[3].summary(),
                    f"{len(c.categories.covered)}/6",
                    f"{c.passed}/{c.failed}/{c.errors}",
                    score,
                ]
            )
        else:
            rows.append([method.label, "indisponible", "", "", "", "", "", "", "", ""])
    print("Comparaison des stratégies (valeurs mesurées)")
    _print_table(
        ["Méthode", "Cas", "Gén. ms", "Exéc. ms", "1-way", "2-way", "3-way", "Catég.", "OK/Échec/Err", "Mutation"],
        rows,
    )
    for method, reason in comparison.unavailable.items():
        _error(f"{method.label} : Jenny indisponible — {reason}")
    for path in export_comparison(comparison, args.output_dir):
        print(f"Fichier écrit : {path}")
    if comparison.unavailable:
        return EXIT_JENNY_UNAVAILABLE
    failures = any(not c.all_passed for c in comparison.campaigns.values())
    return EXIT_TEST_FAILURE if failures else EXIT_OK


def cmd_mutation(args: argparse.Namespace) -> int:
    suites = {}
    for method in COMPARISON_ORDER:
        try:
            suites[method] = generate(method)
        except JennyError as exc:
            _error(f"{method.label} ignoré : Jenny indisponible ({exc})")
    report = run_mutation_analysis(suites)
    print("Analyse de mutation : un mutant est « tué » si au moins un cas le détecte.")
    rows = [
        [mutant.mutant_id, mutant.title, *[("tué" if report.detail(m, mutant.mutant_id).killed else "SURVIT") for m in report.methods]]
        for mutant in report.mutants
    ]
    rows.append(["Score", "", *[f"{report.score(m):.0f} %" for m in report.methods]])
    _print_table(["Mutant", "Défaut injecté", *[m.label for m in report.methods]], rows)
    return EXIT_OK


def cmd_mapping(args: argparse.Namespace) -> int:
    print("Table de correspondance : les lettres sont des ÉTIQUETTES DE VALEURS Jenny,")
    print("et non les coefficients a, b, c. Exemple : « 1a 2c 3d » => a = -10, b = 0, c = 1.")
    _print_table(
        ["Étiquette", "Dimension", "Coefficient", "Valeur"],
        [[r["etiquette"], r["dimension"], r["coefficient"], r["valeur"]] for r in mapping_rows()],
    )
    return EXIT_OK


def cmd_jenny(args: argparse.Namespace) -> int:
    try:
        adapter = JennyAdapter()
        adapter.verify()
    except JennyError as exc:
        _error(f"Jenny indisponible : {exc}\n{BUILD_HINT}")
        return EXIT_JENNY_UNAVAILABLE
    digest = hashlib.sha256(adapter.executable.read_bytes()).hexdigest()
    source = project_root() / "tools" / "jenny" / "src" / "jenny.c"
    print(f"Exécutable    : {adapter.executable}")
    print(f"SHA-256       : {digest}")
    if source.is_file():
        print(f"Source        : {source}")
        print(f"SHA-256 source: {hashlib.sha256(source.read_bytes()).hexdigest()}")
    print("Auto-test     : « jenny -n1 2 » => 1a, 1b : OK")
    run = adapter.run([5, 5, 5], 1)
    print(f"Essai         : {run.command_line} => {len(run.rows)} combinaisons en {run.duration_s * 1000:.1f} ms")
    print("Jenny est opérationnel.")
    return EXIT_OK


def cmd_gui(args: argparse.Namespace) -> int:  # pragma: no cover - interface interactive
    from .gui.app import main as gui_main

    gui_main()
    return EXIT_OK


COMMANDS = {
    "solve": cmd_solve,
    "generate": cmd_generate,
    "test": cmd_test,
    "compare": cmd_compare,
    "mutation": cmd_mutation,
    "mapping": cmd_mapping,
    "jenny": cmd_jenny,
    "gui": cmd_gui,
}


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):  # pragma: no cover - flux non reconfigurable
            pass
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return EXIT_INVALID
    return COMMANDS[args.command](args)
