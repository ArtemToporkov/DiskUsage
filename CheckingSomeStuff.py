import os
import glob
import DiskUsage
from os import stat

for i in os.scandir('C:\\Users\\topor\\Documents'):
    print(i.path)