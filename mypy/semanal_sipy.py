"""Semantic analysis of sipy's `_aliases` unit-equivalence special form.

This is conceptually part of mypy.semanal (semantic analyzer pass 2), and
follows the structure of mypy.semanal_newtype: a small assignment-shaped
special form recognized and interpreted directly during semantic analysis,
rather than type-checked as ordinary Python.

`_aliases` records equivalences between an already-declared SI unit class and
a unit-computation expression, e.g.:

    _aliases = [
        (Hz, 1 / Sec),
    ]

`1 / Sec` here uses the same arithmetic syntax already legal in unit-type
annotation position (e.g. `M/Sec**2`); ordinary operator-overload checking has
no reason to understand it (that's exactly why ComputedType/CompoundType exist
as synthetic ProperTypes mypy's structural typing can't otherwise express), so
this form is interpreted directly rather than being left to normal expression
checking.
"""

from __future__ import annotations

from mypy import sipy
from mypy.nodes import AssignmentStmt, Expression, ListExpr, MypyFile, NameExpr, TupleExpr, TypeInfo
from mypy.semanal_shared import SemanticAnalyzerInterface
from mypy.sipy import UnitExprError, interpret_unit_expr, is_info_sipy_base, is_sipy_aliases_assignment
from mypy.types import Instance, ProperType, ComputedType


class SipyAliasAnalyzer:
    def __init__(self, api: SemanticAnalyzerInterface) -> None:
        self.api = api

    def process_sipy_aliases_declaration(self, s: AssignmentStmt, cur_file: MypyFile) -> bool:
        """Check if `s` declares sipy's `_aliases` unit-equivalence list; if so,
        interpret it and record the result in mypy.sipy.

        Returns True if `s` was recognized as this special form at all (in
        which case it's a special form, whether or not its entries all
        validated cleanly -- validation failures are reported via self.api.fail
        without preventing the recognized entries from being retained).

        The result is recorded in mypy.sipy rather than on `cur_file` because
        only the one unit-definitions module ever declares it; build.py reads
        it from there once, after this module has been analyzed. Semantic
        analysis may revisit this statement across passes, so this overwrites
        rather than appending -- the declaration is the single source of truth
        each time it's re-analyzed.
        """
        if not is_sipy_aliases_assignment(s, cur_file.fullname):
            return False
        assert isinstance(s.rvalue, ListExpr)

        aliases: list[tuple[Instance, (ComputedType | Instance)]] = []
        for item in s.rvalue.items:
            pair = self._process_one(item)
            if pair is not None:
                aliases.append(pair)
        sipy.unit_aliases = aliases
        return True

    def _process_one(self, item: Expression) -> tuple[Instance, (ComputedType | Instance)] | None:
        if not (isinstance(item, TupleExpr) and len(item.items) == 2):
            self.api.fail(
                "Each entry in `_aliases` must be a 2-tuple (unit type, unit expression)", item
            )
            return None
        name_expr, target_expr = item.items
        if not (
            isinstance(name_expr, NameExpr)
            and isinstance(name_expr.node, TypeInfo)
            and is_info_sipy_base(name_expr.node)
        ):
            self.api.fail(
                "First element of an `_aliases` entry must be an SI unit type", name_expr
            )
            return None
        leaf = Instance(name_expr.node, ())

        try:
            target = interpret_unit_expr(target_expr)
        except UnitExprError:
            self.api.fail(
                "Second element of an `_aliases` entry must be a unit expression", target_expr
            )
            return None
        if target is None:
            self.api.fail(
                "Second element of an `_aliases` entry must be a unit expression", target_expr
            )
            return None
        return leaf, target
