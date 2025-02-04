import setuptools

with open(file="README.md", mode="r", encoding="utf-8") as file:
    long_description = file.read()

setuptools.setup(
    name="aranet4",
    version="2.5.1",
    description="Aranet Python client",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Anrijs/Aranet4-Python",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    install_requires=[
        "bleak",
        "requests"
    ],
    entry_points={
        "console_scripts": ["aranetctl=aranet4.aranetctl:entry_point"]
    }
)
