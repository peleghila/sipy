from typing import List, Dict, Tuple

from quiche.egraph import Subst

import mypy.types
from mypy.nodes import MypyFile, TypeInfo, FuncDef, TypeAlias, SymbolNode
from mypy.type_visitor import T
from mypy.types import Instance, ProperType, AnyType, ComputedType, CompoundType, UnboundType, TypeVarType, \
    TypeAliasType, UninhabitedType, UnionType, Type, NoneType, CallableType, TupleType, TypeType, LiteralType, \
    UnpackType, PartialType, TypedDictType, Overloaded, TypeVarTupleType, Parameters, ParamSpecType, DeletedType, \
    ErasedType, PlaceholderType, RawExpressionType, EllipsisType, CallableArgument, TypeList

from quiche import EGraph, EClassID
from quiche.lang.expr_lang import ExprNode, ExprTree
from quiche.rewrite import Rule, ConditionalRule

base_type_name = "src.SUnit1.SIUnit.SIUnit"
dtype_name = "src.SUnit1.SIUnit.dtype"
base_type_module, base_type_classname = base_type_name.rsplit('.', maxsplit=1)
base_type_filename = "D:\\code\\units1\\src\\SUnit1\\SIUnit.py"

def get_base_type(modules: Dict[str,MypyFile]) -> SymbolNode | None:
    if base_type_module not in modules:
        return None
    module = modules[base_type_module]
    if base_type_classname not in module.names:
        return None
    return module.names[base_type_classname].node


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


class EgraphTypeCompare:
    @staticmethod
    def _to_node(t: ComputedType) -> ExprNode:
        if isinstance(t, Instance):
            return ExprNode(t.type.name, ())

        if isinstance(t.left,ComputedType):
            l = EgraphTypeCompare._to_node(t.left)
        elif isinstance(t.left, Instance):
            l = ExprNode(t.left.type.name,())
        else:
            l = ExprNode(t.left,())

        if isinstance(t.right, ComputedType):
            r = EgraphTypeCompare._to_node(t.right)
        elif isinstance(t.right, Instance):
            r = ExprNode(t.right.type.name,())
        else:
            r = ExprNode(t.right,())

        return ExprNode(t.op,(l,r))

    egraph = EGraph()
    @staticmethod
    def rule_apply() -> None:
        Rule.apply_rules(EgraphTypeCompare.egraph_rules, EgraphTypeCompare.egraph)


    class IntSuccessorRule(ConditionalRule):
        """n -> (n - 1) + 1, for any integer n, if (n - 1) is also present."""

        def __init__(self) -> None:
            super().__init__(lhs=None, rhs=None)

        def search(self, egraph: EGraph) -> Tuple[EClassID,Dict[str,int]]:
            return [
                (eid, {"n": node.key})
                for eid, enodes in egraph.eclasses().items()
                for node in enodes
                if isinstance(node.key, int) and not node.args
            ]

        @staticmethod
        def literal_present(egraph: EGraph, value: int) -> bool:
            return any(
                node.key == value and not node.args
                for enodes in egraph.eclasses().values()
                for node in enodes
            )
        def check_condition(self, egraph: EGraph, eid: EClassID, env: Subst) -> bool:
            return self.literal_present(egraph, env["n"] - 1)

        def apply_to_eclass(self, egraph: EGraph, eid: EClassID, env: Subst) -> EClassID:
            if not self.check_condition(egraph, eid, env):
                return eid
            n = env["n"]
            n_minus_1_id = egraph.add(ExprTree(ExprNode(n - 1, ())))
            one_id = egraph.add(ExprTree(ExprNode(1, ())))
            from quiche import ENode
            return egraph.add_enode(ENode("+", (n_minus_1_id, one_id)))
    @staticmethod
    def egraph_reduces_to_1(t: ComputedType) -> bool:
        teclass = EgraphTypeCompare.egraph.add(ExprTree(EgraphTypeCompare._to_node(t)))
        one = EgraphTypeCompare.egraph.add(ExprTree(ExprNode(1,())))
        is_eq = EgraphTypeCompare.egraph.find(teclass) == EgraphTypeCompare.egraph.find(one)
        while not is_eq and not EgraphTypeCompare.egraph.is_saturated():
            EgraphTypeCompare.rule_apply()
            is_eq = EgraphTypeCompare.egraph.find(teclass) == EgraphTypeCompare.egraph.find(one)
        return is_eq

    egraph_rules = [
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
        IntSuccessorRule()
    ]

    @staticmethod
    def egraph_is_same(t1: ComputedType, t2: ProperType) -> bool:
        lhs_id = EgraphTypeCompare.egraph.add(ExprTree(EgraphTypeCompare._to_node(t1)))
        rhs_id = EgraphTypeCompare.egraph.add(ExprTree(EgraphTypeCompare._to_node(t2)))
        is_eq = EgraphTypeCompare.egraph.find(lhs_id) == EgraphTypeCompare.egraph.find(rhs_id)
        while not is_eq and not EgraphTypeCompare.egraph.is_saturated():
            EgraphTypeCompare.rule_apply()
            is_eq = EgraphTypeCompare.egraph.find(lhs_id) == EgraphTypeCompare.egraph.find(rhs_id)
        return is_eq


def deunit_instance(t: ProperType) -> Tuple[ProperType, List[ProperType]]:
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
