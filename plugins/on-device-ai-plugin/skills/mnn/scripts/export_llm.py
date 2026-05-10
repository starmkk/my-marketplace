#!/usr/bin/env python3
"""
MNN-LLM Export Helper Script

Simplifies exporting LLM models to MNN format with common configurations.

Usage:
    python export_llm.py --model Qwen/Qwen2.5-7B
    python export_llm.py --model meta-llama/Llama-3.1-8B --quant 4
    python export_llm.py --model Qwen/Qwen2.5-7B --quant 8 --hqq
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Common model configurations
MODEL_CONFIGS = {
    'qwen': {
        'family': ['Qwen', 'Qwen2', 'Qwen2.5', 'Qwen-VL'],
        'tokenizer_type': 'qwen'
    },
    'llama': {
        'family': ['Llama', 'llama', 'Meta-Llama'],
        'tokenizer_type': 'llama'
    },
    'deepseek': {
        'family': ['deepseek', 'DeepSeek'],
        'tokenizer_type': 'deepseek'
    },
    'phi': {
        'family': ['Phi', 'phi'],
        'tokenizer_type': 'phi'
    }
}

def detect_model_family(model_path):
    """Detect model family from path"""
    model_lower = model_path.lower()
    
    for family, config in MODEL_CONFIGS.items():
        for pattern in config['family']:
            if pattern.lower() in model_lower:
                return family
    
    return 'unknown'

def run_command(cmd, cwd=None):
    """Run shell command and handle errors"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    
    print(result.stdout)
    return True

def export_llm(args):
    """Export LLM model to MNN format"""
    
    # Detect model family
    model_family = detect_model_family(args.model)
    print(f"Detected model family: {model_family}")
    
    # Prepare export command
    cmd = ['python', 'llmexport.py']
    cmd.extend(['--path', args.model])
    cmd.extend(['--export', 'mnn'])
    
    # Add quantization
    if args.quant:
        cmd.extend(['--quant_bit', str(args.quant)])
    
    # Add block size
    if args.block:
        cmd.extend(['--quant_block', str(args.block)])
    
    # Add HQQ if specified
    if args.hqq:
        cmd.append('--hqq')
    
    # Add skip slim if specified
    if args.skip_slim:
        cmd.append('--skip_slim')
    
    # Add lm_quant_bit if specified
    if args.lm_quant:
        cmd.extend(['--lm_quant_bit', str(args.lm_quant)])
    
    print("\n========================================")
    print("Exporting LLM to MNN format")
    print("========================================")
    print(f"Model: {args.model}")
    print(f"Family: {model_family}")
    print(f"Quantization: {args.quant}-bit" if args.quant else "No quantization")
    if args.quant:
        print(f"Block size: {args.block if args.block else 'default'}")
        print(f"HQQ: {'Yes' if args.hqq else 'No'}")
    print("========================================\n")
    
    # Change to transformers/llm directory
    llm_dir = Path('transformers/llm')
    if not llm_dir.exists():
        print(f"Error: {llm_dir} not found")
        print("Please run this script from MNN root directory")
        sys.exit(1)
    
    # Check if requirements are installed
    try:
        import torch
        import transformers
    except ImportError:
        print("\nInstalling requirements...")
        req_cmd = ['pip', 'install', '-r', 'requirements.txt']
        if not run_command(req_cmd, cwd=str(llm_dir)):
            print("Failed to install requirements")
            sys.exit(1)
    
    # Run export
    if not run_command(cmd, cwd=str(llm_dir)):
        print("\nExport failed!")
        sys.exit(1)
    
    # Print output location
    output_dir = llm_dir / 'export' / args.model.split('/')[-1]
    print("\n========================================")
    print("Export Complete!")
    print("========================================")
    print(f"Output directory: {output_dir}")
    
    # List output files
    if output_dir.exists():
        print("\nGenerated files:")
        for file in sorted(output_dir.rglob('*.mnn')):
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"  {file.name}: {size_mb:.2f} MB")
    
    # Print usage instructions
    print("\n========================================")
    print("Usage Instructions")
    print("========================================")
    print("To use this model:")
    print("1. Copy the .mnn file to your mobile app")
    print("2. Load with MNN-LLM API:")
    print("   C++: Llm::createLLM(config)")
    print("   Python: mnnllm.create('model.mnn')")
    print("\nFor more details, see:")
    print("  - references/llm_deployment.md")
    print("  - https://mnn-docs.readthedocs.io/en/latest/transformers/llm.html")
    print()

def main():
    parser = argparse.ArgumentParser(
        description='Export LLM models to MNN format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Export Qwen model with 4-bit quantization
  %(prog)s --model Qwen/Qwen2.5-7B --quant 4
  
  # Export Llama model with 8-bit quantization and HQQ
  %(prog)s --model meta-llama/Llama-3.1-8B --quant 8 --hqq
  
  # Export with custom block size
  %(prog)s --model Qwen/Qwen2.5-7B --quant 4 --block 128
  
Supported models:
  - Qwen (Qwen2, Qwen2.5, Qwen-VL)
  - Llama (Llama 2, Llama 3, TinyLlama)
  - DeepSeek (DeepSeek-V2, DeepSeek-R1)
  - Phi (Phi-2, Phi-3)
  - Baichuan, Yi, InternLM, Gemma
        '''
    )
    
    parser.add_argument('--model', required=True,
                       help='HuggingFace model path (e.g., Qwen/Qwen2.5-7B)')
    parser.add_argument('--quant', type=int, choices=[2, 3, 4, 5, 6, 7, 8],
                       help='Quantization bits (default: 4)')
    parser.add_argument('--block', type=int,
                       help='Quantization block size (default: 64 for 4-bit, 0 for 8-bit)')
    parser.add_argument('--hqq', action='store_true',
                       help='Enable HQQ asymmetric quantization (better accuracy)')
    parser.add_argument('--skip-slim', action='store_true',
                       help='Skip weight slimming optimization')
    parser.add_argument('--lm-quant', type=int,
                       help='Language model head quantization bits')
    
    args = parser.parse_args()
    
    # Set default quant if not specified
    if args.quant is None:
        args.quant = 4
        print("Using default quantization: 4-bit")
    
    export_llm(args)

if __name__ == '__main__':
    main()
