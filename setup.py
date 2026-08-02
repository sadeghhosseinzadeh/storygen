from setuptools import setup, find_packages

setup(
    name="storygen",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "Pillow>=10.0",
    ],
    include_package_data=True,
    package_data={
        "storygen": ["fonts/*.ttf"],
    },
)
