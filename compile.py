#!/usr/bin/env python2.6

import shutil
import os
import py_compile
import zipfile
import glob
import fnmatch
import dis
import marshal
import sys

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
		sys.stdout = open(os.path.join(root, filename.replace(".py","-old.byte")), "w")
		with open(os.path.join(root.replace("res_mods/0.8.8/","res/"), filename.replace(".py",".pyc")), "rb") as pyc_reader:
			pyc_reader.read(8)
			dis.dis(marshal.load(pyc_reader))
		sys.stdout.close()

		sys.stdout = sys.__stdout__
		print "Compiling ", os.path.join(root, filename)
		py_compile.compile(os.path.join(root, filename), doraise=True)

		sys.stdout = open(os.path.join(root, filename.replace(".py","-new.byte")), "w")
		with open(os.path.join(root, filename.replace(".py",".pyc")), "rb") as pyc_reader:
			pyc_reader.read(8)
			dis.dis(marshal.load(pyc_reader))
		sys.stdout.close()

		sys.stdout = sys.__stdout__

# Zip Package
fZip = zipfile.ZipFile( "WOTDecompiled.zip", "w" )
for root, dirnames, filenames in os.walk('res_mods'):
	for filename in fnmatch.filter(filenames, '*.pyc'):
		fZip.write(os.path.join(root, filename))
fZip.close()

def decompile(pycfile):
	with open(pycfile, "rb") as pyc_reader:
		pyc_reader.read(8)
		dis.dis(marshal.load(pyc_reader))
