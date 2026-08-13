"""Compound Sustainability Stress Index — Source Package"""
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("compound-ssi")
except PackageNotFoundError:
    __version__ = "1.0.0-dev"
