from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mbox-processor",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python package for processing MBOX files from Google Takeout",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mbox-processor",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        'beautifulsoup4>=4.9.3',
        'python-magic>=0.4.24',
    ],
    entry_points={
        'console_scripts': [
            'mbox-processor=mbox_processor.cli:main',
        ],
    },
)
