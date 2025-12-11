from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
import numpy as np

# Load CSV
file_path = Path(__file__).parent / "alpr_survey_results.csv"
df = pd.read_csv(file_path)

# Column for noticing surveillance frequency
frequency_col = "How often do you notice surveillance cameras or sensors in your neighborhood or daily routine? (6itkmu)"

# Columns for support or concern
support_cols = [
    "How supportive are you of Automatic License Plate Reader (ALPR) cameras installed by local governments and used by law enforcement? (y7ka0mc)",
    "How supportive are you of private individuals or businesses installing Automatic License Plate Reader (ALPR) cameras and sharing the data voluntarily with police? (uktyzgu)"
]

# Short labels
short_labels = ["Gov ALPR Support", "Private ALPR Support"]

# Recode frequency to ordered categories
def recode_frequency(val):
    if pd.isna(val):
        return None
    val = str(val).lower()
    if "never" in val:
        return "Never"
    elif "rarely" in val:
        return "Rarely"
    elif "sometimes" in val:
        return "Sometimes"
    elif "often" in val:
        return "Often"
    elif "always" in val:
        return "Always"
    else:
        return "Other"

df['frequency_group'] = df[frequency_col].apply(recode_frequency)

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

# Group by frequency and calculate mean support
mean_support = df.groupby('frequency_group')[[c + "_num" for c in support_cols]].mean()
mean_support = mean_support.reindex(["Never","Rarely","Sometimes","Often","Always"])  # optional ordering
mean_support.columns = short_labels

# Plot vertical side-by-side bars
groups = mean_support.index.tolist()
x = np.arange(len(groups))
width = 0.35

plt.figure(figsize=(10,6))
plt.bar(x - width/2, mean_support[short_labels[0]], width, label=short_labels[0])
plt.bar(x + width/2, mean_support[short_labels[1]], width, label=short_labels[1])

plt.xticks(x, groups, rotation=0)
plt.ylabel("Average Support")
plt.title("\n".join(textwrap.wrap(
    "Average Support for ALPR Cameras by How Often Respondents Notice Surveillance in Daily Life", 60
)))

plt.legend(title="Support Question", loc='upper right')
plt.tight_layout()
plt.show()
