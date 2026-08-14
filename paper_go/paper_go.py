#!/usr/bin/env python3
"""Convenience wrapper: python3 paper_go.py 'paper title'"""
import sys

from paper_go.cli import main

if __name__ == "__main__":
    sys.exit(main())
