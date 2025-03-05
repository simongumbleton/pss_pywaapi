cd %~dp0
cd ..
cd pss_pywaapi
py -m pip install twine
py -m twine upload dist/*
