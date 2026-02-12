from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="basher2",
    version="0.1.4",
    install_requires=[],
    extras_require={"dev": ["pytest>=7.0"]},
    author="Yehor Shytikov",
    author_email="egorshitikov@gmail.com",
    description="Python utilities that wrap bash commands",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/genaker/basher",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
) 