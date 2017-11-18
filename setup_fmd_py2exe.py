from distutils.core import setup
import py2exe, sys, os, glob

# automatically add py2exe to command
sys.argv.append('py2exe')

# fix py2exe ability to find applications modules
sys.path.insert(0, 'fmd')

py2exe_options = {
    'bundle_files': 1,
    'compressed': True,
    'optimize': 2,
    'packages': ['netmiko', 'cffi'],
    'dll_excludes': ['w9xpopen.exe', 'crypt32.dll', 'mpr.dll'], # exclude win95 98 and crypto OS dll files
    'includes': [], # additional modules
    #'excludes': []
    'excludes': ['Carbon', 'Carbon.Files', 'Cython.Distutils.build_ext', '_dummy_thread', '_imp', '_scproxy', '_sysconfigdata', '_thread', 'backports.ssl_match_hostname', 'builtins', 'cffi._pycparser', 'configparser', 'distutils.ccompiler', 'distutils.cmd', 'distutils.command', 'distutils.command.bdist', 'distutils.command.build_ext', 'distutils.command.build_py', 'distutils.command.build_scripts', 'distutils.command.install', 'distutils.command.install_scripts', 'distutils.command.sdist', 'distutils.core', 'distutils.debug', 'distutils.dir_util', 'distutils.dist', 'distutils.errors', 'distutils.extension', 'distutils.file_util', 'distutils.filelist', 'distutils.log', 'distutils.msvc9compiler', 'distutils.spawn', 'distutils.sysconfig', 'distutils.util', 'distutils.version', 'dl', 'gssapi', 'importlib.machinery', 'org.python.modules.posix.PosixModule', 'pkg_resources.extern.appdirs', 'pkg_resources.extern.packaging', 'pkg_resources.extern.six', 'pkg_resources.extern.six.moves', 'pysnmp.entity.rfc3413.oneliner', 'pywintypes', 'setuptools.extern.six', 'setuptools.extern.six.moves', 'sitecustomize', 'sspi', 'sspicon', 'testing.udir', 'urllib.parse', 'usercustomize', 'win32pipe', 'wincertstore', 'winreg']  # exluded modules 
}


setup(
  options = {
            'py2exe': py2exe_options,
            },
  console = ['fmd/fmd.py'],
  zipfile = None,
)