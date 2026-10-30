"""Tests de l'interface graphique : chaque bouton est réellement déclenché
(``invoke``) et l'on vérifie l'effet affiché. Ignorés si Tk est indisponible."""

from __future__ import annotations

import time

import pytest

tk = pytest.importorskip("tkinter")

pytestmark = pytest.mark.gui


@pytest.fixture(scope="module")
def tk_root():
    """UNE seule instance Tk pour le module (anomalie A5) : sous Windows, des
    créations répétées de Tk() ont échoué de façon intermittente (lecture de
    init.tcl impossible, « No error »). On réessaie avant de conclure."""
    last_error = None
    for _attempt in range(5):
        try:
            root = tk.Tk()
            break
        except tk.TclError as exc:  # pragma: no cover - dépend de l'environnement
            last_error = exc
            time.sleep(0.5)
    else:  # pragma: no cover
        pytest.skip(f"Affichage graphique indisponible après 5 tentatives : {last_error}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def app(tk_root):
    from quadratic_lab.gui.app import QuadraticLabApp

    window = tk.Toplevel(tk_root)
    window.withdraw()
    application = QuadraticLabApp(window)
    yield application
    window.destroy()


def test_window_title_and_tabs(app):
    assert app.root.title() == "QUADRATIC TESTING LAB"
    tabs = [app.notebook.tab(tab_id, "text") for tab_id in app.notebook.tabs()]
    assert tabs == ["A. Résolution", "B. Tests Uniwise", "C. Tests Pairwise", "D. Comparaison"]


def test_solver_view_solve_button(app):
    view = app.solver_view
    view.set_coefficients("1", "-3", "2")
    view.solve_button.invoke()
    assert "Deux racines réelles distinctes" in view.category_var.get()
    assert view.delta_var.get() == "Delta = 1"
    assert "x1 = 1" in view.solutions_var.get() and "x2 = 2" in view.solutions_var.get()
    assert view.explanation_text.get("1.0", "end").strip()


def test_solver_view_french_comma_and_invalid_input(app):
    view = app.solver_view
    view.set_coefficients("0,5", "-1,5", "1")
    view.solve_button.invoke()
    assert "x1 = 1" in view.solutions_var.get()
    view.set_coefficients("abc", "0", "1")
    view.solve_button.invoke()
    assert "invalide" in view.category_var.get().lower()


@pytest.mark.jenny
def test_uniwise_view_generate_then_execute(app, jenny_adapter):
    view = app.uniwise_view
    view.adapter = jenny_adapter
    view.execute_button.invoke()  # avant génération : message explicite, pas de plantage
    assert "générer" in view.status_var.get().lower()
    view.generate_button.invoke()
    assert "jenny -n1 5 5 5" in view.command_var.get()
    assert len(view.cases_table.get_children()) == len(view.suite.cases)
    view.execute_button.invoke()
    assert "100.0 %" in view.coverage_var.get()
    assert view.campaign.failed == 0
    assert "RÉUSSI" in view.cases_table.item(view.cases_table.get_children()[0], "values")


@pytest.mark.jenny
def test_pairwise_view_shows_75_pairs(app, jenny_adapter):
    view = app.pairwise_view
    view.adapter = jenny_adapter
    view.generate_button.invoke()
    view.execute_button.invoke()
    assert "75/75" in view.coverage_var.get()
    assert len(view.pairs_table.get_children()) == 75


@pytest.mark.jenny
def test_comparison_view(app, jenny_adapter):
    view = app.comparison_view
    view.adapter = jenny_adapter
    view.run_button.invoke()
    rows = [view.table.item(item, "values") for item in view.table.get_children()]
    methods = [row[0] for row in rows]
    assert methods == ["Uniwise", "Pairwise", "3-way (Jenny -n3)", "Exhaustif", "Ciblés"]
    assert len(view.mutation_table.get_children()) >= 8


@pytest.mark.jenny
def test_demonstration_mode_walks_through_all_steps(app, jenny_adapter):
    app.set_adapter(jenny_adapter)
    titles = []
    while app.demo.has_next():
        titles.append(app.demo.next_step())
    assert len(titles) == 8
    assert app.comparison_view.comparison is not None
    assert app.notebook.index(app.notebook.select()) == 3
    app.demo.reset()
    assert app.demo.has_next()


def test_jenny_unavailable_message_in_gui(app, monkeypatch, tmp_path):
    from quadratic_lab.jenny_adapter import ENV_VAR

    monkeypatch.setenv(ENV_VAR, str(tmp_path / "absent.exe"))
    view = app.uniwise_view
    view.adapter = None
    view.generate_button.invoke()
    assert "indisponible" in view.status_var.get().lower()
    assert view.suite is None
