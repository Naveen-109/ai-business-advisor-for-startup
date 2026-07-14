#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test Karnataka handler"""

from app_clean import handle_karnataka_district_query

# Test 1: Direct district name
print("=" * 60)
print("TEST 1: Give me business ideas for Mysuru")
print("=" * 60)
result = handle_karnataka_district_query('Give me business ideas for Mysuru')
if result:
    print("✓ Karnataka handler returned result")
    print(f"Length: {len(result)} characters")
    print("\nFirst 300 characters:")
    print(result[:300])
else:
    print("✗ Karnataka handler returned None")

print("\n" + "=" * 60)
print("TEST 2: Tourism business ideas for Mysuru")
print("=" * 60)
result2 = handle_karnataka_district_query('Tourism business ideas for Mysuru')
if result2:
    print("✓ Karnataka handler returned result")
    print(f"Length: {len(result2)} characters")
    print("\nFirst 300 characters:")
    print(result2[:300])
else:
    print("✗ Karnataka handler returned None")

print("\n" + "=" * 60)
print("TEST 3: Business opportunities in Mangalore")
print("=" * 60)
result3 = handle_karnataka_district_query('Business opportunities in Mangalore')
if result3:
    print("✓ Karnataka handler returned result")
    print(f"Length: {len(result3)} characters")
else:
    print("✗ Karnataka handler returned None")
