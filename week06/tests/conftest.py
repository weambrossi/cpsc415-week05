"""Puts week06/ on the import path so the tests import the scripts beside this folder."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
