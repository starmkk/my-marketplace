#!/usr/bin/env python3
"""
Performance benchmarking for Qwen2.5-Omni
Measures inference speed and memory usage
"""

import time
import torch
from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor
from qwen_omni_utils import process_mm_info

def benchmark_model(model_name, use_flash_attn=True):
    print(f"\nBenchmarking {model_name}")
    print("=" * 50)
    
    # Load model
    print("Loading model...")
    start_load = time.time()
    
    if use_flash_attn:
        model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            attn_implementation="flash_attention_2"
        )
    else:
        model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
    
    processor = Qwen2_5OmniProcessor.from_pretrained(model_name)
    load_time = time.time() - start_load
    
    print(f"Model loaded in {load_time:.2f}s")
    
    # Prepare test input
    conversation = [
        {
            "role": "system",
            "content": [{"type": "text", "text": "You are a helpful assistant."}]
        },
        {
            "role": "user",
            "content": "Write a short story about AI."
        }
    ]
    
    text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
    audios, images, videos = process_mm_info(conversation)
    inputs = processor(text=text, audio=audios, images=images, videos=videos, return_tensors="pt", padding=True)
    inputs = inputs.to(model.device)
    
    # Warm up
    print("Warming up...")
    _ = model.generate(**inputs, return_audio=False, max_new_tokens=10)
    torch.cuda.synchronize()
    
    # Benchmark text generation
    print("Benchmarking text generation...")
    torch.cuda.reset_peak_memory_stats()
    
    start = time.time()
    text_ids = model.generate(**inputs, return_audio=False, max_new_tokens=256)
    torch.cuda.synchronize()
    end = time.time()
    
    # Calculate metrics
    inference_time = end - start
    num_tokens = text_ids.shape[1]
    tokens_per_second = num_tokens / inference_time
    memory_used = torch.cuda.max_memory_allocated() / 1e9
    
    # Print results
    print("\nResults:")
    print(f"  Inference time: {inference_time:.2f}s")
    print(f"  Generated tokens: {num_tokens}")
    print(f"  Speed: {tokens_per_second:.2f} tokens/s")
    print(f"  Peak GPU memory: {memory_used:.2f} GB")
    print(f"  FlashAttention-2: {'Yes' if use_flash_attn else 'No'}")
    
    # Test with audio output
    if torch.cuda.is_available():
        print("\nBenchmarking with audio output...")
        torch.cuda.reset_peak_memory_stats()
        
        start = time.time()
        text_ids, audio = model.generate(**inputs, max_new_tokens=128, speaker="Chelsie")
        torch.cuda.synchronize()
        end = time.time()
        
        audio_inference_time = end - start
        audio_memory = torch.cuda.max_memory_allocated() / 1e9
        
        print(f"  Inference time (with audio): {audio_inference_time:.2f}s")
        print(f"  Peak GPU memory (with audio): {audio_memory:.2f} GB")
    
    # Cleanup
    del model
    torch.cuda.empty_cache()
    
    return {
        'model': model_name,
        'load_time': load_time,
        'inference_time': inference_time,
        'tokens_per_second': tokens_per_second,
        'memory_used': memory_used,
        'flash_attn': use_flash_attn
    }

def main():
    print("Qwen2.5-Omni Performance Benchmark")
    print("=" * 50)
    
    models = [
        "Qwen/Qwen2.5-Omni-7B",
        "Qwen/Qwen2.5-Omni-3B",
    ]
    
    results = []
    
    for model_name in models:
        try:
            result = benchmark_model(model_name, use_flash_attn=True)
            results.append(result)
        except Exception as e:
            print(f"Error benchmarking {model_name}: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("Benchmark Summary")
    print("=" * 50)
    
    for result in results:
        print(f"\nModel: {result['model']}")
        print(f"  Speed: {result['tokens_per_second']:.2f} tokens/s")
        print(f"  Memory: {result['memory_used']:.2f} GB")
        print(f"  FlashAttention-2: {result['flash_attn']}")

if __name__ == "__main__":
    main()
