from fbs.cmdline import command
from os.path import dirname
import subprocess

import fbs.cmdline
import fbs

@command
def compileResources():
    subprocess.call("pyrcc5 -o src/main/python/resources/resources.py src/main/ui/resources.rcc", shell=True)

@command
def symbolGen():
    exec(open('src/main/python/utils/custom.py').read())
    
@command
def build():
    compileResources()
    subprocess.call("fbs freeze", shell=True)
    
if __name__ == '__main__':
    project_dir = dirname(__file__)
    fbs.cmdline.main(project_dir)