import io
from typing import Union


def _num(value: Union[int, float]) -> str:
    match value:
        case int():
            return str(value)
        case float():
            return f'{value:.3f}'
        case _:
            raise RuntimeError()


def _to_string(w: io.IOBase, value, level=0, is_value=False):
    indent = '  ' * level
    if not is_value:
        w.write(indent)
    match value:
        case list():
            if all(isinstance(x, int) or isinstance(x, float) for x in value):
                w.write('[' + ', '.join(_num(x) for x in value) + ']')
            else:
                w.write('[\n')
                for i, v in enumerate(value):
                    _to_string(w, v, level+1)
                    if (i+1) < len(value):
                        w.write(',')
                    w.write('\n')
                w.write(f'{indent}]')
        case dict():
            w.write('{\n')
            for i, (k, v) in enumerate(value.items()):
                _to_string(w, k, level+1)
                w.write(': ')
                _to_string(w, v, level+1, is_value=True)
                if (i+1) < len(value):
                    w.write(',')
                w.write('\n')
            w.write(f'{indent}}}')
        case str():
            # quote
            w.write(f'"{value}"')
        case True:
            w.write('true')
        case False:
            w.write('false')
        case None:
            w.write('null')
        case float() | int():
            w.write(_num(value))
        case _:
            raise RuntimeError()


def to_pretty(value):
    w = io.StringIO()
    _to_string(w, value)
    return w.getvalue()


def get_value(json, key):
    current = json
    for k in key:
        match current:
            case list():
                current = current[k]
            case dict():
                current = current[k]
            case _:
                raise RuntimeError()
    return current
