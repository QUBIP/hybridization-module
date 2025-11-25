from setuptools import find_packages, setup

setup(
    name="kdfix",
    version="0.8.4",
    description="Hybrid Key Derivation Framework using QKD, PQC and classical KEMs",
    author="Jofi Cresta, Ramon Querol",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "pycryptodome",
        "colorlog",
        "pydantic",
        "git+https://github.com/open-quantum-safe/liboqs-python.git@0.12.0"
    ],
    python_requires=">=3.11",
)
