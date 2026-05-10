#!/usr/bin/env python3
"""
Voice chatting demo for Qwen2.5-Omni
Interactive voice conversation with audio input and output
"""

import torch
import soundfile as sf
from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor
from qwen_omni_utils import process_mm_info

def main():
    # Load model
    print("Loading Qwen2.5-Omni...")
    model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
        "Qwen/Qwen2.5-Omni-7B",
        torch_dtype=torch.bfloat16,
        device_map="auto",
        attn_implementation="flash_attention_2"
    )
    processor = Qwen2_5OmniProcessor.from_pretrained("Qwen/Qwen2.5-Omni-7B")
    
    print("Model loaded successfully!")
    print("\nVoice Chatting Demo")
    print("==================")
    print("Available voices: Chelsie (female), Ethan (male)")
    
    # Select voice
    voice = input("\nSelect voice (Chelsie/Ethan) [Chelsie]: ").strip() or "Chelsie"
    if voice not in ["Chelsie", "Ethan"]:
        print("Invalid voice, using Chelsie")
        voice = "Chelsie"
    
    # Initialize conversation
    conversation = [
        {
            "role": "system",
            "content": [
                {"type": "text", "text": "You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, capable of perceiving auditory and visual inputs, as well as generating text and speech."}
            ],
        },
    ]
    
    turn = 1
    print("\nStarting conversation...")
    print("Type 'quit' to exit\n")
    
    while True:
        # Get user input
        user_input = input(f"You (Turn {turn}): ").strip()
        
        if user_input.lower() == 'quit':
            print("Ending conversation. Goodbye!")
            break
        
        if not user_input:
            continue
        
        # Add user message
        conversation.append({
            "role": "user",
            "content": user_input
        })
        
        # Process
        text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
        audios, images, videos = process_mm_info(conversation, use_audio_in_video=False)
        
        inputs = processor(
            text=text,
            audio=audios,
            images=images,
            videos=videos,
            return_tensors="pt",
            padding=True
        )
        inputs = inputs.to(model.device)
        
        # Generate
        print(f"Qwen (Turn {turn}): Generating response...")
        text_ids, audio = model.generate(**inputs, speaker=voice, max_new_tokens=256)
        response = processor.batch_decode(text_ids, skip_special_tokens=True)[0]
        
        # Print response
        print(f"Qwen (Turn {turn}): {response}")
        
        # Save audio
        audio_filename = f"response_turn{turn}.wav"
        sf.write(audio_filename, audio.reshape(-1).detach().cpu().numpy(), samplerate=24000)
        print(f"Audio saved to: {audio_filename}")
        
        # Add assistant response to conversation
        conversation.append({
            "role": "assistant",
            "content": response
        })
        
        turn += 1
        print()

if __name__ == "__main__":
    main()
