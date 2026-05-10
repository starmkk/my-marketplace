#!/bin/bash
# Install Qwen2.5-Omni dependencies

set -e

echo "==================================="
echo "Qwen2.5-Omni Dependency Installation"
echo "==================================="

echo ""
echo "Installing core dependencies..."
pip install transformers==4.52.3
pip install accelerate
pip install qwen-omni-utils[decord] -U
pip install soundfile

echo ""
echo "Core dependencies installed successfully!"

echo ""
read -p "Install FlashAttention-2? (recommended, y/n): " install_flash
if [ "$install_flash" = "y" ] || [ "$install_flash" = "Y" ]; then
    echo "Installing FlashAttention-2..."
    pip install -U flash-attn --no-build-isolation
    echo "FlashAttention-2 installed!"
fi

echo ""
read -p "Install vLLM dependencies? (optional, y/n): " install_vllm
if [ "$install_vllm" = "y" ] || [ "$install_vllm" = "Y" ]; then
    echo "Installing vLLM dependencies..."
    pip install setuptools_scm torchdiffeq resampy x_transformers
    echo "vLLM dependencies installed!"
fi

echo ""
read -p "Install quantization libraries? (optional, y/n): " install_quant
if [ "$install_quant" = "y" ] || [ "$install_quant" = "Y" ]; then
    echo "Installing GPTQ and AWQ..."
    pip install gptqmodel==2.0.0
    pip install autoawq==0.2.9
    echo "Quantization libraries installed!"
fi

echo ""
echo "==================================="
echo "Installation complete!"
echo "==================================="
