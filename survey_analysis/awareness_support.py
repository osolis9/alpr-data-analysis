from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import textwrap

# Load CSV
file_path = Path(__file__).parent / "bay_responses.csv"
df = pd.read_csv(file_path)

# Awareness columns (ALPR facts)
awareness_cols = [
    "In some Bay Area cities, Automatic License Plate Reader (ALPR) cameras store an image of your license plate, vehicle make and model, and location in a searchable database for up to 12 months every time you drive past one. Before today, how aware were you of that fact? (6s6r3ex)",
    "Police can search the Automatic License Plate Reader (ALPR) database for your data without a warrant or approval from any other organization. Before today, how aware were you of that fact? (zke2ete)",
    "Police can legally share your license plate Automatic License Plate Reader (ALPR) data with other local governments/police departments within California at any time without a warrant. Before today, how aware were you of that fact? (skzr4a8)"
]

# Support columns
support_cols = [
    "How supportive are you of Automatic License Plate Reader (ALPR) cameras installed by local governments and used by law enforcement? (y7ka0mc)",
    "How supportive are you of private individuals or businesses installing Automatic License Plate Reader (ALPR) cameras and sharing the data voluntarily with police? (uktyzgu)"
]

# Recode awareness to numeric: 0=Not aware, 1=Somewhat aware, 2=Very aware
def recode_awareness(val):
    if pd.isna(val):
        return None
    val = str(val).lower()
    if "not aware" in val:
        return 0
    elif "somewhat aware" in val:
        return 1
    elif "very aware" in val:
        return 2
    else:
        return None

for col in awareness_cols:
    df[col + "_num"] = df[col].apply(recode_awareness)

# Recode support to numeric if needed
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
            return float(val)  # if already numeric
        except:
            return None

for col in support_cols:
    df[col + "_num"] = df[col].apply(recode_support)

# Calculate average support by awareness for each awareness column
for aware_col in awareness_cols:
    for support_col in support_cols:
        grouped = df.groupby(aware_col + "_num")[support_col + "_num"].mean()

        # Wrap the long title
        wrapped_title = "\n".join(textwrap.wrap(f"{support_col} by awareness of ALPR fact", 50))

        # Plot
        grouped.plot(kind='bar', figsize=(6,4), title=wrapped_title)
        plt.xlabel("Awareness Level (0=Not aware, 2=Very aware)")
        plt.ylabel("Average Support")
        plt.tight_layout()
        plt.show()
