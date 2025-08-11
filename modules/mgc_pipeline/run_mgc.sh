#!/bin/bash

# MGC Pipeline Runner Script
# Usage: ./run_mgc.sh [mode] [grids] [additional_args...]

set -e

MODE=${1:-both}
GRIDS=${2:-"4x4,5x4,6x4"}
shift 2 2>/dev/null || shift $# 2>/dev/null

echo "🚀 Running MGC Pipeline"
echo "Mode: $MODE"
echo "Grids: $GRIDS"
echo "Additional args: $@"
echo ""

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "Consider activating a virtual environment with PyTorch >= 2.2.0"
    echo ""
fi

# Check PyTorch installation
python -c "import torch; print(f'PyTorch {torch.__version__} - CUDA: {torch.cuda.is_available()}')" || {
    echo "❌ PyTorch not found. Please install requirements:"
    echo "pip install -r requirements.txt"
    exit 1
}

# Run the pipeline
echo "Starting MGC pipeline..."
python mgc_pipeline.py --mode "$MODE" --grids "$GRIDS" "$@"

echo ""
echo "✅ MGC Pipeline completed!"
echo "Results saved in results/ directory"

# Show summary if available
if [[ -f "results/mgc_summary.json" ]]; then
    echo ""
    echo "📊 Quick Summary:"
    python -c "
import json
try:
    with open('results/mgc_summary.json', 'r') as f:
        data = json.load(f)
    print('Grid     K          σ_wall     α*^-1')
    print('-' * 35)
    for row in data:
        print(f'{row[\"grid\"]:<8} {row[\"K\"]:<10.6f} {row[\"sigma_wall\"]:<10.6f} {row[\"alpha_inv\"]:<10.6f}')
except:
    pass
"
fi
