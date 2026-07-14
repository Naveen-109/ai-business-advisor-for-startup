#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test Ollama connection"""

import requests

print("Testing Ollama connection...")
print("=" * 60)

# Test v1 API
try:
    print("\n1. Testing v1 API (http://localhost:11434/v1/models)...")
    r = requests.get('http://localhost:11434/v1/models', timeout=5)
    print(f"   Status Code: {r.status_code}")
    if r.status_code == 200:
        print("   ✓ v1 API working!")
        data = r.json()
        print(f"   Response: {data}")
    else:
        print(f"   ✗ v1 API returned {r.status_code}")
except Exception as e:
    print(f"   ✗ v1 API failed: {e}")

# Test legacy API
try:
    print("\n2. Testing legacy API (http://localhost:11434/api/tags)...")
    r = requests.get('http://localhost:11434/api/tags', timeout=5)
    print(f"   Status Code: {r.status_code}")
    if r.status_code == 200:
        print("   ✓ Legacy API working!")
        data = r.json()
        if 'models' in data:
            print(f"   Models: {[m['name'] for m in data['models']]}")
    else:
        print(f"   ✗ Legacy API returned {r.status_code}")
except Exception as e:
    print(f"   ✗ Legacy API failed: {e}")

# Test chat API
try:
    print("\n3. Testing chat API...")
    r = requests.post(
        'http://localhost:11434/api/chat',
        json={
            'model': 'llama3.2',
            'messages': [{'role': 'user', 'content': 'Hello'}],
            'stream': False
        },
        timeout=30
    )
    print(f"   Status Code: {r.status_code}")
    if r.status_code == 200:
        print("   ✓ Chat API working!")
        data = r.json()
        if 'message' in data:
            print(f"   Response: {data['message']['content'][:100]}...")
    else:
        print(f"   ✗ Chat API returned {r.status_code}")
except Exception as e:
    print(f"   ✗ Chat API failed: {e}")

print("\n" + "=" * 60)
print("Test complete!")
