from distutils.core import setup

setup(
    name="qor",
    version="0.0.1",
    description="python framework for kore server",
    packages=["src"],
    entry_points={
        "console_scripts": [
            "yourscript = yourscript:cli",
        ],
    },
)
