"""
Karnataka Districts Business Ideas Integration
Add this to your existing app.py for complete Karnataka district coverage
"""
import random
from karnataka_districts_data import DISTRICT_DATA, KARNATAKA_DISTRICTS

def get_karnataka_district_ideas(district, category=None, count=5):
    """
    Get tailored business ideas for any Karnataka district
    
    Args:
        district: District name (e.g., "Bengaluru Urban", "Mysuru")
        category: Optional category filter
        count: Number of ideas to return
    
    Returns:
        List of business ideas with district-specific context
    """
    if district not in DISTRICT_DATA:
        # Try fuzzy matching
        district = find_closest_district(district)
        if not district:
            return []
    
    district_info = DISTRICT_DATA[district]
    ideas = generate_district_specific_ideas(district, district_info, category)
    
    # Add district context to each idea
    for idea in ideas[:count]:
        idea['district'] = district
        idea['location_benefit'] = get_location_benefit(district, district_info, idea)
    
    return ideas[:count]

def find_closest_district(query):
    """Find closest matching district name"""
    if not query:
        return None
    
    query_lower = query.lower().strip()
    
    # Direct match
    for district in KARNATAKA_DISTRICTS:
        if query_lower == district.lower():
            return district
    
    # Partial match
    for district in KARNATAKA_DISTRICTS:
        if query_lower in district.lower() or district.lower() in query_lower:
            return district
    
    # Common name variations
    name_map = {
        'bangalore': 'Bengaluru Urban',
        'bengaluru': 'Bengaluru Urban',
        'mysore': 'Mysuru',
        'mangalore': 'Dakshina Kannada',
        'hubli': 'Dharwad',
        'belgaum': 'Belagavi',
        'gulbarga': 'Kalaburagi',
        'bijapur': 'Vijayapura',
        'shimoga': 'Shivamogga',
        'tumkur': 'Tumakuru',
        'bellary': 'Ballari',
        'coorg': 'Kodagu'
    }
    
    if query_lower in name_map:
        return name_map[query_lower]
    
    return None

def get_location_benefit(district, district_info, idea):
    """Generate location-specific benefit for the business idea"""
    resources = district_info.get("key_resources", [])
    tourism = district_info.get("tourism", "")
    opportunities = district_info.get("opportunities", [])
    
    benefits = []
    
    # Match idea with district resources
    idea_name_lower = idea['name'].lower()
    
    if "coffee" in idea_name_lower and any("coffee" in str(r).lower() for r in resources):
        benefits.append(f"{district} is known for coffee production")
    
    if "silk" in idea_name_lower and any("silk" in str(r).lower() for r in resources):
        benefits.append(f"{district} has strong sericulture tradition")
    
    if "tourism" in idea_name_lower or "homestay" in idea_name_lower:
        if tourism:
            benefits.append(f"Tourist attractions: {tourism[:100]}...")
    
    if "tech" in idea_name_lower or "software" in idea_name_lower:
        if district == "Bengaluru Urban":
            benefits.append("IT capital with abundant tech talent")
    
    if "agriculture" in idea_name_lower or "farm" in idea_name_lower:
        if any("agriculture" in str(r).lower() for r in resources):
            benefits.append(f"{district} has strong agricultural base")
    
    return benefits[0] if benefits else f"Growing market opportunity in {district}"

def generate_district_specific_ideas(district, district_info, category=None):
    """Generate ideas tailored to district characteristics"""
    ideas = []
    resources = district_info.get("key_resources", [])
    
    # Add ideas based on district resources
    ideas.extend(get_resource_based_ideas(district, resources))
    ideas.extend(get_tourism_based_ideas(district, district_info))
    ideas.extend(get_general_ideas(district))
    
    # Filter by category if specified
    if category:
        ideas = [i for i in ideas if i.get('category') == category]
    
    # Shuffle for variety
    random.shuffle(ideas)
    
    return ideas


def get_resource_based_ideas(district, resources):
    """Get ideas based on district resources"""
    ideas = []
    resources_str = " ".join([str(r).lower() for r in resources])
    
    # Coffee-based ideas
    if "coffee" in resources_str:
        ideas.extend([
            {"name": "Coffee Estate Tourism", "cost": "₹10-25 L", "revenue": "₹2-5 L/month", "timeline": "6-12 months", "skills": "Hospitality, coffee knowledge", "category": "tourism"},
            {"name": "Coffee Roasting & Export", "cost": "₹8-20 L", "revenue": "₹2-5 L/month", "timeline": "4-6 months", "skills": "Coffee roasting, export", "category": "food"},
            {"name": "Specialty Coffee Cafe", "cost": "₹6-15 L", "revenue": "₹1.5-4 L/month", "timeline": "3-5 months", "skills": "Barista, cafe management", "category": "food"}
        ])
    
    # Silk/Sericulture ideas
    if "silk" in resources_str or "sericulture" in resources_str:
        ideas.extend([
            {"name": "Silk Saree Boutique", "cost": "₹5-12 L", "revenue": "₹1.2-3 L/month", "timeline": "3-6 months", "skills": "Fashion, retail", "category": "retail"},
            {"name": "Silk Production Unit", "cost": "₹8-20 L", "revenue": "₹2-5 L/month", "timeline": "8-12 months", "skills": "Sericulture, silk processing", "category": "manufacturing"},
            {"name": "Silk Export Business", "cost": "₹10-25 L", "revenue": "₹2.5-6 L/month", "timeline": "6-10 months", "skills": "Export procedures, quality control", "category": "manufacturing"}
        ])
    
    # IT/Tech ideas
    if "it" in resources_str or "technology" in resources_str or district == "Bengaluru Urban":
        ideas.extend([
            {"name": "Software Development Agency", "cost": "₹3-8 L", "revenue": "₹1.5-4 L/month", "timeline": "2-4 months", "skills": "Programming, project management", "category": "technology"},
            {"name": "Digital Marketing Agency", "cost": "₹2-5 L", "revenue": "₹1-3 L/month", "timeline": "2-3 months", "skills": "SEO, social media, ads", "category": "technology"},
            {"name": "Mobile App Development", "cost": "₹3-8 L", "revenue": "₹1.5-4 L/month", "timeline": "3-5 months", "skills": "App development, UI/UX", "category": "technology"},
            {"name": "AI/ML Consulting", "cost": "₹4-10 L", "revenue": "₹2-5 L/month", "timeline": "3-6 months", "skills": "AI/ML, data science", "category": "technology"}
        ])
    
    # Mining/Industrial ideas
    if "mining" in resources_str or "iron ore" in resources_str:
        ideas.extend([
            {"name": "Mining Equipment Supply", "cost": "₹15-40 L", "revenue": "₹3-8 L/month", "timeline": "6-12 months", "skills": "Mining industry knowledge", "category": "manufacturing"},
            {"name": "Industrial Safety Equipment", "cost": "₹5-12 L", "revenue": "₹1.2-3 L/month", "timeline": "4-6 months", "skills": "Safety standards, B2B sales", "category": "retail"}
        ])
    
    # Textile ideas
    if "textile" in resources_str or "cotton" in resources_str or "handloom" in resources_str:
        ideas.extend([
            {"name": "Garment Manufacturing Unit", "cost": "₹10-25 L", "revenue": "₹2.5-6 L/month", "timeline": "6-10 months", "skills": "Garment production, quality control", "category": "manufacturing"},
            {"name": "Textile Export Business", "cost": "₹15-35 L", "revenue": "₹3-8 L/month", "timeline": "8-12 months", "skills": "Export, textile knowledge", "category": "manufacturing"},
            {"name": "Fashion Boutique", "cost": "₹4-10 L", "revenue": "₹1-2.5 L/month", "timeline": "3-5 months", "skills": "Fashion design, retail", "category": "beauty"}
        ])
    
    # Education ideas
    if "education" in resources_str:
        ideas.extend([
            {"name": "Coaching Center", "cost": "₹3-8 L", "revenue": "₹1-2.5 L/month", "timeline": "3-5 months", "skills": "Teaching, subject expertise", "category": "education"},
            {"name": "Skill Training Institute", "cost": "₹5-12 L", "revenue": "₹1.5-3.5 L/month", "timeline": "4-6 months", "skills": "Training, industry connections", "category": "education"},
            {"name": "Computer Training Center", "cost": "₹4-10 L", "revenue": "₹1.2-3 L/month", "timeline": "3-5 months", "skills": "Computer skills, teaching", "category": "education"}
        ])
    
    return ideas

def get_tourism_based_ideas(district, district_info):
    """Get tourism-related ideas"""
    ideas = []
    tourism = district_info.get("tourism", "")
    
    if tourism:
        ideas.extend([
            {"name": "Homestay Business", "cost": "₹5-15 L", "revenue": "₹80K-2.5 L/month", "timeline": "3-6 months", "skills": "Hospitality, local knowledge", "category": "tourism"},
            {"name": "Local Tour Guide Service", "cost": "₹50K-2 L", "revenue": "₹40K-1.2 L/month", "timeline": "1-2 months", "skills": "Local history, communication", "category": "tourism"},
            {"name": "Adventure Tourism", "cost": "₹8-20 L", "revenue": "₹1.5-4 L/month", "timeline": "4-8 months", "skills": "Adventure sports, safety", "category": "tourism"},
            {"name": "Eco-Resort", "cost": "₹25-60 L", "revenue": "₹4-10 L/month", "timeline": "12-18 months", "skills": "Hospitality, sustainability", "category": "tourism"}
        ])
    
    return ideas

def get_general_ideas(district):
    """Get general business ideas applicable to all districts"""
    return [
        # Food & Beverages
        {"name": "Cloud Kitchen", "cost": "₹4-12 L", "revenue": "₹1.5-4 L/month", "timeline": "2-4 months", "skills": "Cooking, online ordering", "category": "food"},
        {"name": "Bakery & Sweets Shop", "cost": "₹6-15 L", "revenue": "₹1.5-4 L/month", "timeline": "3-6 months", "skills": "Baking, confectionery", "category": "food"},
        {"name": "Millet-Based Products", "cost": "₹3-10 L", "revenue": "₹1-2.5 L/month", "timeline": "3-6 months", "skills": "Food processing, marketing", "category": "food"},
        {"name": "Catering Service", "cost": "₹2.5-8 L", "revenue": "₹1-3 L/month", "timeline": "2-3 months", "skills": "Cooking, event management", "category": "food"},
        
        # Retail
        {"name": "Franchise Store", "cost": "₹8-20 L", "revenue": "₹1.5-4 L/month", "timeline": "4-6 months", "skills": "Retail management, customer service", "category": "retail"},
        {"name": "Supermarket", "cost": "₹15-40 L", "revenue": "₹2.5-6 L/month", "timeline": "6-10 months", "skills": "Retail, inventory management", "category": "retail"},
        {"name": "Rural Retail Kiosk", "cost": "₹1-3 L", "revenue": "₹30K-80K/month", "timeline": "1-2 months", "skills": "Basic retail, local knowledge", "category": "retail"},
        
        # Healthcare
        {"name": "Diagnostic Center", "cost": "₹10-25 L", "revenue": "₹2-5 L/month", "timeline": "6-10 months", "skills": "Medical knowledge, lab management", "category": "healthcare"},
        {"name": "Yoga/Fitness Studio", "cost": "₹3-8 L", "revenue": "₹80K-2 L/month", "timeline": "2-4 months", "skills": "Yoga/fitness training, management", "category": "healthcare"},
        {"name": "Ayurvedic Products", "cost": "₹4-10 L", "revenue": "₹1-2.5 L/month", "timeline": "4-6 months", "skills": "Ayurveda knowledge, manufacturing", "category": "healthcare"},
        {"name": "Pharmacy", "cost": "₹5-12 L", "revenue": "₹1.2-3 L/month", "timeline": "3-5 months", "skills": "Pharmaceutical knowledge, licensing", "category": "healthcare"},
        
        # Automobile
        {"name": "Bike/Car Service Center", "cost": "₹8-20 L", "revenue": "₹1.5-4 L/month", "timeline": "4-6 months", "skills": "Automobile repair, management", "category": "automobile"},
        {"name": "Spare Parts Shop", "cost": "₹5-12 L", "revenue": "₹1-2.5 L/month", "timeline": "3-5 months", "skills": "Auto parts knowledge, retail", "category": "automobile"},
        {"name": "EV Charging Station", "cost": "₹10-25 L", "revenue": "₹80K-2 L/month", "timeline": "6-10 months", "skills": "Electrical, EV technology", "category": "automobile"},
        {"name": "Car Wash & Detailing", "cost": "₹3-8 L", "revenue": "₹80K-2 L/month", "timeline": "2-4 months", "skills": "Car care, customer service", "category": "automobile"},
        
        # Beauty & Lifestyle
        {"name": "Unisex Salon", "cost": "₹4-10 L", "revenue": "₹1-2.5 L/month", "timeline": "3-5 months", "skills": "Hair styling, beauty services", "category": "beauty"},
        {"name": "Spa & Wellness Center", "cost": "₹8-20 L", "revenue": "₹1.5-4 L/month", "timeline": "4-6 months", "skills": "Spa treatments, management", "category": "beauty"},
        {"name": "Fashion Boutique", "cost": "₹5-12 L", "revenue": "₹1-2.5 L/month", "timeline": "3-5 months", "skills": "Fashion, retail", "category": "beauty"},
        
        # Agriculture (general)
        {"name": "Organic Farming", "cost": "₹2.5-6.5 L", "revenue": "₹80K-2 L/month", "timeline": "6-12 months", "skills": "Farming, organic certification", "category": "agriculture"},
        {"name": "Dairy Farm", "cost": "₹4-12 L", "revenue": "₹1.2-3 L/month", "timeline": "4-8 months", "skills": "Animal husbandry", "category": "agriculture"},
        {"name": "Mushroom Cultivation", "cost": "₹1.5-4 L", "revenue": "₹60K-1.5 L/month", "timeline": "2-4 months", "skills": "Mushroom farming", "category": "agriculture"},
        {"name": "Poultry Farming", "cost": "₹4-10 L", "revenue": "₹1-2.5 L/month", "timeline": "3-6 months", "skills": "Poultry management", "category": "agriculture"},
        
        # Manufacturing
        {"name": "Handicraft Production", "cost": "₹2-6 L", "revenue": "₹60K-1.5 L/month", "timeline": "3-6 months", "skills": "Craftsmanship, design", "category": "manufacturing"},
        {"name": "Furniture Manufacturing", "cost": "₹6-15 L", "revenue": "₹1.2-3 L/month", "timeline": "4-6 months", "skills": "Carpentry, design", "category": "manufacturing"},
        {"name": "Small-Scale Machining", "cost": "₹10-25 L", "revenue": "₹2-5 L/month", "timeline": "6-10 months", "skills": "Machining, technical knowledge", "category": "manufacturing"}
    ]

# API endpoint function for easy integration
def get_karnataka_ideas_api(location=None, category=None, count=5):
    """
    API-friendly function to get Karnataka business ideas
    Can be called from app.py endpoints
    """
    if location:
        # Try to find district
        district = find_closest_district(location)
        if district:
            return get_karnataka_district_ideas(district, category, count)
    
    # If no specific district, return general ideas
    ideas = get_general_ideas("Karnataka")
    if category:
        ideas = [i for i in ideas if i.get('category') == category]
    
    random.shuffle(ideas)
    return ideas[:count]

# List all districts function
def list_all_karnataka_districts():
    """Return all 31 Karnataka districts with info"""
    return [
        {
            "district": district,
            "description": DISTRICT_DATA[district]["description"],
            "key_resources": DISTRICT_DATA[district]["key_resources"],
            "tourism": DISTRICT_DATA[district]["tourism"]
        }
        for district in KARNATAKA_DISTRICTS
    ]
