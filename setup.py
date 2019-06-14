import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="compose_sql",
    version="0.1.0",
    author="Alieh Rymašeŭski",
    author_email="alieh.rymasheuski@gmail.com",
    description="A tool to compose SQL based on strings",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MacmillanPlatform/compose_sql",
    packages=setuptools.find_packages(),
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: SQL",
        "Topic :: Database",
    ],
)
