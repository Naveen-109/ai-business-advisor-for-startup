"""
Karnataka Districts Business Ideas Database
Complete data for all 31 districts with tailored business opportunities
"""

# All 31 Karnataka Districts
KARNATAKA_DISTRICTS = [
    "Bagalkote", "Ballari", "Belagavi", "Bengaluru Urban", "Bengaluru Rural",
    "Bidar", "Vijayapura", "Chamarajanagar", "Chikkaballapur", "Chikkamagaluru",
    "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag",
    "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar",
    "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara",
    "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Yadgir", "Vijayanagara"
]

# Business Categories
BUSINESS_CATEGORIES = {
    "agriculture": "Agriculture & Farming",
    "food": "Food & Beverages",
    "tourism": "Tourism & Hospitality",
    "retail": "Retail & Wholesale",
    "technology": "Technology & Digital",
    "manufacturing": "Manufacturing & Industry",
    "healthcare": "Healthcare & Wellness",
    "education": "Education & Training",
    "automobile": "Automobile Services",
    "beauty": "Beauty & Lifestyle"
}

# District-specific data with local resources, culture, and opportunities
DISTRICT_DATA = {
    "Bagalkote": {
        "description": "Known for red soil, temples, and agriculture",
        "key_resources": ["Red soil", "Limestone", "Temples", "Agriculture"],
        "culture": "Rich in historical temples and traditional crafts",
        "tourism": "Badami caves, Aihole, Pattadakal (UNESCO sites)",
        "opportunities": ["Stone carving", "Temple tourism", "Agriculture processing"]
    },
    "Ballari": {
        "description": "Mining hub with iron ore and historical sites",
        "key_resources": ["Iron ore", "Mining", "Agriculture", "Historical forts"],
        "culture": "Vijayanagara heritage, traditional mining community",
        "tourism": "Hampi (UNESCO), historical monuments",
        "opportunities": ["Mining equipment", "Heritage tourism", "Steel fabrication"]
    },
    "Belagavi": {
        "description": "Border district with diverse agriculture and military presence",
        "key_resources": ["Sugarcane", "Military cantonment", "Education hubs"],
        "culture": "Marathi-Kannada blend, traditional music",
        "tourism": "Gokak Falls, military heritage, hill stations",
        "opportunities": ["Sugar processing", "Defense supplies", "Education services"]
    },
    "Bengaluru Urban": {
        "description": "IT capital of India, startup hub, cosmopolitan city",
        "key_resources": ["IT industry", "Startups", "Education", "Research"],
        "culture": "Modern cosmopolitan with traditional roots",
        "tourism": "Tech parks, palaces, gardens, nightlife",
        "opportunities": ["Tech startups", "Co-working spaces", "Cloud kitchens", "EdTech"]
    },
    "Bengaluru Rural": {
        "description": "Agricultural belt around Bengaluru with growing urbanization",
        "key_resources": ["Sericulture", "Horticulture", "Dairy", "Proximity to Bengaluru"],
        "culture": "Traditional farming communities",
        "tourism": "Nandi Hills, temples, weekend getaways",
        "opportunities": ["Organic farming", "Farm stays", "Dairy products", "Logistics"]
    },
    "Bidar": {
        "description": "Historical city with Bahmani architecture and agriculture",
        "key_resources": ["Bidriware craft", "Agriculture", "Historical monuments"],
        "culture": "Bidriware metal craft, Sufi heritage",
        "tourism": "Bidar Fort, Bahmani tombs, religious sites",
        "opportunities": ["Bidriware export", "Heritage tourism", "Handicraft training"]
    },
    "Vijayapura": {
        "description": "Historical capital with Adil Shahi architecture",
        "key_resources": ["Agriculture", "Historical monuments", "Textiles"],
        "culture": "Adil Shahi heritage, traditional weaving",
        "tourism": "Gol Gumbaz, Ibrahim Rauza, monuments",
        "opportunities": ["Heritage tourism", "Textile manufacturing", "Agro-processing"]
    },
    "Chamarajanagar": {
        "description": "Forest-rich district with wildlife and silk production",
        "key_resources": ["Forests", "Wildlife", "Sericulture", "Sandalwood"],
        "culture": "Tribal communities, forest-based livelihoods",
        "tourism": "Bandipur National Park, BR Hills, wildlife safaris",
        "opportunities": ["Eco-tourism", "Silk production", "Forest products", "Wildlife tourism"]
    },
    "Chikkaballapur": {
        "description": "Granite hub with hills and growing industries",
        "key_resources": ["Granite", "Sericulture", "Horticulture", "Hills"],
        "culture": "Traditional silk weaving, granite industry",
        "tourism": "Nandi Hills, Bhoga Nandeeshwara Temple, trekking",
        "opportunities": ["Granite export", "Adventure tourism", "Silk products", "Logistics"]
    },
    "Chikkamagaluru": {
        "description": "Coffee land of Karnataka with scenic hills",
        "key_resources": ["Coffee", "Spices", "Tourism", "Iron ore"],
        "culture": "Coffee plantation heritage, hill station culture",
        "tourism": "Coffee estates, Mullayanagiri, Baba Budangiri, waterfalls",
        "opportunities": ["Coffee tourism", "Homestays", "Spice export", "Adventure sports"]
    },
    "Chitradurga": {
        "description": "Fort city with mining and agriculture",
        "key_resources": ["Iron ore", "Agriculture", "Historical fort"],
        "culture": "Warrior heritage, fort architecture",
        "tourism": "Chitradurga Fort, Vani Vilas Sagar Dam",
        "opportunities": ["Mining services", "Heritage tourism", "Agro-processing"]
    },
    "Dakshina Kannada": {
        "description": "Coastal district with education, healthcare, and cashew",
        "key_resources": ["Cashew", "Education", "Healthcare", "Ports", "Beaches"],
        "culture": "Tulu culture, coastal cuisine, Yakshagana",
        "tourism": "Beaches, temples, water sports, cuisine",
        "opportunities": ["Cashew processing", "Medical tourism", "Beach resorts", "Seafood export"]
    },
    "Davanagere": {
        "description": "Cotton hub and textile center",
        "key_resources": ["Cotton", "Textiles", "Education"],
        "culture": "Textile industry, traditional weaving",
        "tourism": "Temples, lakes, educational institutions",
        "opportunities": ["Textile manufacturing", "Cotton trading", "Garment export"]
    },
    "Dharwad": {
        "description": "Education and cultural hub with twin city Hubli",
        "key_resources": ["Education", "Culture", "Agriculture", "Industry"],
        "culture": "Classical music, literature, educational excellence",
        "tourism": "Universities, cultural centers, temples",
        "opportunities": ["Education services", "Cultural tourism", "Food processing"]
    },
    "Gadag": {
        "description": "Industrial town with textiles and agriculture",
        "key_resources": ["Textiles", "Agriculture", "Industry"],
        "culture": "Traditional weaving, temple architecture",
        "tourism": "Temples, historical sites",
        "opportunities": ["Textile manufacturing", "Agro-processing", "Industrial supplies"]
    },
    "Hassan": {
        "description": "Temple architecture and coffee with Hoysala heritage",
        "key_resources": ["Coffee", "Temples", "Agriculture", "Tourism"],
        "culture": "Hoysala architecture, traditional crafts",
        "tourism": "Belur, Halebidu, Shravanabelagola (Jain pilgrimage)",
        "opportunities": ["Heritage tourism", "Coffee estates", "Handicrafts", "Hospitality"]
    },
    "Haveri": {
        "description": "Agricultural district with handloom tradition",
        "key_resources": ["Agriculture", "Handloom", "Temples"],
        "culture": "Traditional weaving, temple culture",
        "tourism": "Temples, historical sites",
        "opportunities": ["Handloom products", "Agro-processing", "Rural tourism"]
    },
    "Kalaburagi": {
        "description": "Historical city with Bahmani heritage and pulses",
        "key_resources": ["Pulses", "Historical monuments", "Education"],
        "culture": "Bahmani architecture, Sufi heritage",
        "tourism": "Khwaja Banda Nawaz Dargah, Gulbarga Fort",
        "opportunities": ["Pulse processing", "Heritage tourism", "Religious tourism"]
    },
    "Kodagu": {
        "description": "Scotland of India - coffee, spices, and tourism",
        "key_resources": ["Coffee", "Spices", "Tourism", "Forests"],
        "culture": "Kodava culture, martial traditions, unique cuisine",
        "tourism": "Coffee estates, Abbey Falls, Talacauvery, wildlife",
        "opportunities": ["Coffee tourism", "Homestays", "Spice export", "Adventure tourism"]
    },
    "Kolar": {
        "description": "Gold mining heritage with sericulture and dairy",
        "key_resources": ["Gold mines (historical)", "Sericulture", "Dairy", "Horticulture"],
        "culture": "Mining heritage, silk tradition",
        "tourism": "Kolar Gold Fields, temples, historical sites",
        "opportunities": ["Silk products", "Dairy farming", "Heritage tourism", "Horticulture"]
    },
    "Koppal": {
        "description": "Historical district with agriculture and mining",
        "key_resources": ["Agriculture", "Iron ore", "Historical sites"],
        "culture": "Vijayanagara heritage, traditional farming",
        "tourism": "Hampi nearby, historical monuments",
        "opportunities": ["Agro-processing", "Mining services", "Heritage tourism"]
    },
    "Mandya": {
        "description": "Sugar bowl of Karnataka with extensive irrigation",
        "key_resources": ["Sugarcane", "Rice", "Irrigation", "KRS Dam"],
        "culture": "Agricultural prosperity, traditional farming",
        "tourism": "KRS Dam, Ranganathittu Bird Sanctuary, Srirangapatna",
        "opportunities": ["Sugar mills", "Rice processing", "Agro-tourism", "Dairy"]
    },
    "Mysuru": {
        "description": "Cultural capital with heritage, tourism, and silk",
        "key_resources": ["Tourism", "Silk", "Sandalwood", "Education", "IT"],
        "culture": "Royal heritage, Dasara festival, classical arts",
        "tourism": "Mysore Palace, Chamundi Hills, gardens, yoga",
        "opportunities": ["Heritage tourism", "Silk products", "Yoga centers", "Hospitality"]
    },
    "Raichur": {
        "description": "Agricultural district with thermal power and mining",
        "key_resources": ["Agriculture", "Thermal power", "Limestone", "Cotton"],
        "culture": "Traditional farming, historical forts",
        "tourism": "Raichur Fort, dams, historical sites",
        "opportunities": ["Agro-processing", "Power sector services", "Mining equipment"]
    },
    "Ramanagara": {
        "description": "Silk cocoon market and film shooting location",
        "key_resources": ["Sericulture", "Granite", "Film locations", "Hills"],
        "culture": "Silk production, film industry connections",
        "tourism": "Ramadevara Betta (Sholay hills), rock climbing, silk farms",
        "opportunities": ["Silk production", "Adventure tourism", "Film tourism", "Granite"]
    },
    "Shivamogga": {
        "description": "Gateway to Malnad with forests, waterfalls, and areca nut",
        "key_resources": ["Areca nut", "Forests", "Iron ore", "Waterfalls"],
        "culture": "Malnad culture, forest-based livelihoods",
        "tourism": "Jog Falls, Sharavathi Valley, Agumbe, Sakrebailu",
        "opportunities": ["Areca nut processing", "Eco-tourism", "Adventure sports", "Spices"]
    },
    "Tumakuru": {
        "description": "Coconut city with education and proximity to Bengaluru",
        "key_resources": ["Coconut", "Education", "Sericulture", "Industry"],
        "culture": "Agricultural traditions, educational institutions",
        "tourism": "Devarayanadurga, Siddaganga Mutt, temples",
        "opportunities": ["Coconut products", "Education services", "Logistics", "Manufacturing"]
    },
    "Udupi": {
        "description": "Temple town with cuisine, education, and beaches",
        "key_resources": ["Temples", "Education", "Beaches", "Fisheries", "Banking"],
        "culture": "Krishna temple, Udupi cuisine, banking heritage",
        "tourism": "Krishna Temple, Malpe Beach, St. Mary's Island, water sports",
        "opportunities": ["Hospitality", "Udupi restaurants", "Beach resorts", "Seafood"]
    },
    "Uttara Kannada": {
        "description": "Coastal district with forests, beaches, and spices",
        "key_resources": ["Forests", "Beaches", "Spices", "Fisheries", "Tourism"],
        "culture": "Coastal culture, forest communities, traditional fishing",
        "tourism": "Karwar beaches, Dandeli wildlife, river rafting, Gokarna",
        "opportunities": ["Eco-tourism", "Adventure sports", "Spice export", "Beach resorts"]
    },
    "Yadgir": {
        "description": "Agricultural district with historical sites",
        "key_resources": ["Agriculture", "Limestone", "Historical monuments"],
        "culture": "Traditional farming, historical heritage",
        "tourism": "Yadgir Fort, Sharana Basaveshwara Temple",
        "opportunities": ["Agro-processing", "Limestone products", "Rural development"]
    },
    "Vijayanagara": {
        "description": "New district carved from Ballari with Hampi heritage",
        "key_resources": ["Historical monuments", "Agriculture", "Tourism"],
        "culture": "Vijayanagara Empire heritage, temple architecture",
        "tourism": "Hampi (UNESCO World Heritage Site)",
        "opportunities": ["Heritage tourism", "Hospitality", "Handicrafts", "Agro-processing"]
    }
}
