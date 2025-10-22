from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import textwrap

# Load CSV
file_path = Path(__file__).parent / "bay_responses.csv"
df = pd.read_csv(file_path)

# Column indicating if someone felt unfairly treated
unfair_col = "Have you ever felt uncomfortable or treated unfairly due to surveillance technology? (5bdjc2c)"

# Support columns
support_cols = [
    "How supportive are you of Automatic License Plate Reader (ALPR) cameras installed by local governments and used by law enforcement? (y7ka0mc)",
    "How supportive are you of private individuals or businesses installing Automatic License Plate Reader (ALPR) cameras and sharing the data voluntarily with police? (uktyzgu)"
]

# Short labels for plotting
short_labels = ["Gov ALPR Support", "Private ALPR Support"]

# Recode unfair treatment to boolean
def recode_unfair(val):
    if pd.isna(val):
        return None
    val = str(val).lower()
    if "yes" in val:
        return "Felt Unfairly Treated"
    elif "no" in val:
        return "Did Not Feel Unfairly Treated"
    else:
        return None

df['unfair_group'] = df[unfair_col].apply(recode_unfair)

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

# Group by unfair treatment and calculate mean support
mean_support = df.groupby('unfair_group')[[c + "_num" for c in support_cols]].mean()
mean_support.columns = short_labels

# Plot vertical side-by-side bars
groups = mean_support.index.tolist()
x = range(len(groups))
width = 0.35

plt.figure(figsize=(8,6))
plt.bar([i - width/2 for i in x], mean_support[short_labels[0]], width, label=short_labels[0])
plt.bar([i + width/2 for i in x], mean_support[short_labels[1]], width, label=short_labels[1])

plt.xticks(x, groups)
plt.ylabel("Average Support")
plt.title("\n".join(textwrap.wrap(
    "Average Support for ALPR Cameras by Whether Respondents Felt Unfairly Treated by Surveillance", 60
)))

plt.legend(title="Support Question", loc='upper right')
plt.tight_layout()
plt.show()
