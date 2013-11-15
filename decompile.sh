#!/usr/bin/env bash

for file in `find . -name '*.pyc' -type f`; do
	uncompyle2 -o "${file%.*}.py" $file

	if [ $? -ne 0 ]; then
		echo "Decompiling $file failed"
	fi
done
#find . -name '*.pyc' -type f -exec bash -c 'echo $1 && ~/Documents/Code/pycdc/bin/pycdc "$1" > "${1/.pyc/.py}"' -- {} \;
#find . -name '*.pyc' -type f -exec bash -c 'uncompyle2 -o "${1/.pyc/_uncompyle.py}" "$1"' -- {} \;
