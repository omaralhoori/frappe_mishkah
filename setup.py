from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in mishkah/__init__.py
from mishkah import __version__ as version

setup(
	name="mishkah",
	version=version,
	description="App for managing mishkah students",
	author="Omar Alhori",
	author_email="app@mishkah.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
