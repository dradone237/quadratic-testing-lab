"""Rapports de tests (S-62) : CSV, JSON et rapport de validation Markdown.

Toutes les statistiques sont calculées à partir des objets réellement
produits par l'exécution ; rien n'est saisi à la main. Les résultats pytest
et la couverture de code ne sont repris que s'ils existent sur disque
(``pytest_junit.xml``, ``coverage.json``) ; sinon le rapport l'indique.
"""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from datetime import datetime
from decimal import Context, Decimal
from fractions import Fraction
from pathlib import Path

from .combinatorial import GeneratedSuite, Method
from .jenny_adapter import project_root
from .mapping import DEFAULT_DOMAIN, mapping_rows
from .models import MATH_CATEGORIES, Category, Status
from .oracle import REL_TOL, OracleExpectation, expected_result
from .runner import COMPARISON_ORDER, CampaignResult, CaseOutcome, ComparisonResult
from .solver import format_exact, format_number, format_roots

REPORTS_DIR = project_root() / "reports"

CSV_COLUMNS = [
    "id",
    "methode",
    "combinaison_jenny",
    "a",
    "b",
    "c",
    "discriminant",
    "categorie_attendue",
    "categorie_obtenue",
    "racines_attendues",
    "racines_calculees",
    "comparaison",
    "statut",
    "message_erreur",
]

#: Anomalies réellement rencontrées pendant le développement (journal).
ANOMALIES = [
    {
        "id": "A1",
        "constat": "Deux tests comparaient le solveur à une valeur de référence calculée avec les opérateurs "
        "Decimal (-x, (√5 - 1)/2) : ces opérateurs arrondissent au contexte par défaut (28 chiffres).",
        "cause": "Défaut dans les TESTS, pas dans le solveur (qui était juste à 50 chiffres).",
        "correction": "Calculs de référence faits dans un contexte explicite à 60 chiffres (copy_negate, Context).",
        "test": "tests/test_solver.py::test_irrational_roots_sqrt2, ::test_coefficients_at_the_domain_limit",
    },
    {
        "id": "A2",
        "constat": "Un test « très grands coefficients » utilisait b = -3·10¹², hors du domaine |x| ≤ 10¹².",
        "cause": "Défaut dans le TEST ; le solveur avait correctement répondu INVALID_INPUT.",
        "correction": "Cas remplacé par 10¹¹(x-1)(x-2) ; test explicite du rejet juste hors limites ajouté.",
        "test": "tests/test_solver.py::test_coefficient_just_outside_the_domain_is_rejected",
    },
    {
        "id": "A3",
        "constat": "Jenny signale ses erreurs (ex. « dimensions must be smaller than 52 ») sur la sortie "
        "standard avec un code de retour 0.",
        "cause": "Comportement de l'outil tiers : le code de retour seul ne suffit pas.",
        "correction": "L'adaptateur rejette toute ligne commençant par « jenny: » (JennyExecutionError).",
        "test": "tests/test_jenny_adapter.py::test_real_jenny_reports_errors_on_stdout_with_exit_code_zero",
    },
    {
        "id": "A4",
        "constat": "Dans rapport_validation.md, le texte « |x| ≤ 10¹² » de l'anomalie A2 cassait le tableau "
        "Markdown (la barre verticale était lue comme un séparateur de colonnes).",
        "cause": "Défaut du générateur de rapport : contenu des cellules non échappé.",
        "correction": "Échappement systématique de « | » en « \\| » dans toutes les cellules de tableau.",
        "test": "tests/test_regression.py::test_a4_markdown_table_cells_are_escaped",
    },
    {
        "id": "A5",
        "constat": "Lors d'une exécution complète, un test GUI a été ignoré : Tk() n'a pas pu lire init.tcl "
        "(« couldn't read file … init.tcl: No error »), alors que le fichier existe.",
        "cause": "Environnement Windows : échec intermittent de lecture lors de créations répétées de Tk() "
        "dans le même processus (machine chargée).",
        "correction": "Une seule instance Tk par module de test (fenêtres Toplevel par test) et 5 tentatives "
        "avant de déclarer l'affichage indisponible.",
        "test": "tests/test_gui.py (fixtures tk_root et app)",
    },
    {
        "id": "A6",
        "constat": "Sous Ubuntu (clone frais), test_build_command_uniwise_and_pairwise échouait : chemin "
        "« /usr/bin/python3.12 » obtenu au lieu de « .venv/bin/python ».",
        "cause": "Défaut du TEST : sous Linux, le python d'un venv est un lien symbolique que find_jenny() "
        "résout ; le test supposait un chemin inchangé (vrai seulement sous Windows).",
        "correction": "Le test compare au chemin résolu par l'adaptateur.",
        "test": "tests/test_jenny_adapter.py::test_build_command_uniwise_and_pairwise",
    },
    {
        "id": "A7",
        "constat": "Jenny compilé tel quel sous Ubuntu 64 bits produit d'autres combinaisons (29 cas Pairwise au "
        "lieu de 28), incohérentes avec la documentation.",
        "cause": "jenny.c déclare ub4 (« 4 octets ») comme unsigned long, qui fait 8 octets sous Linux 64 bits : "
        "le générateur pseudo-aléatoire change.",
        "correction": "build_jenny.sh compile une copie où ub4/sb4 passent sur 32 bits (2 lignes) ; sorties "
        "-n1/-n2/-n3 vérifiées identiques octet par octet à Windows.",
        "test": "tests/test_jenny_adapter.py::test_real_jenny_matches_reference_outputs",
    },
]


# ---------------------------------------------------------------------------
# Mise en forme
# ---------------------------------------------------------------------------
def _fraction_to_decimal(value: Fraction, prec: int = 60) -> Decimal:
    ctx = Context(prec=prec)
    return ctx.divide(Decimal(value.numerator), Decimal(value.denominator))


def delta_text(expectation: OracleExpectation) -> str:
    if expectation.discriminant is None:
        return ""
    return format_exact(_fraction_to_decimal(expectation.discriminant, prec=120))


def _expected_roots_text(expectation: OracleExpectation) -> str:
    return " | ".join(format_roots([_fraction_to_decimal(r) for r in expectation.roots]))


def _row(method: str, case, expectation: OracleExpectation, outcome: CaseOutcome | None) -> dict:
    row = {
        "id": case.case_id,
        "methode": method,
        "combinaison_jenny": case.jenny_combination or "",
        "a": format_exact(case.a),
        "b": format_exact(case.b),
        "c": format_exact(case.c),
        "discriminant": delta_text(expectation),
        "categorie_attendue": expectation.category.value,
        "categorie_obtenue": "",
        "racines_attendues": _expected_roots_text(expectation),
        "racines_calculees": "",
        "comparaison": "",
        "statut": Status.NOT_RUN.label,
        "message_erreur": "",
    }
    if outcome is not None:
        row["statut"] = outcome.status.label
        row["message_erreur"] = outcome.error or ""
        if outcome.actual is not None:
            row["categorie_obtenue"] = outcome.actual.category.value
            row["racines_calculees"] = " | ".join(format_roots(outcome.actual.roots))
        if outcome.verdict is not None:
            row["comparaison"] = outcome.verdict.summary()
    return row


def case_rows(source: GeneratedSuite | CampaignResult) -> list[dict]:
    if isinstance(source, CampaignResult):
        method = source.method.value
        return [_row(method, o.case, o.expected, o) for o in source.outcomes]
    method = source.method.value
    return [_row(method, case, expected_result(case.a, case.b, case.c), None) for case in source.cases]


# ---------------------------------------------------------------------------
# Écriture des fichiers
# ---------------------------------------------------------------------------
def write_cases_csv(source: GeneratedSuite | CampaignResult, path: Path) -> Path:
    """CSV « ; » encodé en UTF-8 avec BOM (lisible directement par Excel)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, delimiter=";")
        writer.writeheader()
        writer.writerows(case_rows(source))
    return path


def write_jenny_raw(suite: GeneratedSuite, path: Path) -> Path | None:
    """Conserve la sortie brute de Jenny, preuve de son exécution réelle."""
    if suite.raw_output is None:
        return None
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    run = suite.jenny_run
    header = [
        f"# Commande      : {suite.command}",
        f"# Exécutable    : {suite.executable}",
        f"# Arguments     : {list(run.command[1:]) if run else ''}",
        f"# Code retour   : {run.returncode if run else ''}",
        f"# Durée (s)     : {run.duration_s:.6f}" if run else "# Durée (s)     :",
        f"# Date          : {datetime.now().isoformat(timespec='seconds')}",
        f"# Lignes        : {len(suite.cases)}",
        "# --- sortie standard brute de Jenny ci-dessous (non modifiée) ---",
    ]
    path.write_text("\n".join(header) + "\n" + suite.raw_output, encoding="utf-8")
    return path


def _coverage_json(campaign: CampaignResult, with_missing: bool = True) -> dict:
    result = {}
    for strength, report in campaign.coverage.items():
        entry = {"couverts": report.covered_count, "total": report.total, "pourcentage": report.percent}
        if with_missing:
            entry["manquants"] = [report.format_element(e) for e in report.missing]
        else:
            entry["nombre_manquants"] = len(report.missing)
        if report.out_of_domain:
            entry["valeurs_hors_matrice"] = [f"{name}={value}" for name, value in report.out_of_domain]
        result[f"{strength}-way"] = entry
    return result


def _categories_json(campaign: CampaignResult) -> dict:
    return {
        "atteintes": [c.value for c in MATH_CATEGORIES if c in campaign.categories.covered],
        "manquantes": [c.value for c in campaign.categories.missing],
        "repartition": {c.value: campaign.categories.counts.get(c, 0) for c in MATH_CATEGORIES},
    }


def campaign_dict(campaign: CampaignResult) -> dict:
    suite = campaign.suite
    return {
        "methode": suite.method.value,
        "libelle": suite.method.label,
        "generateur": suite.generator,
        "commande_jenny": suite.command,
        "executable": suite.executable,
        "date": datetime.now().isoformat(timespec="seconds"),
        "duree_generation_s": round(suite.duration_s, 6),
        "duree_execution_s": round(campaign.duration_s, 6),
        "tolerance_relative": f"1e-{len(str(REL_TOL.denominator)) - 1}",
        "statistiques": {
            "total": campaign.total,
            "reussis": campaign.passed,
            "echecs": campaign.failed,
            "erreurs": campaign.errors,
        },
        "couverture": _coverage_json(campaign),
        "categories": _categories_json(campaign),
        "sortie_brute_jenny": suite.raw_output,
        "cas": case_rows(campaign),
    }


def _write_json(data: dict, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_campaign_json(campaign: CampaignResult, path: Path) -> Path:
    return _write_json(campaign_dict(campaign), path)


def export_suite(suite: GeneratedSuite, out_dir: Path = REPORTS_DIR) -> list[Path]:
    """Fichiers de la commande ``generate`` (cas générés, non exécutés)."""
    out_dir = Path(out_dir)
    paths = [write_cases_csv(suite, out_dir / f"{suite.method.value}_cases.csv")]
    raw = write_jenny_raw(suite, out_dir / f"jenny_{suite.method.value}_raw.txt")
    return paths + ([raw] if raw else [])


def export_campaign(campaign: CampaignResult, out_dir: Path = REPORTS_DIR) -> list[Path]:
    out_dir = Path(out_dir)
    method = campaign.method.value
    paths = [
        write_cases_csv(campaign, out_dir / f"{method}_cases.csv"),
        write_campaign_json(campaign, out_dir / f"{method}_results.json"),
    ]
    raw = write_jenny_raw(campaign.suite, out_dir / f"jenny_{method}_raw.txt")
    return paths + ([raw] if raw else [])


def comparison_dict(comparison: ComparisonResult) -> dict:
    methods = {}
    mutation = comparison.mutation
    for method, campaign in comparison.campaigns.items():
        entry = {
            "libelle": method.label,
            "generateur": campaign.suite.generator,
            "commande_jenny": campaign.suite.command,
            "nombre_cas": campaign.total,
            "duree_generation_s": round(campaign.suite.duration_s, 6),
            "duree_execution_s": round(campaign.duration_s, 6),
            "reussis": campaign.passed,
            "echecs": campaign.failed,
            "erreurs": campaign.errors,
            "couverture": _coverage_json(campaign, with_missing=False),
            "categories": _categories_json(campaign),
        }
        if mutation is not None and method in mutation.methods:
            entry["mutants_tues"] = sorted(mutation.killed(method))
            entry["score_mutation_pourcentage"] = round(mutation.score(method), 2)
        methods[method.value] = entry
    data = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "methodes": methods,
        "indisponibles": {m.value: reason for m, reason in comparison.unavailable.items()},
    }
    if mutation is not None:
        data["mutation"] = {
            "mutants": [
                {"id": m.mutant_id, "titre": m.title, "description": m.description, "declencheur": m.trigger}
                for m in mutation.mutants
            ],
            "resultats": {
                method.value: {
                    m.mutant_id: {
                        "tue": mutation.detail(method, m.mutant_id).killed,
                        "cas": list(mutation.detail(method, m.mutant_id).killing_cases),
                    }
                    for m in mutation.mutants
                }
                for method in mutation.methods
            },
        }
    return data


def write_comparison_json(comparison: ComparisonResult, path: Path) -> Path:
    return _write_json(comparison_dict(comparison), path)


# ---------------------------------------------------------------------------
# Résultats pytest et couverture de code (s'ils existent)
# ---------------------------------------------------------------------------
def read_pytest_summary(junit_path: Path) -> dict | None:
    path = Path(junit_path)
    if not path.is_file():
        return None
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    duration = 0.0
    for suite in suites:
        for key in totals:
            totals[key] += int(suite.get(key, 0))
        duration += float(suite.get("time", 0))
    passed = totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
    return {
        "tests": totals["tests"],
        "echecs": totals["failures"],
        "erreurs": totals["errors"],
        "ignores": totals["skipped"],
        "reussis": passed,
        "duree_s": duration,
    }


def read_code_coverage(coverage_path: Path) -> dict | None:
    path = Path(coverage_path)
    if not path.is_file():
        return None
    totals = json.loads(path.read_text(encoding="utf-8"))["totals"]
    lines = 100.0 * totals["covered_lines"] / totals["num_statements"] if totals["num_statements"] else 100.0
    branches = 100.0 * totals["covered_branches"] / totals["num_branches"] if totals.get("num_branches") else 100.0
    return {
        "lignes_pourcentage": round(lines, 2),
        "branches_pourcentage": round(branches, 2),
        "global_pourcentage": round(totals["percent_covered"], 2),
        "lignes": f"{totals['covered_lines']}/{totals['num_statements']}",
        "branches": f"{totals.get('covered_branches', 0)}/{totals.get('num_branches', 0)}",
    }


# ---------------------------------------------------------------------------
# Rapport de validation Markdown
# ---------------------------------------------------------------------------
def _cell(value: object) -> str:
    """Échappe la barre verticale, qui casserait le tableau Markdown (ex. |x|)."""
    return str(value).replace("|", "\\|")


def _table(headers: list[str], rows: Iterable[Iterable[object]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(_cell(cell) for cell in row) + " |" for row in rows]
    return lines


def _ordered(comparison: ComparisonResult) -> list[tuple[Method, CampaignResult]]:
    return [(m, comparison.campaigns[m]) for m in COMPARISON_ORDER if m in comparison.campaigns]


def write_validation_report(
    comparison: ComparisonResult,
    path: Path,
    junit_path: Path | None = None,
    coverage_path: Path | None = None,
) -> Path:
    path = Path(path)
    junit = read_pytest_summary(junit_path) if junit_path else None
    code_cov = read_code_coverage(coverage_path) if coverage_path else None
    ordered = _ordered(comparison)
    out: list[str] = [
        "# Rapport de validation — QUADRATIC TESTING LAB",
        "",
        f"*Généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')} à partir des "
        "résultats réellement exécutés. Aucune valeur n'est saisie à la main.*",
        "",
        "## 1. Objectifs des tests",
        "",
        "- **Question mathématique** : le programme calcule-t-il correctement les solutions de a·x² + b·x + c = 0 ?",
        "- **Question de génie logiciel** : comment démontrer, par une stratégie de tests rigoureuse, qu'il "
        "fonctionne dans les scénarios prévus et gère correctement les situations anormales ?",
        "- Moyens : génération combinatoire réelle par Jenny (Uniwise `-n1`, Pairwise `-n2`, 3-way `-n3`), "
        "référence exhaustive (125 cas), cas ciblés calculés à la main, oracle indépendant (rationnels exacts), "
        "tests par propriétés (Hypothesis) et analyse de mutation.",
        f"- Critère de conformité d'un cas : même catégorie, discriminant identique (exact), racines à moins de "
        f"10⁻⁴⁰ en relatif, résidu relatif ≤ 10⁻⁴⁰, relations de Viète vérifiées.",
        "",
        "## 2. Partitions des coefficients",
        "",
        "Chaque coefficient est partitionné en classes d'équivalence : grand négatif, petit négatif, zéro, "
        "petit positif, grand positif. Pour b, ±2 remplace ±1 afin de pouvoir produire Δ = 0 (b² = 4ac avec a = c = ±1).",
        "",
        *_table(
            ["Étiquette Jenny", "Dimension", "Coefficient", "Valeur"],
            ([r["etiquette"], r["dimension"], r["coefficient"], r["valeur"]] for r in mapping_rows()),
        ),
        "",
        "Les lettres a…e sont des **étiquettes de valeurs** Jenny, sans rapport avec les noms des coefficients.",
        "",
        "## 3. Commandes Jenny exécutées",
        "",
    ]
    for method, campaign in ordered:
        suite = campaign.suite
        if suite.command:
            run = suite.jenny_run
            out.append(
                f"- `{suite.command}` — {len(suite.cases)} combinaisons, code retour {run.returncode if run else '?'}, "
                f"{(run.duration_s * 1000 if run else 0):.1f} ms — exécutable `{suite.executable}`"
            )
    for method, reason in comparison.unavailable.items():
        out.append(f"- {method.label} : **Jenny indisponible** — {reason}")
    out += ["", "Les sorties brutes sont conservées dans `reports/jenny_<méthode>_raw.txt`.", ""]

    out += ["## 4. Combinaisons générées", ""]
    for method, campaign in ordered:
        suite = campaign.suite
        if not suite.command:
            continue
        out.append(f"### {method.label} — `{suite.command}`")
        out.append("")
        if len(suite.cases) > 40:
            out.append(f"{len(suite.cases)} combinaisons (liste complète dans `{method.value}_cases.csv`).")
        else:
            out += _table(
                ["ID", "Combinaison", "a", "b", "c"],
                ([c.case_id, f"`{c.jenny_combination}`", c.a, c.b, c.c] for c in suite.cases),
            )
        out.append("")

    out += ["## 5. Cas réellement exécutés", ""]
    out += _table(
        ["Méthode", "Générateur", "Cas exécutés", *[c.value for c in MATH_CATEGORIES]],
        (
            [m.label, c.suite.generator, c.total, *[c.categories.counts.get(cat, 0) for cat in MATH_CATEGORIES]]
            for m, c in ordered
        ),
    )
    out.append("")

    out += ["## 6. Résultats", ""]
    out += _table(
        ["Méthode", "Cas", "Réussis", "Échecs", "Erreurs", "1-way", "2-way", "3-way", "Catégories", "Exécution (ms)"],
        (
            [
                m.label,
                c.total,
                c.passed,
                c.failed,
                c.errors,
                f"{c.coverage[1].percent:.1f} %",
                f"{c.coverage[2].percent:.1f} %",
                f"{c.coverage[3].percent:.1f} %",
                f"{len(c.categories.covered)}/{c.categories.total}",
                f"{c.duration_s * 1000:.1f}",
            ]
            for m, c in ordered
        ),
    )
    out.append("")
    if junit:
        out.append(
            f"**Suite pytest** : {junit['tests']} tests — {junit['reussis']} réussis, {junit['echecs']} échecs, "
            f"{junit['erreurs']} erreurs, {junit['ignores']} ignorés ({junit['duree_s']:.1f} s)."
        )
    else:
        out.append("**Suite pytest** : résultats non disponibles (lancer `tools/run_validation.ps1`).")
    out.append("")

    out += ["## 7. Couverture", ""]
    for m, c in ordered:
        notes = [f"1-way {c.coverage[1].summary()}", f"2-way {c.coverage[2].summary()}", f"3-way {c.coverage[3].summary()}"]
        missing = ", ".join(cat.value for cat in c.categories.missing) or "aucune"
        out.append(f"- **{m.label}** : {' ; '.join(notes)} ; catégories non atteintes : {missing}.")
        if c.coverage[1].out_of_domain:
            out.append("  (cas hors matrice pédagogique : la couverture t-wise n'y est pas l'objectif)")
    out.append("")
    if code_cov:
        out.append(
            f"**Couverture du code métier** (pytest-cov, GUI exclue) : lignes {code_cov['lignes_pourcentage']} % "
            f"({code_cov['lignes']}), branches {code_cov['branches_pourcentage']} % ({code_cov['branches']}). "
            "Six blocs sont exclus par `# pragma: no cover` : cinq gardes défensives inatteignables dans le "
            "domaine validé et la commande interactive `gui` (voir docs/RAPPORT_VALIDATION.md)."
        )
    else:
        out.append("**Couverture du code** : non disponible (lancer `tools/run_validation.ps1`).")
    out.append("")

    out += ["## 8. Écarts détectés", ""]
    deviations = [(m, o) for m, c in ordered for o in c.outcomes if o.status is not Status.PASS]
    if deviations:
        out += _table(
            ["Méthode", "Cas", "Statut", "Détail"],
            ([m.label, o.case.case_id, o.status.label, o.error or ""] for m, o in deviations),
        )
    else:
        total = sum(c.total for _, c in ordered)
        out.append(f"Aucun écart : les {total} cas exécutés sont conformes à l'oracle indépendant.")
    out.append("")
    mutation = comparison.mutation
    if mutation is not None:
        out.append("**Analyse de mutation** — capacité de chaque stratégie à détecter des défauts injectés :")
        out.append("")
        out += _table(
            ["Mutant", "Défaut injecté", "Déclencheur", *[m.label for m in mutation.methods]],
            (
                [
                    mut.mutant_id,
                    mut.title,
                    mut.trigger,
                    *[("tué" if mutation.detail(m, mut.mutant_id).killed else "**survit**") for m in mutation.methods],
                ]
                for mut in mutation.mutants
            ),
        )
        out.append(
            "| **Score** | | | " + " | ".join(f"**{mutation.score(m):.0f} %**" for m in mutation.methods) + " |"
        )
        out.append("")

    out += ["## 9. Anomalies corrigées", ""]
    out += _table(
        ["ID", "Constat", "Cause", "Correction", "Test de non-régression"],
        ([a["id"], a["constat"], a["cause"], a["correction"], f"`{a['test']}`"] for a in ANOMALIES),
    )
    out.append("")

    out += [
        "## 10. Limites de la stratégie",
        "",
        "- **Pairwise ≠ exhaustif** : 100 % des paires ne signifie pas 100 % des triplets ; un défaut qui ne se "
        "déclenche que pour une combinaison précise de trois valeurs peut échapper à Pairwise.",
    ]
    pairwise = comparison.campaigns.get(Method.PAIRWISE)
    if pairwise is not None:
        missing = ", ".join(c.value for c in pairwise.categories.missing) or "aucune"
        out.append(
            f"- **Branches non garanties** : la campagne Pairwise réelle ({pairwise.total} cas) n'atteint pas les "
            f"catégories suivantes : {missing}. D'où les cas ciblés."
        )
    out += [
        "- **Matrice réduite** : 5 valeurs par coefficient ne représentent pas les décimaux, les très petites ou "
        "très grandes valeurs ; ceux-ci sont couverts par les cas ciblés et les tests par propriétés.",
        "- **Oracle numérique** : pour les racines irrationnelles, la validation repose sur une tolérance "
        "(10⁻⁴⁰) ; elle prouve la proximité, pas l'égalité. Le discriminant et la catégorie sont, eux, vérifiés "
        "exactement.",
        "- **Moins de tests ≠ meilleure méthode** : le nombre de cas doit être mis en regard de la couverture et du "
        "score de mutation.",
        "- **Aucune stratégie de test ne prouve l'absence de défauts** ; elle augmente la confiance.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out), encoding="utf-8")
    return path


def export_comparison(
    comparison: ComparisonResult,
    out_dir: Path = REPORTS_DIR,
    junit_path: Path | None = None,
    coverage_path: Path | None = None,
) -> list[Path]:
    out_dir = Path(out_dir)
    paths: list[Path] = []
    for campaign in comparison.campaigns.values():
        paths += export_campaign(campaign, out_dir)
    paths.append(write_comparison_json(comparison, out_dir / "comparison.json"))
    junit_path = junit_path or out_dir / "pytest_junit.xml"
    coverage_path = coverage_path or out_dir / "coverage.json"
    paths.append(write_validation_report(comparison, out_dir / "rapport_validation.md", junit_path, coverage_path))
    return paths
