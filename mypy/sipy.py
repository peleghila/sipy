from mypy.nodes import MypyFile

base_type_name = "src.SUnit1.SIUnit.SIUnit"
base_type_module, base_type_classname = base_type_name.rsplit('.', maxsplit=1)
base_type_filename = "D:\\code\\units1\\src\\SUnit1\\SIUnit.py"

def get_base_type(modules: dict[str,MypyFile]):
    module = modules[base_type_module]
    if base_type_classname not in module.names:
        return None
    return module.names[base_type_classname].node
