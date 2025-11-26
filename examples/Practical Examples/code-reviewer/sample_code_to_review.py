"""
Sample Python file with intentional code issues for testing the code reviewer.

This file demonstrates various code quality issues that the multi-agent
reviewer should detect.
"""

import os, sys, json  # Multiple imports on one line (style issue)
from typing import *  # Wildcard import (style issue)


# Missing docstring and type hints
def process_data(data):
    result = []
    # Magic number (readability issue)
    for i in range(10):
        # Inefficient string concatenation (optimization issue)
        s = ""
        for item in data:
            s = s + str(item)  # Should use join
        result.append(s)
    return result


class DataProcessor:
    # Missing docstring
    def __init__(self, x, y, z, a, b, c):  # Too many parameters (complexity issue)
        self.x = x
        self.y = y
        self.z = z
        self.a = a
        self.b = b
        self.c = c

    # Complex nested logic (complexity issue)
    def complex_method(self, value):
        if value > 0:
            if value < 10:
                if value % 2 == 0:
                    if value > 5:
                        return "special"
                    else:
                        return "normal"
                else:
                    return "odd"
            else:
                return "large"
        else:
            return "negative"

    # Security issue: using eval
    def dangerous_eval(self, user_input):
        return eval(user_input)  # Critical security vulnerability!

    # SQL injection vulnerability
    def query_database(self, username):
        query = f"SELECT * FROM users WHERE username = '{username}'"  # SQL injection risk
        return query


# Variable names are not descriptive (readability issue)
def calc(a, b):
    x = a + b
    y = x * 2
    z = y - 5
    return z


# Long line that exceeds PEP 8 recommendation
def very_long_function_name_that_takes_many_parameters(parameter1, parameter2, parameter3, parameter4, parameter5, parameter6):
    return parameter1 + parameter2 + parameter3 + parameter4 + parameter5 + parameter6


# Missing error handling (security/readability issue)
def read_file(filename):
    f = open(filename)  # File not closed, no error handling
    content = f.read()
    return content


# Code duplication (complexity issue)
def get_user_data_1():
    data = {"name": "Alice", "age": 30}
    print("Getting user data")
    return data


def get_user_data_2():
    data = {"name": "Bob", "age": 25}
    print("Getting user data")
    return data


# Hardcoded credentials (critical security issue!)
API_KEY = "sk-1234567890abcdef"
PASSWORD = "admin123"


if __name__ == "__main__":
    # Unvalidated user input (security issue)
    user_input = input("Enter command: ")
    os.system(user_input)  # Command injection vulnerability!
