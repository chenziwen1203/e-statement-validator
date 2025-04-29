from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="estatementvalidator",
    version="0.0.1",
    author="Chen Ziwen",
    author_email="chenziwen23ad@163.com",
    description="A Python module for validating electronic statements (PDF documents)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chenziwen1203/estatementvalidator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.6",
    install_requires=[
        "requests>=2.25.1",
        "PyPDF2>=2.0.0",
        "Pillow>=8.0.0",
        "qrcode>=7.3",
        "opencv-python>=4.5.0",
    ],
    entry_points={
        "console_scripts": [
            "estatementvalidator=estatementvalidator:main",
        ],
    },
) 