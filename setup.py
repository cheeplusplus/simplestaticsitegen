import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sssg",
    version="0.0.3",
    author="AndrewNeo",
    author_email="andrew@andrewneo.com",
    description="Simple static site generator with Jinja",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AndrewNeo/simplestaticsitegen",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    install_requires=["jinja2", "markdown", "python-frontmatter"],
    entry_points={
        "console_scripts": ["sssg = sssg.__main__:main"]
    }
)
