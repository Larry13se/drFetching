# CSV Combiner and Insights Notebook
# This notebook combines multiple CSV files with the same structure and provides insights

import pandas as pd
import os
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
sns.set_style('whitegrid')

# ============================================================================
# STEP 1: Configuration
# ============================================================================

# Specify your folder path containing CSV files
FOLDER_PATH = 'path/to/your/csv/folder'  # UPDATE THIS PATH

# Columns to drop (before analysis)
COLUMNS_TO_DROP = [
    'SESSION_FINGERPRINT', 'SESSION_TIMESTAMP', 'BROWSER_TYPE', 'THREAD_ID',
    'USER_AGENT', 'SCREEN_RESOLUTION', 'TIMEZONE', 'SESSION_DURATION',
    'DR_COUNT', 'DR_COUNT_REGULAR', 'DR_COUNT_CN'
]

# ============================================================================
# STEP 2: Load and Combine CSV Files
# ============================================================================

def load_csv_files(folder_path):
    """Load all CSV files from a folder"""
    csv_files = list(Path(folder_path).glob('*.csv'))
    
    if not csv_files:
        print(f"⚠️ No CSV files found in {folder_path}")
        return []
    
    print(f"📁 Found {len(csv_files)} CSV files")
    
    dataframes = []
    stats_before = []
    
    for i, file_path in enumerate(csv_files, 1):
        df = None
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-8-sig']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                
                # Fix the LEAD TYPE column name if it has encoding issues
                df.columns = [col.strip() if 'LEAD TYPE' not in col else 'LEAD TYPE' 
                             for col in df.columns]
                
                # Store stats before combining
                stats_before.append({
                    'File': file_path.name,
                    'Rows': len(df),
                    'Columns': len(df.columns),
                    'Encoding': encoding
                })
                
                dataframes.append(df)
                print(f"✅ {i}. {file_path.name}: {len(df)} rows (encoding: {encoding})")
                break
                
            except Exception as e:
                if encoding == encodings[-1]:  # Last encoding attempt
                    print(f"❌ Error loading {file_path.name}: Could not decode with any encoding")
                continue
    
    return dataframes, stats_before

# Load files
print("="*70)
print("LOADING CSV FILES")
print("="*70)
dataframes, stats_before = load_csv_files(FOLDER_PATH)

if not dataframes:
    print("No data to process. Please check your folder path.")
else:
    # Display individual file statistics
    print("\n📊 BEFORE COMBINING - Individual File Statistics:")
    df_stats_before = pd.DataFrame(stats_before)
    print(df_stats_before.to_string(index=False))
    print(f"\nTotal Rows Across All Files: {df_stats_before['Rows'].sum():,}")

# ============================================================================
# STEP 3: Combine All DataFrames
# ============================================================================

if dataframes:
    print("\n" + "="*70)
    print("COMBINING FILES")
    print("="*70)
    
    combined_df = pd.concat(dataframes, ignore_index=True)
    print(f"✅ Combined into single DataFrame: {len(combined_df):,} rows × {len(combined_df.columns)} columns")
    
    # Show column names (to verify LEAD TYPE column)
    print("\n📋 Column Names in Combined Data:")
    for i, col in enumerate(combined_df.columns, 1):
        print(f"{i:2d}. {col}")

# ============================================================================
# STEP 4: Drop Unnecessary Columns
# ============================================================================

if dataframes:
    print("\n" + "="*70)
    print("DROPPING COLUMNS")
    print("="*70)
    
    # Check which columns exist
    existing_cols_to_drop = [col for col in COLUMNS_TO_DROP if col in combined_df.columns]
    missing_cols = [col for col in COLUMNS_TO_DROP if col not in combined_df.columns]
    
    if existing_cols_to_drop:
        combined_df = combined_df.drop(columns=existing_cols_to_drop)
        print(f"✅ Dropped {len(existing_cols_to_drop)} columns")
        for col in existing_cols_to_drop:
            print(f"   • {col}")
    
    if missing_cols:
        print(f"\n⚠️ {len(missing_cols)} columns not found (already missing):")
        for col in missing_cols:
            print(f"   • {col}")
    
    print(f"\n📊 Final shape: {len(combined_df):,} rows × {len(combined_df.columns)} columns")

# ============================================================================
# STEP 5: AFTER COMBINING - Statistics
# ============================================================================

if dataframes:
    print("\n" + "="*70)
    print("AFTER COMBINING - Statistics")
    print("="*70)
    
    print(f"Total Rows: {len(combined_df):,}")
    print(f"Total Columns: {len(combined_df.columns)}")
    print(f"Memory Usage: {combined_df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    print("\n🔍 Missing Values Summary:")
    missing = combined_df.isnull().sum()
    missing_pct = (missing / len(combined_df) * 100).round(2)
    missing_df = pd.DataFrame({
        'Column': missing.index,
        'Missing Count': missing.values,
        'Missing %': missing_pct.values
    })
    missing_df = missing_df[missing_df['Missing Count'] > 0].sort_values('Missing Count', ascending=False)
    
    if len(missing_df) > 0:
        print(missing_df.to_string(index=False))
    else:
        print("✅ No missing values!")

# ============================================================================
# STEP 6: DR1 Column Analysis
# ============================================================================

if dataframes and 'DR1' in combined_df.columns:
    print("\n" + "="*70)
    print("DR1 COLUMN ANALYSIS")
    print("="*70)
    
    # Get unique values and counts
    dr1_counts = combined_df['DR1'].value_counts().reset_index()
    dr1_counts.columns = ['DR1 Value', 'Count']
    dr1_counts['Percentage'] = (dr1_counts['Count'] / len(combined_df) * 100).round(2)
    
    print(f"\n📈 Total Unique Values in DR1: {combined_df['DR1'].nunique()}")
    print(f"📊 Total Non-Null Values: {combined_df['DR1'].notna().sum():,}")
    print(f"❌ Null Values: {combined_df['DR1'].isna().sum():,}")
    
    print("\n🔝 Top 20 DR1 Values:")
    print(dr1_counts.head(20).to_string(index=False))
    
    # Store for filtering
    dr1_value_counts = dr1_counts.copy()
    
    # Visualization
    plt.figure(figsize=(12, 6))
    top_15 = dr1_counts.head(15)
    plt.barh(range(len(top_15)), top_15['Count'])
    plt.yticks(range(len(top_15)), top_15['DR1 Value'])
    plt.xlabel('Count')
    plt.title('Top 15 DR1 Values Distribution')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()

# ============================================================================
# STEP 7: Filter Data by DR1 Values (OPTIONAL)
# ============================================================================

if dataframes and 'DR1' in combined_df.columns:
    print("\n" + "="*70)
    print("FILTER DATA BY DR1 VALUES")
    print("="*70)
    
    print("\n🔧 To filter out specific DR1 values, create a list:")
    print("Example:")
    print("values_to_remove = ['Value1', 'Value2', 'Value3']")
    print("filtered_df = combined_df[~combined_df['DR1'].isin(values_to_remove)]")
    
    # Example filter (uncomment and modify as needed)
    # values_to_remove = ['example_value_1', 'example_value_2']
    # filtered_df = combined_df[~combined_df['DR1'].isin(values_to_remove)]
    # print(f"\n✅ Filtered Data: {len(filtered_df):,} rows (removed {len(combined_df) - len(filtered_df):,} rows)")
    
    # Create a placeholder for your filter
    values_to_remove = ["Username field not found","Password field not found","Both login button XPaths failed","Failed to solve CAPTCHA after login button click","Max retries reached"]  # ADD YOUR VALUES HERE
    
    if values_to_remove:
        filtered_df = combined_df[~combined_df['DR1'].isin(values_to_remove)]
        print(f"\n✅ Applied filter on {len(values_to_remove)} values")
        print(f"Original rows: {len(combined_df):,}")
        print(f"Filtered rows: {len(filtered_df):,}")
        print(f"Removed rows: {len(combined_df) - len(filtered_df):,}")
    else:
        filtered_df = combined_df.copy()
        print("\n⚠️ No filter values specified. Using all data.")

# ============================================================================
# STEP 8: Export Combined Data
# ============================================================================

if dataframes:
    print("\n" + "="*70)
    print("EXPORT DATA")
    print("="*70)
    
    # Export combined data
    output_file = 'combined_data.csv'
    combined_df.to_csv(output_file, index=False)
    print(f"✅ Combined data exported to: {output_file}")
    
    # Export filtered data if filter was applied
    if values_to_remove and 'filtered_df' in locals():
        filtered_output = 'filtered_data.csv'
        filtered_df.to_csv(filtered_output, index=False)
        print(f"✅ Filtered data exported to: {filtered_output}")
    
    # Export DR1 analysis
    if 'dr1_value_counts' in locals():
        dr1_output = 'dr1_analysis.csv'
        dr1_value_counts.to_csv(dr1_output, index=False)
        print(f"✅ DR1 analysis exported to: {dr1_output}")

print("\n" + "="*70)
print("✨ PROCESSING COMPLETE!")
print("="*70)