from fbs.cmdline import command
from os.path import dirname
import subprocess

import fbs.cmdline

@command
def compileResources():
    subprocess.call("pyrcc5 -o src/main/python/resources/resources.py src/main/ui/resources.rcc", shell=True)

if __name__ == '__main__':
    project_dir = dirname(__file__)
    fbs.cmdline.main(project_dir)