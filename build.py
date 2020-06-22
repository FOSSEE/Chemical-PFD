from fbs.cmdline import command
from os.path import dirname
import subprocess
import sys
import fbs.cmdline
import fbs

sys.path.append('src/main/python/')

@command
def compileResources():
    subprocess.call("pyrcc5 -o src/main/python/resources/resources.py src/main/ui/resources.rcc", shell=True)

@command
def symbolGen():
    from utils import custom
    custom.main()
    
@command
def build():
    compileResources()
    subprocess.call("fbs freeze", shell=True)
    
if __name__ == '__main__':
    project_dir = dirname(__file__)
    fbs.cmdline.main(project_dir)