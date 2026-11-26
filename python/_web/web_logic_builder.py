# Datei-Version: 1.02 (2026-11-25) - web_logic_builder.py
# ----------------------------------------------------------------------------------------------
# Name:           web_logic_builder.py
# Path:           _web/web_logic_builder.py
# Version:        1.02
# Last Update:    2026-11-25
# Author:         Harold Linke
# Licence:        LGPL V2.1
# History of Change:
#   1.00  2026-11-25  Neu (Version 5.26): Baukasten fuer logische Ausdruecke in disjunktiver Normalform (UND-Gruppen, mit ODER verbunden), Ersatz der
#   1.01  2026-11-25  Eingangsvariablen SwitchA#, SwitchB#, SwitchD# (1 bis 250) in der Auswahl (die ersten 16 je Gruppe, andere Nummern eintippen), Pruefung der Nummer (Version 5.28)
#   1.02  2026-11-25  Auswahl der Eingaenge in Gruppen (Eingang dieser Zeile, Variable der Tabelle, Schalter A, B, C, D, Eigener Name); Schalter mit Nummernfeld 1 bis 250, SwitchC aufgenommen (Version 5.29)
#                     Texteingabe 'A AND B OR A AND NOT C OR D' im Parameterformular der Funktion Logic. Wiederverwendbarer Baustein:
#                     reine Funktionen parse_dnf, format_dnf, describe_dnf, check_dnf, collect_variables und die Oberflaeche LogicBuilder
# ----------------------------------------------------------------------------------------------
"""Baukasten fuer logische Ausdruecke in disjunktiver Normalform (DNF).

Ein Ausdruck besteht aus Bedingungen (Zeilen), die mit ODER verbunden sind. Eine Bedingung besteht aus Eingaengen,
die mit UND verbunden sind; jeder Eingang kann mit "nicht" umgekehrt werden.

    A AND B OR A AND NOT C OR D     ->  (A und B) oder (A und nicht C) oder D

Das Makro bleibt unveraendert: Der Baukasten erzeugt denselben Text wie die bisherige Eingabe. Die Funktionen parse_dnf,
format_dnf, describe_dnf und check_dnf sind reine Funktionen (ohne Oberflaeche) und lassen sich einzeln pruefen.
Die Oberflaeche (LogicBuilder) kann fuer weitere Makros verwendet werden: Namen in FUNCS eintragen.
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

FUNCS = ("Logic",)                             # Makros, deren Parameter '...' der Baukasten bearbeitet
INCH = "#InCh"                                 # symbolische Variable: Eingang der Zeile (DCC, Selectrix, CAN)
SWITCH_FAMILIES = ("SwitchA", "SwitchB", "SwitchC", "SwitchD")   # Eingangsvariablen SwitchA1 ... SwitchA250 usw. (1.02: mit SwitchC)
SWITCH_MAX = 250                                # hoechste Nummer (Is_Switch_Var_then_Add_to_Ctr: 1..250)
SWITCH_RE = re.compile(r"^(Switch[A-D])(\d+)$")
INCH_RE = re.compile(r"^#InCh(\+\d+)?$")
INCH_LISTED = 8                                 # #InCh, #InCh+1 ... #InCh+7 stehen in der Auswahl
GROUPS = ("inch", "vars", "A", "B", "C", "D", "own")   # Gruppen der Eingaenge (1.02)
NAME_RE = re.compile(r"^#?[A-Za-z_][A-Za-z0-9_]*(\+\d+)?$")   # Variablenname, auch #InCh+1


def is_builder_func(name) -> bool:
    return str(name or "") in FUNCS


def group_of(name, variables=()) -> str:
    """Gruppe eines Eingangs: inch (#InCh, #InCh+n), A bis D (Switch<X><Nr>), vars (Variable der Tabelle), sonst own (eigener Name)."""
    name = str(name or "").strip()
    if INCH_RE.match(name):
        return "inch"
    m = SWITCH_RE.match(name)
    if m:
        return m.group(1)[-1]
    if name and name in (variables or ()):
        return "vars"
    return "own" if name else "inch"


# ------------------------------------------------------------------ reine Funktionen
def parse_dnf(text):
    """Text -> (Bedingungen, None) oder (None, Fehlertext).

    Bedingungen: Liste von Listen aus {"neg": bool, "name": str}. Leerer Text ergibt eine leere Bedingung.
    Klammern und andere Aufbauten, die keine DNF sind, werden mit einem Fehlertext abgelehnt."""
    toks = str(text or "").replace("\n", " ").replace("\t", " ").split()
    groups: list = [[]]
    neg = False
    want = True                                # als Naechstes wird ein Name erwartet
    for tok in toks:
        up = tok.upper()
        if up == "OR" or up == "AND":
            if want:
                return None, "Operator ohne Eingang davor: " + tok
            if up == "OR":
                groups.append([])
            want = True
            neg = False
        elif up == "NOT":
            if not want or neg:
                return None, "NOT an falscher Stelle"
            neg = True
        else:
            if not want:
                return None, "Zwischen '%s' und dem davor fehlt AND oder OR" % tok
            if "(" in tok or ")" in tok:
                return None, "Klammern sind nicht möglich"
            groups[-1].append({"neg": neg, "name": tok})
            neg = False
            want = False
    if toks and (want or neg):
        return None, "Der Ausdruck endet mit einem Operator"
    return groups, None


def format_dnf(groups) -> str:
    """Bedingungen -> Text fuer das Makro ('A AND B OR A AND NOT C OR D'). Leere Eingaenge und Bedingungen fallen weg."""
    parts = []
    for g in groups:
        items = [("NOT " if it.get("neg") else "") + str(it.get("name") or "").strip()
                 for it in g if str(it.get("name") or "").strip()]
        if items:
            parts.append(" AND ".join(items))
    return " OR ".join(parts)


def describe_dnf(groups, word_and="und", word_or="oder", word_not="nicht") -> str:
    """Klartext mit Klammern: '(A und nicht C) oder D'."""
    parts = []
    for g in groups:
        items = [(word_not + " " if it.get("neg") else "") + str(it.get("name") or "").strip()
                 for it in g if str(it.get("name") or "").strip()]
        if items:
            parts.append((" %s " % word_and).join(items))
    multi = len(parts) > 1
    return (" %s " % word_or).join(("(" + p + ")") if multi and (" %s " % word_and) in p else p for p in parts)


def check_dnf(groups, tr=lambda s: s) -> list:
    """Prueft die Bedingungen. Rueckgabe: Liste von Fehlertexten (leer = in Ordnung)."""
    errors = []
    n_names = 0
    for gi, g in enumerate(groups, 1):
        seen: dict = {}
        used = [it for it in g if str(it.get("name") or "").strip() or it.get("neg")]
        if not used and len(groups) > 1:
            errors.append(tr("Bedingung %d ist leer. Eingang wählen oder die Bedingung löschen.") % gi)
            continue
        for it in used:
            name = str(it.get("name") or "").strip()
            if not name:
                errors.append(tr("Bedingung %d: Es fehlt ein Eingang.") % gi)
                continue
            n_names += 1
            sm = SWITCH_RE.match(name)
            if sm and not 1 <= int(sm.group(2)) <= SWITCH_MAX:
                errors.append(tr("Bedingung %d: Die Nummer von '%s' muss zwischen 1 und 250 liegen.") % (gi, name))
                continue
            if not NAME_RE.match(name):
                errors.append(tr("Bedingung %d: '%s' ist kein gültiger Variablenname (Buchstaben, Ziffern und _, keine Leerzeichen).") % (gi, name))
                continue
            if name in seen:
                if seen[name] == bool(it.get("neg")):
                    errors.append(tr("Bedingung %d: '%s' kommt doppelt vor.") % (gi, name))
                else:
                    errors.append(tr("Bedingung %d: '%s' und 'nicht %s' zusammen sind nie erfüllt.") % (gi, name, name))
            seen[name] = bool(it.get("neg"))
    if n_names == 0 and not errors:
        errors.append(tr("Bitte mindestens einen Eingang angeben."))
    return errors


def split_args(text) -> list:
    """Argumente einer Makrozeile an den Kommas trennen (Klammern beachten)."""
    out, depth, cur = [], 0, ""
    for ch in str(text or ""):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    out.append(cur.strip())
    return out


def variables_in_line(macro_line, par_names_of, is_var_par) -> list:
    """Variablennamen einer Makrozeile (Zelle der Spalte Beleuchtung).

    par_names_of(name) liefert die Parameternamen des Makros (zum Beispiel ['DstVar', '...']) oder None,
    is_var_par(parname) sagt, ob der Parameter eine Variable ist. Fuer Logic zaehlen auch die Namen im Ausdruck."""
    found: list = []
    text = str(macro_line or "").replace("\n", " ")
    for m in re.finditer(r"([A-Za-z_]\w*)\s*\(([^()]*)\)", text):
        name, body = m.group(1), m.group(2)
        pars = par_names_of(name)
        if not pars:
            continue
        args = split_args(body)
        for i, par in enumerate(pars):
            if i >= len(args):
                break
            if is_var_par(par) and NAME_RE.match(args[i]) and not args[i].startswith("#"):
                found.append(args[i])
        if name in FUNCS:
            groups, err = parse_dnf(" ".join(args[1:]))
            if groups:
                for g in groups:
                    found += [it["name"] for it in g if NAME_RE.match(it["name"]) and not it["name"].startswith("#")]
    return found


def unique_sorted(names) -> list:
    seen, out = set(), []
    for n in names:
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return sorted(out, key=lambda s: s.lower())


# ------------------------------------------------------------------ Oberflaeche
class LogicBuilder:
    """Baukasten im Parameterformular. Mit .value (Text fuer das Makro) und errors() wie ein Eingabefeld benutzbar.

    Aufruf innerhalb des Dialogs: LogicBuilder(ui, aktueller_text, variablen, tr, titel)."""

    def __init__(self, ui, text, variables, tr, title=""):
        self.ui = ui
        self.tr = tr
        self.variables = [v for v in (variables or []) if v != INCH and not SWITCH_RE.match(v)]   # 1.02: Schalter und #InCh haben eigene Gruppen
        groups, err = parse_dnf(text)
        self.text_mode = groups is None
        self.groups = groups if groups else [[{"neg": False, "name": ""}]]
        if groups is not None and len(self.groups) == 1 and not self.groups[0]:
            self.groups = [[{"neg": False, "name": INCH}]]    # neuer Ausdruck: der Eingang dieser Zeile
        self.text_value = str(text or "")
        ui = self.ui
        with ui.column().classes("w-full gap-1"):
            if title:
                ui.label(title).classes("text-bold")
            if self.text_mode:
                ui.label(tr("Der Ausdruck lässt sich nicht als Bedingungen darstellen (%s). Er bleibt als Text bearbeitbar.") % tr(err)).classes("text-caption text-orange-9")
            self.col = ui.column().classes("w-full gap-2")
            self.text_in = ui.input(label=tr("Ausdruck als Text"), value=self.text_value).props("outlined dense").classes("w-full")
            self.text_in.tooltip(tr("Beispiel: A AND B OR A AND NOT C OR D"))
            self.text_in.on_value_change(lambda e: self._changed())
            self.preview = ui.label().classes("text-body2").style("white-space:pre-wrap")
            self.macro_lbl = ui.label().classes("text-caption").style("opacity:.75;font-family:monospace")
            self.err_lbl = ui.label().classes("text-negative").style("white-space:pre-wrap")
            self.hint = ui.label(tr("Art des Eingangs: „Eingang dieser Zeile“ (#InCh, über DCC, Selectrix oder CAN – weitere Eingänge der Zeile sind #InCh+1, #InCh+2 …), „Variable der Tabelle“, „Schalter A“ bis „Schalter D“ (SwitchA1 bis SwitchA250 usw.) oder „Eigener Name“.")).classes("text-caption").style("opacity:.75")
            self.sw = ui.switch(tr("Als Text bearbeiten"), value=self.text_mode, on_change=self._mode_changed)

            @ui.refreshable
            def groups_ui():
                self._build_groups()
            self._groups_ui = groups_ui
            with self.col:
                groups_ui()
        self._apply_mode()
        self._changed()

    # ---- Wert
    @property
    def value(self) -> str:
        return str(self.text_in.value or "").strip() if self.text_mode else format_dnf(self.groups)

    def errors(self) -> list:
        if self.text_mode:
            groups, err = parse_dnf(self.text_in.value)
            if groups is None:
                return [self.tr(err)]
            return check_dnf(groups, self.tr)
        return check_dnf(self.groups, self.tr)

    def show_errors(self, errs):
        self.err_lbl.set_text("\n".join(errs))

    # ---- Aufbau
    def _build_groups(self):
        ui, tr = self.ui, self.tr
        for gi, g in enumerate(self.groups):
            if gi > 0:
                ui.label(tr("ODER")).classes("text-bold text-primary").style("padding-left:8px")
            with ui.card().props("flat bordered").classes("w-full").style("padding:8px 12px"):
                with ui.row().classes("w-full items-center justify-between no-wrap"):
                    ui.label(tr("Bedingung %d: alle diese Eingänge treffen zu") % (gi + 1)).classes("text-caption")
                    if len(self.groups) > 1:
                        ui.button(icon="delete", on_click=lambda _=None, i=gi: self._del_group(i)).props("flat dense round size=sm").tooltip(tr("Bedingung löschen"))
                for ii, it in enumerate(g):
                    with ui.row().classes("items-center no-wrap").style("gap:8px"):
                        ui.label(tr("UND") if ii > 0 else "").classes("text-caption").style("width:32px;text-align:right")
                        ui.checkbox(tr("nicht"), value=bool(it.get("neg")), on_change=lambda e, it=it: self._set(it, "neg", bool(e.value)))
                        grp = it.get("grp") or group_of(it.get("name"), self.variables)
                        it["grp"] = grp
                        labels = {"inch": tr("Eingang dieser Zeile"), "vars": tr("Variable der Tabelle"), "A": tr("Schalter A"), "B": tr("Schalter B"),
                                  "C": tr("Schalter C"), "D": tr("Schalter D"), "own": tr("Eigener Name")}
                        ui.select(labels, value=grp, on_change=lambda e, it=it: self._group_changed(it, e.value)).props("outlined dense").classes("w-48").tooltip(tr("Art des Eingangs"))
                        nm = str(it.get("name") or "")
                        if grp == "inch":
                            opts = ["#InCh"] + ["#InCh+%d" % n for n in range(1, INCH_LISTED)]
                            if nm and nm not in opts:
                                opts.append(nm)
                            ui.select(opts, value=nm or None, with_input=True, new_value_mode="add-unique",
                                      on_change=lambda e, it=it: self._set(it, "name", str(e.value or "").strip())).props("outlined dense").classes("w-40")
                        elif grp == "vars":
                            opts = list(self.variables)
                            if nm and nm not in opts:
                                opts.append(nm)
                            ui.select(opts, value=nm or None, with_input=True, new_value_mode="add-unique",
                                      on_change=lambda e, it=it: self._set(it, "name", str(e.value or "").strip())).props("outlined dense").classes("w-56").tooltip(tr("Variable wählen oder einen Namen eintippen"))
                        elif grp in ("A", "B", "C", "D"):
                            m_ = SWITCH_RE.match(nm)
                            ui.number(label=tr("Nummer (1 bis 250)"), value=int(m_.group(2)) if m_ else None, min=1, max=SWITCH_MAX, step=1, precision=0,
                                      on_change=lambda e, it=it, grp=grp: self._set(it, "name", ("Switch%s%d" % (grp, int(e.value))) if e.value else "")).props("outlined dense").classes("w-44")
                        else:
                            ui.input(value=nm, label=tr("Name"), on_change=lambda e, it=it: self._set(it, "name", str(e.value or "").strip())).props("outlined dense").classes("w-56")
                        if len(g) > 1:
                            ui.button(icon="close", on_click=lambda _=None, g=g, it=it: self._del_item(g, it)).props("flat dense round size=sm").tooltip(tr("Eingang entfernen"))
                ui.button(tr("+ UND weiterer Eingang"), on_click=lambda _=None, g=g: self._add_item(g)).props("flat dense no-caps size=sm color=primary")
        ui.button(tr("+ ODER weitere Bedingung"), on_click=self._add_group).props("outline dense no-caps color=primary")

    # ---- Aktionen
    def _set(self, it, key, val):
        it[key] = val
        self._changed()

    def _group_changed(self, it, grp):
        if grp == it.get("grp"):
            return
        it["grp"] = grp
        it["name"] = INCH if grp == "inch" else ("Switch%s1" % grp if grp in ("A", "B", "C", "D") else "")
        self._groups_ui.refresh()
        self._changed()

    def _add_item(self, g):
        g.append({"neg": False, "name": "", "grp": "vars" if self.variables else "own"})
        self._groups_ui.refresh()
        self._changed()

    def _del_item(self, g, it):
        if it in g:
            g.remove(it)
        self._groups_ui.refresh()
        self._changed()

    def _add_group(self):
        self.groups.append([{"neg": False, "name": "", "grp": "vars" if self.variables else "own"}])
        self._groups_ui.refresh()
        self._changed()

    def _del_group(self, i):
        if 0 <= i < len(self.groups) and len(self.groups) > 1:
            del self.groups[i]
        self._groups_ui.refresh()
        self._changed()

    def _mode_changed(self, e):
        want_text = bool(e.value)
        if want_text == self.text_mode:
            return
        if want_text:
            self.text_in.value = format_dnf(self.groups)
            self.text_mode = True
        else:
            groups, err = parse_dnf(self.text_in.value)
            if groups is None:
                self.ui.notify(self.tr("Der Text lässt sich nicht als Bedingungen darstellen: %s") % self.tr(err), type="warning")
                self.sw.value = True
                return
            self.groups = groups if groups else [[{"neg": False, "name": ""}]]
            self.text_mode = False
            self._groups_ui.refresh()
        self._apply_mode()
        self._changed()

    def _apply_mode(self):
        self.col.set_visibility(not self.text_mode)
        self.text_in.set_visibility(self.text_mode)
        self.hint.set_visibility(not self.text_mode)

    def _changed(self):
        self.err_lbl.set_text("")
        tr = self.tr
        if self.text_mode:
            groups, err = parse_dnf(self.text_in.value)
        else:
            groups, err = self.groups, None
        if groups is None:
            self.preview.set_text("")
        else:
            d = describe_dnf(groups, tr("und"), tr("oder"), tr("nicht"))
            self.preview.set_text(tr("Das Ergebnis ist 1, wenn gilt: %s") % d if d else "")
        self.macro_lbl.set_text(tr("Im Makro: %s") % self.value if self.value else "")
