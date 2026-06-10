#!/usr/bin/env python3
"""
Batch inference example for Qwen2.5-Omni
Demonstrates processing multiple requests efficiently
"""

import argparse
import torch
from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor
from qwen_omni_utils import process_mm_info


def main():
    parser = argparse.ArgumentParser(description='Qwen2.5-Omni batch inference')
    parser.add_argument(
        '--model',
        default='Qwen/Qwen2.5-Omni-7B',
        help='Model path or HuggingFace model ID (default: Qwen/Qwen2.5-Omni-7B)',
    )
    args = parser.parse_args()
    model_path = args.model

    # Load model
    print(f"Loading model from {model_path}...")
    model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        attn_implementation="flash_attention_2"
    )
    processor = Qwen2_5OmniProcessor.from_pretrained(model_path)

    # Prepare batch conversations
    conversations = [
        # Text-only
        [
            {"role": "system", "content": [{"type": "text", "text": "You are a helpful assistant."}]},
            {"role": "user", "content": "What is AI?"}
        ],
        # Image input
        [
            {"role": "system", "content": [{"type": "text", "text": "You are a helpful assistant."}]},
            {"role": "user", "content": [
                {"type": "image", "image": "path/to/image.jpg"},
                {"type": "text", "text": "Describe this image"}
            ]}
        ],
        # Audio input
        [
            {"role": "system", "content": [{"type": "text", "text": "You are a helpful assistant."}]},
            {"role": "user", "content": [
                {"type": "audio", "audio": "path/to/audio.wav"},
                {"type": "text", "text": "Transcribe this audio"}
            ]}
        ],
    ]

    # Process batch
    print("Processing batch...")
    text = processor.apply_chat_template(conversations, add_generation_prompt=True, tokenize=False)
    audios, images, videos = process_mm_info(conversations, use_audio_in_video=False)

    inputs = processor(
        text=text, audio=audios, images=images, videos=videos,
        return_tensors="pt", padding=True
    )
    inputs = inputs.to(model.device)

    # Generate (text-only for speed)
    print("Generating responses...")
    text_ids = model.generate(**inputs, return_audio=False, max_new_tokens=256)
    results = processor.batch_decode(text_ids, skip_special_tokens=True)

    for i, result in enumerate(results):
        print(f"\n--- Response {i+1} ---")
        print(result)

    print("\nBatch processing complete!")


if __name__ == "__main__":
    main()
