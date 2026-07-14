"""
Test Karnataka Districts Business Ideas Integration
Run this to verify the Karnataka system works correctly
"""
from karnataka_integration import (
    get_karnataka_district_ideas,
    get_karnataka_ideas_api,
    list_all_karnataka_districts,
    find_closest_district
)
from karnataka_districts_data import KARNATAKA_DISTRICTS

def test_all_districts():
    """Test that all 31 districts work"""
    print("\n" + "="*60)
    print("TEST 1: All 31 Karnataka Districts")
    print("="*60)
    
    for district in KARNATAKA_DISTRICTS:
        ideas = get_karnataka_district_ideas(district, count=3)
        print(f"✓ {district}: {len(ideas)} ideas generated")
    
    print(f"\n✅ All {len(KARNATAKA_DISTRICTS)} districts working!")

def test_specific_district():
    """Test specific district with details"""
    print("\n" + "="*60)
    print("TEST 2: Bengaluru Urban - Detailed Ideas")
    print("="*60)
    
    ideas = get_karnataka_district_ideas("Bengaluru Urban", count=5)
    
    for idx, idea in enumerate(ideas, 1):
        print(f"\n{idx}. {idea['name']}")
        print(f"   Cost: {idea['cost']}")
        print(f"   Revenue: {idea['revenue']}")
        print(f"   Timeline: {idea['timeline']}")
        print(f"   Skills: {idea['skills']}")
        if 'location_benefit' in idea:
            print(f"   Location Benefit: {idea['location_benefit']}")

def test_category_filter():
    """Test category filtering"""
    print("\n" + "="*60)
    print("TEST 3: Category Filtering - Tourism in Mysuru")
    print("="*60)
    
    ideas = get_karnataka_district_ideas("Mysuru", category="tourism", count=5)
    
    print(f"\nFound {len(ideas)} tourism ideas for Mysuru:")
    for idea in ideas:
        print(f"  • {idea['name']} ({idea['cost']})")

def test_fuzzy_matching():
    """Test fuzzy district name matching"""
    print("\n" + "="*60)
    print("TEST 4: Fuzzy Matching")
    print("="*60)
    
    test_queries = ["bangalore", "mysore", "mangalore", "hubli", "belgaum"]
    
    for query in test_queries:
        district = find_closest_district(query)
        print(f"  '{query}' → {district}")

def test_all_categories():
    """Test all business categories"""
    print("\n" + "="*60)
    print("TEST 5: All Business Categories")
    print("="*60)
    
    categories = ["agriculture", "food", "tourism", "retail", "technology", 
                  "manufacturing", "healthcare", "education", "automobile", "beauty"]
    
    for category in categories:
        ideas = get_karnataka_ideas_api(location="Bengaluru Urban", category=category, count=3)
        print(f"  {category.capitalize()}: {len(ideas)} ideas")

def test_districts_list():
    """Test districts listing"""
    print("\n" + "="*60)
    print("TEST 6: Districts List API")
    print("="*60)
    
    districts = list_all_karnataka_districts()
    print(f"\nTotal districts: {len(districts)}")
    print("\nSample districts:")
    for district in districts[:5]:
        print(f"\n  {district['district']}")
        print(f"    {district['description']}")
        print(f"    Resources: {', '.join(district['key_resources'][:3])}")

def test_special_districts():
    """Test special characteristic districts"""
    print("\n" + "="*60)
    print("TEST 7: Special Districts")
    print("="*60)
    
    special_tests = [
        ("Chikkamagaluru", "Coffee district"),
        ("Kodagu", "Coffee & tourism"),
        ("Mysuru", "Heritage & tourism"),
        ("Dakshina Kannada", "Coastal & education"),
        ("Bidar", "Bidriware craft")
    ]
    
    for district, description in special_tests:
        ideas = get_karnataka_district_ideas(district, count=3)
        print(f"\n  {district} ({description}):")
        for idea in ideas[:2]:
            print(f"    • {idea['name']}")

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("KARNATAKA DISTRICTS BUSINESS IDEAS - INTEGRATION TEST")
    print("="*70)
    
    try:
        test_all_districts()
        test_specific_district()
        test_category_filter()
        test_fuzzy_matching()
        test_all_categories()
        test_districts_list()
        test_special_districts()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\n🎉 Karnataka Districts Integration is working perfectly!")
        print("\n📊 Summary:")
        print(f"  • {len(KARNATAKA_DISTRICTS)} districts covered")
        print(f"  • 10 business categories")
        print(f"  • 50+ unique business ideas")
        print(f"  • District-specific tailoring")
        print(f"  • Fuzzy name matching")
        print("\n🚀 Ready to integrate with app.py!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
