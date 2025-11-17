#!/usr/bin/env python3
"""
RelationOS Analysis Tool - Main Entry Point
Human-in-the-loop monitoring and analysis of MBSE relations
"""

import sys
import os
from pathlib import Path

def get_cli_module():
    """Get CLI module with proper import handling"""
    try:
        # Try relative import first (when run as module)
        from .commands.cli import main as cli_main
        return cli_main
    except ImportError:
        # Fall back to absolute import (when run as script)
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))

        from commands import cli
        return cli.main

def main():
    """
    Main entry point for RelationOS analysis
    Dispatches to CLI interface for argument processing
    """
    try:
        cli_main = get_cli_module()
        return cli_main()
    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"Error details: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
