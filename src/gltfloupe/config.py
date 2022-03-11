from typing import Optional, Tuple
import pathlib
import os
import toml
from glglue.windowconfig import WindowConfig

INI_FILE = pathlib.Path(os.environ['USERPROFILE']) / 'gltfloupe.toml'


def save(ini: str, window_config: WindowConfig):
    data = {
        'window': window_config._asdict(),
        'ini': ini,
    }

    with INI_FILE.open('w') as w:
        toml.dump(data, w)


def load() -> Tuple[Optional[str], Optional[WindowConfig]]:
    try:
        src = INI_FILE.read_bytes().decode('utf-8')
        data = toml.loads(src)
        config = WindowConfig(**data['window'])
        assert(config.width)
        assert(config.height)
        return data['ini'], config
    except Exception:
        return None, None
