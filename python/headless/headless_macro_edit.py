# Datei-Version: 1.01 (2026-11-19) - headless_macro_edit.py  # v1.01
# Name: headless_macro_edit.py
# Path: headless/headless_macro_edit.py
# Version: 1.01  # v1.01
# Last Update: 2026-11-19
# Author: Harold Linke
# Licence: LGPL V2.1
# History of Change:
#   1.00  2026-11-19  Syntax und Parameterzahl bei manuell bearbeiteten Makros pruefen
#   1.01  2026-11-19  Felder der Tabellenzeile (LEDs, InCnt, LocInCh) aus dem Makrotext ableiten wie der Auswahldialog
"""Syntax checks for manually edited configuration cells and the row fields derived from the macro."""  # v1.01
from __future__ import annotations

import math  # v1.01
import re


class MacroSyntaxError(ValueError):
    pass


def parse_call(text: str) -> tuple[str, list[str]] | None:
    """Parse a single macro call; directives and multi-line configurations are not calls.

    This checks the call structure, not the C++ meaning of parameter expressions.
    """
    text = text.strip()
    if not text or text.startswith(("#", "//")):
        return None
    match = re.match(r"([A-Za-z_][A-Za-z_0-9]*)\s*\(", text)
    if not match:
        raise MacroSyntaxError("Ein Makroaufruf muss mit einem Namen und einer öffnenden Klammer beginnen.")
    stack = [")"]
    args = []
    start = match.end()
    quote = None
    escaped = False
    pairs = {"(": ")", "[": "]", "{": "}"}
    for i in range(start, len(text)):
        ch = text[i]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch in pairs:
            stack.append(pairs[ch])
        elif ch in ")]}":
            if not stack or ch != stack.pop():
                raise MacroSyntaxError("Die Klammern im Makrotext stimmen nicht überein.")
            if not stack:
                value = text[start:i].strip()
                if value:
                    args.append(value)
                elif args:
                    raise MacroSyntaxError("Ein Makroparameter ist leer.")
                if text[i + 1:].strip():
                    raise MacroSyntaxError("Nach dem Makroaufruf steht zusätzlicher Text.")
                return match.group(1), args
        elif ch == "," and len(stack) == 1:
            value = text[start:i].strip()
            if not value:
                raise MacroSyntaxError("Ein Makroparameter ist leer.")
            args.append(value)
            start = i + 1
    raise MacroSyntaxError("Der Makroaufruf hat eine nicht geschlossene Klammer oder Zeichenkette.")


def expected_argument_count(template: str, parameter_types: dict[str, str]) -> int | None:
    """Count parameters only for ordinary, fully described fixed-arity templates."""
    try:
        parsed = parse_call(template)
    except MacroSyntaxError:
        return None
    if parsed is None:
        return None
    count = 0
    for parameter in parsed[1]:
        if not re.fullmatch(r"#?[A-Za-z_][A-Za-z_0-9]*", parameter):
            return None
        if parameter.startswith("#") or parameter in ("LED", "InCh", "Cx", "B_LED_Cx"):
            count += 1
        elif parameter not in parameter_types:
            return None
        else:
            count += {"RGB": 3, "RGB2": 6}.get(parameter_types[parameter], 1)
    return count


# Row fields derived from the macro (same rules as the selection dialog in M09_Select_Macro)  # v1.01
HOUSE_LIKE_TYPES = ("House", "ColTab", "PattConf")  # v1.01: these macros are only filled by their own dialogs  # v1.01


def cell_text(value) -> str:  # v1.01
    """Cell value as text; whole numbers without decimals."""
    if value is None:
        return ""
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value).strip()


def named_argument(template: str, args: list[str], name: str, parameter_types: dict[str, str]) -> str | None:  # v1.01
    """Value of the template parameter 'name' in the argument list of a call (RGB parameters use 3, RGB2 use 6 arguments)."""
    try:
        parsed = parse_call(template)
    except MacroSyntaxError:
        return None
    if parsed is None:
        return None
    position = 0
    for parameter in parsed[1]:
        width = 1 if parameter.startswith("#") or parameter in ("LED", "InCh", "Cx", "B_LED_Cx") \
            else {"RGB": 3, "RGB2": 6}.get(parameter_types.get(parameter, ""), 1)
        if parameter == name:
            return args[position] if position < len(args) else None
        position += width
    return None


def cx_to_led_channel(cx: str, led_channels: int) -> str | None:  # v1.01
    count = abs(led_channels)
    if cx == "C_ALL":
        return "1"
    if cx in ("C1", "C2", "C3"):
        start = int(cx[1])
        return f"C{start}-{start + count - 1}"
    return {"C12": "C1-2", "C23": "C2-3"}.get(cx)


def led_spec(lib_leds, template: str, args: list[str], led_channels, parameter_types: dict[str, str]) -> str | None:  # v1.01
    """Content of the LEDs column for the macro; None if it can not be derived from the text."""
    spec = cell_text(lib_leds)
    if spec.startswith("LedCnt"):
        value = named_argument(template, args, spec, parameter_types)
        return value if value is not None and re.fullmatch(r"\d+", value) else None
    if spec == "Cx":
        cx = named_argument(template, args, "Cx", parameter_types) or named_argument(template, args, "B_LED_Cx", parameter_types)
        try:
            channels = int(float(cell_text(led_channels) or 0))
        except ValueError:
            channels = 0
        return cx_to_led_channel(cx, channels) if cx else None
    return spec


def input_count(mode, template: str, text: str, args: list[str], parameter_types: dict[str, str], count_inch) -> int | None:  # v1.01
    """Number of input channels used by the macro. count_inch(statement, mode) counts '#InCh' uses (Logic / Comma)."""
    mode = cell_text(mode)
    if mode in ("n", "States", "BinStates"):
        value = named_argument(template, args, "InCh_Cnt" if mode == "n" else mode, parameter_types)
        if value is None or not re.fullmatch(r"\d+", value):
            return None
        number = int(value)
        if mode != "BinStates":
            return number
        return math.ceil(math.log2(number)) if number > 0 else None
    if mode == "Logic":
        return count_inch(args[1], "Logic") if len(args) > 1 else None
    if mode == "2?":
        return count_inch(text.split("(", 1)[1], "Comma") or 2
    try:
        return int(float(mode)) if mode else 0
    except ValueError:
        return None


def macro_row_fields(lib: dict, text: str, parameter_types: dict[str, str], count_inch) -> dict | None:  # v1.01
    """Values of the row fields (leds, incnt, locinch) for a typed macro; None if the macro has its own dialog.

    lib: cells of the Lib_Macros row (typ, leds, incnt, locinch, sngled, template). Missing values are None.
    """
    if cell_text(lib.get("typ")) in HOUSE_LIKE_TYPES:
        return None
    parsed = parse_call(text)
    if parsed is None:
        return None
    template = cell_text(lib.get("template"))
    locinch = cell_text(lib.get("locinch"))
    return {"leds": led_spec(lib.get("leds"), template, parsed[1], lib.get("sngled"), parameter_types),
            "incnt": input_count(lib.get("incnt"), template, text, parsed[1], parameter_types, count_inch),
            "locinch": int(float(locinch)) if re.fullmatch(r"-?\d+(\.\d+)?", locinch) else 0}
