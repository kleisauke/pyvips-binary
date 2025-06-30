import sys

from os import path
from setuptools import setup

base_dir = path.dirname(__file__)
src_dir = path.join(base_dir, 'pyvips', 'pyvips')

# When executing the setup.py, we need to be able to import ourselves, this
# means that we need to add the pyvips/ directory to the sys.path.
sys.path.insert(0, src_dir)


if 'bdist_wheel' in sys.argv:
    cffi_modules = ['pyvips/pyvips/pyvips_build.py:ffibuilder']
else:
    cffi_modules = []

setup(
    cffi_modules=cffi_modules,
    # Must be kept in sync with `requires-python` in pyproject.toml
    options={'bdist_wheel': {'py_limited_api': f'cp37'}},
)
