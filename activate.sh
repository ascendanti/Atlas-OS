#!/bin/bash
# Atlas Personal OS - Quick Start Script

# Activate virtual environment
source venv/bin/activate

# Show welcome message
echo "🚀 Atlas Personal OS - Activated"
echo ""
echo "Available commands:"
echo "  python main.py --help       # Show all commands"
echo "  python main.py task list    # List tasks"
echo "  python main.py task add     # Add task"
echo ""
echo "Development:"
echo "  pytest tests/               # Run tests"
echo "  black .                     # Format code"
echo ""
echo "To deactivate: deactivate"
