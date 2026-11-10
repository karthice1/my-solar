"""
Executable module entry point for structural subsystem.
Allows 'python -m structural <command>' as an alias for 'python -m structural.cli <command>'.
"""

from structural.cli import main

if __name__ == "__main__":
    main()
