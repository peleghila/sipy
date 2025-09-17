from mypy.nodes import MypyFile
from mypy.types import Instance, ProperType, AnyType

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
    if isinstance(candidate, AnyType):
        return False
    assert(False)

