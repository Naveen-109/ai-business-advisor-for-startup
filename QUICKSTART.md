# ⚡ Quick Start Guide

## 🚀 Get Started in 3 Minutes

### Step 1: Install Dependencies (1 min)
```bash
pip install -r requirements.txt
```

### Step 2: Setup Data & Models (1 min)
```bash
python data_preparation.py
python train_models.py
```

### Step 3: Launch Application (30 sec)
```bash
python app.py
```
**Or use launcher:**
- Windows: Double-click `launch.bat`
- Linux/Mac: `./launch.sh`

### Step 4: Open Browser
```
http://localhost:5000
```

---

## 💬 Try These Queries

### Profit Predictions
```
Predict my profit with sales of $20000, expenses of $12000
```

### Business Ideas
```
Give me business ideas for Mysuru
```

### Strategic Advice
```
How can I increase my sales?
```

### Karnataka Districts
```
Tourism opportunities in Kodagu
Tech startups in Bangalore
Agriculture business in Mandya
```

---

## 🤖 Enable AI (Optional)

### Install Ollama
1. Download from https://ollama.ai
2. Install and run: `ollama serve`
3. Download model: `ollama pull llama3.2`
4. Restart Flask app

**Note**: Works perfectly without Ollama!

---

## 🧪 Test Everything
```bash
python verify_all_features.py
```

---

## 📊 What You Get

- ✅ **3 ML Models** - Profit predictions
- ✅ **31 Districts** - Karnataka coverage
- ✅ **10 Categories** - Business sectors
- ✅ **50+ Ideas** - Unique opportunities
- ✅ **AI Chat** - Strategic advice
- ✅ **Web Interface** - Modern UI

---

## 🎯 Key Features

| Feature | Description |
|---------|-------------|
| **ML Predictions** | 3 models (Linear, RF, LSTM) |
| **AI Chat** | Ollama LLM integration |
| **Business Ideas** | Location-specific opportunities |
| **Karnataka** | All 31 districts covered |
| **API** | RESTful endpoints |
| **Auth** | User management |

---

## 📁 Essential Files

```
app.py                          # Main application
requirements.txt                # Dependencies
data_preparation.py             # Data setup
train_models.py                 # Model training
karnataka_districts_data.py     # District data
karnataka_integration.py        # Integration
templates/index.html            # Web UI
static/style.css                # Styling
```

---

## 🔧 Troubleshooting

### Models not loading?
```bash
python train_models.py
```

### Port 5000 busy?
Edit `app.py`, change port to 5001

### Ollama not working?
Check if running: `ollama serve`

### Dependencies missing?
```bash
pip install -r requirements.txt
```

---

## 📚 Full Documentation

See **README.md** for complete documentation.

---

## 🎉 You're Ready!

Your AI/ML Business Advisor is now running at:
**http://localhost:5000**

Start chatting and exploring business opportunities!

---

*Quick Start Guide | Version 1.0.0*
