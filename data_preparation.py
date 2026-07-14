"""
Data Preparation Script
Generates realistic small business dataset with proper feature engineering
"""
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta

def generate_realistic_business_data(n_samples=1000, seed=42):
    """Generate realistic small business dataset for startups"""
    np.random.seed(seed)
    
    # Generate dates
    start_date = datetime(2021, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(n_samples)]
    
    # Base sales with trend and seasonality
    trend = np.linspace(8000, 22000, n_samples)
    seasonality = 3000 * np.sin(2 * np.pi * np.arange(n_samples) / 365)
    noise = np.random.normal(0, 800, n_samples)
    sales = trend + seasonality + noise + np.random.normal(10000, 1500, n_samples)
    sales = np.maximum(sales, 1000)  # Minimum sales
    
    # Expenses correlated with sales
    expenses = (sales * 0.6) + np.random.normal(0, 500, n_samples)
    expenses = np.maximum(expenses, 500)
    
    # Marketing spend (strategic variable)
    # Varies from 5% to 15% of sales
    marketing_ratio = np.random.uniform(0.05, 0.15, n_samples)
    marketing_spend = sales * marketing_ratio + np.random.normal(0, 300, n_samples)
    marketing_spend = np.maximum(marketing_spend, 100)
    
    # Employee count with growth over time
    base_employees = 5
    growth_rate = np.linspace(0, 30, n_samples)
    employee_count = base_employees + growth_rate + np.random.normal(0, 2, n_samples)
    employee_count = np.maximum(np.round(employee_count), 3)
    
    # Seasonality factor (-1 to 1)
    seasonality_factor = np.sin(2 * np.pi * np.arange(n_samples) / 365)
    
    # Competition level (1-5 scale)
    competition_level = np.random.choice([1, 2, 3, 4, 5], n_samples, p=[0.1, 0.2, 0.35, 0.25, 0.1])
    
    # Customer satisfaction (affecting sales)
    customer_satisfaction = 3.5 + np.random.normal(0, 0.8, n_samples)
    customer_satisfaction = np.clip(customer_satisfaction, 1, 5)
    
    # Market growth indicator (external factor)
    market_growth = np.linspace(0.8, 1.3, n_samples)
    
    # Profit calculation
    profit = sales - expenses - marketing_spend - (employee_count * 800)  # Rough salary estimate
    
    # Data dictionary
    data = {
        'date': dates,
        'sales': sales,
        'expenses': expenses,
        'marketing_spend': marketing_spend,
        'employee_count': employee_count,
        'seasonality': seasonality_factor,
        'competition_level': competition_level,
        'customer_satisfaction': customer_satisfaction,
        'market_growth': market_growth,
        'profit': profit
    }
    
    df = pd.DataFrame(data)
    
    # Add some realistic missing values (2% instead of 5%)
    null_indices = np.random.choice(df.index, size=int(0.02 * len(df)), replace=False)
    df.loc[null_indices, 'marketing_spend'] = np.nan
    
    return df

def clean_and_engineer_features(df):
    """Clean data and engineer additional features"""
    print(f"Original data shape: {df.shape}")
    print(f"Null values before cleaning:\n{df.isnull().sum()}")
    
    # Handle missing values
    df_cleaned = df.copy()
    
    # Fill missing marketing spend with mean of that month
    df_cleaned['date'] = pd.to_datetime(df_cleaned['date'])
    df_cleaned['month'] = df_cleaned['date'].dt.month
    monthly_marketing_mean = df_cleaned.groupby('month')['marketing_spend'].transform('mean')
    df_cleaned['marketing_spend'].fillna(monthly_marketing_mean, inplace=True)
    
    # Fill any remaining NaN with overall mean
    df_cleaned['marketing_spend'].fillna(df_cleaned['marketing_spend'].mean(), inplace=True)
    
    # Sort by date
    df_cleaned = df_cleaned.sort_values('date').reset_index(drop=True)
    
    # Remove extreme outliers (values beyond 3.5 standard deviations)
    numeric_cols = ['sales', 'expenses', 'marketing_spend', 'employee_count', 'profit']
    outlier_indices = []
    
    for col in numeric_cols:
        mean = df_cleaned[col].mean()
        std = df_cleaned[col].std()
        mask = (df_cleaned[col] > mean + 3.5*std) | (df_cleaned[col] < mean - 3.5*std)
        outlier_indices.extend(df_cleaned[mask].index.tolist())
    
    outlier_indices = list(set(outlier_indices))
    if outlier_indices:
        print(f"Removed {len(outlier_indices)} outlier records")
        df_cleaned = df_cleaned.drop(outlier_indices).reset_index(drop=True)
    
    # Feature Engineering
    print("\nEngineering features...")
    
    # Cost ratios
    df_cleaned['expense_ratio'] = df_cleaned['expenses'] / df_cleaned['sales'].replace(0, 1)
    df_cleaned['marketing_ratio'] = df_cleaned['marketing_spend'] / df_cleaned['sales'].replace(0, 1)
    
    # Profit metrics
    df_cleaned['profit_margin'] = (df_cleaned['profit'] / df_cleaned['sales'].replace(0, 1)) * 100
    
    # Employee productivity
    df_cleaned['sales_per_employee'] = df_cleaned['sales'] / df_cleaned['employee_count'].replace(0, 1)
    
    # Marketing efficiency (sales generated per marketing dollar)
    df_cleaned['marketing_efficiency'] = df_cleaned['sales'] / df_cleaned['marketing_spend'].replace(0, 1)
    
    # Time-based features
    df_cleaned['year'] = df_cleaned['date'].dt.year
    df_cleaned['month'] = df_cleaned['date'].dt.month
    df_cleaned['quarter'] = df_cleaned['date'].dt.quarter
    df_cleaned['day_of_year'] = df_cleaned['date'].dt.dayofyear
    df_cleaned['day_of_week'] = df_cleaned['date'].dt.dayofweek
    df_cleaned['is_quarter_end'] = df_cleaned['date'].dt.is_quarter_end.astype(int)
    
    # Lagged features (previous day metrics)
    df_cleaned['sales_lag_7'] = df_cleaned['sales'].shift(7)
    df_cleaned['profit_lag_7'] = df_cleaned['profit'].shift(7)
    
    # Fill NaN values in lagged features with mean
    df_cleaned['sales_lag_7'].fillna(df_cleaned['sales_lag_7'].mean(), inplace=True)
    df_cleaned['profit_lag_7'].fillna(df_cleaned['profit_lag_7'].mean(), inplace=True)
    
    # Growth rates
    df_cleaned['sales_growth'] = df_cleaned['sales'].pct_change() * 100
    df_cleaned['sales_growth'].fillna(0, inplace=True)
    
    print(f"Cleaned data shape: {df_cleaned.shape}")
    print(f"Null values after cleaning:\n{df_cleaned.isnull().sum()}")
    
    return df_cleaned

def analyze_data(df):
    """Analyze the dataset and print summary statistics"""
    print("\n" + "="*70)
    print("DATA ANALYSIS SUMMARY")
    print("="*70)
    
    print(f"\nDataset Overview:")
    print(f"Total Records: {len(df):,}")
    print(f"Date Range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"Duration: {(df['date'].max() - df['date'].min()).days} days")
    
    print(f"\n--- Core Business Metrics ---")
    for col in ['sales', 'expenses', 'profit', 'marketing_spend', 'employee_count']:
        if col in df.columns:
            print(f"\n{col.upper()}:")
            print(f"  Mean: ${df[col].mean():,.2f}" if col != 'employee_count' else f"  Mean: {df[col].mean():.1f}")
            print(f"  Median: ${df[col].median():,.2f}" if col != 'employee_count' else f"  Median: {df[col].median():.1f}")
            print(f"  Std Dev: ${df[col].std():,.2f}" if col != 'employee_count' else f"  Std Dev: {df[col].std():.1f}")
            print(f"  Min: ${df[col].min():,.2f}" if col != 'employee_count' else f"  Min: {df[col].min():.0f}")
            print(f"  Max: ${df[col].max():,.2f}" if col != 'employee_count' else f"  Max: {df[col].max():.0f}")
    
    print(f"\n--- Efficiency Metrics ---")
    print(f"Average Profit Margin: {df['profit_margin'].mean():.2f}%")
    print(f"Average Sales per Employee: ${df['sales_per_employee'].mean():,.2f}")
    print(f"Average Marketing Efficiency: {df['marketing_efficiency'].mean():.2f}x")
    
    print(f"\n--- Correlation Analysis ---")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    correlation_with_profit = df[numeric_cols].corr()['profit'].sort_values(ascending=False)
    print("Features correlated with profit (top 10):")
    for i, (feature, corr) in enumerate(correlation_with_profit.head(10).items(), 1):
        print(f"  {i}. {feature}: {corr:.4f}")
    
    print(f"\n--- Competition Level Distribution ---")
    comp_dist = df['competition_level'].value_counts().sort_index()
    for level, count in comp_dist.items():
        print(f"  Level {int(level)}: {count} days ({count/len(df)*100:.1f}%)")
    
    print(f"\n--- Data Quality ---")
    print(f"Null values: {df.isnull().sum().sum()}")
    print(f"Duplicates: {df.duplicated().sum()}")
    
    print("\n" + "="*70)

def prepare_data():
    """Main function to prepare data"""
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Generate realistic sample data
    print("Generating realistic startup business data...")
    df = generate_realistic_business_data(1000)
    
    # Save raw data
    df.to_csv('data/raw_business_data.csv', index=False)
    print("✓ Raw data saved to data/raw_business_data.csv")
    
    # Clean data and engineer features
    print("\nCleaning and engineering features...")
    df_cleaned = clean_and_engineer_features(df)
    
    # Analyze data
    analyze_data(df_cleaned)
    
    # Save cleaned data
    df_cleaned.to_csv('data/cleaned_business_data.csv', index=False)
    print("\n✓ Cleaned data saved to data/cleaned_business_data.csv")
    
    # Save data summary statistics
    summary_stats = {
        'total_records': len(df_cleaned),
        'date_range': {
            'start': df_cleaned['date'].min().strftime('%Y-%m-%d'),
            'end': df_cleaned['date'].max().strftime('%Y-%m-%d')
        },
        'metrics': {}
    }
    
    for col in ['sales', 'expenses', 'profit', 'marketing_spend', 'employee_count']:
        if col in df_cleaned.columns:
            summary_stats['metrics'][col] = {
                'mean': float(df_cleaned[col].mean()),
                'median': float(df_cleaned[col].median()),
                'std_dev': float(df_cleaned[col].std()),
                'min': float(df_cleaned[col].min()),
                'max': float(df_cleaned[col].max())
            }
    
    with open('data/data_summary.json', 'w') as f:
        json.dump(summary_stats, f, indent=2)
    
    print("✓ Data summary saved to data/data_summary.json")
    
    return df_cleaned

if __name__ == "__main__":
    prepare_data()




