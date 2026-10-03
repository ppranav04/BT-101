#!/usr/bin/env bash
# Reproducible LeRobot environment for BT-101 (Phase 2+).
#
# Builds the `lerobot` conda env exactly as validated on 2026-10-03:
#   Python 3.12, ffmpeg (conda-forge), torch 2.11 + CUDA 13.0 (Blackwell sm_120),
#   LeRobot v0.6.1 editable from ~/lerobot with extras core_scripts,training,feetech.
#
# Requires miniforge (conda) already installed and an NVIDIA driver >= 580.
# Does NOT delete anything: if the env or the clone already exist, it stops.
# Arm calibration lives in ~/.cache/huggingface/lerobot/calibration and is untouched.

set -euo pipefail

ENV_NAME="lerobot"
PYTHON_VERSION="3.12"
LEROBOT_DIR="$HOME/lerobot"
LEROBOT_TAG="v0.6.1"
LEROBOT_EXTRAS="core_scripts,training,feetech"
TORCH_INDEX="https://download.pytorch.org/whl/cu130"

source "$(conda info --base)/etc/profile.d/conda.sh"

if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
    echo "Conda env '$ENV_NAME' already exists. Remove it first: conda env remove -n $ENV_NAME" >&2
    exit 1
fi
if [ -e "$LEROBOT_DIR" ]; then
    echo "$LEROBOT_DIR already exists. Move or remove it first." >&2
    exit 1
fi

echo "==> Creating conda env '$ENV_NAME' (Python $PYTHON_VERSION) + ffmpeg"
conda create -y -n "$ENV_NAME" "python=$PYTHON_VERSION"
conda activate "$ENV_NAME"
conda install -y ffmpeg -c conda-forge
ffmpeg -encoders 2>/dev/null | grep -q libsvtav1 || { echo "ffmpeg is missing libsvtav1" >&2; exit 1; }

# Install torch first from an explicit CUDA index, so the LeRobot install
# can't pull in a build without sm_120 support.
echo "==> Installing torch + torchvision ($TORCH_INDEX)"
pip install --index-url "$TORCH_INDEX" torch torchvision
python - <<'EOF'
import torch
assert torch.cuda.is_available(), "CUDA not available"
assert "sm_120" in torch.cuda.get_arch_list(), "torch build lacks sm_120 (Blackwell)"
print("torch", torch.__version__, "CUDA", torch.version.cuda, "OK")
EOF

echo "==> Cloning LeRobot $LEROBOT_TAG"
git clone https://github.com/huggingface/lerobot.git "$LEROBOT_DIR"
git -C "$LEROBOT_DIR" checkout "$LEROBOT_TAG"

echo "==> Installing LeRobot [$LEROBOT_EXTRAS]"
torch_before=$(python -c "import torch; print(torch.__version__)")
pip install -e "$LEROBOT_DIR[$LEROBOT_EXTRAS]"
torch_after=$(python -c "import torch; print(torch.__version__)")
if [ "$torch_before" != "$torch_after" ]; then
    echo "LeRobot install replaced torch ($torch_before -> $torch_after). Check CUDA support." >&2
    exit 1
fi

echo "==> Verifying"
python -c "import lerobot, torch, scservo_sdk; print('lerobot', lerobot.__version__, '| torch', torch.__version__, '| cuda', torch.cuda.is_available())"
pip check

echo "Done. Activate with: conda activate $ENV_NAME"
