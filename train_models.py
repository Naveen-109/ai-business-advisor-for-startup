"""
Model Building Script
Trains multiple ML models and compares their performance
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import joblib
import os
import json

def load_data():
    """Load cleaned business data"""
    df = pd.read_csv('data/cleaned_business_data.csv')
    df['date'] = pd.to_datetime(df['date'])
    return df

def prepare_features(df):
    """Prepare features for ML models"""
    # Create time-based features
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day_of_year'] = df['date'].dt.dayofyear
    df['day_of_week'] = df['date'].dt.dayofweek
    
    # Feature columns (excluding date and target)
    feature_cols = ['sales', 'expenses', 'marketing_spend', 'employee_count', 
                   'seasonality', 'competition_level', 'year', 'month', 
                   'day_of_year', 'day_of_week']
    
    X = df[feature_cols].values
    y = df['profit'].values
    
    return X, y, feature_cols

def train_linear_regression(X_train, X_test, y_train, y_test):
    """Train Linear Regression model"""
    print("\n=== Training Linear Regression ===")
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Metrics
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    
    print(f"Train RMSE: {train_rmse:.2f}")
    print(f"Test RMSE: {test_rmse:.2f}")
    print(f"Train MAE: {train_mae:.2f}")
    print(f"Test MAE: {test_mae:.2f}")
    print(f"Train R²: {train_r2:.4f}")
    print(f"Test R²: {test_r2:.4f}")
    
    return model, {
        'train_rmse': train_rmse,
        'test_rmse': test_rmse,
        'train_mae': train_mae,
        'test_mae': test_mae,
        'train_r2': train_r2,
        'test_r2': test_r2
    }

def train_random_forest(X_train, X_test, y_train, y_test):
    """Train Random Forest model"""
    print("\n=== Training Random Forest ===")
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)
    
    # Predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Metrics
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    
    print(f"Train RMSE: {train_rmse:.2f}")
    print(f"Test RMSE: {test_rmse:.2f}")
    print(f"Train MAE: {train_mae:.2f}")
    print(f"Test MAE: {test_mae:.2f}")
    print(f"Train R²: {train_r2:.4f}")
    print(f"Test R²: {test_r2:.4f}")
    
    return model, {
        'train_rmse': train_rmse,
        'test_rmse': test_rmse,
        'train_mae': train_mae,
        'test_mae': test_mae,
        'train_r2': train_r2,
        'test_r2': test_r2
    }

def prepare_lstm_data(X, y, lookback=30):
    """Prepare data for LSTM (time series format)"""
    X_lstm = []
    y_lstm = []
    
    for i in range(lookback, len(X)):
        X_lstm.append(X[i-lookback:i])
        y_lstm.append(y[i])
    
    return np.array(X_lstm), np.array(y_lstm)

def train_lstm(X_train, X_test, y_train, y_test, feature_dim):
    """Train LSTM model"""
    print("\n=== Training LSTM ===")
    
    lookback = 30
    X_train_lstm, y_train_lstm = prepare_lstm_data(X_train, y_train, lookback)
    X_test_lstm, y_test_lstm = prepare_lstm_data(X_test, y_test, lookback)
    
    # Build LSTM model
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(lookback, feature_dim)),
        Dropout(0.2),
        LSTM(50, return_sequences=False),
        Dropout(0.2),
        Dense(25),
        Dense(1)
    ])
    
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    
    # Train model
    history = model.fit(
        X_train_lstm, y_train_lstm,
        batch_size=32,
        epochs=50,
        validation_data=(X_test_lstm, y_test_lstm),
        verbose=1
    )
    
    # Predictions
    y_pred_train = model.predict(X_train_lstm, verbose=0).flatten()
    y_pred_test = model.predict(X_test_lstm, verbose=0).flatten()
    
    # Metrics
    train_rmse = np.sqrt(mean_squared_error(y_train_lstm, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test_lstm, y_pred_test))
    train_mae = mean_absolute_error(y_train_lstm, y_pred_train)
    test_mae = mean_absolute_error(y_test_lstm, y_pred_test)
    train_r2 = r2_score(y_train_lstm, y_pred_train)
    test_r2 = r2_score(y_test_lstm, y_pred_test)
    
    print(f"Train RMSE: {train_rmse:.2f}")
    print(f"Test RMSE: {test_rmse:.2f}")
    print(f"Train MAE: {train_mae:.2f}")
    print(f"Test MAE: {test_mae:.2f}")
    print(f"Train R²: {train_r2:.4f}")
    print(f"Test R²: {test_r2:.4f}")
    
    return model, {
        'train_rmse': train_rmse,
        'test_rmse': test_rmse,
        'train_mae': train_mae,
        'test_mae': test_mae,
        'train_r2': train_r2,
        'test_r2': test_r2
    }

def compare_models(results):
    """Compare model performance and select the best one"""
    print("\n=== Model Comparison ===")
    
    best_model = None
    best_score = float('inf')
    best_model_name = None
    
    for model_name, metrics in results.items():
        print(f"\n{model_name}:")
        print(f"  Test RMSE: {metrics['test_rmse']:.2f}")
        print(f"  Test R²: {metrics['test_r2']:.4f}")
        
        # Use test_rmse as the comparison metric
        if metrics['test_rmse'] < best_score:
            best_score = metrics['test_rmse']
            best_model_name = model_name
    
    print(f"\nBest Model: {best_model_name} (Test RMSE: {best_score:.2f})")
    return best_model_name

def main():
    """Main training function"""
    # Create models directory
    os.makedirs('models', exist_ok=True)
    
    # Load data
    print("Loading data...")
    df = load_data()
    
    # Prepare features
    X, y, feature_cols = prepare_features(df)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=False
    )
    
    # Scale features (for better LSTM performance)
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Save scaler
    joblib.dump(scaler, 'models/scaler.pkl')
    joblib.dump(feature_cols, 'models/feature_cols.pkl')
    
    # Train models
    results = {}
    
    # Linear Regression
    lr_model, lr_metrics = train_linear_regression(X_train_scaled, X_test_scaled, y_train, y_test)
    joblib.dump(lr_model, 'models/linear_regression.pkl')
    results['Linear Regression'] = lr_metrics
    
    # Random Forest
    rf_model, rf_metrics = train_random_forest(X_train_scaled, X_test_scaled, y_train, y_test)
    joblib.dump(rf_model, 'models/random_forest.pkl')
    results['Random Forest'] = rf_metrics
    
    # LSTM
    lstm_model, lstm_metrics = train_lstm(X_train_scaled, X_test_scaled, y_train, y_test, X_train_scaled.shape[1])
    lstm_model.save('models/lstm_model.h5')
    results['LSTM'] = lstm_metrics
    
    # Compare and select best model
    best_model_name = compare_models(results)
    
    # Save best model info
    with open('models/best_model.txt', 'w') as f:
        f.write(best_model_name)
    
    # Save all results
    with open('models/model_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nModels saved to models/ directory")
    print(f"Best model: {best_model_name}")

if __name__ == "__main__":
    main()




