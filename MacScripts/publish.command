#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd "${DIR}"
cd ..
cd pss_pywaapi
python3 -m pip install twine
python3 -m twine upload dist/*
