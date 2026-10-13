from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('cc'), 'C compiler required')
class WineUnixRuntimeTests(unittest.TestCase):
    def test_relocated_loaded_runtime_and_ambiguous_modules(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            modules = []
            for installation in ('wine-11.0', 'other-wine'):
                module = directory / installation / 'lib/wine/x86_64-unix/ntdll.so'
                module.parent.mkdir(parents=True)
                subprocess.run(['cc', '-shared', '-fPIC', '-x', 'c', '-', '-o', str(module)],
                               input='int wine_server_call(void *p) { return p != 0; }',
                               text=True, check=True, capture_output=True, timeout=15)
                modules.append(str(module))
            executable = directory / 'runtime-test'
            subprocess.run(['cc', '-D_GNU_SOURCE', '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-I', str(ROOT / 'src'), '-x', 'c', '-', '-ldl', '-o', str(executable)],
                           input='''#include "native_wine_unix_runtime.h"
#include <assert.h>
int main(int argc, char **argv) {
    assert(argc == 3);
    assert(!uurb_loaded_wine_runtime());
    void *first = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    assert(first);
    void *found = uurb_loaded_wine_runtime();
    assert(found && dlsym(found, "wine_server_call"));
    dlclose(found);
    void *second = dlopen(argv[2], RTLD_NOW | RTLD_LOCAL);
    assert(second && !uurb_loaded_wine_runtime());
    dlclose(second);
    found = uurb_loaded_wine_runtime();
    assert(found); dlclose(found); dlclose(first);
    assert(!uurb_loaded_wine_runtime());
    return 0;
}
''', text=True, check=True, capture_output=True, timeout=15)
            subprocess.run([str(executable), *modules], check=True, capture_output=True, timeout=5)


if __name__ == '__main__':
    unittest.main()
