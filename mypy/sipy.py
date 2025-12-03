from mypy.nodes import MypyFile
from mypy.types import Instance, ProperType, AnyType, ComputedType, CompoundType, UnboundType, TypeVarType, \
    TypeAliasType, UninhabitedType, UnionType

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


def is_sipy_base(candidate: ProperType) -> bool:
    if isinstance(candidate, Instance):
        return candidate.type.has_base(base_type_name)
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

