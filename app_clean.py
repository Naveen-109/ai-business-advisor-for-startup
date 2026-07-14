#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI/ML Business Advisor - Clean & Optimized
Main Flask application with ML models and Ollama LLM integration
"""
import sys
import io
# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
import os
import json
import re

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret-change-in-production')

# Global variables
scaler = None
feature_cols = None
models = {}
best_model_name = None
llm_enabled = False  # Disabled by user - can be re-enabled later
USERS_FILE = os.path.join('data', 'users.json')

# Admin configuration
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')  # Change this in production!

# Karnataka Districts Integration
try:
    from karnataka_integration import (
        get_karnataka_district_ideas,
        find_closest_district,
        KARNATAKA_DISTRICTS
    )
    from karnataka_districts_data import DISTRICT_DATA
    KARNATAKA_ENABLED = True
    print("✓ Karnataka Districts Integration loaded")
except ImportError as e:
    KARNATAKA_ENABLED = False
    print(f"⚠ Karnataka integration not available: {e}")

# ============================================================================
# USER MANAGEMENT
# ============================================================================

def load_users():
    """Load users from JSON file"""
    try:
        if not os.path.exists('data'):
            os.makedirs('data')
        if not os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'w') as f:
                json.dump({}, f)
            return {}
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users):
    """Save users to JSON file"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception:
        return False

def create_user(username, password, email=None):
    """Create a new user"""
    users = load_users()
    if username in users:
        return False, 'Username already exists'
    users[username] = {
        'password': generate_password_hash(password),
        'email': email or '',
        'created_at': datetime.utcnow().isoformat(),
        'chats': []
    }
    ok = save_users(users)
    return ok, None if ok else 'Unable to save user'

def verify_user(username, password):
    """Verify user credentials"""
    users = load_users()
    u = users.get(username)
    if not u:
        return False
    return check_password_hash(u.get('password', ''), password)

def verify_admin(username, password):
    """Verify admin credentials"""
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def is_admin():
    """Check if current session is admin"""
    return session.get('is_admin', False)

# ============================================================================
# ML MODEL MANAGEMENT
# ============================================================================

def load_models():
    """Load all trained ML models"""
    global scaler, feature_cols, models, best_model_name
    
    try:
        scaler = joblib.load('models/scaler.pkl')
        feature_cols = joblib.load('models/feature_cols.pkl')
        
        with open('models/best_model.txt', 'r') as f:
            best_model_name = f.read().strip()
        
        models['Linear Regression'] = joblib.load('models/linear_regression.pkl')
        models['Random Forest'] = joblib.load('models/random_forest.pkl')
        
        try:
            from tensorflow import keras
            models['LSTM'] = keras.models.load_model('models/lstm_model.h5')
        except:
            print("Warning: LSTM model not loaded")
        
        print(f"Models loaded successfully. Best model: {best_model_name}")
        return True
    except Exception as e:
        print(f"Error loading models: {str(e)}")
        return False

def check_ollama():
    """Check if Ollama LLM is available"""
    global llm_enabled
    try:
        import requests
        print("Checking Ollama availability...", flush=True)
        
        # Try v1 API first
        try:
            r = requests.get('http://localhost:11434/v1/models', timeout=5)
            if r.status_code == 200:
                data = r.json()
                if 'data' in data and len(data['data']) > 0:
                    llm_enabled = True
                    print(f"✓ Ollama is available. LLM support enabled.", flush=True)
                    print(f"✓ Available models: {[m.get('id', 'unknown') for m in data['data']]}", flush=True)
                    return True
        except Exception as e:
            print(f"v1 API check failed: {e}", flush=True)
        
        # Try legacy API
        try:
            r = requests.get('http://localhost:11434/api/tags', timeout=5)
            if r.status_code == 200:
                data = r.json()
                if 'models' in data and len(data['models']) > 0:
                    llm_enabled = True
                    print(f"✓ Ollama is available. LLM support enabled.", flush=True)
                    print(f"✓ Available models: {[m['name'] for m in data['models']]}", flush=True)
                    return True
        except Exception as e:
            print(f"Legacy API check failed: {e}", flush=True)
        
        llm_enabled = False
        print("⚠ Ollama not available. Using rule-based responses.", flush=True)
        return False
    except Exception as e:
        print(f"Ollama check failed: {str(e)}", flush=True)
        llm_enabled = False
        return False

def refresh_llm_status():
    """Force refresh LLM status"""
    global llm_enabled
    print("Refreshing LLM status...", flush=True)
    result = check_ollama()
    print(f"LLM status after refresh: {llm_enabled}", flush=True)
    return result

# ============================================================================
# BUSINESS DATA EXTRACTION
# ============================================================================

def extract_business_data(message):
    """Extract business metrics from user message using regex"""
    data = {}
    message_lower = message.lower()
    
    # Extract sales
    sales_patterns = [
        r'sales[:\s]+[\$]?([\d,]+)',
        r'revenue[:\s]+[\$]?([\d,]+)',
        r'i\s+(?:have|make|earn|get)\s+[\$]?([\d,]+)\s+(?:in\s+)?sales',
    ]
    for pattern in sales_patterns:
        match = re.search(pattern, message_lower)
        if match:
            data['sales'] = float(match.group(1).replace(',', ''))
            break
    
    # Extract expenses
    expense_patterns = [
        r'expenses?[:\s]+[\$]?([\d,]+)',
        r'costs?[:\s]+[\$]?([\d,]+)',
    ]
    for pattern in expense_patterns:
        match = re.search(pattern, message_lower)
        if match:
            data['expenses'] = float(match.group(1).replace(',', ''))
            break
    
    # Extract marketing spend
    marketing_patterns = [r'marketing[:\s]+[\$]?([\d,]+)']
    for pattern in marketing_patterns:
        match = re.search(pattern, message_lower)
        if match:
            data['marketing_spend'] = float(match.group(1).replace(',', ''))
            break
    
    # Extract employee count
    employee_patterns = [r'(\d+)\s+employees?', r'employee[:\s]+(\d+)']
    for pattern in employee_patterns:
        match = re.search(pattern, message_lower)
        if match:
            data['employee_count'] = float(match.group(1))
            break
    
    # Extract competition level
    competition_patterns = [r'competition[:\s]+(\d+)']
    for pattern in competition_patterns:
        match = re.search(pattern, message_lower)
        if match:
            data['competition_level'] = float(match.group(1))
            break
    
    return data

def prepare_input_features(data):
    """Prepare input features for ML prediction"""
    now = datetime.now()
    
    features = {
        'sales': float(data.get('sales', 10000)),
        'expenses': float(data.get('expenses', 7000)),
        'marketing_spend': float(data.get('marketing_spend', 1000)),
        'employee_count': float(data.get('employee_count', 20)),
        'seasonality': float(data.get('seasonality', 0)),
        'competition_level': float(data.get('competition_level', 3)),
        'year': now.year,
        'month': now.month,
        'day_of_year': now.timetuple().tm_yday,
        'day_of_week': now.weekday()
    }
    
    feature_array = np.array([[features[col] for col in feature_cols]])
    feature_array_scaled = scaler.transform(feature_array)
    
    return feature_array_scaled, features

def make_prediction(business_data, model_type=None):
    """Make ML prediction using trained models"""
    if not scaler or not feature_cols or not models:
        return None
    
    try:
        features_scaled, features_dict = prepare_input_features(business_data)
        
        if model_type is None or model_type not in models:
            model_type = best_model_name if best_model_name in models else list(models.keys())[0]
        
        model = models[model_type]
        
        if model_type == 'LSTM':
            lookback = 30
            sequence = np.repeat(features_scaled, lookback, axis=0).reshape(1, lookback, -1)
            prediction = model.predict(sequence, verbose=0)[0][0]
        else:
            prediction = model.predict(features_scaled)[0]
        
        # Get predictions from all models
        all_predictions = {}
        for model_name, model_obj in models.items():
            try:
                if model_name == 'LSTM':
                    lookback = 30
                    sequence = np.repeat(features_scaled, lookback, axis=0).reshape(1, lookback, -1)
                    pred = model_obj.predict(sequence, verbose=0)[0][0]
                else:
                    pred = model_obj.predict(features_scaled)[0]
                all_predictions[model_name] = float(pred)
            except:
                pass
        
        return {
            'prediction': float(prediction),
            'model_used': model_type,
            'all_predictions': all_predictions,
            'features': features_dict
        }
    except Exception as e:
        print(f"Error making prediction: {e}")
        return None

# ============================================================================
# OLLAMA LLM INTEGRATION
# ============================================================================

def get_ollama_models():
    """Get list of available Ollama models"""
    try:
        import requests
        try:
            response = requests.get('http://localhost:11434/v1/models', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'data' in data:
                    return [m.get('id') for m in data.get('data', []) if 'id' in m]
        except:
            pass
        
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'models' in data:
                    return [model['name'].split(':')[0] for model in data['models']]
        except:
            pass
    except:
        pass
    return []

def get_llm_response(user_message, context=None):
    """Get response from Ollama LLM"""
    global llm_enabled
    
    # Double-check LLM status
    if not llm_enabled:
        print("[DEBUG] LLM disabled, attempting to refresh status...", flush=True)
        refresh_llm_status()
        if not llm_enabled:
            print("[DEBUG] LLM still disabled after refresh, returning None", flush=True)
            return None
    
    print(f"[DEBUG] Attempting LLM response for message: {user_message[:50]}...", flush=True)
    
    try:
        import requests
        
        system_prompt = """You are an expert AI Business Advisor for startups. You provide:
- Strategic profit optimization and growth strategies
- Data-driven sales and revenue improvement tactics
- Cost reduction and efficiency optimization advice
- Marketing strategies and ROI optimization
- Market analysis and competitive positioning

Guidelines:
1. Be specific and actionable with data-driven recommendations
2. Use ML predictions to validate and support your advice
3. Provide 3-5 key recommendations per response
4. Keep responses professional but approachable"""
        
        user_prompt = user_message
        if context:
            user_prompt += f"\n\nData Context:\n{context}"
        
        available_models = get_ollama_models()
        models_to_try = available_models if available_models else ['llama3.2', 'llama3', 'mistral']
        
        print(f"[DEBUG] Trying models: {models_to_try}", flush=True)
        
        for model_name in models_to_try:
            try:
                print(f"[DEBUG] Trying model: {model_name}", flush=True)
                # Try new API
                api_response = requests.post(
                    'http://localhost:11434/v1/chat/completions',
                    json={
                        'model': model_name,
                        'messages': [
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': user_prompt}
                        ],
                        'temperature': 0.7,
                        'max_tokens': 500
                    },
                    timeout=30
                )
                
                if api_response.status_code == 200:
                    data = api_response.json()
                    if 'choices' in data and len(data['choices']) > 0:
                        response_text = data['choices'][0]['message']['content']
                        print(f"[DEBUG] LLM response received (length: {len(response_text)})", flush=True)
                        return response_text
            except Exception as e:
                print(f"[DEBUG] v1 API failed for {model_name}: {e}", flush=True)
            
            try:
                # Try legacy API
                api_response = requests.post(
                    'http://localhost:11434/api/chat',
                    json={
                        'model': model_name,
                        'messages': [
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': user_prompt}
                        ],
                        'stream': False
                    },
                    timeout=30
                )
                
                if api_response.status_code == 200:
                    data = api_response.json()
                    if 'message' in data and 'content' in data['message']:
                        response_text = data['message']['content']
                        print(f"[DEBUG] LLM response received (length: {len(response_text)})", flush=True)
                        return response_text
            except Exception as e:
                print(f"[DEBUG] Legacy API failed for {model_name}: {e}", flush=True)
                continue
        
        print("[DEBUG] All LLM attempts failed", flush=True)
        return None
    except Exception as e:
        print(f"[DEBUG] Error getting LLM response: {e}", flush=True)
        return None

# ============================================================================
# KARNATAKA DISTRICTS HANDLER
# ============================================================================

def handle_karnataka_district_query(message):
    """Detect and handle Karnataka district-specific queries"""
    if not KARNATAKA_ENABLED:
        return None
    
    message_lower = message.lower()
    is_karnataka_query = 'karnataka' in message_lower
    mentioned_district = None
    
    # Check for district mentions
    for district in KARNATAKA_DISTRICTS:
        if district.lower() in message_lower:
            mentioned_district = district
            is_karnataka_query = True
            break
    
    # Check common city names
    city_to_district = {
        'bangalore': 'Bengaluru Urban', 'bengaluru': 'Bengaluru Urban',
        'mysore': 'Mysuru', 'mysuru': 'Mysuru',
        'mangalore': 'Dakshina Kannada', 'hubli': 'Dharwad',
        'belgaum': 'Belagavi', 'coorg': 'Kodagu', 'hampi': 'Vijayanagara'
    }
    
    for city, district in city_to_district.items():
        if city in message_lower:
            mentioned_district = district
            is_karnataka_query = True
            break
    
    if not is_karnataka_query:
        return None
    
    # Determine category
    category = None
    if 'agriculture' in message_lower or 'farming' in message_lower:
        category = 'agriculture'
    elif 'food' in message_lower or 'restaurant' in message_lower:
        category = 'food'
    elif 'tourism' in message_lower or 'hotel' in message_lower:
        category = 'tourism'
    elif 'tech' in message_lower or 'software' in message_lower:
        category = 'technology'
    
    # Get ideas
    if mentioned_district:
        ideas = get_karnataka_district_ideas(mentioned_district, category, 5)
        district_name = mentioned_district
    else:
        ideas = get_karnataka_district_ideas('Bengaluru Urban', category, 5)
        district_name = "Karnataka"
    
    if not ideas:
        return None
    
    # Format response
    response = f"\n\n🏛️ **BUSINESS IDEAS FOR {district_name.upper()}**\n\n"
    
    if mentioned_district and mentioned_district in DISTRICT_DATA:
        info = DISTRICT_DATA[mentioned_district]
        response += f"📍 **About {mentioned_district}:**\n{info['description']}\n\n"
        response += f"**Key Resources:** {', '.join(info['key_resources'][:4])}\n"
        if info.get('tourism'):
            response += f"**Tourism:** {info['tourism'][:100]}...\n"
        response += "\n"
    
    response += f"Here are {len(ideas)} tailored business opportunities:\n\n"
    
    for idx, idea in enumerate(ideas, 1):
        response += f"**{idx}. {idea['name']}**\n"
        if 'location_benefit' in idea:
            response += f"   📍 {idea['location_benefit']}\n"
        response += f"   💰 Startup Cost: {idea['cost']}\n"
        response += f"   ⏱️ Timeline: {idea['timeline']}\n"
        response += f"   💵 Revenue Potential: {idea['revenue']}\n"
        response += f"   🎯 Skills Needed: {idea['skills']}\n\n"
    
    response += "---\n\n💡 **NEXT STEPS:**\n"
    response += "• Research local demand and competition\n"
    response += "• Connect with local entrepreneurs\n"
    response += "• Visit district industries center\n"
    response += "• Apply for government schemes (MSME, Startup Karnataka)\n\n"
    
    return response

# ============================================================================
# BUSINESS ADVICE GENERATION
# ============================================================================

def generate_business_advice(message, conversation_history=None):
    """Generate intelligent business advice using LLM and ML models"""
    import sys
    message_lower = message.lower()
    
    # Check for Karnataka district queries FIRST
    with open('debug.log', 'a', encoding='utf-8') as f:
        f.write(f"[DEBUG] Checking Karnataka for message: {message[:50]}...\n")
        f.write(f"[DEBUG] llm_enabled at start: {llm_enabled}\n")
        f.flush()
    
    karnataka_response = handle_karnataka_district_query(message)
    
    with open('debug.log', 'a', encoding='utf-8') as f:
        if karnataka_response:
            f.write(f"[DEBUG] Karnataka handler returned response (length: {len(karnataka_response)})\n")
            f.flush()
        else:
            f.write("[DEBUG] Karnataka handler returned None, continuing to LLM...\n")
            f.write(f"[DEBUG] llm_enabled before LLM call: {llm_enabled}\n")
            f.flush()
    
    if karnataka_response:
        return karnataka_response
    
    # Check if user wants prediction
    wants_prediction = any(keyword in message_lower for keyword in [
        'predict', 'forecast', 'projection', 'estimate', 'profit', 'revenue'
    ])
    
    # Extract business data
    business_data = extract_business_data(message)
    has_data = len(business_data) > 0
    
    # Make prediction if relevant
    prediction_info = None
    if wants_prediction or has_data:
        prediction_data = {
            'sales': business_data.get('sales', 15000),
            'expenses': business_data.get('expenses', 8000),
            'marketing_spend': business_data.get('marketing_spend', 1500),
            'employee_count': business_data.get('employee_count', 20),
            'competition_level': business_data.get('competition_level', 3)
        }
        prediction_info = make_prediction(prediction_data)
    
    # Build context for LLM
    context_parts = []
    if prediction_info:
        context_parts.append(f"=== ML PREDICTION ===")
        context_parts.append(f"Predicted Profit: ${prediction_info['prediction']:.2f}")
        context_parts.append(f"Model: {prediction_info['model_used']}")
        context_parts.append(f"All Predictions: {', '.join([f'{k}: ${v:.2f}' for k, v in prediction_info['all_predictions'].items()])}")
    
    context = "\n".join(context_parts) if context_parts else None
    
    # Get LLM response
    llm_response = get_llm_response(message, context)
    
    if llm_response:
        response = llm_response
        if prediction_info and "prediction" not in response.lower():
            response += f"\n\n📊 **ML Prediction:** ${prediction_info['prediction']:.2f}"
    else:
        # Fallback to rule-based
        response = generate_rule_based_response(message, prediction_info, business_data)
    
    return response

def generate_rule_based_response(message, prediction_info=None, business_data=None):
    """Generate rule-based response when LLM is not available"""
    message_lower = message.lower()
    response_parts = []
    
    # Add prediction if available
    if prediction_info:
        response_parts.append(f"📊 **Profit Prediction:** ${prediction_info['prediction']:.2f}")
        response_parts.append(f"**Model:** {prediction_info['model_used']}")
        response_parts.append("")
    
    # Provide advice based on keywords
    if 'profit' in message_lower or 'predict' in message_lower:
        response_parts.append("💡 **Profit Optimization Strategies:**")
        response_parts.append("1. **Revenue Growth** - Increase sales through marketing and expansion")
        response_parts.append("2. **Cost Reduction** - Optimize operations and eliminate waste")
        response_parts.append("3. **Efficiency** - Automate tasks and improve productivity")
        response_parts.append("4. **Pricing Strategy** - Optimize pricing model")
        response_parts.append("")
    
    if 'sales' in message_lower or 'revenue' in message_lower:
        response_parts.append("📈 **Sales Growth Strategies:**")
        response_parts.append("1. **Digital Marketing** - SEO, SEM, social media")
        response_parts.append("2. **Customer Retention** - Loyalty programs, excellent service")
        response_parts.append("3. **Market Expansion** - New markets, new segments")
        response_parts.append("4. **Product Innovation** - New offerings, bundling")
        response_parts.append("")
    
    if 'cost' in message_lower or 'expense' in message_lower:
        response_parts.append("💸 **Cost Reduction Strategies:**")
        response_parts.append("1. **Supplier Optimization** - Negotiate better rates")
        response_parts.append("2. **Operational Efficiency** - Lean processes, automation")
        response_parts.append("3. **Technology** - Cloud services, automation tools")
        response_parts.append("")
    
    if not response_parts:
        response_parts.append("🤖 **I'm your AI Business Advisor!**")
        response_parts.append("I can help with:")
        response_parts.append("• Profit predictions using ML models")
        response_parts.append("• Business ideas for Karnataka districts")
        response_parts.append("• Strategic advice for growth")
        response_parts.append("• Marketing and sales strategies")
    
    return "\n".join(response_parts)

# ============================================================================
# API ENDPOINTS
# ============================================================================
# ADMIN ROUTES
# ============================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if verify_admin(username, password):
            session['is_admin'] = True
            session['admin_username'] = username
            flash('Admin login successful')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard - view all users and chat history"""
    if not is_admin():
        flash('Admin access required')
        return redirect(url_for('admin_login'))
    
    users = load_users()
    
    # Calculate statistics
    total_users = len(users)
    total_chats = sum(len(user.get('chats', [])) for user in users.values())
    
    # Get recent activity (last 10 chats across all users)
    all_chats = []
    for username, user_data in users.items():
        for chat in user_data.get('chats', []):
            all_chats.append({
                'username': username,
                'message': chat.get('message', ''),
                'response': chat.get('response', ''),
                'timestamp': chat.get('timestamp', ''),
                'created_at': user_data.get('created_at', '')
            })
    
    # Sort by timestamp (most recent first)
    all_chats.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    recent_chats = all_chats[:10]
    
    return render_template('admin_dashboard.html', 
                         users=users, 
                         total_users=total_users,
                         total_chats=total_chats,
                         recent_chats=recent_chats)

@app.route('/admin/user/<username>')
def admin_user_detail(username):
    """View detailed chat history for a specific user"""
    if not is_admin():
        flash('Admin access required')
        return redirect(url_for('admin_login'))
    
    users = load_users()
    user = users.get(username)
    
    if not user:
        flash('User not found')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_user_detail.html', username=username, user=user)

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('is_admin', None)
    session.pop('admin_username', None)
    flash('Admin logged out')
    return redirect(url_for('admin_login'))

# ============================================================================
# USER ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    # Refresh LLM status to ensure accuracy
    refresh_llm_status()
    
    return jsonify({
        'status': 'healthy',
        'models_loaded': len(models) > 0,
        'llm_enabled': llm_enabled,
        'best_model': best_model_name,
        'available_models': list(models.keys())
    })

@app.route('/models', methods=['GET'])
def list_models():
    """List available models"""
    return jsonify({
        'models': list(models.keys()),
        'best_model': best_model_name
    })

@app.route('/enable-llm', methods=['POST'])
def enable_llm():
    """Force enable LLM"""
    global llm_enabled
    print("Force enabling LLM via API...", flush=True)
    result = refresh_llm_status()
    return jsonify({
        'llm_check_result': result,
        'llm_enabled': llm_enabled,
        'message': 'LLM enabled successfully' if llm_enabled else 'LLM failed to enable'
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Main chatbot endpoint"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        history = data.get('history', [])
        
        print(f"[CHAT ENDPOINT] Received message: {message[:50]}...", flush=True)
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        print("[CHAT ENDPOINT] Calling generate_business_advice...", flush=True)
        response = generate_business_advice(message, history)
        print(f"[CHAT ENDPOINT] Got response (length: {len(response)})", flush=True)
        
        return jsonify({
            'response': response,
            'user_message': message,
            'llm_enabled': llm_enabled,
            'backend': 'app_clean.py',
            'version': '2.0'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    """ML prediction endpoint"""
    try:
        data = request.get_json()
        prediction_result = make_prediction(data)
        
        if prediction_result:
            return jsonify(prediction_result)
        else:
            return jsonify({'error': 'Prediction failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# USER AUTHENTICATION
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if verify_user(username, password):
            session['username'] = username
            flash('Login successful')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        email = request.form.get('email', '').strip()
        
        ok, error = create_user(username, password, email)
        if ok:
            flash('Registration successful')
            return redirect(url_for('login'))
        else:
            flash(error or 'Registration failed')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.pop('username', None)
    flash('Logged out')
    return redirect(url_for('index'))

# ============================================================================
# INITIALIZATION & STARTUP
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60, flush=True)
    print("AI/ML Business Advisor - Starting...", flush=True)
    print("="*60 + "\n", flush=True)
    
    # Load ML models
    if not load_models():
        print("Warning: Models not loaded. Run train_models.py first.", flush=True)
    
    # Check Ollama
    check_ollama()
    
    print("\nStarting Flask server...", flush=True)
    print(f"Available ML models: {list(models.keys())}", flush=True)
    print(f"LLM enabled: {llm_enabled}", flush=True)
    print("\n" + "="*60, flush=True)
    
    app.run(debug=False, host='0.0.0.0', port=5000)
