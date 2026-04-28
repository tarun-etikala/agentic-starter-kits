"""Test file with intentional ruff violations to validate CI."""
import os
import sys
import json  # F401: unused import

x = 1  # F841: unused variable

def bad_format(   a,b,    c ):  # formatting violation
    if type(a) == str:  # E721: type comparison
        return   a
    return b
