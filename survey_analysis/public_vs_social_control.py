from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
import numpy as np

# Load CSV
file_path = Path(__file__).parent / "bay_responses.csv"
df = pd.read_csv(file_path)

# Columns
perception_col = "Do you believe surveillance is being used more for public safety or social control? (cfu4j56)"
support_cols = [
    "How supportive are you of Automatic License Plate Reader (ALPR) cameras installed by local governments and used by law enforcement? (y7ka0mc)",
    "How supportive are you of private individuals or businesses installing Automatic License Plate Reader (ALPR) cameras and sharing the data voluntarily with police? (uktyzgu)"
]

# Short labels for legend
short_labels = [
    "Gov ALPR Support",
    "Private ALPR Support"
]

# Recode perception
def recode_perception(val):
    if pd.isna(val):
        return None
    val = str(val).lower()
    if "public safety" in val:
        return "Public Safety"
    elif "social control" in val:
        return "Social Control"
    elif "both" in val or "neutral" in val:
        return "Both/Neutral"
    else:
        return None

df['perception'] = df[perception_col].apply(recode_perception)

# Recode support to numeric
def recode_support(val):
    if pd.isna(val):
        return None
    val = str(val).lower()
    if "strongly oppose" in val:
        return 0
    elif "oppose" in val:
        return 1
    elif "neutral" in val:
        return 2
    elif "support" in val:
        return 3
    elif "strongly support" in val:
        return 4
    else:
        try:
            return float(val)
        except:
            return None

for col in support_cols:
    df[col + "_num"] = df[col].apply(recode_support)

# Group by perception and calculate mean support
mean_support = df.groupby('perception')[[c + "_num" for c in support_cols]].mean()
mean_support.columns = short_labels

# Plot vertical side-by-side bars
perceptions = mean_support.index.tolist()
x = np.arange(len(perceptions))
width = 0.35  # bar width

plt.figure(figsize=(8,6))
plt.bar(x - width/2, mean_support[short_labels[0]], width, label=short_labels[0])
plt.bar(x + width/2, mean_support[short_labels[1]], width, label=short_labels[1])

plt.xticks(x, perceptions, rotation=0)
plt.ylabel("Average Support")
plt.title("\n".join(textwrap.wrap(
    "Average Support for ALPR Cameras by Perception of Surveillance (Public Safety vs. Social Control)", 60
)))

plt.legend(title="Support Question", loc='upper right')
plt.tight_layout()
plt.show()
