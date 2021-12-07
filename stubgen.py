from typing import NamedTuple, Optional, Tuple, List
import pathlib
import io
import re
import types
HERE = pathlib.Path(__file__).absolute().parent
SYSTEM_KEY = re.compile(r'__(.*)__')


TYPE_MOD = {
    'ImU32': 'int',  # uint32
    'ImGuiID': 'int',  # uint32
    'unsigned int': 'int',  # uint32
    'double': 'float',
    'const float[:]': '',
}

RET_MOD = {
    'get_io': '_IO'
}

ENUM_NAMES = []


class Param(NamedTuple):
    name: str
    type: Optional[str] = None
    default: Optional[str] = None

    def __str__(self) -> str:
        if self.name:
            if self.type:
                if self.default:
                    return f'{self.name}: {self.type} = {self.default}'
                else:
                    return f'{self.name}: {self.type}'
            elif self.default:
                return f'{self.name} = {self.default}'
            else:
                return f'{self.name}'
        else:
            raise RuntimeError()


def get_ret_aprams(key: str, doc: str) -> Tuple[str, List[Param]]:
    if key == 'dockspace':
        pass

    params = []
    ret = RET_MOD.get(key, 'None')
    if doc:
        m_params = re.match(f'{key}\(([^\n]*)\)\n', doc)
        if m_params:
            if m_params.group(1):
                for param in m_params.group(1).split(','):
                    default_value = None
                    if '=' in param:
                        type_name, default_value = param.split('=', maxsplit=1)
                        type_name = type_name.strip().split()
                    else:
                        type_name = param.split()

                    param_type = None
                    if len(type_name) == 1:
                        param_name = type_name[0]
                        param_type = None
                    elif len(type_name) >= 2:
                        param_name = type_name[-1]
                        param_type = ' '.join(type_name[0:-1])

                    if param_type and re.match(r'ImGui\w+', param_type):
                        if param_type not in ENUM_NAMES:
                            ENUM_NAMES.append(param_type)

                    if param_type:
                        param_type = TYPE_MOD.get(param_type, param_type)

                    params.append(
                        Param(param_name, param_type, default_value))

        m_ret = re.search(
            r'\n\s+Returns:\n\s+(\w+): .*?.\n', doc)
        # r'\n\s+Returns:\n\s+ bytes: the payload data that was set by :func:`set_drag_drop_payload`.\n\n    .. wraps::\n        const ImGuiPayload* AcceptDragDropPayload(const char* type, ImGuiDragDropFlags flags = 0)\n    '
        if m_ret:
            ret = m_ret.group(1)

    ret = TYPE_MOD.get(ret, ret)

    return ret, params


def export_instance(w: io.IOBase, key: str, instance: object) -> bool:
    # print(instance, [k for k in dir(instance)])
    # print(instance.__doc__)
    w.write(f'class {key}:\n')
    has_member = False
    for k in dir(instance):
        if k.startswith('__'):
            continue
        w.write(f'    {k}: Any\n')
        has_member = True
        # v = getattr(instance, k)
        # print(k, v)
    return has_member


def export(w: io.IOBase, module: types.ModuleType):

    functions = []
    for key, value in module.__dict__.items():
        m = SYSTEM_KEY.match(key)
        if m:
            continue
        if key in ['plot_histogram', 'plot_lines']:
            # exclude
            continue
        match value:
            case int():
                w.write(f'{key}: int\n')
            case float():
                w.write(f'{key}: float\n')
            case type():
                # w.write(f'class {key}:\n')
                # w.write('   pass\n')
                instance = None
                match key:
                    case '_Colors':
                        instance = value(imgui.core.GuiStyle())
                        pass
                    case 'Vec2':
                        instance = value(1, 2)
                    case 'Vec4':
                        instance = value(1, 2, 3, 4)
                    case _:
                        instance = value()
                if instance and export_instance(w, key, instance):
                    pass
                else:
                    w.write('    pass\n')
            case types.BuiltinFunctionType():
                ret, params = get_ret_aprams(key, value.__doc__)
                sio = io.StringIO()
                sio.write(f'def {key}(')
                for i, param in enumerate(params):
                    if i:
                        sio.write(', ')
                    sio.write(str(param))
                sio.write(f')-> {ret}:\n')
                if value.__doc__:
                    sio.write("    '''")
                    sio.write(value.__doc__)
                    sio.write("'''\n")
                sio.write("...\n")
                functions.append(sio.getvalue())
            case _:
                print(module, key, type(value), value)

    for enum in ENUM_NAMES:
        w.write(f'{enum}= int\n')

    for f in functions:
        w.write(f)


if __name__ == '__main__':
    parent = HERE / 'typings/imgui'
    parent.parent.mkdir(parents=True, exist_ok=True)
    import imgui
    import imgui.core
    imgui.create_context()
    with (parent / '__init__.pyi').open('w', encoding='utf-8') as w:
        w.write('from .core import *\n')
    with (parent / 'core.pyi').open('w', encoding='utf-8') as w:
        w.write('from typing import Any\n')
        export(w, getattr(globals()['imgui'], 'core'))
