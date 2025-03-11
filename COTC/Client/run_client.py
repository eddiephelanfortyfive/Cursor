#!/usr/bin/env python3
"""
Run Client

Script to start the monitoring client agent.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from client_agent import main

if __name__ == "__main__":
    print("Starting System Metrics & Stock Data Client Agent...")
    main() 