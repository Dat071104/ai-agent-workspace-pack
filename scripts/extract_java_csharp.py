#!/usr/bin/env python3
"""Regex extraction of Java and C# for the lite codegraph.

Neither language ships a parser with Python, so this is the same honest trade as
the JS/TS extractor: comments and string literals are blanked, then braces are
walked to learn which type and method each token sits in. That is far short of a
real parser, so `build_code_index.py` marks every Java/C# CALLS edge `weak`.

Per-file result matches `extract_js`/`extract_python`:
    {"symbols": {...}, "raw_calls": [...], "imports": [...], "import_names": {}}

Choices that keep the index honest:
    - Every type (class, interface, enum, record, struct) is kind `class`, because
      EXTENDS resolution only looks at classes. Methods are `Type.method`.
    - Constructors are `Type.<init>`, so `new Foo()` resolves to the class once.
    - Overloads are merged into one `Type.method` node and marked, never split:
      regex call sites cannot tell `save(int)` from `save(String)`, so the node
      keeps the first declaration's `line` and gains `"overloads": N` (N >= 2
      distinct declarations; absent for a single declaration).
    - Routes ride on the method symbol, as Python decorator routes do.
    - Generic arguments nest one level (`A<B<C>>`); deeper nesting is not seen as a call.
    - Java `import a.b.C;` becomes an IMPORTS lead. C# `using` names namespaces,
      not files, so C# contributes no import edges at all.
"""

from __future__ import annotations

import re
import sys
from bisect import bisect_right
from functools import lru_cache
from pathlib import Path

sys.dont_write_bytecode = True

# Not calls or methods: control flow and operators that look like `name(`.
KEYWORDS = {
    "if", "for", "foreach", "while", "switch", "catch", "return", "new", "throw",
    "using", "lock", "synchronized", "else", "do", "try", "typeof", "sizeof",
    "nameof", "checked", "unchecked", "fixed", "default", "when", "assert",
    "case", "base", "this", "super", "await", "yield", "where", "in", "is", "as",
}

# Comments and string/char literals. Verbatim/raw C# strings and Java text blocks
# come before the plain forms so the longer delimiter wins.
TOKEN_RE = re.compile(
    r'''//[^\n]*
    |/\*.*?(?:\*/|\Z)
    |"""(?:.*?)(?:"""|\Z)
    |\$?@\$?"(?:[^"]|"")*"
    |"(?:\\.|[^"\\\n])*"?
    |'(?:\\.|[^'\\\n])*'?''',
    re.S | re.X,
)
# One scan finds braces, type headers, and `name(` candidates in source order.
EVENT_RE = re.compile(
    r"(?P<brace>[{}])"
    r"|(?<![.\w@])(?P<tkind>class|interface|enum|struct|record(?:\s+(?:struct|class))?)"
    r"\s+(?P<tname>[A-Za-z_]\w*)"
    r"|(?<![\w$@])(?P<call>[A-Za-z_]\w*)(?:<(?:[\w.,\s?\[\]]|<[\w.,\s?\[\]]*>)+>)?\s*\("
)
# What may follow a method's `)`: Java throws, C# constraints and ctor chaining,
# then the body opener. `;` is accepted only for bodiless interface/abstract members.
DECL_TAIL_RE = re.compile(
    r"\s*(?:throws\s+[\w.,\s<>]+?)?\s*(?:where\s+[^{;=]+?)?"
    r"\s*(?::\s*(?:base|this)\s*\([^)]*\))?\s*(\{|=>|;)"
)
JAVA_MAPPING_RE = re.compile(r"@(Get|Post|Put|Delete|Patch|Request)Mapping\b(?:\s*\(([^)]*)\))?")
CS_ROUTE_RE = re.compile(r"\[\s*(?:Http(Get|Post|Put|Delete|Patch)|(Route))\b(?:\s*\(([^)]*)\))?")
JAVA_IMPORT_RE = re.compile(r"^\s*import\s+(static\s+)?([\w.]+?)(\.\*)?\s*;", re.M)
JAVA_PACKAGE_RE = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.M)


def blank_tokens(text: str, keep_strings: bool) -> str:
    """Blank comments (and, optionally, literals) without moving any character.

    Length and newlines are preserved so offsets and line numbers stay valid.
    """
    def repl(match: re.Match) -> str:
        token = match.group(0)
        if keep_strings and token[0] in "\"'$@":
            return token
        return re.sub(r"[^\n]", " ", token)

    return TOKEN_RE.sub(repl, text)


def neutralize_paren_braces(blank: str) -> str:
    """Blank `{`/`}` that sit inside parentheses, keeping every offset."""
    out, depth = [], 0
    for ch in blank:
        depth += ch == "("
        depth -= ch == ")" and depth > 0
        out.append(" " if ch in "{}" and depth else ch)
    return "".join(out)


def _clean_bases(raw: list[str]) -> list[str]:
    bases = []
    for item in raw:
        name = item.strip().split(".")[-1].strip()
        if re.fullmatch(r"[A-Za-z_]\w*", name):
            bases.append(name)
    return bases


def parse_bases(tail: str, lang: str) -> list[str]:
    """Base types from the text between a type's name and its opening brace."""
    tail = re.split(r"\bwhere\b", tail)[0]
    previous = None
    while previous != tail:  # generics and primary-constructor parameters nest
        previous = tail
        tail = re.sub(r"<[^<>]*>|\([^()]*\)", "", tail)
    if lang == "csharp":
        return _clean_bases(tail.split(":", 1)[1].split(",")) if ":" in tail else []
    found: list[str] = []
    for keyword in ("extends", "implements"):
        part = re.search(rf"\b{keyword}\s+(.*?)(?=\bimplements\b|\bpermits\b|$)", tail, re.S)
        if part:
            found += part.group(1).split(",")
    return _clean_bases(found)


def _first_argument(expr: str) -> str:
    """Text up to the first top-level `,` or unmatched closer, skipping string contents."""
    depth, quoted = 0, False
    for i, ch in enumerate(expr):
        if ch == '"':
            quoted = not quoted
        elif quoted:
            continue
        elif ch in ",)}]" and depth == 0:
            return expr[:i]
        else:
            depth += (ch in "({[") - (ch in ")}]")
    return expr


def _first_string(args: str) -> str:
    """The path literal; "" when none is given; a marker for any other expression,
    so `"/api" + SUFFIX` is unresolved rather than reported as `/api`."""
    named = re.search(r"\b(?:value|path)\s*=\s*", args)
    if named:
        expr = args[named.end():]
    elif not args.strip() or re.match(r"\s*[A-Za-z_]\w*\s*=(?!=)", args):
        return ""  # no path, only named options such as `produces = ...`
    else:
        expr = args
    expr = _first_argument(expr).strip()
    if expr.startswith("{"):  # Java array of paths: the first one
        expr = _first_argument(expr[1:]).strip()
    literal = re.fullmatch(r'@?"([^"]*)"', expr)  # `@"..."` is a C# verbatim string
    if literal:
        return literal.group(1)
    return f"<unresolved:{' '.join(expr.split())}>" if expr else ""


def parse_route(annotations: str, lang: str) -> tuple[str, str] | None:
    """(VERB, path) from a Spring mapping or ASP.NET route attribute, if any."""
    if lang == "java":
        found = JAVA_MAPPING_RE.search(annotations)
        if not found:
            return None
        verb = found.group(1).upper()
        args = found.group(2) or ""
        if verb == "REQUEST":
            method = re.search(r"RequestMethod\.(\w+)", args)
            verb = method.group(1).upper() if method else "ANY"
        return verb, _first_string(args)
    verb, path, seen = "", "", False
    for found in CS_ROUTE_RE.finditer(annotations):
        seen = True
        verb = verb or (found.group(1) or "").upper()  # group 1 is empty for [Route]
        path = path or _first_string(found.group(3) or "")
    return (verb or "ANY", path) if seen else None


def join_route(base: str, path: str, controller: str, action: str, lang: str) -> str:
    """Class-level prefix + method path, ASP.NET tokens expanded, leading slash."""
    if lang == "csharp" and path.startswith(("/", "~/")):
        base = ""  # an absolute action route ignores the controller prefix
    for piece in (path, base):  # a constant we cannot read: say so, never invent a path
        if piece.startswith("<unresolved:"):
            return piece
    parts = [p.strip("/") for p in (base, path) if p.strip("/")]
    joined = "/".join(parts)
    joined = re.sub(r"\[controller\]", controller.removesuffix("Controller").lower(), joined, flags=re.I)
    joined = re.sub(r"\[action\]", action.lower(), joined, flags=re.I)
    return "/" + joined.lstrip("~/")


class Scanner:
    """One pass over a blanked source file, tracking which type/method is open."""

    def __init__(self, text: str, lang: str) -> None:
        self.lang = lang
        self.blank = blank_tokens(text, keep_strings=False)
        self.visible = blank_tokens(text, keep_strings=True)  # same offsets, strings kept
        self.outside_parens = neutralize_paren_braces(self.blank)  # `@Get({"/a"})` is not a block
        self.newlines = [i for i, ch in enumerate(text) if ch == "\n"]
        self.symbols: dict[str, dict] = {}
        self.declarations: dict[str, set[int]] = {}  # method qualname -> declaration offsets
        self.raw_calls: list[dict] = []
        self.class_base: dict[str, str] = {}  # type qualname -> class-level route prefix
        self.expr_ranges: list[tuple[int, int, str]] = []  # C# `=>` bodies: (start, end, owner)
        # Brace stack entries: (kind, qualname, is_interface); kind is type/method/other.
        self.stack: list[tuple[str, str, bool]] = []
        self.pending: tuple[str, str, bool] | None = None  # claimed by the next `{`
        self.pos = 0

    def line_at(self, index: int) -> int:
        return bisect_right(self.newlines, index - 1) + 1

    def statement_start(self, index: int) -> int:
        return max(self.outside_parens.rfind(ch, 0, index) for ch in ";{}") + 1

    def annotations(self, index: int) -> str:
        return self.visible[self.statement_start(index):index]

    def owner_at(self, index: int) -> str:
        for start, end, qual in self.expr_ranges:
            if start <= index < end:
                return qual
        for kind, qual, _ in reversed(self.stack):
            if kind == "method":
                return qual
        return "<module>"

    def enclosing_type(self) -> tuple[str, bool]:
        for kind, qual, is_interface in reversed(self.stack):
            if kind == "type":
                return qual, is_interface
        return "", False

    def run(self) -> None:
        while True:
            match = EVENT_RE.search(self.blank, self.pos)
            if not match:
                return
            self.pos = match.end()
            if match.group("brace"):
                self.on_brace(match.group("brace"))
            elif match.group("tkind"):
                self.on_type(match)
            else:
                self.on_call(match)

    def on_brace(self, brace: str) -> None:
        if brace == "{":
            self.stack.append(self.pending or ("other", "", False))
            self.pending = None
        elif self.stack:
            self.stack.pop()

    def on_type(self, match: re.Match) -> None:
        name = match.group("tname")
        if name in KEYWORDS:
            return
        outer, _ = self.enclosing_type()
        qual = f"{outer}.{name}" if outer else name
        end = re.compile(r"[{;]").search(self.blank, self.pos)
        tail_end = end.start() if end else len(self.blank)
        self.symbols.setdefault(qual, {
            "kind": "class",
            "name": name,
            "line": self.line_at(match.start()),
            "bases": parse_bases(self.blank[self.pos:tail_end], self.lang),
        })
        route = parse_route(self.annotations(match.start()), self.lang)
        if route:
            self.class_base[qual] = route[1]
        if end and self.blank[tail_end] == "{":
            self.pending = ("type", qual, match.group("tkind") == "interface")
        self.pos = tail_end  # the tail holds bases and record parameters, not calls

    def method_decl(self, match: re.Match, before: str, lead: str) -> re.Match | None:
        """The text after `)` when `name(` opens a member declaration, else None."""
        top = self.stack[-1] if self.stack else ("other", "", False)
        if top[0] != "type" or before.endswith("."):
            return None
        if before and not (before[-1] in "]>?)" or before[-1].isalnum() or before[-1] == "_"):
            return None
        if re.search(r"\b(?:new|return|throw|else|case|await|yield)$", before):
            return None
        depth, close = 0, match.end() - 1
        for close in range(close, len(self.blank)):
            depth += self.blank[close] == "("
            depth -= self.blank[close] == ")"
            if depth == 0:
                break
        tail = DECL_TAIL_RE.match(self.blank, close + 1)
        if tail and (tail.group(1) != ";" or top[2] or "abstract" in lead):
            return tail
        return None

    def on_call(self, match: re.Match) -> None:
        name = match.group("call")
        if name in KEYWORDS:
            return
        start = match.start("call")
        lead = self.blank[self.statement_start(start):start]
        before = lead.rstrip()
        if before.endswith(("@", "[")):
            return  # annotation or attribute name, not a call
        decl = self.method_decl(match, before, lead)
        if decl is not None:
            self.on_method(name, start, decl)
        else:  # library-named calls (get, Add) may be project methods: resolution decides
            self.raw_calls.append({
                "from": self.owner_at(start), "name": name,
                "attr": before.endswith("."), "line": self.line_at(start),
            })

    def on_method(self, name: str, start: int, decl: re.Match) -> None:
        type_qual, _ = self.enclosing_type()
        type_name = type_qual.rsplit(".", 1)[-1]
        member = "<init>" if name == type_name else name
        qual = f"{type_qual}.{member}"
        info = self.symbols.setdefault(qual, {
            "kind": "method", "name": member, "line": self.line_at(start), "bases": [],
        })
        starts = self.declarations.setdefault(qual, set())
        starts.add(start)
        if len(starts) > 1:  # merged, not split: mark it so consumers can tell
            info["overloads"] = len(starts)
        route = parse_route(self.annotations(start), self.lang)
        if route and "route" not in info:
            prefix = self.class_base.get(type_qual, "")
            info["route"] = f"{route[0]} " + join_route(prefix, route[1], type_name, name, self.lang)
        if decl.group(1) == "{":
            self.pending = ("method", qual, False)
        elif decl.group(1) == "=>":
            end = self.blank.find(";", decl.end())
            self.expr_ranges.append((decl.end(), len(self.blank) if end < 0 else end, qual))
        self.pos = decl.start(1)  # the parameter list is not a call site


def extract(path: Path, lang: str) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    scanner = Scanner(text, lang)
    scanner.run()
    imports = java_imports(scanner.blank) if lang == "java" else []
    return {
        "symbols": scanner.symbols,
        "raw_calls": scanner.raw_calls,
        "imports": imports,
        "import_names": {},
    }


def java_imports(blank_text: str) -> list[str]:
    """`import a.b.C;` names. Static and wildcard imports name no single file."""
    return [
        m.group(2) for m in JAVA_IMPORT_RE.finditer(blank_text)
        if not m.group(1) and not m.group(3)
    ]


def java_file_imports(path: Path) -> list[str]:
    """Import names for the file-level dependency graph (REPO_MAP, scan_deps)."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    return java_imports(blank_tokens(text, keep_strings=False))


def extract_java(path: Path, rel: str) -> dict:
    return extract(path, "java")


def extract_csharp(path: Path, rel: str) -> dict:
    return extract(path, "csharp")


@lru_cache(maxsize=1024)
def _java_source_root(source: str, mtime_ns: int) -> Path | None:
    """Directory the file's `package` line is relative to, or None if unknown."""
    path = Path(source)
    found = JAVA_PACKAGE_RE.search(blank_tokens(path.read_text(encoding="utf-8", errors="ignore"), False))
    if not found:
        return None
    parts = found.group(1).split(".")
    here = path.parent
    if len(here.parts) < len(parts) or list(here.parts[-len(parts):]) != parts:
        return None  # directory layout does not match the package line
    return here.parents[len(parts) - 1]


def resolve_java_import(root: Path, source: Path, name: str) -> tuple[Path | None, str]:
    """Resolve `a.b.C` to `<source root>/a/b/C.java`; same convention as resolve_import.

    The source root is inferred from the importing file's own `package` line, so
    a hit is `heuristic`: other modules or generated sources are invisible here.
    A nested type (`a.b.Outer.Inner`) falls back to its enclosing top-level file.
    """
    try:
        source_root = _java_source_root(str(source), source.stat().st_mtime_ns)
    except OSError:
        return None, ""
    parts = [p for p in name.split(".") if p]
    if source_root is None or len(parts) < 2:
        return None, ""
    for end in range(len(parts), 1, -1):
        target = source_root.joinpath(*parts[:end]).with_suffix(".java")
        if target.is_file():
            try:
                target.relative_to(root)
            except ValueError:
                return None, ""
            return target, "heuristic"
    return None, ""
