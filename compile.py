#!/usr/bin/env python2.6

import shutil
import os
import py_compile
import zipfile
import glob
import fnmatch

# Remove any previous directory
if os.path.exists("res_mods"):
	shutil.rmtree("res_mods")

# Create Directories
os.mkdir("res_mods")
os.mkdir("res_mods/0.8.8")

# Copy python files
shutil.copytree("res/scripts", "res_mods/0.8.8/scripts")

# Compile Files
for root, dirnames, filenames in os.walk('res_mods'):
  for filename in fnmatch.filter(filenames, '*.py'):
      py_compile.compile(os.path.join(root, filename), doraise=True)

# Zip Package
fZip = zipfile.ZipFile( "WOTDecompiled.zip", "w" )
for root, dirnames, filenames in os.walk('res_mods'):
  for filename in fnmatch.filter(filenames, '*.pyc'):
	fZip.write(os.path.join(root, filename))
fZip.close()
