from typing import Optional, Tuple
import pathlib
import os
import toml
from .gui.glfw_window import WindowStatus

INI_FILE = pathlib.Path(os.environ['USERPROFILE']) / 'gltfloupe.toml'


def save(ini: str, window_status: WindowStatus):
    data = {
        'window': window_status._asdict(),
        'ini': ini,
    }

    with INI_FILE.open('w') as w:
        toml.dump(data, w)


def load() -> Tuple[Optional[str], Optional[WindowStatus]]:
    try:
        src = INI_FILE.read_bytes().decode('utf-8')
        data = toml.loads(src)
        return data['ini'], WindowStatus(**data['window'])
    except Exception:
        return None, None
