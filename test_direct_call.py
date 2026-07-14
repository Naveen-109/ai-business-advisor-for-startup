#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Direct test of generate_business_advice"""

from app_clean import generate_business_advice

print("=" * 60)
print("Testing: Give me business ideas for Mysuru")
print("=" * 60)

response = generate_business_advice('Give me business ideas for Mysuru')

print("\n" + "=" * 60)
print("RESPONSE:")
print("=" * 60)
print(response)
print("\n" + "=" * 60)

if 'MYSURU' in response:
    print("✓ SUCCESS: Response contains MYSURU")
else:
    print("✗ FAIL: Response does NOT contain MYSURU")
