import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sssg",
    version="0.0.8",
    author="Kauko",
    author_email="kauko@biosynth.link",
    description="Simple static site generator with Jinja",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cheeplusplus/simplestaticsitegen",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        "jinja2",
        "markdown",
        "pymdown-extensions",
        "python-frontmatter",
        "pathmatch"
    ],
    entry_points={
        "console_scripts": ["sssg = sssg.__main__:main"]
    }
)
