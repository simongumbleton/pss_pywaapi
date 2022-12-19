cd %~dp0
cd ..
cd pss_pywaapi
python -m pip install twine
python -m twine upload dist/*
