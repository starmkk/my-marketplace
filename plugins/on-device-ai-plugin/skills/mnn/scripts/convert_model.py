#!/usr/bin/env python3
"""
MNN Model Converter Script

Automates model conversion from various frameworks to MNN format
with common optimization and quantization options.

필수 환경변수:
    MNN_SOURCE_PATH  MNN 소스코드 레포 로컬 클론 경로
                     $MNN_SOURCE_PATH/build/MNNConvert 바이너리를 우선 탐색하고,
                     없으면 PATH에서 MNNConvert를 찾는다.

Usage:
    python convert_model.py --input model.onnx --output model.mnn
    python convert_model.py --input model.onnx --output model.mnn --fp16
    python convert_model.py --input model.onnx --output model.mnn --int8 --hqq
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from _env import ensure_mnn_env
ensure_mnn_env()

def run_command(cmd):
    """Run shell command and handle errors"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    
    print(result.stdout)
    return result.stdout

def convert_model(args):
    """Convert model to MNN format"""
    
    # Determine framework
    framework_map = {
        '.pb': 'TF',
        '.onnx': 'ONNX',
        '.caffemodel': 'CAFFE',
        '.pt': 'TORCHSCRIPT',
        '.pth': 'TORCHSCRIPT'
    }
    
    input_path = Path(args.input)
    framework = args.framework or framework_map.get(input_path.suffix)
    
    if not framework:
        print(f"Cannot determine framework from {input_path.suffix}")
        print("Please specify --framework")
        sys.exit(1)
    
    # MNNConvert 바이너리 탐색: $MNN_SOURCE_PATH/build/MNNConvert 우선, 없으면 PATH 폴백
    mnn_convert_bin = "MNNConvert"
    built_bin = Path(os.environ["MNN_SOURCE_PATH"]) / "build" / "MNNConvert"
    if built_bin.exists():
        mnn_convert_bin = str(built_bin)

    # Build MNNConvert command
    cmd = [mnn_convert_bin]
    cmd.extend(['-f', framework])
    cmd.extend(['--modelFile', args.input])
    cmd.extend(['--MNNModel', args.output])
    cmd.extend(['--bizCode', args.biz_code])
    
    # Add optimization level
    if args.optimize:
        cmd.extend(['--optimizeLevel', str(args.optimize)])
    
    # Add quantization options
    if args.fp16:
        cmd.append('--fp16')
    elif args.int8:
        cmd.extend(['--weightQuantBits', '8'])
        if args.hqq:
            cmd.append('--hqq')
        if args.quant_block:
            cmd.extend(['--weightQuantBlock', str(args.quant_block)])
    elif args.int4:
        cmd.extend(['--weightQuantBits', '4'])
        cmd.extend(['--weightQuantBlock', str(args.quant_block or 64)])
        if args.hqq:
            cmd.append('--hqq')
    
    # Keep input format
    if args.keep_input_format:
        cmd.append('--keepInputFormat')
    
    # Run conversion
    print(f"\nConverting {args.input} to {args.output}...")
    print(f"Framework: {framework}")
    
    if args.fp16:
        print("Quantization: FP16")
    elif args.int8:
        print(f"Quantization: Int8 (HQQ={args.hqq})")
    elif args.int4:
        print(f"Quantization: Int4 (block={args.quant_block or 64})")
    
    run_command(cmd)
    
    # Print model size
    output_path = Path(args.output)
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"\nModel saved: {args.output}")
        print(f"Size: {size_mb:.2f} MB")

def main():
    parser = argparse.ArgumentParser(
        description='Convert models to MNN format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic conversion
  %(prog)s --input model.onnx --output model.mnn
  
  # With FP16 quantization
  %(prog)s --input model.onnx --output model.mnn --fp16
  
  # With Int8 quantization and HQQ
  %(prog)s --input model.onnx --output model.mnn --int8 --hqq
  
  # With Int4 quantization for LLMs
  %(prog)s --input model.onnx --output model.mnn --int4 --quant-block 64
        '''
    )
    
    parser.add_argument('--input', required=True,
                       help='Input model file')
    parser.add_argument('--output', required=True,
                       help='Output MNN model file')
    parser.add_argument('--framework',
                       choices=['TF', 'CAFFE', 'ONNX', 'TORCHSCRIPT'],
                       help='Source framework (auto-detected if not specified)')
    parser.add_argument('--biz-code', default='MNN',
                       help='Business code (default: MNN)')
    parser.add_argument('--optimize', type=int, choices=[0, 1, 2], default=2,
                       help='Optimization level: 0=None, 1=Basic, 2=Full (default: 2)')
    
    # Quantization options
    quant_group = parser.add_mutually_exclusive_group()
    quant_group.add_argument('--fp16', action='store_true',
                            help='Enable FP16 quantization')
    quant_group.add_argument('--int8', action='store_true',
                            help='Enable Int8 quantization')
    quant_group.add_argument('--int4', action='store_true',
                            help='Enable Int4 quantization (for LLMs)')
    
    parser.add_argument('--hqq', action='store_true',
                       help='Enable HQQ asymmetric quantization (for Int8/Int4)')
    parser.add_argument('--quant-block', type=int,
                       help='Quantization block size (default: 0 for Int8, 64 for Int4)')
    parser.add_argument('--keep-input-format', action='store_true',
                       help='Keep original input format (NHWC/NCHW)')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    convert_model(args)

if __name__ == '__main__':
    main()
