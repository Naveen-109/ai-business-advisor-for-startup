"""
Quick verification script to test all major features
Run this to ensure everything is working correctly
"""
import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*50)
    print("TEST 1: Health Check")
    print("="*50)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✓ Server is healthy")
            print(f"  Models loaded: {data.get('models_loaded')}")
            print(f"  Best model: {data.get('best_model')}")
            print(f"  Available models: {', '.join(data.get('available_models', []))}")
            print(f"  LLM enabled: {data.get('llm_enabled')}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_prediction():
    """Test ML prediction"""
    print("\n" + "="*50)
    print("TEST 2: ML Prediction")
    print("="*50)
    try:
        payload = {
            "sales": 20000,
            "expenses": 12000,
            "marketing_spend": 2500,
            "employee_count": 25,
            "competition_level": 3
        }
        response = requests.post(f"{BASE_URL}/predict", json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✓ Prediction successful")
            print(f"  Predicted Profit: ${data.get('prediction', 0):.2f}")
            print(f"  Model used: {data.get('model_used')}")
            print(f"  All predictions:")
            for model, pred in data.get('all_predictions', {}).items():
                print(f"    • {model}: ${pred:.2f}")
            return True
        else:
            print(f"✗ Prediction failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_chat_prediction():
    """Test chat with prediction"""
    print("\n" + "="*50)
    print("TEST 3: Chat with Prediction")
    print("="*50)
    try:
        payload = {
            "message": "Predict my profit with sales of $15000, expenses of $8000, marketing $1500"
        }
        response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            print("✓ Chat prediction successful")
            print(f"  LLM enabled: {data.get('llm_enabled')}")
            response_text = data.get('response', '')
            # Show first 200 chars
            print(f"  Response preview: {response_text[:200]}...")
            return True
        else:
            print(f"✗ Chat failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_business_ideas():
    """Test business ideas generation"""
    print("\n" + "="*50)
    print("TEST 4: Business Ideas Generation")
    print("="*50)
    try:
        payload = {
            "message": "Give me business ideas for Bangalore"
        }
        response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            if 'BUSINESS IDEAS' in response_text:
                print("✓ Business ideas generated successfully")
                # Count ideas
                idea_count = response_text.count('**1.') + response_text.count('**2.')
                print(f"  Ideas generated: {idea_count}+")
                print(f"  Response length: {len(response_text)} characters")
                return True
            else:
                print("✗ No business ideas in response")
                return False
        else:
            print(f"✗ Request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_business_ideas_api():
    """Test business ideas API endpoint"""
    print("\n" + "="*50)
    print("TEST 5: Business Ideas API")
    print("="*50)
    try:
        payload = {
            "location": "Bangalore",
            "category": "technology",
            "count": 3
        }
        response = requests.post(f"{BASE_URL}/api/business-ideas", json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            ideas = data.get('ideas', [])
            print(f"✓ API returned {len(ideas)} business ideas")
            if ideas:
                print(f"  Example: {ideas[0].get('name', 'N/A')}")
                print(f"  Cost: {ideas[0].get('startup_cost', 'N/A')}")
                print(f"  Revenue: {ideas[0].get('revenue_potential', 'N/A')}")
            return True
        else:
            print(f"✗ API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_strategic_advice():
    """Test strategic advice"""
    print("\n" + "="*50)
    print("TEST 6: Strategic Advice")
    print("="*50)
    try:
        payload = {
            "message": "How can I increase my profit margin?"
        }
        response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            if len(response_text) > 100:
                print("✓ Strategic advice generated")
                print(f"  Response length: {len(response_text)} characters")
                # Check for strategy keywords
                has_strategies = any(word in response_text.lower() for word in 
                                   ['strategy', 'strategies', 'optimization', 'growth', 'revenue'])
                print(f"  Contains strategies: {has_strategies}")
                return True
            else:
                print("✗ Response too short")
                return False
        else:
            print(f"✗ Request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_models_endpoint():
    """Test models listing endpoint"""
    print("\n" + "="*50)
    print("TEST 7: Models Endpoint")
    print("="*50)
    try:
        response = requests.get(f"{BASE_URL}/models", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✓ Models endpoint working")
            print(f"  Available models: {', '.join(data.get('models', []))}")
            print(f"  Best model: {data.get('best_model')}")
            return True
        else:
            print(f"✗ Request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AI/ML BUSINESS ADVISOR - FEATURE VERIFICATION")
    print("="*60)
    print("\nMake sure the Flask server is running: python app.py")
    print("Testing server at:", BASE_URL)
    
    tests = [
        ("Health Check", test_health),
        ("ML Prediction", test_prediction),
        ("Chat Prediction", test_chat_prediction),
        ("Business Ideas (Chat)", test_business_ideas),
        ("Business Ideas (API)", test_business_ideas_api),
        ("Strategic Advice", test_strategic_advice),
        ("Models Endpoint", test_models_endpoint),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed ({passed*100//total}%)")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed! Your application is fully functional!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
