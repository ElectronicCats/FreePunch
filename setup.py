"""Setup script for Checador."""

from pathlib import Path
from setuptools import setup, find_packages

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="checador",
    version="1.0.0",
    description="Open-source fingerprint time clock system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/checador",
    packages=find_packages(),
    package_data={
        "checador": ["templates/*.html"],
    },
    include_package_data=True,
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-multipart>=0.0.6",
        "aiofiles>=23.0.0",
        "argon2-cffi>=23.0.0",
        "toml>=0.10.2",
        "jinja2>=3.1.0",
        "sqlalchemy>=2.0.0",
        "aiosqlite>=0.19.0",
        "httpx>=0.25.0",
    ],
    entry_points={
        "console_scripts": [
            "checador=checador.cli.main:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)