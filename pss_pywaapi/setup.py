from setuptools import setup

def readme():
    with open('README.md') as f:
        README = f.read()
    return README


setup(
    name="pss_pywaapi",
    version="1.0.5",
    description="Helper package for interfacing with Wwise using waapi.",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/simongumbleton/pss_pywaapi",
    author="Simon Gumbleton",
    author_email="simongumbleton@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3"
    ],
    setup_requires=['wheel'],
    packages=["pss_helpers"],
    py_modules=['pss_pywaapi'],
    include_package_data=True,
    install_requires=["waapi_client","PyWave"],
)
