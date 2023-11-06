import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {'packages': ['core','pathlib'], 'excludes': []}

setup(  name = 'OpenMATB',
        version = '1.0.0',
        description = 'An Open MATB application',
        options = {'build_exe': build_exe_options},
        executables = [Executable('main.py')])