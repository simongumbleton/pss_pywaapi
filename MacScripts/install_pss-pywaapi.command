#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd "${DIR}"
cd ..
cd pss_pywaapi
pip3 install csg-pywaapi --upgrade
