import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    'includes': ['pyglet', 'rstr', 'parallel', 'pylsl'],
    'excludes': [],
    'include_files': ['parameters.csv', 'config.ini', 'inpout32.dll', 'VERSION',
                      'includes/', 'locales/'],
    'include_msvcr': True

}

setup(name='OpenMATB',
      version='1.0.0',
      description='An Open MATB application',
      options={'build_exe': build_exe_options},
      executables=[Executable('main.py')])
