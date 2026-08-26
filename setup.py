import os
from setuptools import setup, find_packages

# Read the contents of README.md for the long description
here = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(here, "README.md")
long_description = ""
if os.path.exists(readme_path):
    with open(readme_path, encoding="utf-8") as f:
        long_description = f.read()

# Read requirements.txt dynamically
requirements_path = os.path.join(here, "requirements.txt")
install_requires = []
if os.path.exists(requirements_path):
    with open(requirements_path, encoding="utf-8") as f:
        install_requires = [
            line.strip()
            for line in f.readlines()
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="pragyanai-demandx",
    version="1.0.0",
    author="PragyanAI",
    author_email="contact@pragyanai.com",
    description="AI-Aggregated Demand-to-Learning Platform with RAG Compiler and Expert Reverse Bidding",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/pragyanai-demandx",
    license="Apache-2.0",
    packages=find_packages(exclude=["tests*", ".github*"]),
    include_package_data=True,
    python_requires=">=3.10, <3.13",
    install_requires=install_requires,
    extras_require={
        "dev": [
            "pytest>=8.2.0,<9.0.0",
            "pytest-mock>=3.14.0,<4.0.0",
            "pytest-cov>=5.0.0,<6.0.0",
            "flake8>=7.0.0,<8.0.0",
            "black>=24.4.0,<25.0.0",
            "isort>=5.13.0,<6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pragyanai-seed=config.seed_data:populate_seed_data",
            "pragyanai-run=app:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Education",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="education marketplace genai rag langchain groq edtech faiss",
    project_urls={
        "Bug Tracker": "https://github.com/your-org/pragyanai-demandx/issues",
        "Source Code": "https://github.com/your-org/pragyanai-demandx",
    },
)
