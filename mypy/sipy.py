from typing import ClassVar, Dict, List, Set, Tuple, cast, Sequence, Optional

from quiche.egraph import EMatch, Subst

import mypy.types
from mypy.nodes import AssignmentStmt, Expression, FuncDef, IntExpr, ListExpr, MypyFile, NameExpr, OpExpr, \
    SymbolNode, TypeAlias, TypeInfo
from mypy.type_visitor import T
from mypy.types import Instance, ProperType, AnyType, ComputedType, CompoundType, UnboundType, TypeVarType, \
    TypeAliasType, UninhabitedType, UnionType, Type, NoneType, CallableType, TupleType, TypeType, LiteralType, \
    UnpackType, PartialType, TypedDictType, Overloaded, TypeVarTupleType, Parameters, ParamSpecType, DeletedType, \
    ErasedType, PlaceholderType, RawExpressionType, EllipsisType, CallableArgument, TypeList

from quiche import EGraph, EClassID, ENode
from quiche.lang.expr_lang import ExprNode, ExprTree
from quiche.rewrite import Rule, ConditionalRule

base_type_name = "src.SUnit1.SIUnit.SIUnit"
dtype_name = "src.SUnit1.SIUnit.dtype"
base_type_module, base_type_classname = base_type_name.rsplit('.', maxsplit=1)
base_type_filename = "D:\\code\\units1\\src\\SUnit1\\SIUnit.py"

def get_base_type(modules: Dict[str,MypyFile]) -> TypeInfo | None:
    if base_type_module not in modules:
        return None
    module = modules[base_type_module]
    if base_type_classname not in module.names:
        return None
    node = module.names[base_type_classname].node
    if isinstance(node, TypeInfo):
        return node
    return None


def is_info_sipy_base(typenode: TypeInfo) -> bool:
    return typenode.has_base(base_type_name)

def is_funcdef_sipy_dtype(node: FuncDef) -> bool:
    if node is None: return False
    return node.fullname == dtype_name

def is_sipy_base(candidate: ProperType) -> bool:
    from mypy.type_visitor import SyntheticTypeVisitor
    class IsBase(SyntheticTypeVisitor[bool]):
        def visit_unbound_type(self, t: UnboundType) -> bool:
            return False
        def visit_any(self, t: AnyType) -> bool:
            return False
        def visit_none_type(self, t: NoneType) -> bool:
            return False
        def visit_literal_type(self, t: LiteralType) -> bool:
            return False
        def visit_type_var(self, t: TypeVarType) -> bool:
            return False
        def visit_callable_type(self, t: CallableType) -> bool:
            return False
        def visit_overloaded(self, t: Overloaded) -> bool:
            return False
        def visit_param_spec(self, t: ParamSpecType) -> bool:
            return False
        def visit_type_type(self, t: TypeType) -> bool:
            return False
        def visit_ellipsis_type(self, t: EllipsisType) -> bool:
            return False
        def visit_raw_expression_type(self, t: RawExpressionType) -> bool:
            return False
        def visit_uninhabited_type(self, t: UninhabitedType) -> bool:
            return False
        def visit_deleted_type(self, t: DeletedType) -> bool:
            return False
        def visit_type_var_tuple(self, t: TypeVarTupleType) -> bool:
            return False

        def visit_type_list(self, t: TypeList) -> bool:
            pass

        def visit_callable_argument(self, t: CallableArgument) -> bool:
            pass

        def visit_placeholder_type(self, t: PlaceholderType) -> bool:
            pass

        def visit_erased_type(self, t: ErasedType) -> bool:
            pass


        def visit_partial_type(self, t: PartialType) -> bool:
            pass


        def visit_typeddict_type(self, t: TypedDictType) -> bool:
            return any(item.accept(self) for item in t.items.values())
        def visit_union_type(self, t: UnionType) -> bool:
            return any(item.accept(self) for item in t.items)
        def visit_tuple_type(self, t: TupleType) -> bool:
            return any(item.accept(self) for item in t.items)
        def visit_parameters(self, t: Parameters) -> bool:
            return any(item.accept(self) for item in t.arg_types)


        def visit_type_alias_type(self, t: TypeAliasType) -> bool:
            if t.alias is None:
                return False
            return t.alias.target.accept(self)
        def visit_unpack_type(self, t: UnpackType) -> bool:
            return t.type.accept(self)

        def visit_compound_type(self, t: CompoundType) -> bool:
            return t.base_type.accept(self)

        def visit_computed_type(self, t: ComputedType) -> bool:
            lhs = not isinstance(t.left, ProperType) or t.left.accept(self)
            rhs = not isinstance(t.right, ProperType) or t.right.accept(self)
            return lhs and rhs

        def visit_instance(self, t: Instance) -> bool:
            return is_info_sipy_base(t.type)

    ret = candidate.accept(IsBase())
    assert ret is not None, candidate
    return ret


class UnitExprError(Exception):
    """Raised by interpret_unit_expr when an OpExpr looks like it's trying to be
    an SI-unit computation but has an invalid operand or operator. Callers
    report their own diagnostic using left/right/op_expr, since what counts as
    an appropriate fallback/error message differs by call site."""

    def __init__(self, left: "ProperType | int | None", right: "ProperType | int | None", op_expr: OpExpr) -> None:
        self.left = left
        self.right = right
        self.op_expr = op_expr


def interpret_unit_expr(o: Expression) -> Optional[ComputedType | Instance]:
    """Pure syntactic interpretation of an SI-unit computation such as
    `M/Sec**2` or `1/Sec`, mirroring the arithmetic already legal in unit-type
    annotation position. Only needs semantic analysis (name binding), not full
    type inference. Returns None if `o` isn't unit-computation-shaped at all.
    Raises UnitExprError if it looks like one but has an invalid operand or
    operator (exactly one side resolves, or the operator isn't */**//)."""
    if isinstance(o, NameExpr):
        if isinstance(o.node, TypeInfo) and is_info_sipy_base(o.node):
            return Instance(o.node, ())
        return None
    if not isinstance(o, OpExpr):
        return None

    left: "ProperType | int | None"
    if isinstance(o.left, IntExpr):
        left = o.left.value if (o.left.value == 1 and o.op == '/') else None
    else:
        left = interpret_unit_expr(o.left)

    from mypy.checkexpr import ExpressionChecker
    right: "ProperType | int | None"
    if ExpressionChecker.is_numeric_literal_expr(o.right):
        right = ExpressionChecker.get_numeric_literal_value(o.right) if o.op == '**' else None
    else:
        right = interpret_unit_expr(o.right)

    if left is None and right is None:
        return None
    if (left is None) != (right is None):
        raise UnitExprError(left, right, o)
    if o.op not in {'*', '**', '/'}:
        raise UnitExprError(left, right, o)
    # Both are non-None here: the checks above returned when neither resolved
    # and raised when exactly one did.
    assert left is not None and right is not None
    return ComputedType(left, right, o.op, o.line, o.column)


def is_sipy_aliases_assignment(s: AssignmentStmt, cur_mod_id: str) -> bool:
    """Structural recognition of sipy's `_aliases` special form: a bare
    module-level `_aliases = [...]` assignment in the sipy unit-definitions
    module. Purely syntactic -- needs only `s` and the current module's
    fullname, no semantic-analysis-time state -- so both semanal_sipy.py
    (during semantic analysis, to recognize and interpret the form) and
    checker.py (to skip normal RHS checking of it, since its arithmetic
    syntax like `1 / Sec` isn't meant to be ordinary checkable Python) just
    call this directly, rather than needing a stored flag on the shared
    AssignmentStmt node -- which is instantiated for every assignment
    statement in every file mypy ever checks, not just sipy's."""
    return (
        cur_mod_id == base_type_module
        and len(s.lvalues) == 1
        and isinstance(s.lvalues[0], NameExpr)
        and s.lvalues[0].name == "_aliases"
        and isinstance(s.rvalue, ListExpr)
    )


# The unit equivalences declared by the sipy unit-definitions module's
# `_aliases` list (e.g. Hz == 1/Sec). Recorded here during semantic analysis of
# that module (see mypy.semanal_sipy) and turned into e-graph rewrite rules by
# load_unit_alias_rules() below. There is exactly one such module per process,
# so this lives next to the e-graph it feeds rather than being attached to a
# node -- in particular not to MypyFile, which is instantiated for every module
# mypy ever reads, none of which but this one would ever have a value here.
unit_aliases: "List[Tuple[Instance, (ComputedType | Instance)]]" = []


class EgraphTypeCompare:
    @staticmethod
    def _to_node(t: ComputedType | Instance) -> ExprNode:
        if isinstance(t, Instance):
            return ExprNode(t.type.name, ())

        if isinstance(t.left,ComputedType):
            l = EgraphTypeCompare._to_node(t.left)
        elif isinstance(t.left, Instance):
            l = ExprNode(t.left.type.name,())
        else:
            assert isinstance(t.left, int)
            l = ExprNode(t.left,())

        if isinstance(t.right, ComputedType):
            r = EgraphTypeCompare._to_node(t.right)
        elif isinstance(t.right, Instance):
            r = ExprNode(t.right.type.name,())
        else:
            assert isinstance(t.right, int)
            r = ExprNode(t.right,())

        return ExprNode(t.op,(l,r))

    egraph = EGraph()
    alias_rules: List[Rule] = []

    @staticmethod
    def rule_apply() -> None:
        Rule.apply_rules(EgraphTypeCompare.egraph_rules + EgraphTypeCompare.alias_rules, EgraphTypeCompare.egraph)


    class IntSuccessorRule(ConditionalRule):
        """n -> (n - 1) + 1, for any integer n, if (n - 1) is also present.

        The e-graph has no arithmetic of its own, so the symbolic "+" node
        produced by the (x ** y) * x -> x ** (y + 1) rule never folds into a
        literal: this rule is what makes e.g. the 3 of an annotated (Sec**3)
        equal to the 2 + 1 that Sec*Sec*Sec rewrites to.
        """

        # Both search() and apply_to_eclass() are overridden, so the lhs/rhs
        # patterns a plain Rule matches and substitutes with are never
        # consulted -- but Rule's interface is typed for real QuicheTrees, so
        # give it one rather than lying to it with None.
        _unused_pattern: ClassVar[ExprTree] = ExprTree(ExprNode("n", ()))

        def __init__(self) -> None:
            super().__init__(lhs=self._unused_pattern, rhs=self._unused_pattern)

        @staticmethod
        def literal_eclass(egraph: EGraph, value: int) -> EClassID | None:
            """The e-class holding the int literal `value`, or None if the
            graph doesn't contain it.

            This O(1) hashcons hit is exactly equivalent to scanning every
            e-node in the graph: hashcons is keyed by *canonicalized* e-nodes,
            a leaf e-node is its own canonicalization, and repair() only ever
            re-keys e-nodes taken from an e-class's `uses` list -- which is
            only ever populated for e-nodes that have arguments. So a literal,
            once added, stays under an unchanging key forever. The scan is
            worth avoiding because egraph.eclasses() rebuilds its whole
            e-class -> e-node index on any call made after the graph has been
            mutated, which is every call once a round's rewrites start landing.
            """
            eid = egraph.hashcons.get(ENode(value, ()))
            return eid.find() if eid is not None else None

        def search(self, egraph: EGraph) -> Sequence[EMatch]:
            """Match each int literal whose predecessor is also in the graph,
            binding "n" to the literal's e-class and "n_minus_1" to its
            predecessor's.

            Resolving the predecessor here, where the int value is in hand, is
            what keeps the substitution honestly typed as a Subst
            (str -> EClassID). Stashing the raw int in it instead would make
            every EClassID annotation downstream of it a lie -- and it isn't
            needed: applying the rule wants the *e-class of* (n - 1), never the
            number itself.
            """
            matches: List[EMatch] = []
            for enode, eid in egraph.hashcons.items():
                if not isinstance(enode.key, int) or enode.args:
                    continue
                pred = self.literal_eclass(egraph, enode.key - 1)
                if pred is not None:
                    matches.append((eid.find(), {"n": eid.find(), "n_minus_1": pred}))
            return matches

        def check_condition(self, egraph: EGraph, eid: EClassID, env: Subst) -> bool:
            # search() only emits matches whose predecessor resolved, so this
            # is really just a guard on the shape of the substitution.
            return "n_minus_1" in env

        def apply_to_eclass(self, egraph: EGraph, eid: EClassID, env: Subst) -> EClassID:
            if not self.check_condition(egraph, eid, env):
                return eid
            one_id = egraph.add_enode(ENode(1, ()))
            return egraph.add_enode(ENode("+", (env["n_minus_1"], one_id)))

    @staticmethod
    def get_iter_limit(t1: ComputedType, t2: ProperType | None = None) -> int:
        def depth(t: ProperType | int) -> int:
            if isinstance(t, ComputedType):
                return 1 + max(depth(t.left), depth(t.right))
            else:
                return 1
        ast_depth = depth(t1) if t2 is None else max(depth(t1), depth(t2))
        return min(2*ast_depth + 4, 30) # 4 to leave room for constant folding etc, 30 is egg default limit

    @staticmethod
    def restart_if_needed(found: bool) -> None:
        if found or EgraphTypeCompare.egraph.is_saturated(): # if finished by finding or saturation, ok
            return
        elif len(EgraphTypeCompare.egraph.hashcons) < 10000: # haven't hit the egg default limit
            return
        # dump it all out, start over next time
        EgraphTypeCompare.egraph = EGraph()

    @staticmethod
    def egraph_reduces_to_1(t: ComputedType) -> bool:
        teclass = EgraphTypeCompare.egraph.add(ExprTree(EgraphTypeCompare._to_node(t)))
        one = EgraphTypeCompare.egraph.add(ExprTree(ExprNode(1,())))
        is_eq = EgraphTypeCompare.egraph.find(teclass) == EgraphTypeCompare.egraph.find(one)
        iter_limit = EgraphTypeCompare.get_iter_limit(t)
        while not is_eq and not EgraphTypeCompare.egraph.is_saturated() and iter_limit > 0:
            EgraphTypeCompare.rule_apply()
            is_eq = EgraphTypeCompare.egraph.find(teclass) == EgraphTypeCompare.egraph.find(one)
            iter_limit -= 1
        EgraphTypeCompare.restart_if_needed(is_eq)
        return is_eq

    egraph_rules = [
        IntSuccessorRule(),
        ExprTree.make_rule(lambda x, y, z: ((x * y) / z, x * (y / z))),
        ExprTree.make_rule(lambda x, y: ((x / y)  * y, x)),
        ExprTree.make_rule(lambda x: (x / x, ExprNode(1, ()))),
        ExprTree.make_rule(lambda x: (x * 1, x)),
        ExprTree.make_rule(lambda x: (x / 1, x)),
        ExprTree.make_rule(lambda x: (x ** -1, 1/x)),
        ExprTree.make_rule(lambda x: (x * x, x ** 2)),
        ExprTree.make_rule(lambda x: (x ** 2, x * x)),
        # ExprTree.make_rule(lambda x: (x ** 0, 1)),
        ExprTree.make_rule(lambda x,y: ((x ** y) * x, x ** (y + 1))),
    ]

    @staticmethod
    def egraph_is_same(t1: ComputedType, t2: ProperType) -> bool:
        assert isinstance(t2, (Instance,ComputedType)), t2
        lhs_id = EgraphTypeCompare.egraph.add(ExprTree(EgraphTypeCompare._to_node(t1)))
        rhs_id = EgraphTypeCompare.egraph.add(ExprTree(EgraphTypeCompare._to_node(t2)))
        is_eq = EgraphTypeCompare.egraph.find(lhs_id) == EgraphTypeCompare.egraph.find(rhs_id)
        iter_limit = EgraphTypeCompare.get_iter_limit(t1,t2)
        while not is_eq and not EgraphTypeCompare.egraph.is_saturated() and iter_limit > 0:
            EgraphTypeCompare.rule_apply()
            is_eq = EgraphTypeCompare.egraph.find(lhs_id) == EgraphTypeCompare.egraph.find(rhs_id)
            iter_limit -= 1
        EgraphTypeCompare.restart_if_needed(is_eq)
        return is_eq


class UnitExprTree(ExprTree):
    """An ExprTree for ground unit-alias rules. Plain ExprTree treats *any*
    non-int leaf as a free pattern variable during e-graph matching (see
    quiche's ExprTree.is_pattern_symbol), which is correct for the generic
    arithmetic identities in egraph_rules (x, y, z, n are meant to unify with
    anything) but wrong for unit-alias rules, where every leaf name (e.g.
    "Hz", "Sec") is a concrete constant, not a variable -- left as plain
    ExprTree, a rule like Hz -> 1/Sec would spuriously match any other named
    leaf ("Sec", "M", ...) and corrupt the graph. literal_names excludes the
    known alias-related names from ever being treated as pattern variables.
    """

    literal_names: ClassVar[Set[str]] = set()

    def __init__(self, root: ExprNode) -> None:
        super().__init__(root)
        # ExprTree.__init__ hardcodes plain ExprTree for children, so redo it
        # here with UnitExprTree -- otherwise only the root node would get the
        # literal_names override and every nested leaf (e.g. "Sec" inside
        # "1/Sec") would fall back to plain ExprTree's "any non-int leaf is a
        # pattern variable" behavior, corrupting the graph exactly as
        # described above.
        self._children = [UnitExprTree(arg) for arg in root.args]

    def is_pattern_symbol(self) -> bool:
        return super().is_pattern_symbol() and self.value() not in UnitExprTree.literal_names


def collect_leaf_names(node: ExprNode) -> Set[str]:
    if not node.args:
        return {node.key} if isinstance(node.key, str) else set()
    names: Set[str] = set()
    for child in node.args:
        names |= collect_leaf_names(child)
    return names


def load_unit_alias_rules() -> None:
    """Turn the `unit_aliases` recorded during semantic analysis of the sipy
    unit-definitions module into bidirectional e-graph rewrite rules.

    Called exactly once, from build.py, right after that module has been
    processed -- the same guarded special-casing 'builtins' and 'typing' get
    there. Because there is only ever the one declaring module, this is a
    plain read-and-set rather than something that accumulates or has to
    tolerate being called speculatively before the data exists.

    Note this only ever adds knowledge to the e-graph: EgraphTypeCompare's
    e-graph is never reset between builds (One Big Egraph), since unit math
    and aliasing are global, always-correct facts rather than equivalences
    scoped to one build or file."""
    rules: List[Rule] = []
    literal_names: Set[str] = set()
    for leaf_instance, target in unit_aliases:
        lhs_node = EgraphTypeCompare._to_node(leaf_instance)
        rhs_node = EgraphTypeCompare._to_node(target)
        literal_names |= collect_leaf_names(lhs_node) | collect_leaf_names(rhs_node)
        lhs = UnitExprTree(lhs_node)
        rhs = UnitExprTree(rhs_node)
        # bidirectional, matching the existing x**2/x*x convention already in egraph_rules
        rules += [Rule(lhs, rhs), Rule(rhs, lhs)]
    UnitExprTree.literal_names = literal_names
    EgraphTypeCompare.alias_rules = rules

def split_unit_type(t: Type) -> Tuple[Type, ProperType | None]:
    """If t carries an SI unit, split it into (plain type, unit); else (t, None)."""
    proper_t = mypy.types.get_proper_type(t)
    if proper_t is None:
        return t, None
    if isinstance(proper_t, CompoundType):
        return proper_t.numeric_type, proper_t.base_type
    elif isinstance(proper_t, Instance):
        if hasattr(proper_t, 'args') and proper_t.args:
            new_t, units = deunit_instance(proper_t)
            assert len(units) <= 1
            return new_t, (units[0] if units else None)
        return t, None
    else:
        return t, None

def deunit_instance(t: ProperType) -> Tuple[ProperType, List[ProperType]]:
    """Early in semantic analysis, unitful types with no computations can appear as Instance[Unit],
   strip out all the units from the args and the args' args, as part of the transformation
   into CompoundType(Unit,Instance)."""
    assert isinstance(t,ProperType),t
    if isinstance(t, (Instance,TypeAliasType)):
        if not t.args:
            return t, []
        else:
            new_args: List[Type] = []
            collected_units = []
            for _a in t.args:
                if isinstance(_a, TypeAliasType) and _a.alias is not None and _a.is_recursive:  # Recursive aliases (e.g. R = Dict[str, R]) can't be finitely unrolled;                                        # treat them as unit-free rather than expanding them forever.
                    new_args.append(_a)
                    continue
                a = mypy.types.get_proper_type(_a)
                if is_sipy_base(a):
                    # separate out the unit
                    if isinstance(a, CompoundType):
                        new_args.append(a.numeric_type)
                        collected_units.append(a.base_type)
                    elif isinstance(a, Instance):
                        assert len(a.args) == 1
                        new_args.append(mypy.types.get_proper_type(a.args[0]))
                        collected_units.append(a.copy_modified(args=[]))
                else:
                    new_a, a_units = deunit_instance(a)
                    new_args.append(new_a)
                    collected_units.extend(a_units)
            new_t = t.copy_modified(args=list(new_args))
            return new_t, collected_units
    else:
        return t, []
