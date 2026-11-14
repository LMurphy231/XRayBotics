import subprocess
import sys
import importlib.util as util

def install(module):
    if util.find_spec(module) is None:
        subprocess.run([sys.executable, "-m", "pip", "install", module], check=True)

def install_required():
    """Attempts to install all required modules for the XRayBotics System"""
    required_packages = [
        'numpy',
        'labquest',
        'xlsxwriter',
        'matplotlib',
    ]
    for package in required_packages:
        install(package)
