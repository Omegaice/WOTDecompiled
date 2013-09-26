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
import dis, marshal, struct, sys, time, types, warnings

# Remove any previous directory
if os.path.exists("res_mods"):
	shutil.rmtree("res_mods")

# Create Directories
os.mkdir("res_mods")
os.mkdir("res_mods/0.8.8")

# Copy python files
shutil.copytree("res/scripts", "res_mods/0.8.8/scripts")

# Compile Files
INDENT = " " * 3
MAX_HEX_LEN = 16
NAME_OFFSET = 20

def to_hexstr(bytes_value, level=0, wrap=False):
    indent = INDENT*level
    line = " ".join(("%02x",) * MAX_HEX_LEN)
    last = " ".join(("%02x",) * (len(bytes_value) % MAX_HEX_LEN))
    lines = (line,) * (len(bytes_value) // MAX_HEX_LEN)
    if last:
        lines += (last,)
    if wrap:
        template = indent + ("\n"+indent).join(lines)
    else:
        template = " ".join(lines)
    try:
        return template % tuple(bytes_value)
    except TypeError:
        return template % tuple(ord(char) for char in bytes_value)

def show_consts(consts, level=0):
    indent = INDENT*level
    i = 0
    for obj in consts:
        if isinstance(obj, types.CodeType):
            print(indent+"%s (code object)" % i)
            show_code(obj, level=level+1)
        else:
            print(indent+"%s %r" % (i, obj))
        i += 1

def show_bytecode(code, level=0):
    indent = INDENT*level
    print(to_hexstr(code.co_code, level, wrap=True))
    print(indent+"disassembled:")
    dis.disassemble(code)

def show_code(code, level=0):
    indent = INDENT*level

    for name in dir(code):
        if not name.startswith("co_"):
            continue
        if name in ("co_code", "co_consts"):
            continue
        value = getattr(code, name)
        if isinstance(value, str):
            value = repr(value)
        elif name == "co_flags":
            value = "0x%05x" % value
        elif name == "co_lnotab":
            value = "0x(%s)" % to_hexstr(value)
        print("%s%s%s" % (indent, (name+":").ljust(NAME_OFFSET), value))
    print("%sco_consts" % indent)
    show_consts(code.co_consts, level=level+1)
    print("%sco_code" % indent)
    show_bytecode(code, level=level+1)

# Compile Files
for root, dirnames, filenames in os.walk('res_mods'):
	for filename in fnmatch.filter(filenames, '*.py'):
		sys.stdout = open(os.path.join(root, filename.replace(".py","-old.byte")), "w")
		with open(os.path.join(root.replace("res_mods/0.8.8/","res/"), filename.replace(".py",".pyc")), "rb") as pyc_reader:
			pyc_reader.read(8)
			show_code(marshal.load(pyc_reader), level=1)
		sys.stdout.close()

		sys.stdout = sys.__stdout__
		print "Compiling ", os.path.join(root, filename)
		py_compile.compile(os.path.join(root, filename), doraise=True)

		sys.stdout = open(os.path.join(root, filename.replace(".py","-new.byte")), "w")
		with open(os.path.join(root, filename.replace(".py",".pyc")), "rb") as pyc_reader:
			pyc_reader.read(8)
			show_code(marshal.load(pyc_reader), level=1)
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
