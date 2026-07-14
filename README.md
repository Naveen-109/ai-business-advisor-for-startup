# 🤖 AI/ML Business Advisor Chatbot

> **Intelligent business predictions and strategic advice powered by Machine Learning and Local LLM**

A comprehensive AI-powered chatbot that combines ML models with Ollama LLM to provide profit forecasting, business ideas, and strategic advice for entrepreneurs across Karnataka's 31 districts.

---

## ✨ Features

### 🧠 **Machine Learning**
- **3 Trained Models**: Linear Regression, Random Forest, LSTM Neural Network
- **Profit Predictions**: Real-time forecasting with ensemble methods
- **Financial Analysis**: Margins, ratios, and benchmarks
- **1000+ Training Records**: Realistic business data

### 🤖 **AI-Powered Chat**
- **Ollama LLM Integration**: Natural language understanding
- **Context-Aware**: Maintains conversation flow
- **Intelligent Fallback**: Works with or without LLM
- **Strategic Advice**: Growth, optimization, and marketing strategies

### 🏛️ **Karnataka Districts**
- **31 Districts Covered**: Complete Karnataka coverage
- **10 Business Categories**: Agriculture to Technology
- **50+ Business Ideas**: Tailored to local resources
- **District-Specific**: Resources, culture, tourism data

### 📊 **Business Intelligence**
- **Market Analysis**: Size, growth, demand
- **Competitor Insights**: Market positioning
- **Success Stories**: Local case studies
- **Location-Based Ideas**: City and district specific

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Prepare Data & Train Models
```bash
python data_preparation.py
python train_models.py
```

### 3. Start the Application
```bash
python app_clean.py
```
Or use the launcher:
- **Windows**: Double-click `launch.bat`
- **Linux/Mac**: `./launch.sh`

> **Note**: We use `app_clean.py` (optimized version) instead of `app.py`

### 4. Open in Browser
```
http://localhost:5000
```

---

## 🎯 Usage Examples

### Profit Predictions
```
"Predict my profit with sales of $20000, expenses of $12000"
"What profit can I expect with 25 employees and $3000 marketing spend?"
```

### Karnataka Business Ideas (NEW! 🏛️)
```
"Give me business ideas for Mysuru"
"Tourism opportunities in Kodagu"
"Tech startups in Bangalore"
"Agriculture business in Mandya"
"Food business ideas in Udupi"
```
**All 31 Karnataka districts supported!** Click the sidebar buttons or type district names.

### Strategic Advice
```
"How can I increase my profit margin?"
"What are the best marketing strategies for startups?"
"How to reduce operational costs?"
```

---

## 📁 Project Structure

```
AI-ML-Business-Advisor/
│
├── 📄 Core Application
│   ├── app.py                          # Main Flask application (2,699 lines)
│   ├── requirements.txt                # Python dependencies
│   └── .gitignore                      # Git ignore rules
│
├── 🧠 Machine Learning
│   ├── data_preparation.py             # Data generation & cleaning
│   ├── train_models.py                 # Model training pipeline
│   ├── data/                           # Training datasets
│   │   ├── cleaned_business_data.csv
│   │   └── raw_business_data.csv
│   └── models/                         # Trained ML models
│       ├── linear_regression.pkl
│       ├── random_forest.pkl
│       ├── lstm_model.h5
│       ├── scaler.pkl
│       └── feature_cols.pkl
│
├── 🏛️ Karnataka Integration
│   ├── karnataka_districts_data.py     # All 31 districts data
│   └── karnataka_integration.py        # Integration module
│
├── 🌐 Frontend
│   ├── templates/
│   │   ├── index.html                  # Main chatbot UI
│   │   └── login.html                  # User authentication
│   └── static/
│       ├── style.css                   # Modern styling
│       └── script.js                   # Frontend logic
│
├── 🧪 Testing
│   ├── test_karnataka_integration.py   # Karnataka tests
│   └── verify_all_features.py          # Feature verification
│
├── 🚀 Launchers
│   ├── launch.bat                      # Windows launcher
│   └── launch.sh                       # Linux/Mac launcher
│
└── 📚 Documentation
    ├── README.md                       # This file
    └── QUICKSTART.md                   # Quick reference guide
```

---

## 🔧 Configuration

### Ollama LLM (Optional but Recommended)

1. **Install Ollama**
   ```bash
   # Download from https://ollama.ai
   ```

2. **Start Ollama Server**
   ```bash
   ollama serve
   ```

3. **Download a Model**
   ```bash
   ollama pull llama3.2
   # or
   ollama pull llama3
   ```

4. **Restart Flask App**
   - The app will automatically detect and use Ollama

**Note**: The chatbot works perfectly without Ollama using intelligent rule-based responses.

---

## 🌟 Key Capabilities

### Machine Learning Models
- **Linear Regression**: Fast, interpretable baseline
- **Random Forest**: Ensemble method for accuracy
- **LSTM**: Deep learning for time series patterns
- **Auto-Selection**: Best model chosen based on RMSE

### Natural Language Processing
- **Metric Extraction**: Automatically parses business data from text
- **Intent Detection**: Understands prediction vs advice vs ideas
- **Context Management**: Maintains conversation history
- **Fuzzy Matching**: Handles variations in district names

### Karnataka Districts Coverage

**All 31 Districts**:
Bagalkote • Ballari • Belagavi • Bengaluru Urban • Bengaluru Rural • Bidar • Vijayapura • Chamarajanagar • Chikkaballapur • Chikkamagaluru • Chitradurga • Dakshina Kannada • Davanagere • Dharwad • Gadag • Hassan • Haveri • Kalaburagi • Kodagu • Kolar • Koppal • Mandya • Mysuru • Raichur • Ramanagara • Shivamogga • Tumakuru • Udupi • Uttara Kannada • Yadgir • Vijayanagara

**10 Business Categories**:
1. Agriculture & Farming
2. Food & Beverages
3. Tourism & Hospitality
4. Retail & Wholesale
5. Technology & Digital
6. Manufacturing & Industry
7. Healthcare & Wellness
8. Education & Training
9. Automobile Services
10. Beauty & Lifestyle

---

## 📊 API Endpoints

### Core Endpoints
```
GET  /                    # Web interface
GET  /health              # System status
POST /chat                # Main chatbot
POST /predict             # ML predictions
GET  /models              # Available models
```

### User Management
```
GET/POST /login           # User login
GET/POST /register        # User registration
GET      /logout          # Logout
POST     /api/save-chat   # Save chat history
GET      /api/history     # Get chat history
```

### Business Intelligence
```
POST /api/business-ideas  # Generate business ideas
POST /api/market-data     # Market intelligence
POST /api/competitors     # Competitor analysis
POST /api/success-stories # Success case studies
```

---

## 🧪 Testing

### Run All Tests
```bash
python verify_all_features.py
```

### Test Karnataka Integration
```bash
python test_karnataka_integration.py
```

### Manual API Testing
```bash
# Health check
curl http://localhost:5000/health

# Profit prediction
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"sales": 20000, "expenses": 12000, "marketing_spend": 2500, "employee_count": 25, "competition_level": 3}'

# Chat
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Give me business ideas for Mysuru"}'
```

---

## 💡 Use Cases

### For Entrepreneurs
- Validate business ideas with ML predictions
- Get location-specific opportunities
- Receive strategic growth advice
- Explore market opportunities

### For Business Owners
- Analyze current performance
- Optimize costs and revenue
- Plan expansion strategies
- Benchmark against industry

### For Investors
- Evaluate business opportunities
- Assess market potential
- Analyze financial projections
- Research competitive landscape

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Flask (Python) |
| **ML** | scikit-learn, TensorFlow/Keras |
| **Data** | Pandas, NumPy |
| **Frontend** | HTML, CSS, JavaScript |
| **LLM** | Ollama (llama3.2, llama3, mistral) |
| **Auth** | Werkzeug security |
| **API** | RESTful with CORS |

---

## 📈 Performance

- **Response Time**: < 1 second (without LLM)
- **ML Prediction**: < 200ms
- **LLM Response**: 2-10 seconds (after first query)
- **Training Data**: 1000+ records
- **Model Accuracy**: Cross-validated RMSE

---

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production (Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Cloud Platforms
- **Heroku**: Ready to deploy
- **AWS**: EC2, Elastic Beanstalk, Lambda
- **Google Cloud**: App Engine, Cloud Run
- **Azure**: App Service
- **DigitalOcean**: Droplet, App Platform

---

## 🔐 Security

- **Password Hashing**: Werkzeug security
- **Session Management**: Flask sessions
- **CORS**: Configured for API access
- **Input Validation**: Robust data parsing
- **Error Handling**: Graceful degradation

---

## 🎓 Learning Resources

This project demonstrates:
- Full-stack web development
- Machine learning implementation
- AI/LLM integration
- Natural language processing
- RESTful API design
- Production-ready architecture

---

## 🤝 Contributing

Contributions are welcome! Areas for enhancement:
- Additional ML models
- More business categories
- Extended geographic coverage
- Multilingual support
- Advanced visualizations
- Mobile application

---

## 📄 License

This project is open source and available for educational purposes.

---

## 🙏 Acknowledgments

- **Ollama**: Local LLM framework
- **scikit-learn**: ML library
- **TensorFlow**: Deep learning
- **Flask**: Web framework
- **Karnataka Government**: District data inspiration

---

## 📞 Support

### Documentation
- **README.md**: This file (main documentation)
- **QUICKSTART.md**: Quick reference guide

### Testing
```bash
python verify_all_features.py
python test_karnataka_integration.py
```

### Issues
- Check logs in terminal
- Review `data/` and `models/` directories
- Verify Ollama is running (if using LLM)
- Ensure all dependencies are installed

---

## 🎉 Success Metrics

- ✅ **31/31 Districts**: Complete Karnataka coverage
- ✅ **3 ML Models**: Trained and deployed
- ✅ **50+ Ideas**: Unique business opportunities
- ✅ **10 Categories**: Complete sector coverage
- ✅ **1000+ Records**: Training dataset
- ✅ **Production Ready**: Tested and documented

---

**🚀 Start helping entrepreneurs make data-driven decisions today!**

*Built with ❤️ for Karnataka's entrepreneurial ecosystem*

---

*Last Updated: December 8, 2025*
*Version: 1.0.0*
*Status: Production Ready*
