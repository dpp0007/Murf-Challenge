#!/usr/bin/env python3
"""
Entry point for running the Kisan Mitra agent.
Use: python run_agent.py dev
"""
import sys
from src.agent import server, cli

if __name__ == "__main__":
    cli.run_app(server)
