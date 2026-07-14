"""
Flask Backend API - AI Business Advisor Chatbot
Integrates ML models with local LLM for intelligent business advice
"""
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_cors import CORS
import sys
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
import os
import json
import re

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret-change-me')

# Load models and scaler
scaler = None
feature_cols = None
models = {}
best_model_name = None
llm_enabled = False

# Simple user storage (file-based). For production use a real DB.
USERS_FILE = os.path.join('data', 'users.json')

def load_users():
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
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception:
        return False

from werkzeug.security import generate_password_hash, check_password_hash

def create_user(username, password, email=None):
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
    users = load_users()
    u = users.get(username)
    if not u:
        return False
    return check_password_hash(u.get('password', ''), password)

def load_models():
    """Load all trained models"""
    global scaler, feature_cols, models, best_model_name
    
    try:
        # Load scaler and feature columns
        scaler = joblib.load('models/scaler.pkl')
        feature_cols = joblib.load('models/feature_cols.pkl')
        
        # Load best model name
        with open('models/best_model.txt', 'r') as f:
            best_model_name = f.read().strip()
        
        # Load all models
        models['Linear Regression'] = joblib.load('models/linear_regression.pkl')
        models['Random Forest'] = joblib.load('models/random_forest.pkl')
        
        # Load LSTM model (if available)
        try:
            from tensorflow import keras  # type: ignore
            models['LSTM'] = keras.models.load_model('models/lstm_model.h5')
        except ImportError:
            print("Warning: TensorFlow not available. LSTM model will not be loaded.")
        except Exception as e:
            print(f"Warning: Could not load LSTM model: {str(e)}")
        
        print(f"Models loaded successfully. Best model: {best_model_name}")
        return True
    except Exception as e:
        print(f"Error loading models: {str(e)}")
        return False

def check_ollama():
    """Check if Ollama is available"""
    global llm_enabled
    try:
        import requests
        # Try known Ollama endpoints (/v1/models or legacy /api/tags)
        try:
            r = requests.get('http://localhost:11434/v1/models', timeout=2)
            if r.status_code == 200:
                llm_enabled = True
                print("Ollama is available via /v1/models. LLM support enabled.")
                return True
        except Exception:
            pass

        try:
            r = requests.get('http://localhost:11434/api/tags', timeout=2)
            if r.status_code == 200:
                llm_enabled = True
                print("Ollama is available via /api/tags. LLM support enabled.")
                return True
        except Exception:
            pass

        llm_enabled = False
        print("Ollama API not responding on expected endpoints. Rule-based responses will be used.")
        return False
    except Exception as e:
        print(f"Ollama not available: {str(e)}")
        print("  Install and start Ollama for AI-powered responses:")
        print("  1. Download from https://ollama.ai")
        print("  2. Run: ollama serve")
        print("  3. Run: ollama pull llama3.2 (or another model)")
        llm_enabled = False
        return False


# Currency conversion helpers (module-level so they are available everywhere)
def _get_usd_to_inr_rate(rate=None):
    try:
        if rate is not None:
            return float(rate)
        return float(os.environ.get('USD_TO_INR', '83'))
    except Exception:
        return 83.0


def _format_inr(value):
    if value is None:
        return '₹N/A'
    v = float(value)
    # Use Indian numbering: crores (1e7) and lakhs (1e5)
    if abs(v) >= 1e9:
        # For extremely large values, fall back to billions but also show crores optionally
        return f"₹{round(v/1e9,2)}B"
    if abs(v) >= 1e7:
        # Crores
        return f"₹{round(v/1e7,2)} Cr"
    if abs(v) >= 1e5:
        # Lakhs
        return f"₹{round(v/1e5,2)} L"
    if abs(v) >= 1e3:
        return f"₹{int(round(v)):,}"
    return f"₹{round(v,2)}"


def _convert_currency_string(s, rate=None):
    """Convert $ amounts and ranges (with optional K/M/B suffix) into INR string."""
    if not isinstance(s, str):
        return s
    if '₹' in s:
        return s
    rate = _get_usd_to_inr_rate(rate)

    def _parse_amount(num_str, suffix):
        mult = 1.0
        if suffix:
            sf = suffix.upper()
            if sf == 'K':
                mult = 1e3
            elif sf == 'M':
                mult = 1e6
            elif sf == 'B':
                mult = 1e9
        try:
            return float(num_str) * mult * rate
        except Exception:
            return None

    # ranges like $1.5M - $2M
    s = re.sub(r"\$(\d+(?:\.\d+)?)([KMBkmb]?)\s*-\s*\$(\d+(?:\.\d+)?)([KMBkmb]?)",
               lambda m: (_format_inr(_parse_amount(m.group(1), m.group(2))) + '-' + _format_inr(_parse_amount(m.group(3), m.group(4))) + ' (approx)')
               , s)

    # single amounts like $5000, $2.5M, $3000+, $4000/month
    s = re.sub(r"\$(\d+(?:\.\d+)?)([KMBkmb]?)(\+?)(/[^\s,]+)?",
               lambda m: (_format_inr(_parse_amount(m.group(1), m.group(2))) + (m.group(3) or '') + (m.group(4) or '') + ' (approx)')
               , s)
    return s


def _convert_usd_to_inr_in_list(idea_list, rate=None):
    if not isinstance(idea_list, list):
        return idea_list
    out = []
    for item in idea_list:
        if not isinstance(item, dict):
            out.append(item)
            continue
        new = item.copy()
        for key in ('startup_cost', 'revenue_potential'):
            val = new.get(key)
            if isinstance(val, str) and '$' in val and '₹' not in val:
                new[key] = _convert_currency_string(val, rate=rate)
        out.append(new)
    return out


def _convert_currency_in_dict(dct, rate=None):
    """Convert any $ occurrences in a dict's string fields (market entries, success stories)."""
    if not isinstance(dct, dict):
        return dct
    out = {}
    for k, v in dct.items():
        if isinstance(v, str) and '$' in v and '₹' not in v:
            out[k] = _convert_currency_string(v, rate=rate)
        else:
            out[k] = v
    return out

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
        r'spend(?:ing)?[:\s]+[\$]?([\d,]+)',
    ]
    for pattern in expense_patterns:
        match = re.search(pattern, message_lower)
        if match:
            data['expenses'] = float(match.group(1).replace(',', ''))
            break
    
    # Extract marketing spend
    marketing_patterns = [
        r'marketing[:\s]+[\$]?([\d,]+)',
        r'advertising[:\s]+[\$]?([\d,]+)',
    ]
    for pattern in marketing_patterns:
        match = re.search(pattern, message_lower)
        if match:
            data['marketing_spend'] = float(match.group(1).replace(',', ''))
            break
    
    # Extract employee count
    employee_patterns = [
        r'(\d+)\s+employees?',
        r'employee[:\s]+(\d+)',
        r'staff[:\s]+(\d+)',
    ]
    for pattern in employee_patterns:
        match = re.search(pattern, message_lower)
        if match:
            data['employee_count'] = float(match.group(1))
            break
    
    # Extract competition level
    competition_patterns = [
        r'competition[:\s]+(\d+)',
        r'competitive[:\s]+level[:\s]+(\d+)',
    ]
    for pattern in competition_patterns:
        match = re.search(pattern, message_lower)
        if match:
            data['competition_level'] = float(match.group(1))
            break
    
    return data

def prepare_input_features(data):
    """Prepare input features for prediction"""
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
    """Make ML prediction using all available models"""
    if not scaler or not feature_cols or not models:
        return None
    
    try:
        features_scaled, features_dict = prepare_input_features(business_data)
        
        # Use best model if no specific model requested
        if model_type is None or model_type not in models:
            model_type = best_model_name if best_model_name in models else list(models.keys())[0]
        
        model = models[model_type]
        
        # Make prediction
        if model_type == 'LSTM':
            lookback = 30
            sequence = np.repeat(features_scaled, lookback, axis=0).reshape(1, lookback, -1)
            prediction = model.predict(sequence, verbose=0)[0][0]
        else:
            prediction = model.predict(features_scaled)[0]
        
        # Get predictions from all models for comparison
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
            except Exception as e:
                print(f"Error getting prediction from {model_name}: {e}")
        
        return {
            'prediction': float(prediction),
            'model_used': model_type,
            'all_predictions': all_predictions,
            'features': features_dict
        }
    except Exception as e:
        print(f"Error making prediction: {e}")
        return None

def get_ollama_models():
    """Get list of available Ollama models"""
    try:
        import requests
        # Prefer /v1/models (newer API), fallback to /api/tags
        try:
            response = requests.get('http://localhost:11434/v1/models', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'data' in data:
                    return [m.get('id') for m in data.get('data', []) if 'id' in m]
        except Exception:
            pass

        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'models' in data:
                    return [model['name'].split(':')[0] for model in data['models']]
        except Exception:
            pass
    except:
        pass
    return []

def get_llm_response(user_message, context=None):
    """Get response from local LLM (Ollama)"""
    global llm_enabled
    if not llm_enabled:
        return None
    
    try:
        import requests
        
        # Build context for the LLM
        system_prompt = """You are an expert AI Business Advisor for startups. You provide:
- Strategic profit optimization and growth strategies
- Data-driven sales and revenue improvement tactics
- Cost reduction and efficiency optimization advice
- Data-driven marketing strategies and ROI optimization
- Market analysis and competitive positioning
- Scalability and growth roadmap guidance
- Risk assessment and mitigation strategies
- Financial management and cash flow optimization
- Team building and talent strategies

You have access to ML models that can predict business profit based on metrics like sales, expenses, marketing spend, employee count, and competition level.

Guidelines:
1. Be specific and actionable with data-driven recommendations
2. Use the ML predictions to validate and support your advice
3. Consider both short-term wins and long-term strategy
4. Address the user's specific context and constraints
5. Provide 3-5 key recommendations per response
6. Use formatting with bullet points and headers for clarity
7. Reference specific metrics when available
8. Keep responses professional but approachable"""
        
        user_prompt = user_message
        if context:
            context_str = f"\n\nData Context:\n{context}"
            user_prompt += context_str
        
        # Get available Ollama models
        available_models = get_ollama_models()

        # Models to try in priority order
        models_to_try = available_models if available_models else ['llama3.2', 'llama3', 'mistral', 'phi3', 'qwen2:3b', 'neural-chat']
        response = None
        used_model = None

        for model_name in models_to_try:
            try:
                # Try newer /v1/chat endpoint first
                try:
                    api_response = requests.post(
                        'http://localhost:11434/v1/chat',
                        json={
                            'model': model_name,
                            'messages': [
                                {'role': 'system', 'content': system_prompt},
                                {'role': 'user', 'content': user_prompt}
                            ],
                            'temperature': 0.7
                        },
                        timeout=60
                    )

                    if api_response.status_code == 200:
                        data = api_response.json()
                        # Try common response shapes
                        if isinstance(data, dict):
                            # OpenAI-like: choices -> message -> content
                            if 'choices' in data and len(data['choices'])>0:
                                first = data['choices'][0]
                                if 'message' in first and 'content' in first['message']:
                                    response = first['message']['content']
                            # Ollama sometimes returns message->content
                            if not response and 'message' in data and 'content' in data['message']:
                                response = data['message']['content']
                            # Direct text
                            if not response and 'text' in data:
                                response = data['text']
                        if response:
                            used_model = model_name
                            print(f"LLM response generated using: {used_model}")
                            break
                except Exception:
                    # Fallback to legacy /api/chat if /v1/chat fails
                    pass

                # Legacy endpoint fallback
                api_response = requests.post(
                    'http://localhost:11434/api/chat',
                    json={
                        'model': model_name,
                        'messages': [
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': user_prompt}
                        ],
                        'stream': False,
                        'temperature': 0.7,
                        'top_p': 0.9
                    },
                    timeout=60
                )

                if api_response.status_code == 200:
                    data = api_response.json()
                    if 'message' in data and 'content' in data['message']:
                        response = data['message']['content']
                        used_model = model_name
                        print(f"LLM response generated using (legacy): {used_model}")
                        break
            except requests.exceptions.Timeout:
                print(f"Timeout with model {model_name}")
                continue
            except requests.exceptions.RequestException as e:
                print(f"Connection error with model {model_name}: {e}")
                continue
            except Exception as e:
                print(f"Error with model {model_name}: {e}")
                continue

        return response
    except Exception as e:
        print(f"Error getting LLM response: {e}")
        return None

def generate_business_advice(message, conversation_history=None):
    """Generate intelligent business advice using LLM and ML models"""
    message_lower = message.lower()
    
    # Check if user is asking for business ideas
    wants_ideas = any(keyword in message_lower for keyword in [
        'idea', 'ideas', 'startup idea', 'business idea', 'side hustle', 'side project',
        'passive income', 'what should i', 'what can i', 'business to start', 
        'how to start', 'launch', 'new venture', 'opportunity', 'niche'
    ])
    
    # If asking for ideas, generate them
    if wants_ideas:
        ideas = generate_business_ideas(message)
        
        ideas_text = "\n\n🚀 **BUSINESS IDEAS FOR YOU**\n\n"
        ideas_text += "Based on your query, here are 5 business opportunities:\n\n"
        
        for idx, idea in enumerate(ideas[:5], 1):
            ideas_text += f"**{idx}. {idea['name']}**\n"
            ideas_text += f"   {idea['description']}\n"
            if 'location_benefit' in idea:
                ideas_text += f"   📍 {idea['location_benefit']}\n"
            ideas_text += f"   💰 Startup Cost: {idea['startup_cost']}\n"
            ideas_text += f"   ⏱️ Timeline: {idea['timeline']}\n"
            ideas_text += f"   💵 Revenue Potential: {idea['revenue_potential']}\n"
            ideas_text += f"   🎯 Skills Needed: {idea['skills_needed']}\n\n"
        
        ideas_text += "---\n\n💡 **NEXT STEPS:**\n"
        ideas_text += "• Validate demand: Talk to potential customers in your area/market\n"
        ideas_text += "• Build MVP: Create a minimum viable product/service quickly\n"
        ideas_text += "• Test market: Launch to small audience first\n"
        ideas_text += "• Gather feedback: Listen to early users/customers\n"
        ideas_text += "• Iterate: Improve based on feedback\n\n"
        ideas_text += "Which idea interests you most? I can help you develop it further!"
        
        return ideas_text
    
    # Check if user wants prediction or is providing business data
    wants_prediction = any(keyword in message_lower for keyword in [
        'predict', 'forecast', 'projection', 'estimate', 'profit', 'revenue',
        'what will', 'how much', 'sales of', 'expenses of', 'simulate', 'scenario'
    ])
    
    # Extract business data from message
    business_data = extract_business_data(message)
    has_data = len(business_data) > 0
    
    # Make prediction if relevant
    prediction_info = None
    if wants_prediction or has_data:
        # Use defaults for missing values
        prediction_data = {
            'sales': business_data.get('sales', 15000),
            'expenses': business_data.get('expenses', 8000),
            'marketing_spend': business_data.get('marketing_spend', 1500),
            'employee_count': business_data.get('employee_count', 20),
            'competition_level': business_data.get('competition_level', 3)
        }
        prediction_info = make_prediction(prediction_data)
    
    # Build comprehensive context for LLM
    context_parts = []
    if prediction_info:
        context_parts.append(f"=== ML PREDICTION ANALYSIS ===")
        context_parts.append(f"Predicted Profit: ${prediction_info['prediction']:.2f}")
        context_parts.append(f"Primary Model: {prediction_info['model_used']}")
        context_parts.append(f"\nAll Model Predictions:")
        for model_name, pred_value in prediction_info['all_predictions'].items():
            context_parts.append(f"  • {model_name}: ${pred_value:.2f}")
        
        context_parts.append(f"\nBusiness Metrics:")
        sales_val = business_data.get('sales', 0)
        expenses_val = business_data.get('expenses', 0)
        marketing_val = business_data.get('marketing_spend', 0)
        employees_val = business_data.get('employee_count', 0)
        competition_val = business_data.get('competition_level', 0)
        
        context_parts.append(f"  • Sales: ${sales_val:,.0f}")
        context_parts.append(f"  • Expenses: ${expenses_val:,.0f}")
        context_parts.append(f"  • Marketing Spend: ${marketing_val:,.0f}")
        context_parts.append(f"  • Employees: {employees_val:.0f}")
        context_parts.append(f"  • Competition Level: {competition_val}/5")
        
        # Add profitability analysis
        if prediction_info['prediction'] > 0:
            profit_margin = (prediction_info['prediction'] / business_data.get('sales', 1)) * 100
            context_parts.append(f"\nProfitability Metrics:")
            context_parts.append(f"  • Profit Margin: {profit_margin:.1f}%")
        
        context_parts.append(f"=== END PREDICTION ===")
    
    context = "\n".join(context_parts) if context_parts else None
    
    # Get LLM response
    llm_response = get_llm_response(message, context)
    
    if llm_response:
        # LLM response available
        response = llm_response
        
        # Add prediction info if available and not already in response
        if prediction_info and "prediction" not in response.lower():
            response += f"\n\n📊 **ML Model Analysis:**\n"
            response += f"Based on your metrics, our ensemble ML models predict a profit of **${prediction_info['prediction']:.2f}**.\n"
            response += f"Model: {prediction_info['model_used']}\n"
            if len(prediction_info['all_predictions']) > 1:
                response += f"Cross-validation: {', '.join([f'{k}: ${v:.2f}' for k, v in prediction_info['all_predictions'].items()])}\n"
    else:
        # Fallback to enhanced rule-based responses
        response = generate_rule_based_response(message, prediction_info, business_data)
    
    return response

def generate_rule_based_response(message, prediction_info=None, business_data=None):
    """Generate intelligent rule-based response when LLM is not available"""
    message_lower = message.lower()
    
    # Build response
    response_parts = []
    
    # Add prediction if available
    if prediction_info:
        response_parts.append(f"📊 **Profit Prediction:** ${prediction_info['prediction']:.2f}")
        response_parts.append(f"**Model:** {prediction_info['model_used']}")
        if len(prediction_info['all_predictions']) > 1:
            response_parts.append(f"**Cross-validation:** {', '.join([f'{k}: ${v:.2f}' for k, v in prediction_info['all_predictions'].items()])}")
        response_parts.append("")
        
        # Add business intelligence based on metrics
        if business_data and 'sales' in business_data:
            sales = business_data.get('sales', 0)
            expenses = business_data.get('expenses', 0)
            profit = prediction_info['prediction']
            
            if sales > 0:
                profit_margin = (profit / sales) * 100
                expense_ratio = (expenses / sales) * 100
                response_parts.append(f"**Financial Analysis:**")
                response_parts.append(f"• Profit Margin: {profit_margin:.1f}%")
                response_parts.append(f"• Expense Ratio: {expense_ratio:.1f}%")
                
                # Benchmark analysis
                if profit_margin < 10:
                    response_parts.append(f"⚠️ Your margin is below industry average (15-25%)")
                elif profit_margin > 25:
                    response_parts.append(f"✓ Excellent profit margin! Consider reinvestment.")
                response_parts.append("")
    
    # Provide advice based on keywords
    if 'profit' in message_lower or 'predict' in message_lower:
        response_parts.append("💡 **Profit Optimization Strategies:**")
        response_parts.append("1. **Revenue Growth** - Increase sales through marketing, new products, or market expansion")
        response_parts.append("2. **Cost Reduction** - Negotiate supplier contracts, optimize operations, eliminate waste")
        response_parts.append("3. **Efficiency** - Automate repetitive tasks, streamline workflows, improve productivity")
        response_parts.append("4. **Product Mix** - Focus on high-margin products/services")
        response_parts.append("5. **Pricing Strategy** - Analyze competitor pricing and optimize your pricing model")
        response_parts.append("")
    
    if 'sales' in message_lower or 'revenue' in message_lower or 'grow' in message_lower:
        response_parts.append("📈 **Sales Growth Strategies:**")
        response_parts.append("1. **Digital Marketing** - SEO, SEM, social media, email marketing")
        response_parts.append("2. **Customer Retention** - Loyalty programs, personalization, excellent service")
        response_parts.append("3. **Market Expansion** - New geographic markets, new customer segments")
        response_parts.append("4. **Product Innovation** - New offerings, bundling, premium versions")
        response_parts.append("5. **Partnership** - Strategic partnerships, resellers, affiliate programs")
        response_parts.append("6. **Customer Acquisition** - Referral programs, content marketing, advertising")
        response_parts.append("")
    
    if 'expense' in message_lower or 'cost' in message_lower or 'reduce' in message_lower:
        response_parts.append("💸 **Cost Reduction Strategies:**")
        response_parts.append("1. **Supplier Optimization** - Negotiate rates, consolidate vendors, explore alternatives")
        response_parts.append("2. **Operational Efficiency** - Lean processes, automation, waste reduction")
        response_parts.append("3. **Labor Optimization** - Productivity improvement, skill development, outsourcing")
        response_parts.append("4. **Technology** - Cloud services, SaaS consolidation, automation tools")
        response_parts.append("5. **Energy & Utilities** - LED lighting, smart systems, conservation measures")
        response_parts.append("6. **Renegotiate Contracts** - Insurance, services, subscriptions")
        response_parts.append("")
    
    if 'marketing' in message_lower or 'customer' in message_lower or 'brand' in message_lower:
        response_parts.append("📢 **Marketing & Customer Strategies:**")
        response_parts.append("1. **Digital Presence** - Website, SEO, Google Business, social media profiles")
        response_parts.append("2. **Content Strategy** - Blog, videos, case studies, educational content")
        response_parts.append("3. **Paid Advertising** - Google Ads, Facebook/Instagram, LinkedIn, retargeting")
        response_parts.append("4. **Social Media** - Organic engagement, influencer partnerships, community building")
        response_parts.append("5. **Email Marketing** - Newsletter, promotions, customer segmentation")
        response_parts.append("6. **Analytics** - Track CAC, LTV, ROI for each channel, optimize allocation")
        response_parts.append("")
    
    if 'competition' in message_lower or 'competitor' in message_lower:
        response_parts.append("🎯 **Competitive Strategy:**")
        response_parts.append("1. **Market Analysis** - Know your competitors' strengths/weaknesses")
        response_parts.append("2. **Differentiation** - Unique value proposition, superior quality/service")
        response_parts.append("3. **Pricing Strategy** - Competitive pricing with clear value communication")
        response_parts.append("4. **Customer Experience** - Superior service, faster delivery, better support")
        response_parts.append("5. **Innovation** - Stay ahead with new features, technology, business models")
        response_parts.append("6. **Brand Building** - Reputation, customer loyalty, thought leadership")
        response_parts.append("")
    
    if 'employee' in message_lower or 'team' in message_lower or 'staff' in message_lower:
        response_parts.append("👥 **Team & Employee Strategies:**")
        response_parts.append("1. **Recruitment** - Hire talent aligned with company values and growth goals")
        response_parts.append("2. **Training** - Skill development, professional growth, career paths")
        response_parts.append("3. **Retention** - Competitive compensation, positive culture, advancement opportunities")
        response_parts.append("4. **Productivity** - Clear goals, feedback, recognition, optimal tools")
        response_parts.append("5. **Culture** - Positive environment, team building, work-life balance")
        response_parts.append("6. **Outsourcing** - Consider outsourcing non-core functions for efficiency")
        response_parts.append("")
    
    if not response_parts or (not prediction_info and len(response_parts) == 0):
        response_parts.append("🤖 **I'm your AI Business Advisor!** I help startups with:")
        response_parts.append("")
        response_parts.append("**Core Functions:**")
        response_parts.append("• 💡 **Generate Business Ideas** - Creative startup and side hustle opportunities")
        response_parts.append("• 📊 Profit predictions using advanced ML models")
        response_parts.append("• 💡 Strategic business advice and analysis")
        response_parts.append("• 📈 Sales and revenue growth strategies")
        response_parts.append("• 💸 Cost reduction and efficiency optimization")
        response_parts.append("• 📢 Marketing and customer acquisition strategies")
        response_parts.append("• 🎯 Competitive positioning and market analysis")
        response_parts.append("• 👥 Team building and talent strategies")
        response_parts.append("• 💰 Financial planning and cash flow management")
        response_parts.append("")
        response_parts.append("**Try asking me:**")
        response_parts.append("• \"Give me 5 business ideas for a tech startup\"")
        response_parts.append("• \"What side hustles can I start with $500?\"")
        response_parts.append("• \"Show me passive income business ideas\"")
        response_parts.append("• \"Predict my profit with sales of $20000, expenses of $10000, marketing of $2000\"")
        response_parts.append("• \"I have 25 employees and $50K monthly revenue, what's my profit forecast?\"")
        response_parts.append("• \"How can I increase my sales by 30% in the next quarter?\"")
        response_parts.append("• \"What are the best ways to reduce my operating costs?\"")
        response_parts.append("• \"What marketing channels should I focus on for B2B?\"")
        response_parts.append("• \"How do I compete with larger competitors?\"")
    
    return "\n".join(response_parts)

@app.route('/chat', methods=['POST'])
def chat():
    """Main chatbot endpoint - integrates ML and LLM"""
    try:
        data = request.json
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Generate intelligent response
        response = generate_business_advice(user_message, conversation_history)
        
        return jsonify({
            'response': response,
            'user_message': user_message,
            'llm_enabled': llm_enabled
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    """ML prediction endpoint (kept for compatibility)"""
    try:
        data = request.json
        
        if not scaler or not feature_cols or not models:
            return jsonify({'error': 'Models not loaded'}), 500
        
        prediction_info = make_prediction(data)
        
        if prediction_info:
            return jsonify({
                'prediction': prediction_info['prediction'],
                'model_used': prediction_info['model_used'],
                'all_predictions': prediction_info['all_predictions'],
                'features_used': prediction_info['features']
            })
        else:
            return jsonify({'error': 'Prediction failed'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'models_loaded': best_model_name is not None,
        'best_model': best_model_name,
        'available_models': list(models.keys()),
        'llm_enabled': llm_enabled
    })

@app.route('/models', methods=['GET'])
def list_models():
    """List available models"""
    return jsonify({
        'available_models': list(models.keys()),
        'best_model': best_model_name,
        'llm_enabled': llm_enabled
    })

@app.route('/analytics', methods=['POST'])
def get_analytics():
    """Advanced analytics endpoint for business metrics"""
    try:
        data = request.json
        
        sales = float(data.get('sales', 20000))
        expenses = float(data.get('expenses', 10000))
        marketing = float(data.get('marketing_spend', 2000))
        employees = float(data.get('employee_count', 20))
        
        # Calculate comprehensive metrics
        analytics = {
            'financial': {
                'profit': sales - expenses - marketing,
                'profit_margin': ((sales - expenses - marketing) / sales * 100) if sales > 0 else 0,
                'expense_ratio': (expenses / sales * 100) if sales > 0 else 0,
                'marketing_ratio': (marketing / sales * 100) if sales > 0 else 0,
            },
            'operational': {
                'sales_per_employee': (sales / employees) if employees > 0 else 0,
                'profit_per_employee': ((sales - expenses - marketing) / employees) if employees > 0 else 0,
                'marketing_efficiency': (sales / marketing) if marketing > 0 else 0,
            },
            'benchmarks': {
                'industry_profit_margin': 20.0,
                'industry_expense_ratio': 50.0,
                'industry_marketing_ratio': 10.0,
            },
            'recommendations': generate_analytics_recommendations(sales, expenses, marketing, employees)
        }
        
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_analytics_recommendations(sales, expenses, marketing, employees):
    """Generate targeted recommendations based on metrics"""
    recommendations = []
    
    # Profit margin analysis
    profit_margin = ((sales - expenses - marketing) / sales * 100) if sales > 0 else 0
    if profit_margin < 15:
        recommendations.append({
            'area': 'Profitability',
            'priority': 'High',
            'issue': 'Low profit margin detected',
            'actions': [
                'Reduce operational expenses by 5-10%',
                'Increase prices by 3-5%',
                'Focus on high-margin products'
            ]
        })
    
    # Expense ratio analysis
    expense_ratio = (expenses / sales * 100) if sales > 0 else 0
    if expense_ratio > 60:
        recommendations.append({
            'area': 'Cost Control',
            'priority': 'High',
            'issue': 'High expense ratio',
            'actions': [
                'Audit all expenses for optimization',
                'Negotiate supplier contracts',
                'Consider automation'
            ]
        })
    
    # Marketing efficiency
    if marketing > 0:
        marketing_efficiency = sales / marketing
        if marketing_efficiency < 5:
            recommendations.append({
                'area': 'Marketing ROI',
                'priority': 'Medium',
                'issue': 'Low marketing efficiency',
                'actions': [
                    'Analyze marketing channel performance',
                    'Reduce low-ROI channels',
                    'Test new channels'
                ]
            })
    
    # Employee productivity
    if employees > 0:
        sales_per_employee = sales / employees
        if sales_per_employee < 500:
            recommendations.append({
                'area': 'Productivity',
                'priority': 'Medium',
                'issue': 'Low sales per employee',
                'actions': [
                    'Provide sales training',
                    'Improve tools and processes',
                    'Consider hiring optimization'
                ]
            })
    
    return recommendations

def generate_karnataka_district_ideas(district):
    """Generate district-specific business ideas for Karnataka"""
    
    district_ideas = {
        'bangalore': [
            {
                'name': 'IT Services & Staffing Company',
                'description': 'Supply tech talent to Bangalore\'s booming IT industry. High demand for developers, designers, QA engineers.',
                'location_benefit': 'Leverage Bangalore\'s massive tech ecosystem and talent pool',
                'startup_cost': '$5000-15000',
                'timeline': '2-3 months',
                'revenue_potential': '$10000-50000+/month',
                'skills_needed': 'Tech recruiting, HR, client management, contract negotiation'
            },
            {
                'name': 'Co-working Space for Startups',
                'description': 'Create affordable, community-focused workspace for early-stage startups and freelancers.',
                'location_benefit': 'Bangalore has thousands of startups needing affordable office space',
                'startup_cost': '$50000-150000',
                'timeline': '2-3 months setup',
                'revenue_potential': '$20000-100000+/month',
                'skills_needed': 'Real estate negotiation, community management, operations'
            },
            {
                'name': 'Startup Accelerator/Incubator',
                'description': 'Help early-stage startups with mentorship, funding connections, and resources.',
                'location_benefit': 'Bangalore has active startup community and investor networks',
                'startup_cost': '$20000-50000',
                'timeline': '3-4 months',
                'revenue_potential': '$5000-20000+/month',
                'skills_needed': 'Startup knowledge, networking, mentorship, fundraising'
            },
            {
                'name': 'Tech Upskilling Academy',
                'description': 'Teach in-demand tech skills (Python, React, data science, cloud) to career changers.',
                'location_benefit': 'Bangalore has high demand for skilled developers and professionals',
                'startup_cost': '$10000-25000',
                'timeline': '6-8 weeks setup',
                'revenue_potential': '$5000-25000/month',
                'skills_needed': 'Tech expertise, teaching, curriculum design, marketing'
            },
            {
                'name': 'App Development Studio',
                'description': 'Build mobile/web apps for startups and businesses. Services-based model with retainers.',
                'location_benefit': 'Bangalore startups and businesses need custom app development',
                'startup_cost': '$5000-15000',
                'timeline': '4-6 weeks',
                'revenue_potential': '$10000-50000+/month per team',
                'skills_needed': 'Full-stack development, project management, sales'
            }
        ],
        'mysore': [
            {
                'name': 'Silk Industry Business',
                'description': 'Produce and sell Mysore silk sarees and products. Traditional craft with high margins.',
                'location_benefit': 'Mysore is famous for silk; leverage local craftsmanship',
                'startup_cost': '$5000-15000',
                'timeline': '4-6 weeks',
                'revenue_potential': '$3000-15000/month',
                'skills_needed': 'Textile knowledge, production, e-commerce, quality control'
            },
            {
                'name': 'Heritage Tourism Business',
                'description': 'Organize palace tours, cultural experiences, heritage walks around Mysore Palace.',
                'location_benefit': 'Mysore Palace attracts 2+ million tourists annually',
                'startup_cost': '$2000-5000',
                'timeline': '3-4 weeks',
                'revenue_potential': '$3000-10000/month',
                'skills_needed': 'Local history knowledge, guiding, customer service, marketing'
            },
            {
                'name': 'Sandalwood Products Business',
                'description': 'Produce and sell sandalwood crafts, incense, oils. Traditional specialty of the region.',
                'location_benefit': 'Mysore is known for sandalwood; authentic sourcing advantage',
                'startup_cost': '$3000-8000',
                'timeline': '4-6 weeks',
                'revenue_potential': '$2000-12000/month',
                'skills_needed': 'Product development, sourcing, e-commerce, branding'
            },
            {
                'name': 'Agricultural Export Business',
                'description': 'Export local crops (sugarcane, cotton, silk cocoons) to national/international markets.',
                'location_benefit': 'Mysore region has strong agricultural base',
                'startup_cost': '$10000-30000',
                'timeline': '2-3 months',
                'revenue_potential': '$10000-50000+/month',
                'skills_needed': 'Agriculture knowledge, export/import, logistics, relationships'
            },
            {
                'name': 'Coffee Shop/Cafe (Premium)',
                'description': 'Open specialty coffee cafe targeting tourists and locals with quality service.',
                'location_benefit': 'High tourism traffic and growing local cafe culture',
                'startup_cost': '$10000-25000',
                'timeline': '6-8 weeks',
                'revenue_potential': '$3000-10000/month',
                'skills_needed': 'Hospitality, coffee knowledge, management, marketing'
            }
        ],
        'mangalore': [
            {
                'name': 'Seafood Export Business',
                'description': 'Collect and export fresh seafood to national and international markets.',
                'location_benefit': 'Mangalore is a major coastal city with fishing industry',
                'startup_cost': '$10000-25000',
                'timeline': '6-8 weeks',
                'revenue_potential': '$15000-50000+/month',
                'skills_needed': 'Seafood knowledge, cold chain management, export, relationships'
            },
            {
                'name': 'Spice Trading/Export',
                'description': 'Trade in local spices (pepper, cardamom, cinnamon) to domestic and export markets.',
                'location_benefit': 'Proximity to spice-growing regions and port facilities',
                'startup_cost': '$5000-15000',
                'timeline': '4-6 weeks',
                'revenue_potential': '$8000-30000/month',
                'skills_needed': 'Spice knowledge, sourcing, trading, export procedures'
            },
            {
                'name': 'Coffee Bean Export',
                'description': 'Source local coffee beans and export to coffee specialty markets globally.',
                'location_benefit': 'Karnataka is major coffee producer; Mangalore has port access',
                'startup_cost': '$5000-15000',
                'timeline': '4-6 weeks',
                'revenue_potential': '$8000-25000/month',
                'skills_needed': 'Coffee knowledge, sourcing, export, quality control, marketing'
            },
            {
                'name': 'Coconut Product Manufacturing',
                'description': 'Process coconut into value-added products (oil, copra, dry coconut).',
                'location_benefit': 'Mangalore region has abundant coconut production',
                'startup_cost': '$8000-20000',
                'timeline': '6-8 weeks setup',
                'revenue_potential': '$5000-20000/month',
                'skills_needed': 'Processing knowledge, manufacturing, quality, sales'
            },
            {
                'name': 'Port-Based Logistics/Customs Brokerage',
                'description': 'Help businesses navigate port procedures and handle imports/exports.',
                'location_benefit': 'Mangalore port is major trade hub with high business volume',
                'startup_cost': '$5000-15000',
                'timeline': '2-3 months licensing',
                'revenue_potential': '$5000-25000+/month',
                'skills_needed': 'Customs knowledge, documentation, relationships, networking'
            }
        ],
        'hubli': [
            {
                'name': 'Cotton Trade Business',
                'description': 'Trade in raw and processed cotton with textile mills and exporters.',
                'location_benefit': 'Hubli-Dharwad is textile hub; major cotton trading center',
                'startup_cost': '$10000-30000',
                'timeline': '4-6 weeks',
                'revenue_potential': '$15000-50000+/month',
                'skills_needed': 'Cotton grading, trading, logistics, relationships with mills'
            },
            {
                'name': 'Textile/Fabric Printing Business',
                'description': 'Print custom designs on fabric for local textile industries.',
                'location_benefit': 'Hubli is textile manufacturing center with existing demand',
                'startup_cost': '$15000-40000',
                'timeline': '6-8 weeks',
                'revenue_potential': '$8000-30000/month',
                'skills_needed': 'Textile printing, design, operations, quality control'
            },
            {
                'name': 'Cotton Ginning & Processing',
                'description': 'Gin and process raw cotton into usable fiber for textile mills.',
                'location_benefit': 'Major cotton-growing region; high local demand',
                'startup_cost': '$50000-150000',
                'timeline': '2-3 months setup',
                'revenue_potential': '$20000-100000+/month',
                'skills_needed': 'Ginning process knowledge, machinery, quality, sales'
            },
            {
                'name': 'Steel & Engineering Products',
                'description': 'Manufacture or trade small steel products for local industries.',
                'location_benefit': 'Industrial hub with manufacturing base',
                'startup_cost': '$20000-50000',
                'timeline': '2-3 months',
                'revenue_potential': '$10000-40000/month',
                'skills_needed': 'Engineering knowledge, manufacturing, quality, sales'
            },
            {
                'name': 'Automotive Parts Distribution',
                'description': 'Distribute automotive parts to local repair shops and manufacturers.',
                'location_benefit': 'Industrial hub with automotive sector presence',
                'startup_cost': '$10000-25000',
                'timeline': '4-6 weeks',
                'revenue_potential': '$8000-30000/month',
                'skills_needed': 'Automotive knowledge, relationships, logistics, sales'
            }
        ],
        'hassan': [
            {
                'name': 'Coffee Bean Farming & Export',
                'description': 'Grow and export premium coffee beans from Hassan\'s coffee plantations.',
                'location_benefit': 'Hassan is major coffee-growing region with premium varieties',
                'startup_cost': '$15000-40000',
                'timeline': '6-12 months (seasonal)',
                'revenue_potential': '$10000-40000/month',
                'skills_needed': 'Coffee farming, harvesting, processing, export logistics'
            },
            {
                'name': 'Cardamom Business',
                'description': 'Trade in green and processed cardamom to spice markets.',
                'location_benefit': 'Hassan is major cardamom producing region',
                'startup_cost': '$5000-15000',
                'timeline': '4-6 weeks',
                'revenue_potential': '$8000-30000/month',
                'skills_needed': 'Spice knowledge, sourcing, grading, trading, export'
            },
            {
                'name': 'Organic Farm Products E-commerce',
                'description': 'Sell organic coffee, spices, and vegetables from Hassan farms online.',
                'location_benefit': 'Hassan is organic farming hub; direct farmer relationships',
                'startup_cost': '$3000-8000',
                'timeline': '3-4 weeks',
                'revenue_potential': '$2000-10000/month',
                'skills_needed': 'E-commerce, farming knowledge, packaging, marketing'
            },
            {
                'name': 'Agri-tourism (Farm Stays)',
                'description': 'Create farm stay experiences for tourists interested in farming/agriculture.',
                'location_benefit': 'Beautiful coffee/cardamom plantations; growing tourism interest',
                'startup_cost': '$20000-50000',
                'timeline': '2-3 months setup',
                'revenue_potential': '$5000-20000/month',
                'skills_needed': 'Hospitality, farm knowledge, marketing, customer service'
            },
            {
                'name': 'Agricultural Equipment Rental',
                'description': 'Rent farming equipment (tractors, harvesters) to local farmers.',
                'location_benefit': 'High agricultural activity; many small farmers need equipment',
                'startup_cost': '$30000-80000',
                'timeline': '3-4 weeks registration',
                'revenue_potential': '$8000-30000+/month',
                'skills_needed': 'Equipment knowledge, maintenance, customer relationships'
            }
        ],
        'shimoga': [
            {
                'name': 'Coffee & Spice Trading',
                'description': 'Trade coffee, cardamom, and other spices from Western Ghats region.',
                'location_benefit': 'Gateway to coffee and spice plantations',
                'startup_cost': '$8000-20000',
                'timeline': '4-6 weeks',
                'revenue_potential': '$10000-35000/month',
                'skills_needed': 'Spice/coffee knowledge, sourcing, trading, logistics'
            },
            {
                'name': 'Eco-Tourism Business',
                'description': 'Organize eco-tours, trekking, wildlife experiences in Western Ghats.',
                'location_benefit': 'Rich biodiversity and scenic beauty; growing eco-tourism demand',
                'startup_cost': '$3000-8000',
                'timeline': '4-6 weeks',
                'revenue_potential': '$3000-12000/month',
                'skills_needed': 'Nature knowledge, guiding, customer service, marketing'
            },
            {
                'name': 'Jaggery/Sugar Cane Processing',
                'description': 'Process sugarcane into jaggery and sell to local and distant markets.',
                'location_benefit': 'High sugarcane cultivation; traditional business with good demand',
                'startup_cost': '$10000-25000',
                'timeline': '6-8 weeks setup',
                'revenue_potential': '$5000-20000/month',
                'skills_needed': 'Processing knowledge, quality control, packaging, sales'
            },
            {
                'name': 'Silk Products Manufacturing',
                'description': 'Produce silk products (sarees, scarves) for local and national markets.',
                'location_benefit': 'Region has traditional silk weaving heritage',
                'startup_cost': '$5000-15000',
                'timeline': '4-6 weeks',
                'revenue_potential': '$3000-15000/month',
                'skills_needed': 'Weaving/textile knowledge, design, quality, e-commerce'
            },
            {
                'name': 'Bamboo Handicrafts Business',
                'description': 'Create bamboo furniture, baskets, and handicrafts from local bamboo.',
                'location_benefit': 'Abundant bamboo; eco-friendly products have growing demand',
                'startup_cost': '$2000-6000',
                'timeline': '3-4 weeks',
                'revenue_potential': '$2000-10000/month',
                'skills_needed': 'Bamboo crafting, design, production, e-commerce, marketing'
            }
        ],
        'belgaum': [
            {
                'name': 'Sugarcane Processing & Trading',
                'description': 'Process sugarcane into sugar, jaggery, and molasses.',
                'location_benefit': 'Major sugarcane growing region with mill infrastructure',
                'startup_cost': '$20000-50000',
                'timeline': '2-3 months setup',
                'revenue_potential': '$15000-60000+/month',
                'skills_needed': 'Sugar processing, quality control, logistics, sales'
            },
            {
                'name': 'Pulse/Grain Trading',
                'description': 'Trade in local pulses, wheat, and grains to larger markets.',
                'location_benefit': 'Agricultural region with significant grain production',
                'startup_cost': '$10000-25000',
                'timeline': '3-4 weeks',
                'revenue_potential': '$10000-40000/month',
                'skills_needed': 'Grain grading, trading, logistics, price knowledge'
            },
            {
                'name': 'Cotton Farming & Trading',
                'description': 'Grow and trade cotton to textile mills and exporters.',
                'location_benefit': 'Major cotton cultivation area with buyer networks',
                'startup_cost': '$10000-30000',
                'timeline': '4-6 weeks',
                'revenue_potential': '$12000-45000/month',
                'skills_needed': 'Cotton farming, quality grading, trading, relationships'
            },
            {
                'name': 'Biotech/Agri-Biotech Company',
                'description': 'Develop bio-products for agriculture (biopesticides, biofertilizers).',
                'location_benefit': 'Agricultural region with farmer focus on innovation',
                'startup_cost': '$25000-60000',
                'timeline': '3-4 months R&D',
                'revenue_potential': '$10000-50000+/month',
                'skills_needed': 'Biotech knowledge, product development, farmer relationships'
            },
            {
                'name': 'Onion & Potato Storage/Trading',
                'description': 'Store and trade onions and potatoes with controlled storage.',
                'location_benefit': 'Region produces significant onion and potato; storage profitable',
                'startup_cost': '$20000-50000',
                'timeline': '4-6 weeks setup',
                'revenue_potential': '$15000-50000+/month',
                'skills_needed': 'Cold storage knowledge, trading, quality control, logistics'
            }
        ],
        'tumkur': [
            {
                'name': 'Silk Thread Production',
                'description': 'Produce silk thread for use in textile and embroidery industries.',
                'location_benefit': 'Region has silk industry base; local demand',
                'startup_cost': '$10000-25000',
                'timeline': '2-3 months setup',
                'revenue_potential': '$8000-30000/month',
                'skills_needed': 'Silk processing, quality control, production management'
            },
            {
                'name': 'Granite Quarrying & Polishing',
                'description': 'Extract and polish granite blocks for construction market.',
                'location_benefit': 'Tumkur is major granite mining and quarrying center',
                'startup_cost': '$30000-100000',
                'timeline': '2-3 months licensing',
                'revenue_potential': '$20000-100000+/month',
                'skills_needed': 'Mining knowledge, quarrying, machinery, sales'
            },
            {
                'name': 'Stone Tile Manufacturing',
                'description': 'Cut and finish granite tiles for construction and home use.',
                'location_benefit': 'Abundant granite resources; growing construction demand',
                'startup_cost': '$15000-40000',
                'timeline': '6-8 weeks setup',
                'revenue_potential': '$10000-40000/month',
                'skills_needed': 'Stone cutting, quality, machinery operation, sales'
            },
            {
                'name': 'Sericulture (Silk Farming)',
                'description': 'Raise silkworms and produce cocoons for silk thread industry.',
                'location_benefit': 'Region has sericulture infrastructure and buyer network',
                'startup_cost': '$5000-15000',
                'timeline': '2-3 months per cycle',
                'revenue_potential': '$3000-15000/month',
                'skills_needed': 'Silkworm farming, cocoon production, quality control'
            },
            {
                'name': 'Brick Manufacturing',
                'description': 'Manufacture bricks for construction industry.',
                'location_benefit': 'High construction activity; local demand for bricks',
                'startup_cost': '$20000-50000',
                'timeline': '4-6 weeks setup',
                'revenue_potential': '$10000-50000+/month',
                'skills_needed': 'Brick-making, kiln operation, quality, sales'
            }
        ],
        'davangere': [
            {
                'name': 'Coffee Processing & Export',
                'description': 'Process raw coffee and export finished coffee products.',
                'location_benefit': 'Major coffee processing hub in India',
                'startup_cost': '$15000-40000',
                'timeline': '6-8 weeks setup',
                'revenue_potential': '$20000-80000+/month',
                'skills_needed': 'Coffee processing, roasting, export logistics, quality'
            },
            {
                'name': 'Chickpea/Pulse Milling',
                'description': 'Mill and process chickpeas and other pulses for export.',
                'location_benefit': 'Major pulse processing center; export market access',
                'startup_cost': '$20000-50000',
                'timeline': '2-3 months setup',
                'revenue_potential': '$15000-60000+/month',
                'skills_needed': 'Milling, quality control, food safety, export procedures'
            },
            {
                'name': 'Spice Grinding & Processing',
                'description': 'Grind and package spices for retail and bulk markets.',
                'location_benefit': 'Central location for spice trade; existing infrastructure',
                'startup_cost': '$10000-25000',
                'timeline': '4-6 weeks setup',
                'revenue_potential': '$8000-35000/month',
                'skills_needed': 'Spice processing, food safety, packaging, marketing'
            },
            {
                'name': 'Agricultural Equipment Manufacturing',
                'description': 'Manufacture small agricultural tools and equipment.',
                'location_benefit': 'Industrial area with manufacturing capability',
                'startup_cost': '$20000-50000',
                'timeline': '2-3 months setup',
                'revenue_potential': '$12000-45000/month',
                'skills_needed': 'Manufacturing, engineering, quality control'
            },
            {
                'name': 'Grain Storage & Trading',
                'description': 'Store and trade grains with farmers and bulk buyers.',
                'location_benefit': 'Agricultural region with grain concentration',
                'startup_cost': '$25000-60000',
                'timeline': '3-4 weeks setup',
                'revenue_potential': '$15000-60000+/month',
                'skills_needed': 'Grain storage, trading, logistics, quality control'
            }
        ],
        'kolar': [
            {
                'name': 'Mining & Mineral Trading',
                'description': 'Trade in minerals and mining products from Kolar\'s mining areas.',
                'location_benefit': 'Historic gold mining region; mineral resources',
                'startup_cost': '$20000-50000',
                'timeline': '2-3 months licensing',
                'revenue_potential': '$15000-60000+/month',
                'skills_needed': 'Mineral knowledge, mining regulations, trading, logistics'
            },
            {
                'name': 'Garlic Processing & Export',
                'description': 'Process and export fresh and processed garlic.',
                'location_benefit': 'Major garlic growing region; export potential',
                'startup_cost': '$10000-25000',
                'timeline': '4-6 weeks setup',
                'revenue_potential': '$8000-40000+/month',
                'skills_needed': 'Garlic processing, quality control, export procedures'
            },
            {
                'name': 'Vegetable Dehydration',
                'description': 'Dehydrate vegetables (onion, garlic, tomato) for retail and food industry.',
                'location_benefit': 'Strong vegetable production base',
                'startup_cost': '$15000-35000',
                'timeline': '2-3 months setup',
                'revenue_potential': '$10000-40000/month',
                'skills_needed': 'Dehydration process, food safety, quality, sales'
            },
            {
                'name': 'Floriculture/Flower Farming',
                'description': 'Grow flowers for wedding, festival, and export markets.',
                'location_benefit': 'Climate suitable for floriculture; growing market',
                'startup_cost': '$8000-20000',
                'timeline': '2-3 months',
                'revenue_potential': '$5000-20000/month',
                'skills_needed': 'Horticulture, farming, marketing, distribution'
            },
            {
                'name': 'Cold Chain Logistics',
                'description': 'Provide cold storage and logistics for perishables.',
                'location_benefit': 'Agricultural region needing cold chain infrastructure',
                'startup_cost': '$30000-80000',
                'timeline': '6-8 weeks setup',
                'revenue_potential': '$15000-60000+/month',
                'skills_needed': 'Logistics, cold chain management, operations'
            }
        ]
    }
    
    # Get ideas for detected district
    return district_ideas.get(district, [])

def generate_state_district_ideas(state, district):
    """Generate district-specific business ideas for multiple Indian states"""
    
    state_ideas = {
        'tamil nadu': {
            'chennai': [
                {'name': 'IT Staffing & Recruitment', 'description': 'Supply tech talent to Chennai\'s booming IT corridor', 'location_benefit': 'Chennai is India\'s 2nd largest IT hub with 50000+ tech companies', 'startup_cost': '$5000-15000', 'timeline': '2-3 months', 'revenue_potential': '$10000-50000+/month', 'skills_needed': 'Tech recruiting, HR, client management'},
                {'name': 'Co-working & Incubator Space', 'description': 'Create shared workspace for startups and freelancers', 'location_benefit': 'High demand from startups in Chennai\'s tech parks', 'startup_cost': '$50000-150000', 'timeline': '2-3 months', 'revenue_potential': '$20000-100000+/month', 'skills_needed': 'Real estate, community management'},
                {'name': 'Fintech/Payment Solutions', 'description': 'Develop payment gateways or fintech apps', 'location_benefit': 'Chennai has major fintech companies (Zoho, etc)', 'startup_cost': '$20000-50000', 'timeline': '3-4 months', 'revenue_potential': '$15000-80000+/month', 'skills_needed': 'Finance, tech, payment systems'},
                {'name': 'Manufacturing Export Business', 'description': 'Export leather goods, textiles, automotive parts', 'location_benefit': 'Chennai is major manufacturing and export hub', 'startup_cost': '$15000-40000', 'timeline': '2-3 months', 'revenue_potential': '$20000-100000+/month', 'skills_needed': 'Manufacturing, export procedures, logistics'},
                {'name': 'Maritime/Shipping Services', 'description': 'Port logistics, customs brokerage, shipping coordination', 'location_benefit': 'Chennai port is major shipping hub', 'startup_cost': '$10000-30000', 'timeline': '2-3 months', 'revenue_potential': '$15000-60000+/month', 'skills_needed': 'Shipping, customs, logistics'}
            ],
            'coimbatore': [
                {'name': 'Textile Manufacturing/Export', 'description': 'Produce and export textiles and fabrics', 'location_benefit': 'Coimbatore is India\'s textile capital', 'startup_cost': '$20000-50000', 'timeline': '2-3 months', 'revenue_potential': '$30000-150000+/month', 'skills_needed': 'Textile production, export, quality control'},
                {'name': 'Engineering Goods Manufacturing', 'description': 'Produce industrial machinery and components', 'location_benefit': 'Strong engineering industry base', 'startup_cost': '$30000-80000', 'timeline': '3-4 months', 'revenue_potential': '$25000-120000+/month', 'skills_needed': 'Engineering, manufacturing, quality'},
                {'name': 'Auto Parts Distribution', 'description': 'Distribute automotive components to manufacturers', 'location_benefit': 'Major automotive hub with demand', 'startup_cost': '$15000-40000', 'timeline': '4-6 weeks', 'revenue_potential': '$15000-60000/month', 'skills_needed': 'Auto industry, logistics, sales'},
                {'name': 'Spice Processing & Export', 'description': 'Process and export local spices', 'location_benefit': 'Coimbatore spices are world-renowned', 'startup_cost': '$8000-20000', 'timeline': '4-6 weeks', 'revenue_potential': '$10000-50000/month', 'skills_needed': 'Spice processing, food safety, export'},
                {'name': 'Rubber & Plastic Products', 'description': 'Manufacture rubber and plastic goods', 'location_benefit': 'Strong rubber and plastics industry', 'startup_cost': '$25000-60000', 'timeline': '3-4 months', 'revenue_potential': '$20000-100000+/month', 'skills_needed': 'Manufacturing, machinery, quality control'}
            ],
            'madurai': [
                {'name': 'Textile Weaving/Saree Business', 'description': 'Produce traditional Madurai silk sarees', 'location_benefit': 'Famous for Madurai silk with high demand', 'startup_cost': '$8000-20000', 'timeline': '4-6 weeks', 'revenue_potential': '$5000-25000/month', 'skills_needed': 'Weaving, textile design, e-commerce'},
                {'name': 'Jasmine Flower Trading', 'description': 'Trade jasmine flowers to other markets', 'location_benefit': 'Madurai is jasmine capital of India', 'startup_cost': '$2000-5000', 'timeline': '1-2 weeks', 'revenue_potential': '$2000-8000/month', 'skills_needed': 'Agriculture, trading, logistics'},
                {'name': 'Temple Ornament Manufacturing', 'description': 'Create religious/temple decorations and ornaments', 'location_benefit': 'High demand in temple city of Madurai', 'startup_cost': '$5000-15000', 'timeline': '3-4 weeks', 'revenue_potential': '$3000-12000/month', 'skills_needed': 'Ornament design, manufacturing, craftsmanship'},
                {'name': 'Organic Agriculture Export', 'description': 'Grow and export organic produce', 'location_benefit': 'Agricultural region with export potential', 'startup_cost': '$10000-25000', 'timeline': '2-3 months', 'revenue_potential': '$8000-40000/month', 'skills_needed': 'Organic farming, export, certification'},
                {'name': 'Tourism Services', 'description': 'Tour guides, accommodation, experiences for pilgrims', 'location_benefit': 'Major pilgrimage destination', 'startup_cost': '$5000-15000', 'timeline': '4-6 weeks', 'revenue_potential': '$5000-20000/month', 'skills_needed': 'Tourism, hospitality, language skills'}
            ]
        },
        'maharashtra': {
            'mumbai': [
                {'name': 'Financial Advisory Services', 'description': 'Provide investment, insurance, wealth management advice', 'location_benefit': 'Mumbai is India\'s financial capital', 'startup_cost': '$10000-30000', 'timeline': '2-3 months', 'revenue_potential': '$20000-100000+/month', 'skills_needed': 'Finance, investments, regulatory knowledge'},
                {'name': 'Real Estate Services', 'description': 'Property brokerage, consultancy, investment advisory', 'location_benefit': 'Massive real estate market in Mumbai', 'startup_cost': '$5000-15000', 'timeline': '3-4 weeks', 'revenue_potential': '$30000-200000+/month', 'skills_needed': 'Real estate, sales, negotiation'},
                {'name': 'Film & Media Production', 'description': 'Produce content for films, web series, ads', 'location_benefit': 'Bollywood capital with huge production demand', 'startup_cost': '$20000-50000', 'timeline': '2-3 months', 'revenue_potential': '$25000-150000+/month', 'skills_needed': 'Film, editing, direction, marketing'},
                {'name': 'App & Software Development', 'description': 'Develop apps and software solutions', 'location_benefit': 'Mumbai has huge tech startup ecosystem', 'startup_cost': '$10000-25000', 'timeline': '2-3 months', 'revenue_potential': '$15000-100000+/month', 'skills_needed': 'Software development, project management'},
                {'name': 'Fashion & Design Studio', 'description': 'Create fashion designs and brand products', 'location_benefit': 'Major fashion hub with retail opportunities', 'startup_cost': '$8000-20000', 'timeline': '4-6 weeks', 'revenue_potential': '$10000-60000/month', 'skills_needed': 'Fashion design, sewing, e-commerce, marketing'}
            ],
            'pune': [
                {'name': 'IT Training & Upskilling Academy', 'description': 'Teach coding, data science, cloud computing', 'location_benefit': 'Pune has 40000+ IT professionals seeking upskilling', 'startup_cost': '$8000-20000', 'timeline': '4-6 weeks', 'revenue_potential': '$8000-50000/month', 'skills_needed': 'IT expertise, teaching, curriculum design'},
                {'name': 'Automotive Service Center', 'description': 'Auto repair, maintenance, customization services', 'location_benefit': 'Major automotive manufacturing hub', 'startup_cost': '$30000-80000', 'timeline': '2-3 months', 'revenue_potential': '$20000-100000+/month', 'skills_needed': 'Automotive repair, customer service'},
                {'name': 'Coworking Space for Startups', 'description': 'Provide affordable workspace and mentorship', 'location_benefit': 'Growing startup ecosystem in Pune', 'startup_cost': '$40000-120000', 'timeline': '2-3 months', 'revenue_potential': '$15000-80000/month', 'skills_needed': 'Community management, business knowledge'},
                {'name': 'Organic Food/Agricultural Products', 'description': 'Sell organic farm products to health-conscious market', 'location_benefit': 'High demand for organic products in Pune', 'startup_cost': '$8000-20000', 'timeline': '4-6 weeks', 'revenue_potential': '$5000-25000/month', 'skills_needed': 'Organic farming, supply chain, e-commerce'},
                {'name': 'EdTech Platform', 'description': 'Create online courses and learning platform', 'location_benefit': 'High education and tech-savvy population', 'startup_cost': '$10000-30000', 'timeline': '2-3 months', 'revenue_potential': '$10000-80000+/month', 'skills_needed': 'Tech, education, content creation'}
            ],
            'nashik': [
                {'name': 'Wine & Vineyard Business', 'description': 'Produce and sell wine products', 'location_benefit': 'Nashik is India\'s wine country', 'startup_cost': '$50000-150000', 'timeline': '3-4 months', 'revenue_potential': '$40000-300000+/month', 'skills_needed': 'Viticulture, wine production, sales'},
                {'name': 'Sugar Processing/Export', 'description': 'Process sugarcane into products for export', 'location_benefit': 'Major sugarcane producing region', 'startup_cost': '$50000-120000', 'timeline': '2-3 months', 'revenue_potential': '$30000-150000+/month', 'skills_needed': 'Sugar processing, export, quality control'},
                {'name': 'Spice Milling', 'description': 'Mill and process spices for export', 'location_benefit': 'Agricultural region with spice production', 'startup_cost': '$15000-40000', 'timeline': '4-6 weeks', 'revenue_potential': '$10000-50000/month', 'skills_needed': 'Spice milling, food safety, export'},
                {'name': 'Onion Trading/Export', 'description': 'Trade onions to national and international markets', 'location_benefit': 'Nashik is onion capital of India', 'startup_cost': '$20000-50000', 'timeline': '3-4 weeks', 'revenue_potential': '$30000-150000+/month', 'skills_needed': 'Trading, logistics, export procedures'},
                {'name': 'Agricultural Tourism', 'description': 'Organize farm stays and agri-tourism experiences', 'location_benefit': 'Beautiful vineyards and farms attract tourists', 'startup_cost': '$20000-50000', 'timeline': '2-3 months', 'revenue_potential': '$10000-50000/month', 'skills_needed': 'Hospitality, marketing, agriculture knowledge'}
            ]
        },
        'gujarat': {
            'ahmedabad': [
                {'name': 'Textile Manufacturing/Export', 'description': 'Produce and export textiles and fabrics', 'location_benefit': 'Major textile hub with export infrastructure', 'startup_cost': '$30000-80000', 'timeline': '2-3 months', 'revenue_potential': '$40000-200000+/month', 'skills_needed': 'Textile production, export, quality'},
                {'name': 'Diamond Polishing/Trading', 'description': 'Polish and trade diamonds', 'location_benefit': 'Ahmedabad is diamond polishing capital', 'startup_cost': '$50000-200000', 'timeline': '3-4 months', 'revenue_potential': '$50000-500000+/month', 'skills_needed': 'Diamond expertise, trading, certification'},
                {'name': 'Software/IT Services', 'description': 'Develop software and IT solutions', 'location_benefit': 'Growing tech sector in Ahmedabad', 'startup_cost': '$10000-25000', 'timeline': '2-3 months', 'revenue_potential': '$15000-100000+/month', 'skills_needed': 'Software development, project management'},
                {'name': 'Pharmaceutical Manufacturing', 'description': 'Manufacture pharmaceutical products', 'location_benefit': 'Major pharma hub with supply chain', 'startup_cost': '$100000-300000', 'timeline': '4-6 months', 'revenue_potential': '$100000-500000+/month', 'skills_needed': 'Pharma knowledge, regulation, quality'},
                {'name': 'Automotive Components', 'description': 'Manufacture auto parts and components', 'location_benefit': 'Strong automotive supplier network', 'startup_cost': '$40000-100000', 'timeline': '3-4 months', 'revenue_potential': '$30000-150000+/month', 'skills_needed': 'Engineering, manufacturing, quality'}
            ],
            'surat': [
                {'name': 'Diamond Business/Polishing', 'description': 'Polishing and trading of diamonds', 'location_benefit': 'Surat is world\'s diamond capital', 'startup_cost': '$50000-200000', 'timeline': '3-4 months', 'revenue_potential': '$100000-1000000+/month', 'skills_needed': 'Diamond expertise, trading, import-export'},
                {'name': 'Textile/Garment Export', 'description': 'Manufacture and export textiles and garments', 'location_benefit': 'Major textile and apparel hub', 'startup_cost': '$30000-80000', 'timeline': '2-3 months', 'revenue_potential': '$50000-300000+/month', 'skills_needed': 'Textile, manufacturing, export logistics'},
                {'name': 'Embroidery Business', 'description': 'Create embroidered products for fashion market', 'location_benefit': 'World-class embroidery craftsmen and market', 'startup_cost': '$10000-25000', 'timeline': '4-6 weeks', 'revenue_potential': '$8000-60000/month', 'skills_needed': 'Embroidery design, craftsmanship, fashion'},
                {'name': 'Chemical & Dye Manufacturing', 'description': 'Produce chemicals and dyes for textile industry', 'location_benefit': 'Major chemical and dye producing center', 'startup_cost': '$50000-150000', 'timeline': '3-4 months', 'revenue_potential': '$40000-200000+/month', 'skills_needed': 'Chemistry, manufacturing, safety regulations'},
                {'name': 'Port Services/Logistics', 'description': 'Provide shipping and port-related services', 'location_benefit': 'Surat is major international port city', 'startup_cost': '$15000-40000', 'timeline': '2-3 months', 'revenue_potential': '$20000-100000+/month', 'skills_needed': 'Shipping, customs, logistics'}
            ],
            'vadodara': [
                {'name': 'Petrochemical Products', 'description': 'Manufacture petrochemical-based products', 'location_benefit': 'Major petrochemical hub', 'startup_cost': '$100000-300000', 'timeline': '4-6 months', 'revenue_potential': '$80000-400000+/month', 'skills_needed': 'Chemistry, petrochemicals, safety'},
                {'name': 'Ceramic Tile Manufacturing', 'description': 'Produce ceramic and vitrified tiles', 'location_benefit': 'Major tile manufacturing center', 'startup_cost': '$80000-200000', 'timeline': '3-4 months', 'revenue_potential': '$50000-250000+/month', 'skills_needed': 'Ceramics, manufacturing, quality control'},
                {'name': 'Pharmaceutical Products', 'description': 'Manufacture pharmaceutical products', 'location_benefit': 'Growing pharma sector', 'startup_cost': '$80000-200000', 'timeline': '4-6 months', 'revenue_potential': '$70000-350000+/month', 'skills_needed': 'Pharmacy, quality, regulation'},
                {'name': 'Plastics Manufacturing', 'description': 'Produce plastic products and moldings', 'location_benefit': 'Industrial area with demand', 'startup_cost': '$40000-100000', 'timeline': '2-3 months', 'revenue_potential': '$30000-150000+/month', 'skills_needed': 'Plastics, machinery, quality'},
                {'name': 'Engineering Services', 'description': 'Provide engineering design and manufacturing', 'location_benefit': 'Industrial hub with engineering demand', 'startup_cost': '$30000-80000', 'timeline': '3-4 months', 'revenue_potential': '$25000-120000+/month', 'skills_needed': 'Engineering, design, manufacturing'}
            ]
        },
        'telangana': {
            'hyderabad': [
                {'name': 'IT Services & Staffing', 'description': 'Supply tech talent to IT companies', 'location_benefit': 'Hyderabad is India\'s 3rd largest IT hub', 'startup_cost': '$8000-20000', 'timeline': '2-3 months', 'revenue_potential': '$15000-80000+/month', 'skills_needed': 'Tech recruiting, HR, client management'},
                {'name': 'Pharma/Biotech Company', 'description': 'Develop pharmaceutical or biotech products', 'location_benefit': 'Hyderabad is pharma capital of India', 'startup_cost': '$50000-150000', 'timeline': '4-6 months', 'revenue_potential': '$50000-300000+/month', 'skills_needed': 'Pharmacy, biotech, regulatory knowledge'},
                {'name': 'Software Development Studio', 'description': 'Create custom software and apps', 'location_benefit': 'Major tech hub with product ecosystem', 'startup_cost': '$12000-30000', 'timeline': '2-3 months', 'revenue_potential': '$20000-120000+/month', 'skills_needed': 'Software development, project management'},
                {'name': 'Startup Accelerator', 'description': 'Mentor and fund early-stage startups', 'location_benefit': 'Thriving startup ecosystem', 'startup_cost': '$50000-150000', 'timeline': '2-3 months', 'revenue_potential': '$20000-100000+/month', 'skills_needed': 'Startup knowledge, mentoring, funding'},
                {'name': 'EdTech Platform', 'description': 'Create online learning platform', 'location_benefit': 'Tech-savvy population with education focus', 'startup_cost': '$15000-40000', 'timeline': '2-3 months', 'revenue_potential': '$15000-100000+/month', 'skills_needed': 'Tech, education, content creation'}
            ],
            'warangal': [
                {'name': 'Textile Manufacturing', 'description': 'Produce textiles and fabrics', 'location_benefit': 'Historic textile center', 'startup_cost': '$25000-60000', 'timeline': '2-3 months', 'revenue_potential': '$20000-100000+/month', 'skills_needed': 'Textile production, export, quality'},
                {'name': 'Handloom Products Business', 'description': 'Produce and sell handloom fabrics', 'location_benefit': 'Famous for Warangal sarees and handlooms', 'startup_cost': '$10000-25000', 'timeline': '4-6 weeks', 'revenue_potential': '$8000-50000/month', 'skills_needed': 'Handloom design, production, e-commerce'},
                {'name': 'Granite & Stone Business', 'description': 'Quarry and process granite', 'location_benefit': 'Rich mineral resources', 'startup_cost': '$50000-150000', 'timeline': '2-3 months', 'revenue_potential': '$30000-150000+/month', 'skills_needed': 'Quarrying, processing, sales'},
                {'name': 'Cement & Building Materials', 'description': 'Manufacture cement and building materials', 'location_benefit': 'Industrial infrastructure present', 'startup_cost': '$200000-500000', 'timeline': '4-6 months', 'revenue_potential': '$150000-800000+/month', 'skills_needed': 'Cement production, quality, regulation'},
                {'name': 'Spice Trading/Processing', 'description': 'Process and trade local spices', 'location_benefit': 'Agricultural region with spice cultivation', 'startup_cost': '$8000-20000', 'timeline': '4-6 weeks', 'revenue_potential': '$8000-40000/month', 'skills_needed': 'Spice processing, export, food safety'}
            ]
        }
    }
    
    # Get state ideas
    if state in state_ideas and district in state_ideas[state]:
        return state_ideas[state][district]
    
    # Fallback to generic location ideas if state/district not found
    return generate_karnataka_district_ideas(district) if district in ['bangalore', 'mysore', 'mangalore'] else []

def generate_business_ideas(message, user_context=None):
    """Generate creative and innovative business ideas"""
    
    # Extract keywords from message
    message_lower = message.lower()
    
    # Determine industry/category focus
    industry_keywords = {
        'tech': ['technology', 'software', 'app', 'ai', 'ml', 'saas', 'web', 'digital', 'tech', 'startup', 'code', 'programming'],
        'ecommerce': ['ecommerce', 'shop', 'store', 'sell', 'products', 'online retail', 'amazon', 'shopify'],
        'service': ['service', 'consulting', 'agency', 'freelance', 'professional', 'coaching'],
        'creator': ['creator', 'content', 'youtube', 'influencer', 'social media', 'podcast', 'blog'],
        'education': ['education', 'course', 'training', 'learning', 'teach', 'tutoring', 'online course'],
        'health': ['health', 'fitness', 'wellness', 'medical', 'therapy', 'nutrition', 'coaching'],
        'sustainability': ['green', 'eco', 'sustainable', 'renewable', 'environment', 'carbon'],
        'general': []
    }
    
    detected_industry = 'general'
    for industry, keywords in industry_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            detected_industry = industry
            break
    
    # Generate ideas based on industry
    business_ideas = {
        'tech': [
            {
                'name': 'AI-Powered Chatbot Services',
                'description': 'Build custom chatbots for small businesses using LLMs. Target businesses that need customer support automation.',
                'startup_cost': '$500-2000',
                'timeline': '3-4 months',
                'revenue_potential': '$2000-10000/month per client',
                'skills_needed': 'API integration, prompt engineering, customer service'
            },
            {
                'name': 'No-Code/Low-Code Development Agency',
                'description': 'Help businesses build applications using no-code tools (Bubble, Flutterflow, Zapier). Faster delivery, lower costs.',
                'startup_cost': '$1000-3000',
                'timeline': '2-3 months',
                'revenue_potential': '$3000-15000/project',
                'skills_needed': 'No-code platforms, business logic, UX design'
            },
            {
                'name': 'SaaS Product - Niche Solution',
                'description': 'Identify a specific problem in underserved market and build a SaaS solution. E.g., accounting for freelancers, scheduling for salons.',
                'startup_cost': '$2000-5000',
                'timeline': '4-6 months MVP',
                'revenue_potential': '$500-5000/month per customer',
                'skills_needed': 'Full-stack development, product management, marketing'
            },
            {
                'name': 'API Integration Services',
                'description': 'Help businesses integrate multiple APIs and tools. Provide integration consulting and implementation.',
                'startup_cost': '$500-1500',
                'timeline': '2 months',
                'revenue_potential': '$1500-8000/integration',
                'skills_needed': 'API knowledge, integration patterns, troubleshooting'
            },
            {
                'name': 'Automation Consulting',
                'description': 'Help businesses automate repetitive processes using tools like Zapier, Make, or custom scripts.',
                'startup_cost': '$300-1000',
                'timeline': '1-2 months',
                'revenue_potential': '$2000-10000/project',
                'skills_needed': 'Workflow automation, process optimization, tool knowledge'
            }
        ],
        'ecommerce': [
            {
                'name': 'Print-on-Demand Store',
                'description': 'Design and sell custom merchandise (t-shirts, mugs, hoodies) with zero inventory. Use Printful, Merch by Amazon.',
                'startup_cost': '$200-500',
                'timeline': '2-3 weeks',
                'revenue_potential': '$500-5000/month',
                'skills_needed': 'Design (Canva), marketing, social media, SEO'
            },
            {
                'name': 'Dropshipping Store (Vetted Suppliers)',
                'description': 'Build a branded store with curated products from reliable suppliers. Focus on niche markets and excellent customer service.',
                'startup_cost': '$500-1500',
                'timeline': '3-4 weeks',
                'revenue_potential': '$1000-10000/month',
                'skills_needed': 'Shopify/WooCommerce, marketing, customer service'
            },
            {
                'name': 'Digital Products Store',
                'description': 'Create and sell digital products (templates, guides, courses, presets, designs) with 100% margins.',
                'startup_cost': '$200-500',
                'timeline': '2-4 weeks',
                'revenue_potential': '$500-3000/month',
                'skills_needed': 'Design, writing, your expertise in a specific area'
            },
            {
                'name': 'Niche Reselling Business',
                'description': 'Identify products with high profit margins in underserved niches. Build authority and brand loyalty.',
                'startup_cost': '$1000-5000',
                'timeline': '4-6 weeks',
                'revenue_potential': '$2000-15000/month',
                'skills_needed': 'Market research, sourcing, marketing, customer service'
            },
            {
                'name': 'Amazon FBA Side Hustle',
                'description': 'Source products, ship to Amazon FBA, and let Amazon handle fulfillment. Passive income potential.',
                'startup_cost': '$1500-5000',
                'timeline': '2-3 months',
                'revenue_potential': '$1000-10000/month',
                'skills_needed': 'Product research, sourcing, inventory management'
            }
        ],
        'service': [
            {
                'name': 'Virtual Assistant Service',
                'description': 'Provide administrative support to busy entrepreneurs and small business owners remotely.',
                'startup_cost': '$200-500',
                'timeline': 'Immediate',
                'revenue_potential': '$2000-8000/month',
                'skills_needed': 'Organization, communication, office software, customer service'
            },
            {
                'name': 'Social Media Management Agency',
                'description': 'Manage social media accounts for small businesses. Create content, schedule posts, engage with audience.',
                'startup_cost': '$300-1000',
                'timeline': '2-3 weeks',
                'revenue_potential': '$1000-5000/month per client',
                'skills_needed': 'Social media platforms, content creation, copywriting, analytics'
            },
            {
                'name': 'Bookkeeping Service',
                'description': 'Offer bookkeeping and financial record management to small businesses. Use QuickBooks, Wave, or Xero.',
                'startup_cost': '$500-1500',
                'timeline': '1-2 months training',
                'revenue_potential': '$1500-8000/month',
                'skills_needed': 'Accounting basics, bookkeeping software, attention to detail'
            },
            {
                'name': 'Copywriting & Content Marketing',
                'description': 'Write website copy, email sequences, landing pages, and blog posts for businesses.',
                'startup_cost': '$200-500',
                'timeline': 'Immediate',
                'revenue_potential': '$1000-5000/month',
                'skills_needed': 'Writing, persuasion, marketing psychology, copywriting framework'
            },
            {
                'name': 'Virtual Business Coaching',
                'description': 'Coach entrepreneurs on specific topics (marketing, sales, finances, productivity) based on your expertise.',
                'startup_cost': '$500-1500',
                'timeline': '1-2 months setup',
                'revenue_potential': '$2000-10000/month',
                'skills_needed': 'Deep expertise in a niche, coaching skills, sales'
            }
        ],
        'creator': [
            {
                'name': 'YouTube Channel (Monetized)',
                'description': 'Create consistent video content on a niche topic. Monetize through ads, sponsorships, affiliates, products.',
                'startup_cost': '$200-500',
                'timeline': '3-6 months to monetization',
                'revenue_potential': '$500-5000+/month',
                'skills_needed': 'Video production, editing, SEO, audience engagement, consistency'
            },
            {
                'name': 'Blog with Affiliate Marketing',
                'description': 'Build a content-rich blog and monetize through affiliate partnerships and sponsorships.',
                'startup_cost': '$100-300',
                'timeline': '4-6 months to revenue',
                'revenue_potential': '$500-3000/month',
                'skills_needed': 'SEO, copywriting, audience research, content marketing'
            },
            {
                'name': 'Podcast with Sponsorships',
                'description': 'Start a podcast on niche topic. Monetize through sponsorships, Patreon, and affiliate links.',
                'startup_cost': '$300-500',
                'timeline': '2-3 months to sponsorship',
                'revenue_potential': '$500-5000/month',
                'skills_needed': 'Audio production, interviewing, marketing, consistency'
            },
            {
                'name': 'Membership Community',
                'description': 'Build exclusive community for your audience with premium content, exclusive access, and community features.',
                'startup_cost': '$500-2000',
                'timeline': '3-4 months setup',
                'revenue_potential': '$1000-10000/month',
                'skills_needed': 'Community management, content creation, platform knowledge'
            },
            {
                'name': 'Online Course Creation',
                'description': 'Package your expertise into a structured course. Sell on Udemy, Teachable, or your own platform.',
                'startup_cost': '$300-1000',
                'timeline': '2-3 months production',
                'revenue_potential': '$1000-5000/month',
                'skills_needed': 'Subject matter expertise, instructional design, video production'
            }
        ],
        'education': [
            {
                'name': 'Online Tutoring Service',
                'description': 'Teach students online in your subject expertise. Use platforms like Wyzant, Chegg, or build your own client base.',
                'startup_cost': '$100-500',
                'timeline': 'Immediate',
                'revenue_potential': '$1000-5000/month',
                'skills_needed': 'Subject expertise, teaching ability, communication'
            },
            {
                'name': 'Skill-Based Course Platform',
                'description': 'Create courses teaching practical skills (coding, design, business, languages) on multiple platforms.',
                'startup_cost': '$300-1000',
                'timeline': '3-4 months',
                'revenue_potential': '$2000-10000+/month',
                'skills_needed': 'Teaching ability, curriculum design, platform knowledge'
            },
            {
                'name': 'Educational Content Creator',
                'description': 'Create educational YouTube videos, TikToks, or Instagram reels on complex topics explained simply.',
                'startup_cost': '$200-500',
                'timeline': '2-4 months to revenue',
                'revenue_potential': '$500-5000+/month',
                'skills_needed': 'Subject expertise, video editing, simplification skills'
            },
            {
                'name': 'Test Prep Tutoring',
                'description': 'Specialize in SAT, ACT, GMAT, GRE, or other certification exam prep. High margins, willing students.',
                'startup_cost': '$200-500',
                'timeline': '1-2 months setup',
                'revenue_potential': '$2000-8000/month',
                'skills_needed': 'Deep exam knowledge, teaching ability, organization'
            },
            {
                'name': 'Language Teaching Service',
                'description': 'Teach languages online to students globally. Use VIPKID, iTalki, or build your own client base.',
                'startup_cost': '$100-300',
                'timeline': 'Immediate',
                'revenue_potential': '$1000-5000+/month',
                'skills_needed': 'Language fluency, teaching ability, patience'
            }
        ],
        'health': [
            {
                'name': 'Fitness Coaching (Online)',
                'description': 'Offer personalized fitness coaching, meal planning, and workout programs to clients online.',
                'startup_cost': '$200-500',
                'timeline': 'Immediate',
                'revenue_potential': '$1000-5000/month',
                'skills_needed': 'Fitness knowledge, coaching ability, motivation skills'
            },
            {
                'name': 'Nutrition Coaching',
                'description': 'Provide personalized nutrition guidance and meal planning. Build recurring client base.',
                'startup_cost': '$300-1000',
                'timeline': '1-2 months',
                'revenue_potential': '$1000-5000/month',
                'skills_needed': 'Nutrition knowledge, counseling skills, sensitivity'
            },
            {
                'name': 'Mental Health Support App/Platform',
                'description': 'Build a community or app providing mental health resources, peer support, and guided meditation.',
                'startup_cost': '$2000-5000',
                'timeline': '4-6 months',
                'revenue_potential': '$1000-10000+/month',
                'skills_needed': 'App development, mental health knowledge, community building'
            },
            {
                'name': 'Wellness Program Consulting',
                'description': 'Help companies implement employee wellness programs. Consulting + recurring revenue model.',
                'startup_cost': '$500-1500',
                'timeline': '2-3 months',
                'revenue_potential': '$2000-10000/month',
                'skills_needed': 'Wellness knowledge, consulting skills, HR understanding'
            },
            {
                'name': 'Sleep Coaching',
                'description': 'Help clients improve sleep quality through personalized coaching and habit formation.',
                'startup_cost': '$200-500',
                'timeline': 'Immediate',
                'revenue_potential': '$1500-6000/month',
                'skills_needed': 'Sleep science knowledge, coaching ability, patience'
            }
        ],
        'sustainability': [
            {
                'name': 'Eco-Friendly Product Store',
                'description': 'Sell sustainable products (reusable, organic, biodegradable) to environmentally conscious consumers.',
                'startup_cost': '$1000-3000',
                'timeline': '4-6 weeks',
                'revenue_potential': '$2000-10000/month',
                'skills_needed': 'Sustainability knowledge, sourcing, marketing, e-commerce'
            },
            {
                'name': 'Sustainability Consulting',
                'description': 'Help businesses reduce environmental impact. Audit, strategy, implementation, and carbon offset.',
                'startup_cost': '$500-1500',
                'timeline': '2-3 months',
                'revenue_potential': '$2000-10000/month',
                'skills_needed': 'Sustainability knowledge, business analysis, communication'
            },
            {
                'name': 'Green Energy Advisory',
                'description': 'Help businesses and homeowners transition to renewable energy. Partner with providers for commissions.',
                'startup_cost': '$500-1500',
                'timeline': '2-3 months',
                'revenue_potential': '$1500-8000/month',
                'skills_needed': 'Energy knowledge, sales, relationship building'
            },
            {
                'name': 'Waste Reduction Consultation',
                'description': 'Help restaurants, hotels, and retailers reduce waste and save money. Win-win proposition.',
                'startup_cost': '$300-1000',
                'timeline': '1-2 months',
                'revenue_potential': '$1500-6000/month',
                'skills_needed': 'Operations understanding, sustainability knowledge, analysis'
            },
            {
                'name': 'Carbon Offset Platform',
                'description': 'Build a marketplace connecting businesses wanting to offset carbon with offset projects.',
                'startup_cost': '$3000-8000',
                'timeline': '4-6 months',
                'revenue_potential': '$2000-15000+/month',
                'skills_needed': 'Full-stack development, sustainability knowledge, business modeling'
            }
        ],
        'general': [
            {
                'name': 'Digital Marketing Agency',
                'description': 'Offer comprehensive digital marketing (SEO, PPC, social media, content) to small businesses.',
                'startup_cost': '$1000-3000',
                'timeline': '3-4 weeks',
                'revenue_potential': '$2000-10000/month per client',
                'skills_needed': 'Marketing fundamentals, analytics, copywriting, various platforms'
            },
            {
                'name': 'Graphic Design Service',
                'description': 'Provide design services for branding, marketing materials, and digital assets.',
                'startup_cost': '$500-1500',
                'timeline': '2-3 weeks',
                'revenue_potential': '$1000-5000/month',
                'skills_needed': 'Design software (Figma, Illustrator), creativity, client communication'
            },
            {
                'name': 'Project Management Consulting',
                'description': 'Help teams improve project delivery using agile, Scrum, or other methodologies.',
                'startup_cost': '$500-1500',
                'timeline': '1-2 months',
                'revenue_potential': '$2000-10000/month',
                'skills_needed': 'Project management experience, certifications, consulting skills'
            },
            {
                'name': 'Niche Blog + Multiple Revenue Streams',
                'description': 'Build authority blog with ads, affiliates, sponsorships, and digital products.',
                'startup_cost': '$100-300',
                'timeline': '4-6 months to revenue',
                'revenue_potential': '$1000-10000+/month',
                'skills_needed': 'SEO, copywriting, product creation, audience building'
            },
            {
                'name': 'Email Newsletter Business',
                'description': 'Build engaged email list in niche topic and monetize through sponsorships, affiliates, products.',
                'startup_cost': '$200-500',
                'timeline': '2-3 months',
                'revenue_potential': '$1000-10000+/month',
                'skills_needed': 'Copywriting, audience building, email marketing, relationship building'
            }
        ]
    }
    
    # Get ideas for detected industry + general ideas
    ideas = business_ideas.get(detected_industry, []) + business_ideas.get('general', [])[:2]

    # Currency conversion helpers were moved to module-level functions

    
    # Check if user is asking for location-based ideas
    location_keywords = [
        'location', 'local', 'neighborhood', 'region', 'area', 'city', 'town',
        'offline', 'physical', 'brick and mortar', 'storefront', 'brick-and-mortar',
        'geo', 'geographic', 'based on location'
    ]
    
    wants_location_ideas = any(keyword in message_lower for keyword in location_keywords)
    
    # Multi-state district detection (5 major Indian states)
    all_districts = {
        # KARNATAKA (21 districts)
        'bangalore': {'state': 'karnataka', 'keywords': ['bangalore', 'bengaluru']},
        'mysore': {'state': 'karnataka', 'keywords': ['mysore', 'mysuru']},
        'hubli': {'state': 'karnataka', 'keywords': ['hubli']},
        'belgaum': {'state': 'karnataka', 'keywords': ['belgaum', 'belagavi']},
        'mangalore': {'state': 'karnataka', 'keywords': ['mangalore', 'mangaluru']},
        'hassan': {'state': 'karnataka', 'keywords': ['hassan']},
        'shimoga': {'state': 'karnataka', 'keywords': ['shimoga']},
        'gulbarga': {'state': 'karnataka', 'keywords': ['gulbarga']},
        'tumkur': {'state': 'karnataka', 'keywords': ['tumkur']},
        'davangere': {'state': 'karnataka', 'keywords': ['davangere']},
        'kolar': {'state': 'karnataka', 'keywords': ['kolar']},
        
        # TAMIL NADU (15 districts - major ones)
        'chennai': {'state': 'tamil nadu', 'keywords': ['chennai', 'madras']},
        'coimbatore': {'state': 'tamil nadu', 'keywords': ['coimbatore', 'kovai']},
        'salem': {'state': 'tamil nadu', 'keywords': ['salem']},
        'madurai': {'state': 'tamil nadu', 'keywords': ['madurai']},
        'tiruchirappalli': {'state': 'tamil nadu', 'keywords': ['tiruchirappalli', 'trichy']},
        
        # MAHARASHTRA (16 districts - major ones)
        'mumbai': {'state': 'maharashtra', 'keywords': ['mumbai', 'bombay']},
        'pune': {'state': 'maharashtra', 'keywords': ['pune', 'poona']},
        'nashik': {'state': 'maharashtra', 'keywords': ['nashik']},
        'aurangabad': {'state': 'maharashtra', 'keywords': ['aurangabad']},
        'nagpur': {'state': 'maharashtra', 'keywords': ['nagpur']},
        
        # GUJARAT (20 districts - major ones)
        'ahmedabad': {'state': 'gujarat', 'keywords': ['ahmedabad', 'amdavad']},
        'surat': {'state': 'gujarat', 'keywords': ['surat']},
        'vadodara': {'state': 'gujarat', 'keywords': ['vadodara', 'baroda']},
        'rajkot': {'state': 'gujarat', 'keywords': ['rajkot']},
        
        # TELANGANA (16 districts - major ones)
        'hyderabad': {'state': 'telangana', 'keywords': ['hyderabad']},
        'warangal': {'state': 'telangana', 'keywords': ['warangal']},
        'karimnagar': {'state': 'telangana', 'keywords': ['karimnagar']},
        'khammam': {'state': 'telangana', 'keywords': ['khammam']},
    }
    
    detected_district = None
    detected_state = None
    for district, info in all_districts.items():
        if any(keyword in message_lower for keyword in info['keywords']):
            detected_district = district
            detected_state = info['state']
            break
    
    # Add location-based ideas if requested or if district detected
    if wants_location_ideas or detected_district:
        # If state district detected, provide state-specific ideas
        if detected_district and detected_state:
            location_based_ideas = generate_state_district_ideas(detected_state, detected_district)
        else:
            location_based_ideas = [
                {
                    'name': 'Local Digital Marketing Agency',
                    'description': 'Manage Google Business, Facebook, local SEO for nearby restaurants, salons, plumbers, etc. High demand, recurring revenue.',
                    'location_benefit': 'Service local businesses in your area who need online presence',
                    'startup_cost': '$500-1500',
                    'timeline': '3-4 weeks',
                    'revenue_potential': '$1500-5000/month per client',
                    'skills_needed': 'Local SEO, Google Business, Facebook Ads, community knowledge'
                },
                {
                    'name': 'Home Services Business (Cleaning, Landscaping, etc.)',
                    'description': 'Offer specialized home services to local customers. Outsource workers and scale. High margins.',
                    'location_benefit': 'Leverage local demand and build reputation in your community',
                    'startup_cost': '$1000-3000',
                    'timeline': '2-4 weeks',
                    'revenue_potential': '$3000-15000/month',
                    'skills_needed': 'Sales, customer service, operations management, scheduling'
                },
                {
                    'name': 'Virtual Assistant for Local Businesses',
                    'description': 'Provide administrative support specifically for local service businesses (contractors, salons, clinics).',
                    'location_benefit': 'Network with local business owners and understand their specific needs',
                    'startup_cost': '$200-500',
                    'timeline': 'Immediate',
                    'revenue_potential': '$2000-8000/month',
                    'skills_needed': 'Organization, communication, QuickBooks, scheduling software'
                },
                {
                    'name': 'Local Tour Guide or Experience Business',
                    'description': 'Create unique local experiences - food tours, hiking guides, historical tours, adventure activities.',
                    'location_benefit': 'Use your local knowledge and unique attractions in your area',
                    'startup_cost': '$500-1500',
                    'timeline': '4-6 weeks',
                    'revenue_potential': '$2000-10000/month',
                    'skills_needed': 'Local knowledge, communication, marketing, customer service'
                },
                {
                    'name': 'Local E-commerce (Regional Products)',
                    'description': 'Sell local/regional products online - crafts, food, artisan goods from your area.',
                    'location_benefit': 'Tap into unique local products and stories to sell regionally/nationally',
                    'startup_cost': '$1000-2500',
                    'timeline': '4-8 weeks',
                    'revenue_potential': '$2000-10000+/month',
                    'skills_needed': 'E-commerce, sourcing, storytelling, digital marketing'
                },
                {
                    'name': 'Personal Training / Group Fitness Classes (Local)',
                    'description': 'Offer fitness classes in local studios, parks, or online. Build local community.',
                    'location_benefit': 'Build strong local client base through word-of-mouth and community events',
                    'startup_cost': '$500-1500',
                    'timeline': '2-4 weeks',
                    'revenue_potential': '$3000-10000/month',
                    'skills_needed': 'Fitness certification, motivation, business management, marketing'
                },
                {
                    'name': 'Pet Care Services (Local)',
                    'description': 'Dog walking, pet sitting, grooming, training in your neighborhood. High demand, recurring.',
                    'location_benefit': 'Service pet owners in your area who value local trusted providers',
                    'startup_cost': '$300-1000',
                    'timeline': '2-3 weeks',
                    'revenue_potential': '$2000-8000/month',
                    'skills_needed': 'Animal handling, customer service, scheduling, marketing'
                },
                {
                    'name': 'Handyman / Home Repair Business',
                    'description': 'Fix and maintain homes in your local area. Start solo, hire contractors as you grow.',
                    'location_benefit': 'Build reputation locally with repeat customers and referrals',
                    'startup_cost': '$1000-2500',
                    'timeline': '1-2 weeks',
                    'revenue_potential': '$4000-12000/month',
                    'skills_needed': 'Technical skills, customer service, sales, business management'
                },
                {
                    'name': 'Event Planning / Party Planning (Local)',
                    'description': 'Plan events, parties, corporate events, weddings for local clients. Customize for community.',
                    'location_benefit': 'Deep understanding of local venues, vendors, and customer preferences',
                    'startup_cost': '$500-1500',
                    'timeline': '4-6 weeks',
                    'revenue_potential': '$3000-15000+/month',
                    'skills_needed': 'Organization, negotiation, creativity, vendor relationships'
                },
                {
                    'name': 'Language Tutoring (In-Person + Online)',
                    'description': 'Teach languages to local students and online. Start local, expand globally.',
                    'location_benefit': 'Build reputation locally while also reaching global students online',
                    'startup_cost': '$200-500',
                    'timeline': 'Immediate',
                    'revenue_potential': '$2000-8000/month',
                    'skills_needed': 'Language fluency, teaching ability, online platform skills'
                }
            ]
        
        ideas = location_based_ideas

    # If the user explicitly asked for ideas (plural) — return an expanded list
    idea_triggers = ['idea', 'ideas', 'more idea', 'more ideas', 'give me ideas', 'more suggestions']
    if any(trig in message_lower for trig in idea_triggers):
        # Build a pool of base ideas from all industries + location based + state/district ideas
        pool = []
        for lst in business_ideas.values():
            pool.extend(lst)
        # include general and any detected location ideas
        if 'general' in business_ideas:
            pool.extend(business_ideas.get('general', []))
        if 'ideas' in locals() and isinstance(ideas, list):
            pool.extend(ideas)

        # include state/district specific ideas if district detected
        if detected_district and detected_state:
            try:
                sd = generate_state_district_ideas(detected_state, detected_district)
                if sd:
                    pool.extend(sd)
            except Exception:
                pass

        # include Karnataka district ideas as fallback
        try:
            pool.extend(generate_karnataka_district_ideas(detected_district or ''))
        except Exception:
            pass

        # Deduplicate by name
        seen = set()
        unique = []
        for item in pool:
            name = item.get('name', '').strip().lower()
            if not name:
                continue
            if name in seen:
                continue
            seen.add(name)
            unique.append(item.copy())

        # If we already have 30 or more, return first 30 (convert USD->INR)
        if len(unique) >= 30:
            return _convert_usd_to_inr_in_list(unique[:30])

        # Otherwise, generate variations to reach 30 ideas
        variants = []
        variant_tags = [
            ' (Subscription Model)',
            ' (Low-Cost / Budget)',
            ' (Premium / High-Ticket)',
            ' (Online-First)',
            ' (Offline / Local)',
            ' (B2B Focus)',
            ' (Direct-to-Consumer)',
            ' (Franchise-Ready)',
            ' (SaaS Variant)',
            ' (Marketplace Approach)'
        ]

        i = 0
        while len(unique) + len(variants) < 30 and i < len(unique) * len(variant_tags) + 50:
            base = unique[i % max(1, len(unique))]
            tag = variant_tags[(i // max(1, len(unique))) % len(variant_tags)]
            new = base.copy()
            # Make name unique by adding a variant tag
            new['name'] = f"{base.get('name','Idea')}{tag}"
            # Slightly tweak the description and numbers to appear distinct
            new['description'] = base.get('description', '') + f" This variant targets a different market segment: {tag.strip(' ()')}."
            # Tweak startup cost and revenue a bit
            sc = base.get('startup_cost', '$1000-5000')
            new['startup_cost'] = sc
            rp = base.get('revenue_potential', '$2000-10000/month')
            new['revenue_potential'] = rp
            # Ensure skills are present
            new['skills_needed'] = base.get('skills_needed', 'General business skills')
            variants.append(new)
            i += 1

        expanded = unique + variants

        # Add a short unique suggestion for each idea to make them actionable
        for idx, item in enumerate(expanded):
            if 'suggestion' not in item or not item.get('suggestion'):
                base_name = item.get('name', 'This idea')
                suggestion = f"Start by validating demand: talk to 10 potential customers for '{base_name}' and collect feedback."
                # rotate suggestions to make them feel different
                variant_actions = [
                    'Create a one-page landing page and run small ads to measure interest.',
                    'Build a basic prototype/MVP and get 5 early adopters.',
                    'Research local competitors and identify a 10% price or feature advantage.',
                    'Offer a pilot or free trial to your first customers to collect testimonials.',
                    'Partner with one local business or influencer to reach initial users.',
                    'Start with a low-cost subscription offer to validate recurring revenue.',
                    'List the service on local marketplaces and measure inbound leads.',
                    'Reach out to 5 industry forums or groups and ask for feedback on your idea.',
                    'Create a short explainer video and share it with targeted communities.',
                    'Prototype the core feature and run usability tests with 3 users.'
                ]
                action = variant_actions[idx % len(variant_actions)]
                item['suggestion'] = suggestion + ' ' + action

        # Trim to 30 and convert USD->INR
        return _convert_usd_to_inr_in_list(expanded[:30])

    # Ensure returned ideas have a suggestion field as well
    for idx, item in enumerate(ideas):
        if 'suggestion' not in item or not item.get('suggestion'):
            variant_actions = [
                'Create a landing page and run small ads to measure interest.',
                'Build a quick prototype and test with 5 users.',
                'Reach out to local businesses for pilot partnerships.',
                'Offer a limited-time discount to attract first customers.',
                'Document the top 3 competitors and find a differentiation angle.'
            ]
            item['suggestion'] = variant_actions[idx % len(variant_actions)]

    # Convert remaining idea currency fields before returning
    return _convert_usd_to_inr_in_list(ideas)

# ============================================================================
# ADVANCED FEATURES: MARKET DATA, COMPETITORS, SUCCESS STORIES
# ============================================================================

def get_market_data(idea_name, state, district):
    """Get detailed market data for a business idea"""
    market_database = {
        # TAMIL NADU - CHENNAI
        ('it staffing & recruitment', 'tamil nadu', 'chennai'): {
            'market_size': '$2.5B',
            'market_growth': '15% annually',
            'market_demand': 'Very High - 50000+ tech companies in Chennai',
            'seasonality': 'Consistent year-round demand',
            'saturation_level': 'Moderate - Growing but competitive',
            'entry_barriers': 'Medium - Requires network and credibility',
            'profit_margins': '25-35% per placement',
            'customer_acquisition': 'LinkedIn, job portals, corporate partnerships'
        },
        ('textile manufacturing/export', 'tamil nadu', 'coimbatore'): {
            'market_size': '$15B',
            'market_growth': '8-10% annually',
            'market_demand': 'High - Global textile demand',
            'seasonality': 'Year-round with seasonal peaks',
            'saturation_level': 'High - Many competitors',
            'entry_barriers': 'Medium - Capital and infrastructure needed',
            'profit_margins': '15-25% for high-end textiles',
            'customer_acquisition': 'B2B trade shows, export agencies, direct sales'
        },
        # MAHARASHTRA - MUMBAI
        ('financial advisory services', 'maharashtra', 'mumbai'): {
            'market_size': '$50B',
            'market_growth': '18% annually',
            'market_demand': 'Very High - Millions of investors',
            'seasonality': 'Tax season peaks (March, July)',
            'saturation_level': 'High - Many advisors available',
            'entry_barriers': 'High - Regulations and certifications needed',
            'profit_margins': '20-40% on advisory fees',
            'customer_acquisition': 'LinkedIn, referrals, seminars, social media'
        },
        ('wine & vineyard business', 'maharashtra', 'nashik'): {
            'market_size': '$500M',
            'market_growth': '12% annually',
            'market_demand': 'High - Growing wine consumption in India',
            'seasonality': 'Strong in Oct-Dec (festivals), weak in Jun-Jul',
            'saturation_level': 'Low-Medium - Only 20+ major wineries',
            'entry_barriers': 'Very High - Licensing, land, capital required',
            'profit_margins': '35-50% on premium wines',
            'customer_acquisition': 'Direct sales, wine bars, online, corporate events'
        },
        # GUJARAT - SURAT
        ('diamond polishing & trading', 'gujarat', 'surat'): {
            'market_size': '$40B',
            'market_growth': '5-8% annually',
            'market_demand': 'High - Global diamond demand',
            'seasonality': 'Year-round, peaks in wedding season',
            'saturation_level': 'Very High - 95% of world diamonds polished here',
            'entry_barriers': 'Very High - Capital, expertise, connections required',
            'profit_margins': '10-20% on polishing, 25-40% on trading',
            'customer_acquisition': 'Industry networks, direct B2B, auctions'
        },
        # TELANGANA - HYDERABAD
        ('it services & staffing', 'telangana', 'hyderabad'): {
            'market_size': '$10B',
            'market_growth': '20% annually',
            'market_demand': 'Very High - 3rd largest IT hub in India',
            'seasonality': 'Consistent demand',
            'saturation_level': 'Moderate - Many companies but growing demand',
            'entry_barriers': 'Medium - Network and credentials needed',
            'profit_margins': '30-40% per placement',
            'customer_acquisition': 'LinkedIn, job portals, corporate partnerships, events'
        },
        ('pharma/biotech company', 'telangana', 'hyderabad'): {
            'market_size': '$15B',
            'market_growth': '10-12% annually',
            'market_demand': 'High - Pharma capital of India',
            'seasonality': 'Year-round demand',
            'saturation_level': 'Moderate - Many competitors',
            'entry_barriers': 'Very High - Regulatory, capital, expertise required',
            'profit_margins': '40-60% on finished products',
            'customer_acquisition': 'B2B partnerships, distributors, hospitals'
        },
        # KARNATAKA - BANGALORE
        ('it services & staffing', 'karnataka', 'bangalore'): {
            'market_size': '$30B',
            'market_growth': '18% annually',
            'market_demand': 'Very High - 60000+ tech companies',
            'seasonality': 'Consistent year-round',
            'saturation_level': 'High - Very competitive',
            'entry_barriers': 'Medium - Requires credibility and network',
            'profit_margins': '25-40% per placement',
            'customer_acquisition': 'LinkedIn, tech events, corporate partnerships'
        }
    }
    
    key = (idea_name.lower(), state.lower(), district.lower())
    entry = market_database.get(key)
    if entry:
        import copy
        return _convert_currency_in_dict(copy.deepcopy(entry))
    return market_database.get(key, {
        'market_size': 'Data unavailable',
        'market_growth': 'Research required',
        'market_demand': 'Research required',
        'seasonality': 'Varies by location',
        'saturation_level': 'Research required',
        'entry_barriers': 'Research required',
        'profit_margins': 'Varies widely',
        'customer_acquisition': 'Use local networks and online channels'
    })


@app.route('/api/business-ideas', methods=['GET', 'POST'])
def api_business_ideas():
    """Return business ideas as JSON with pagination support.
    Accepts: JSON body with { "message": "..." } or query params: ?q=...&count=30&page=1
    """
    try:
        # determine message
        if request.method == 'POST' and request.is_json:
            payload = request.get_json()
            message = payload.get('message', '')
        else:
            message = request.args.get('q', request.args.get('query', ''))

        # pagination params
        try:
            count = int(request.args.get('count', request.args.get('limit', 30)))
        except Exception:
            count = 30
        try:
            page = int(request.args.get('page', 1))
        except Exception:
            page = 1

        if not message:
            return jsonify({'error': 'Missing query/message'}), 400

        ideas = generate_business_ideas(message)
        total = len(ideas)
        # support slicing/pagination
        if count <= 0:
            count = 30
        start = (page - 1) * count
        end = start + count
        page_items = ideas[start:end]

        return jsonify({
            'total': total,
            'page': page,
            'count': len(page_items),
            'per_page': count,
            'ideas': page_items
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_competitors(idea_name, state, district):
    """Get competitor analysis for a business idea"""
    competitor_database = {
        # TAMIL NADU - CHENNAI
        ('it staffing & recruitment', 'tamil nadu', 'chennai'): [
            {'name': 'TeamLease', 'market_share': 'Large', 'strength': 'Scale and brand', 'weakness': 'Less personal service'},
            {'name': 'Adecco', 'market_share': 'Large', 'strength': 'International reach', 'weakness': 'Higher costs'},
            {'name': 'Local recruiters', 'market_share': 'Medium', 'strength': 'Personal touch', 'weakness': 'Limited resources'},
            {'name': 'LinkedIn Recruiting', 'market_share': 'Growing', 'strength': 'Direct access', 'weakness': 'No vetting service'}
        ],
        ('financial advisory services', 'maharashtra', 'mumbai'): [
            {'name': 'Motilal Oswal', 'market_share': 'Large', 'strength': 'Brand reputation', 'weakness': 'High fees'},
            {'name': 'ICICI Direct', 'market_share': 'Large', 'strength': 'Tech platform', 'weakness': 'Less personal'},
            {'name': 'Independent advisors', 'market_share': 'Medium', 'strength': 'Personal service', 'weakness': 'Limited resources'},
            {'name': 'Robo-advisors', 'market_share': 'Growing', 'strength': 'Low cost', 'weakness': 'No human touch'}
        ],
        ('wine & vineyard business', 'maharashtra', 'nashik'): [
            {'name': 'Sula Vineyards', 'market_share': 'Largest', 'strength': 'Scale & distribution', 'weakness': 'Limited innovation'},
            {'name': 'York Winery', 'market_share': 'Large', 'strength': 'Premium positioning', 'weakness': 'High price point'},
            {'name': 'Local wineries', 'market_share': 'Medium', 'strength': 'Quality & artisanal', 'weakness': 'Limited distribution'},
            {'name': 'International wines', 'market_share': 'Growing', 'strength': 'Global brands', 'weakness': 'Import duties'}
        ],
        ('diamond polishing & trading', 'gujarat', 'surat'): [
            {'name': 'Jain Studios', 'market_share': 'Large', 'strength': 'Scale and quality', 'weakness': 'Less flexible'},
            {'name': 'Gem Trading Co', 'market_share': 'Large', 'strength': 'Experience', 'weakness': 'Traditional methods'},
            {'name': 'Individual polishers', 'market_share': 'High', 'strength': 'Artisanal quality', 'weakness': 'Limited capital'},
            {'name': 'International buyers', 'market_share': 'Growing', 'strength': 'Direct purchase', 'weakness': 'Quality variance'}
        ],
        ('it services & staffing', 'telangana', 'hyderabad'): [
            {'name': 'TCS', 'market_share': 'Largest', 'strength': 'Scale and resources', 'weakness': 'Bureaucratic'},
            {'name': 'Infosys', 'market_share': 'Large', 'strength': 'Global reach', 'weakness': 'High cost'},
            {'name': 'HCL', 'market_share': 'Large', 'strength': 'Tech expertise', 'weakness': 'Large only'},
            {'name': 'Small recruiters', 'market_share': 'Growing', 'strength': 'Personal service', 'weakness': 'Limited network'}
        ],
        ('it services & staffing', 'karnataka', 'bangalore'): [
            {'name': 'Accenture', 'market_share': 'Very Large', 'strength': 'Scale', 'weakness': 'Less personal'},
            {'name': 'Cognizant', 'market_share': 'Very Large', 'strength': 'Global network', 'weakness': 'High costs'},
            {'name': 'Wipro', 'market_share': 'Very Large', 'strength': 'Local presence', 'weakness': 'Less flexible'},
            {'name': 'Startup recruiters', 'market_share': 'Growing', 'strength': 'Agile', 'weakness': 'Limited budget'}
        ]
    }
    
    key = (idea_name.lower(), state.lower(), district.lower())
    return competitor_database.get(key, [
        {'name': 'Research required', 'market_share': 'Unknown', 'strength': 'Depends on location', 'weakness': 'Analyze local market'}
    ])

def get_success_stories(idea_name, state, district):
    """Get success stories and case studies for a business idea"""
    success_stories_database = {
        ('it staffing & recruitment', 'tamil nadu', 'chennai'): [
            {
                'title': 'Ramesh\'s Recruitment Agency - From $0 to $50K/month',
                'entrepreneur': 'Ramesh Kumar',
                'timeline': '18 months',
                'initial_investment': '$8,000',
                'current_revenue': '$50,000+/month',
                'key_success_factors': [
                    'Built strong relationships with 20 IT companies',
                    'Focused on high-value placements ($30K+ salaries)',
                    'Used LinkedIn for sourcing and networking',
                    'Maintained 95%+ placement success rate'
                ],
                'lessons_learned': 'Quality over quantity. Better to place 2 high-value candidates than 10 low-value ones.',
                'challenges_faced': 'Initial rejection from companies, took 6 months to get first placement'
            },
            {
                'title': 'Tech Recruitment Network - Built in Chennai',
                'entrepreneur': 'Priya & Vikram',
                'timeline': '24 months',
                'initial_investment': '$12,000',
                'current_revenue': '$80,000+/month',
                'key_success_factors': [
                    'Started with network from previous IT jobs',
                    'Created specialized niche for data science roles',
                    'Built reputation through consistent placements',
                    'Expanded to 3 full-time team members'
                ],
                'lessons_learned': 'Specialization works better than generalization. Target a specific niche and become expert.',
                'challenges_faced': 'High competition, candidates ghosting, company changing requirements'
            }
        ],
        ('wine & vineyard business', 'maharashtra', 'nashik'): [
            {
                'title': 'Premium Wine Vineyard - From Land to Profit',
                'entrepreneur': 'Anil Deshmukh',
                'timeline': '36 months',
                'initial_investment': '$150,000',
                'current_revenue': '$200,000+/month',
                'key_success_factors': [
                    'Invested in premium grape varieties',
                    'Direct-to-consumer sales model',
                    'Agri-tourism (vineyard tours, tastings)',
                    'Built brand around quality and sustainability'
                ],
                'lessons_learned': 'Wine business requires patience. Building reputation takes 2-3 years but pays off.',
                'challenges_faced': 'Weather risks, long maturation period, regulatory compliance'
            },
            {
                'title': 'Wine Export Business - Made in Nashik',
                'entrepreneur': 'Rajesh Sharma',
                'timeline': '24 months',
                'initial_investment': '$80,000',
                'current_revenue': '$120,000+/month',
                'key_success_factors': [
                    'Partnered with local vineyards for supply',
                    'Focused on export to UK, US markets',
                    'Built brand story around Nashik heritage',
                    'Used e-commerce and trade shows'
                ],
                'lessons_learned': 'Exports are high-margin but require export expertise and certifications.',
                'challenges_faced': 'International shipping costs, customs delays, quality consistency'
            }
        ],
        ('diamond polishing & trading', 'gujarat', 'surat'): [
            {
                'title': 'Diamond Polishing Workshop - Small Scale to Success',
                'entrepreneur': 'Jayesh Patel',
                'timeline': '30 months',
                'initial_investment': '$120,000',
                'current_revenue': '$300,000+/month',
                'key_success_factors': [
                    'Inherited polishing skills from family',
                    'Invested in modern cutting equipment',
                    'Built relationships with international buyers',
                    'Maintained exceptional quality standards'
                ],
                'lessons_learned': 'Quality creates reputation. In diamonds, one bad stone can hurt your entire business.',
                'challenges_faced': 'Capital for raw diamonds, volatile diamond prices, skilled labor shortage'
            },
            {
                'title': 'Diamond Trading Business - Leveraging Surat Ecosystem',
                'entrepreneur': 'Mukesh Jain',
                'timeline': '18 months',
                'initial_investment': '$200,000',
                'current_revenue': '$400,000+/month',
                'key_success_factors': [
                    'Started by trading between polishers and buyers',
                    'Built network of 50+ suppliers',
                    'Used Surat\'s diamond exchange for trading',
                    'Specialized in certification and documentation'
                ],
                'lessons_learned': 'Trading works well when you have deep market knowledge and trusted relationships.',
                'challenges_faced': 'Trust in high-value transactions, market volatility, competition'
            }
        ],
        ('it services & staffing', 'karnataka', 'bangalore'): [
            {
                'title': 'IT Training Academy - From Nothing to 500+ Students',
                'entrepreneur': 'Vivek Sharma',
                'timeline': '24 months',
                'initial_investment': '$25,000',
                'current_revenue': '$60,000+/month',
                'key_success_factors': [
                    'Offered specialized Python + Data Science courses',
                    'Built placement partnerships with 30+ companies',
                    'Used online + in-person hybrid model',
                    'Maintained 85%+ placement rate'
                ],
                'lessons_learned': 'Training works when you guarantee placements. Companies will pay premium for trained talent.',
                'challenges_faced': 'Student quality variation, market saturation in some courses, teaching consistency'
            }
        ],
        ('it services & staffing', 'telangana', 'hyderabad'): [
            {
                'title': 'Pharma Staffing - Specialized Niche',
                'entrepreneur': 'Dr. Srinivas',
                'timeline': '20 months',
                'initial_investment': '$15,000',
                'current_revenue': '$70,000+/month',
                'key_success_factors': [
                    'Focused exclusively on pharma companies',
                    'Deep knowledge of pharma regulations',
                    'Built relationships with all major pharma firms',
                    'Offered regulatory compliance training'
                ],
                'lessons_learned': 'Specialization in regulated industries pays premium rates.',
                'challenges_faced': 'High qualification requirements, regulatory knowledge needed, smaller market'
            }
        ]
    }
    
    key = (idea_name.lower(), state.lower(), district.lower())
    return success_stories_database.get(key, [
        {
            'title': 'Case studies coming soon for your location',
            'entrepreneur': 'Researching local success stories...',
            'timeline': 'Variable',
            'initial_investment': 'Varies',
            'current_revenue': 'Varies',
            'key_success_factors': ['Research local entrepreneurs', 'Network with business communities', 'Interview successful founders'],
            'lessons_learned': 'Every location has successful examples. Reach out to local chambers of commerce.',
            'challenges_faced': 'Finding case studies in your specific niche requires networking'
        }
    ])

@app.route('/api/market-data', methods=['POST'])
def api_get_market_data():
    """API endpoint for market data"""
    try:
        data = request.json
        idea_name = data.get('idea_name', '')
        state = data.get('state', '')
        district = data.get('district', '')
        
        market_data = get_market_data(idea_name, state, district)
        
        return jsonify({
            'success': True,
            'market_data': market_data,
            'idea': idea_name,
            'location': f'{district}, {state}'
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/competitors', methods=['POST'])
def api_get_competitors():
    """API endpoint for competitor analysis"""
    try:
        data = request.json
        idea_name = data.get('idea_name', '')
        state = data.get('state', '')
        district = data.get('district', '')
        
        competitors = get_competitors(idea_name, state, district)
        
        return jsonify({
            'success': True,
            'competitors': competitors,
            'idea': idea_name,
            'location': f'{district}, {state}'
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/success-stories', methods=['POST'])
def api_get_success_stories():
    """API endpoint for success stories"""
    try:
        data = request.json
        idea_name = data.get('idea_name', '')
        state = data.get('state', '')
        district = data.get('district', '')
        
        stories = get_success_stories(idea_name, state, district)
        
        return jsonify({
            'success': True,
            'success_stories': stories,
            'idea': idea_name,
            'location': f'{district}, {state}'
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/business-insights', methods=['POST'])
def api_get_business_insights():
    """API endpoint to get all advanced features: market data + competitors + success stories"""
    try:
        data = request.json
        idea_name = data.get('idea_name', '')
        state = data.get('state', '')
        district = data.get('district', '')
        
        insights = {
            'market_data': get_market_data(idea_name, state, district),
            'competitors': get_competitors(idea_name, state, district),
            'success_stories': get_success_stories(idea_name, state, district)
        }
        
        return jsonify({
            'success': True,
            'insights': insights,
            'idea': idea_name,
            'location': f'{district}, {state}'
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/business-ideas', methods=['POST'])
def api_get_business_ideas():
    """API endpoint to generate business ideas from a free-text message"""
    try:
        data = request.json or {}
        message = data.get('message', '')
        ideas = []
        if message:
            ideas = generate_business_ideas(message)

        return jsonify({
            'success': True,
            'ideas': ideas,
            'message': message
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Please provide username and password')
            return redirect(url_for('login'))

        if verify_user(username, password):
            session['username'] = username
            flash('Logged in successfully')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        email = request.form.get('email', '').strip()
        if not username or not password:
            flash('Please provide username and password')
            return redirect(url_for('register'))

        ok, err = create_user(username, password, email)
        if ok:
            session['username'] = username
            flash('Account created and logged in')
            return redirect(url_for('index'))
        else:
            flash(err or 'Registration failed')
            return redirect(url_for('register'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out')
    return redirect(url_for('index'))


@app.route('/api/save-chat', methods=['POST'])
def api_save_chat():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    username = session['username']
    data = request.json or {}
    message = data.get('message')
    response = data.get('response')
    meta = data.get('meta', {})

    if not message and not response:
        return jsonify({'success': False, 'error': 'No chat content provided'}), 400

    users = load_users()
    user = users.get(username)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    chat_entry = {
        'message': message,
        'response': response,
        'meta': meta,
        'timestamp': datetime.utcnow().isoformat()
    }
    user_chats = user.get('chats', [])
    user_chats.append(chat_entry)
    user['chats'] = user_chats
    users[username] = user
    if save_users(users):
        return jsonify({'success': True, 'chat': chat_entry})
    else:
        return jsonify({'success': False, 'error': 'Failed to save chat'}), 500


@app.route('/api/history', methods=['GET'])
def api_history():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    username = session['username']
    users = load_users()
    user = users.get(username)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    return jsonify({'success': True, 'chats': user.get('chats', [])})


@app.route('/extra/chat')
def extra_chat():
    """Serve the lightweight extra chat page"""
    return render_template('extra/chat.html')


def run_cli():
    """Simple interactive CLI mode that uses backend functions directly."""
    print("AI Business Advisor - CLI Mode")
    print("Type a question (e.g. 'Give me 5 business ideas for Chennai') or 'help' for commands. Type 'exit' to quit.")

    while True:
        try:
            user_input = input('\n> ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nExiting CLI.')
            break

        if not user_input:
            continue
        cmd = user_input.lower()

        if cmd in ('exit', 'quit'):
            print('Goodbye!')
            break
        if cmd in ('help', '?'):
            print('\nCommands:')
            print("  help                 Show this help")
            print("  exit                 Quit CLI")
            print("  ideas <text>         Generate business ideas for given text")
            print("  insights <idea>,<state>,<district>  Get market data, competitors, success stories")
            print("  predict <text>       Ask for a profit prediction or include numbers in your text")
            print("  chat <text>          General business advice chat (uses ML + LLM if available)")
            print("  health               Show loaded model & LLM status")
            continue

        if cmd == 'health':
            print('\nHealth:')
            print(f"  Models loaded: {best_model_name is not None}")
            print(f"  Available models: {list(models.keys())}")
            print(f"  LLM enabled: {llm_enabled}")
            continue

        # ideas command
        if cmd.startswith('ideas '):
            _, text = user_input.split(' ', 1)
            ideas = generate_business_ideas(text)
            print(f"\nGenerated {len(ideas)} ideas:\n")
            for i, idea in enumerate(ideas[:10], 1):
                print(f"{i}. {idea.get('name')}")
                print(f"   {idea.get('description')}")
                if idea.get('location_benefit'):
                    print(f"   Location: {idea.get('location_benefit')}")
                print(f"   Startup cost: {idea.get('startup_cost')}")
                print(f"   Timeline: {idea.get('timeline')}")
                print('')
            continue

        if cmd.startswith('insights '):
            try:
                _, params = user_input.split(' ', 1)
                parts = [p.strip() for p in params.split(',')]
                if len(parts) < 3:
                    print("Usage: insights <idea>,<state>,<district>")
                    continue
                idea_name, state, district = parts[0], parts[1], parts[2]
                insights = {
                    'market_data': get_market_data(idea_name, state, district),
                    'competitors': get_competitors(idea_name, state, district),
                    'success_stories': get_success_stories(idea_name, state, district)
                }
                print(json.dumps(insights, indent=2))
            except Exception as e:
                print(f"Error: {e}")
            continue

        if cmd.startswith('predict ') or cmd.startswith('chat ') or True:
            # Default: treat input as a chat message which may include prediction requests
            # Use generate_business_advice which integrates ML + LLM (if enabled)
            if cmd.startswith('predict '):
                _, text = user_input.split(' ', 1)
            elif cmd.startswith('chat '):
                _, text = user_input.split(' ', 1)
            else:
                text = user_input

            print('\nProcessing...')
            resp = generate_business_advice(text, conversation_history=None)
            if resp:
                print('\n' + resp)
            else:
                print('\nNo response generated.')
            continue

if __name__ == '__main__':
    # Load models on startup
    if load_models():
        # Check for Ollama
        check_ollama()
        # If '--cli' flag provided, run interactive CLI instead of starting Flask
        if '--cli' in sys.argv or 'cli' in sys.argv:
            run_cli()
        else:
            print("Starting Flask server...")
            print(f"Available ML models: {list(models.keys())}")
            print(f"LLM enabled: {llm_enabled}")
            app.run(debug=False, port=5000, use_reloader=False)
    else:
        print("Failed to load models. Please train models first by running train_models.py")
