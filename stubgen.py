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
    m_params = re.match(f'{key}\(([^\n]*)\)\n', doc)
    params = []
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

    ret = 'None'
    m_ret = re.search(
        r'\n\s+Returns:\n\s+(\w+): .*?.\n', doc)
    # r'\n\s+Returns:\n\s+ bytes: the payload data that was set by :func:`set_drag_drop_payload`.\n\n    .. wraps::\n        const ImGuiPayload* AcceptDragDropPayload(const char* type, ImGuiDragDropFlags flags = 0)\n    '
    if m_ret:
        ret = m_ret.group(1)

    ret = TYPE_MOD.get(ret, ret)

    return ret, params


def main(w: io.IOBase):

    for klass in ('_DrawData', '_ImGuiViewport', '_ImGuiContext', '_FontAtlas', '_Font'):
        w.write(f'class {klass}: pass\n')

    functions = []

    import imgui
    for key in dir(imgui):
        m = SYSTEM_KEY.match(key)
        if m:
            continue

        if key in ['plot_histogram', 'plot_lines']:
            # exclude
            continue

        value = getattr(imgui, key)
        match value:
            case int():
                w.write(f'{key}: int\n')
            case float():
                w.write(f'{key}: float\n')
            case type():
                w.write(f'class {key}:\n')
                w.write('   pass\n')
            case types.BuiltinFunctionType():
                ret, params = get_ret_aprams(key, value.__doc__)
                sio = io.StringIO()
                sio.write(f'def {key}(')
                for i, param in enumerate(params):
                    if i:
                        sio.write(', ')
                    sio.write(str(param))
                sio.write(f')-> {ret}:\n')
                sio.write("    '''")
                sio.write(value.__doc__)
                sio.write("'''\n")
                sio.write("...\n")
                functions.append(sio.getvalue())
            case _:
                print(key, type(value), value)

    for enum in ENUM_NAMES:
        w.write(f'{enum}= int\n')

    for f in functions:
        w.write(f)


if __name__ == '__main__':
    with (HERE / 'typings/imgui/__init__.pyi').open('w', encoding='utf-8') as w:
        main(w)
