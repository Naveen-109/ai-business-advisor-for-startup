#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix LLM by testing and enabling it"""

import requests

def test_and_enable_llm():
    """Test Ollama and return status"""
    try:
        # Test Ollama
        r = requests.get('http://localhost:11434/api/tags', timeout=5)
        if r.status_code == 200:
            data = r.json()
            if 'models' in data and len(data['models']) > 0:
                print("✓ Ollama is working")
                print(f"✓ Available models: {[m['name'] for m in data['models']]}")
                
                # Test a simple chat
                chat_response = requests.post(
                    'http://localhost:11434/api/chat',
                    json={
                        'model': 'llama3.2',
                        'messages': [{'role': 'user', 'content': 'Hello'}],
                        'stream': False
                    },
                    timeout=10
                )
                
                if chat_response.status_code == 200:
                    print("✓ Chat API working")
                    return True
                else:
                    print(f"✗ Chat API failed: {chat_response.status_code}")
                    return False
            else:
                print("✗ No models available")
                return False
        else:
            print(f"✗ Ollama API failed: {r.status_code}")
            return False
    except Exception as e:
        print(f"✗ Ollama test failed: {e}")
        return False

if __name__ == '__main__':
    print("Testing Ollama LLM...")
    result = test_and_enable_llm()
    print(f"Result: {'WORKING' if result else 'FAILED'}")