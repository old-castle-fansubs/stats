from setuptools import setup, find_packages


setup(
    name="anidex",
    version="1.0.0",
    author="rr-",
    author_email="rr-@sakuya.pl",
    description="anidex.info API",
    packages=find_packages(),
    python_requires=">=3.7.0",
    install_requires=["humanfriendly", "lxml", "requests"],
)
