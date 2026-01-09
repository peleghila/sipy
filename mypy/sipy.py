from mypy.nodes import MypyFile, TypeInfo
from mypy.types import Instance, ProperType, AnyType, ComputedType, CompoundType, UnboundType, TypeVarType, \
    TypeAliasType, UninhabitedType, UnionType

from quiche import EGraph
from quiche.lang.expr_lang import ExprNode, ExprTree
from quiche.rewrite import Rule

base_type_name = "src.SUnit1.SIUnit.SIUnit"
base_type_module, base_type_classname = base_type_name.rsplit('.', maxsplit=1)
base_type_filename = "D:\\code\\units1\\src\\SUnit1\\SIUnit.py"

def get_base_type(modules: dict[str,MypyFile]):
    if base_type_module not in modules:
        return None
    module = modules[base_type_module]
    if base_type_classname not in module.names:
        return None
    return module.names[base_type_classname].node


def is_info_sipy_base(typenode: TypeInfo) -> bool:
    return typenode.has_base(base_type_name)
def is_sipy_base(candidate: ProperType) -> bool:
    if isinstance(candidate, Instance):
        return is_info_sipy_base(candidate.type)
    elif type(candidate) in {AnyType, UnboundType, TypeVarType, UninhabitedType}: #isinstance(candidate, AnyType) or isinstance(candidate, UnboundType):
        return False
    elif isinstance(candidate, ComputedType):
        return ((is_sipy_base(candidate.left) if isinstance(candidate.left, ProperType) else True) and
                (is_sipy_base(candidate.right) if isinstance(candidate.right, ProperType) else True))
    elif isinstance(candidate, CompoundType):
        return is_sipy_base(candidate.base_type)
    elif isinstance(candidate, TypeAliasType):
        return is_sipy_base(candidate.alias.target)
    elif isinstance(candidate, UnionType):
        return any(is_sipy_base(t) for t in candidate.items)
    assert False, str(candidate)


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
    def rule_apply():
        Rule.apply_rules(EgraphTypeCompare.egraph_rules, EgraphTypeCompare.egraph)

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
        ExprTree.make_rule(lambda x: (x ** 2, x * x))
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
