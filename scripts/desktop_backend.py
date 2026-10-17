"""Desktop-specific, read-only topology for the native input/capture worker."""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess


def wine_bin_directory(system=Path('/opt/wine-stable/bin'), local=None):
    local = local if local is not None else Path.home() / '.local/opt/uuway/wine-11.0/bin'
    packaged = Path('/opt/uuway/wine-11.0/bin')
    if (packaged / 'wine').is_file():
        return packaged
    return local if not (system / 'wine').is_file() and (local / 'wine').is_file() else system


def plasma_wayland(environ=None):
    environ = os.environ if environ is None else environ
    return (environ.get('XDG_SESSION_TYPE') == 'wayland' and
            'KDE' in environ.get('XDG_CURRENT_DESKTOP', '').split(':'))


def plasma_topology(data):
    """Accept only one unmirrored, unrotated output at the input origin."""
    outputs = data.get('outputs') if isinstance(data, dict) else None
    if not isinstance(outputs, list) or not 1 <= len(outputs) <= 16:
        raise RuntimeError('Invalid KDE output list')
    active = [output for output in outputs if isinstance(output, dict) and output.get('enabled')]
    if len(active) != 1:
        raise RuntimeError('Native input currently requires one active physical output')
    output = active[0]
    size, position = output.get('size'), output.get('pos')
    if (output.get('connected') is not True or not isinstance(output.get('name'), str) or
            not 0 < len(output['name']) <= 128 or output.get('rotation') != 1 or
            output.get('replicationSource', 0) != 0 or not isinstance(position, dict) or
            position.get('x') != 0 or position.get('y') != 0 or not isinstance(size, dict) or
            not all(type(size.get(k)) is int and 2 <= size[k] <= 4096 and size[k] % 2 == 0
                    for k in ('width', 'height'))):
        raise RuntimeError('Unsupported KDE output layout')
    scale = output.get('scale')
    if type(scale) not in (int, float) or not math.isfinite(scale) or not 0.5 <= scale <= 4:
        raise RuntimeError('Invalid KDE output scale')
    modes = output.get('modes')
    if not isinstance(modes, list) or not 1 <= len(modes) <= 256:
        raise RuntimeError('Invalid KDE mode list')
    current = [mode for mode in modes if isinstance(mode, dict) and mode.get('id') == output.get('currentModeId')]
    if len(current) != 1 or current[0].get('size') != size:
        raise RuntimeError('KDE current mode does not match output geometry')
    # KScreen does not expose Mutter's serial. A stable state fingerprint lets
    # the existing worker detect changes without reporting EDID or monitor IDs.
    state = [output['name'], output['currentModeId'], size, scale, output['rotation']]
    generation = int.from_bytes(hashlib.sha256(json.dumps(state, sort_keys=True).encode()).digest()[:4], 'big')
    return dict(generation=generation, connectors=[output['name']],
                layout=[dict(x=0, y=0, scale=float(scale), transform=0, outputs=1)],
                modes=[dict(width=size['width'], height=size['height'])])


def current_plasma_topology():
    # Screen geometry queries do not need AT-SPI. Avoid registering a new
    # short-lived accessible application on every topology poll.
    environment = dict(os.environ, QT_LINUX_ACCESSIBILITY_ALWAYS_ON='0',
                       QT_ACCESSIBILITY='0', NO_AT_BRIDGE='1')
    result = subprocess.run(['kscreen-doctor', '-j'], capture_output=True, text=True,
                            timeout=5, check=True, env=environment)
    return plasma_topology(json.loads(result.stdout))
