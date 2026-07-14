#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test global variable in app_clean"""

# Import the module
import app_clean

print(f"llm_enabled from module: {app_clean.llm_enabled}")
print(f"models loaded: {len(app_clean.models)}")
print(f"best_model_name: {app_clean.best_model_name}")

# Try to call check_ollama directly
print("\nCalling check_ollama()...")
result = app_clean.check_ollama()
print(f"check_ollama() returned: {result}")
print(f"llm_enabled after check: {app_clean.llm_enabled}")