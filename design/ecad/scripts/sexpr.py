"""A minimal S-expression reader and writer for KiCad files (.kicad_sym, .kicad_mod).

A node is a Python list whose first item is its head symbol: ["pin", "passive", "line",
["at", 0, 3.81, 270], ...]. Atoms are `Sym` (bare symbols such as `yes` or `passive`), str
(quoted strings), int or float. `dumps` writes KiCad's layout: one node per line, nested
nodes indented with tabs, short leaf-only nodes kept on one line. It does not reproduce
KiCad's byte layout exactly; KiCad reads it and rewrites it on save.
"""
import re

_TOKEN = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)
_UNESCAPE = {"n": "\n", "t": "\t"}


class Sym(str):
    """A bare (unquoted) symbol atom."""


def loads(text):
    pos, stack, root = 0, [], []
    while True:
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            if text[pos:].strip():
                raise ValueError(f"unparsable text at offset {pos}: {text[pos:pos + 40]!r}")
            break
        pos = m.end()
        opn, cls, quoted, bare = m.groups()
        if opn:
            node = []
            (stack[-1] if stack else root).append(node)
            stack.append(node)
        elif cls:
            if not stack:
                raise ValueError(f"unbalanced ')' at offset {pos}")
            stack.pop()
        elif quoted is not None:
            stack[-1].append(re.sub(r"\\(.)", lambda e: _UNESCAPE.get(e.group(1), e.group(1)),
                                    quoted, flags=re.S))
        else:
            stack[-1].append(_atom(bare))
    if stack:
        raise ValueError("unbalanced '(' at end of text")
    if len(root) != 1:
        raise ValueError(f"expected one top-level node, found {len(root)}")
    return root[0]


def _atom(tok):
    if re.fullmatch(r"-?\d+", tok):
        return int(tok)
    if re.fullmatch(r"-?(\d+\.\d*|\.\d+|\d+)([eE]-?\d+)?", tok):
        return float(tok)
    return Sym(tok)


def _fmt_atom(a):
    if isinstance(a, Sym):
        return str(a)
    if isinstance(a, str):
        return ('"' + a.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
                .replace("\t", "\\t") + '"')
    if isinstance(a, bool):
        return "yes" if a else "no"
    if isinstance(a, float):
        s = f"{a:.6f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    return str(a)


def _fmt_items(items):
    """A node's leading atoms; the head (first item) is always bare, as KiCad writes it."""
    return " ".join(str(x) if i == 0 and isinstance(x, str) else _fmt_atom(x)
                    for i, x in enumerate(items))


def dumps(node, indent=0):
    tabs = "\t" * indent
    if not any(isinstance(x, list) for x in node):
        return tabs + "(" + _fmt_items(node) + ")"
    n = next(i for i, x in enumerate(node) if isinstance(x, list))
    out = [tabs + "(" + _fmt_items(node[:n])]
    for x in node[n:]:                       # keep the order, atoms after a list included
        out.append(dumps(x, indent + 1) if isinstance(x, list)
                   else "\t" * (indent + 1) + _fmt_atom(x))
    return "\n".join(out) + "\n" + tabs + ")"


def find(node, head):
    """The direct children of `node` whose head is `head`."""
    return [x for x in node if isinstance(x, list) and x and x[0] == head]


def first(node, head, default=None):
    found = find(node, head)
    return found[0] if found else default


def walk(node, head):
    """Every descendant (and `node` itself) whose head is `head`, depth first."""
    if isinstance(node, list):
        if node and node[0] == head:
            yield node
        for x in node:
            yield from walk(x, head)
