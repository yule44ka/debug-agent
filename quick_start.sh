#!/bin/bash
# Quick start script for bug-fixing agent

echo "======================================"
echo "Bug-Fixing Agent - Quick Start"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Run basic tests:"
echo "   python tests/test_basic.py"
echo ""
echo "2. Test agent on a small subset:"
echo "   python eval/run_agent_on_tasks.py --limit 3"
echo ""
echo "3. Evaluate results:"
echo "   python eval/evaluate_pass_at1.py"
echo ""
echo "4. Run on full benchmark (takes time):"
echo "   python eval/run_agent_on_tasks.py"
echo ""
echo "======================================"

