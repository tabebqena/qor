from distutils.core import Extension, setup

setup(
    name="qor",
    version="0.0.1",
    description="python framework for kore server",
    packages=["src"],
    install_requires=[
        "Click",
    ],
    entry_points={
        "console_scripts": [
            "yourscript = yourscript:cli",
        ],
    },
)
