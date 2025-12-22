# parser.py

import pandas as pd
import matplotlib.pyplot as plt
import os

# --------------------------
# CONFIGURATION
# --------------------------
DATA_FILE = "data.csv"      # Path to your dataset
OUTPUT_DIR = "output"       # Folder to save graphs
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------
# LOAD DATA
# --------------------------
df = pd.read_csv(DATA_FILE)

# Optional: replace missing values with 0 or drop
df.fillna(0, inplace=True)

# --------------------------
# SMART COLUMN INSIGHTS
# --------------------------
def generate_insights(df):
    insights = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            min_val = df[col].min()
            max_val = df[col].max()
            mean_val = df[col].mean()
            insights.append(
                f"Column '{col}': min={min_val}, max={max_val}, mean={mean_val:.2f}"
            )
    return "\n".join(insights)

# Save insights to text
with open(os.path.join(OUTPUT_DIR, "insights.txt"), "w") as f:
    f.write(generate_insights(df))

# --------------------------
# GRAPH GENERATION
# --------------------------
def plot_column(col_name):
    series = df[col_name]
    
    plt.figure(figsize=(8, 5))
    plt.plot(series, marker='o', label=col_name)
    
    # Highlight min & max
    min_idx = series.idxmin()
    max_idx = series.idxmax()
    plt.scatter(min_idx, series[min_idx], color='red', label='Min', zorder=5, s=100)
    plt.scatter(max_idx, series[max_idx], color='green', label='Max', zorder=5, s=100)
    
    # Titles & labels
    plt.title(f"{col_name} with Min & Max")
    plt.xlabel("Index")
    plt.ylabel(col_name)
    plt.legend()
    plt.grid(True)
    
    # Save figure
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, f"{col_name}.png")
    plt.savefig(output_path)
    plt.close()
    return output_path

# Generate graphs for all numeric columns
graph_paths = []
for col in df.columns:
    if pd.api.types.is_numeric_dtype(df[col]):
        path = plot_column(col)
        graph_paths.append(path)

# --------------------------
# SUMMARY
# --------------------------
print("✅ Smart insights saved at:", os.path.join(OUTPUT_DIR, "insights.txt"))
print("✅ Graphs generated:")
for path in graph_paths:
    print("  -", path)
