from setuptools import setup, find_packages

setup(
    name="sasya-common",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "PyJWT>=2.8.0",
        "sqlalchemy>=2.0.0",
        "asyncpg>=0.28.0",
    ]
)
