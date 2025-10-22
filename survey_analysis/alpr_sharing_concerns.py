from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
import numpy as np

# Load CSV
file_path = Path(__file__).parent / "bay_responses.csv"
df = pd.read_csv(file_path)

# Map long column names to descriptive short names
rename_map = {
    "In some Bay Area cities, Automatic License Plate Reader (ALPR) cameras store an image of your license plate, vehicle make and model, and location in a searchable database for up to 12 months every time you drive past one. Before today, how aware were you of that fact? (6s6r3ex)": "ALPR_storage_12mo",
    "Police can search the Automatic License Plate Reader (ALPR) database for your data without a warrant or approval from any other organization. Before today, how aware were you of that fact? (zke2ete)": "ALPR_warrantless_search",
    "Police can legally share your license plate Automatic License Plate Reader (ALPR) data with other local governments/police departments within California at any time without a warrant. Before today, how aware were you of that fact? (skzr4a8)": "ALPR_data_sharing",
    "How supportive are you of Automatic License Plate Reader (ALPR) cameras installed by local governments and used by law enforcement? (y7ka0mc)": "support_govt",
    "How supportive are you of private individuals or businesses installing Automatic License Plate Reader (ALPR) cameras and sharing the data voluntarily with police? (uktyzgu)": "support_private"
}
df.rename(columns=rename_map, inplace=True)

# Awareness and support columns
awareness_cols = ["ALPR_storage_12mo", "ALPR_warrantless_search", "ALPR_data_sharing"]
support_cols = ["support_govt", "support_private"]

# Recode awareness
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

# Recode support
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

# X-axis labels and all possible levels
all_levels = [0, 1, 2]
labels_map = {0: "Not aware", 1: "Somewhat aware", 2: "Very aware"}
labels_all = [labels_map[i] for i in all_levels]

# Mapping for descriptive titles
title_map = {
    "ALPR_storage_12mo": "Awareness of ALPR storing license plate + vehicle info for 12 months",
    "ALPR_warrantless_search": "Awareness of warrantless police searches of ALPR data",
    "ALPR_data_sharing": "Awareness of ALPR data sharing with other governments/police"
}

# Output folder for saved plots
output_dir = Path(__file__).parent / "plots"
output_dir.mkdir(exist_ok=True)

# Plot support by awareness and save each plot
for aware_col in awareness_cols:
    grouped = df.groupby(aware_col + "_num")[[c + "_num" for c in support_cols]].mean()
    
    # Reindex to include all levels even if missing
    grouped = grouped.reindex(all_levels)
    
    x = np.array(all_levels)
    width = 0.35

    plt.figure(figsize=(8,5))
    plt.bar(x - width/2, grouped["support_govt_num"], width, label="Govt ALPR Support", color='skyblue')
    plt.bar(x + width/2, grouped["support_private_num"], width, label="Private ALPR Support", color='salmon')

    plt.xticks(x, labels_all)
    plt.ylabel("Average Support (0=Strongly Oppose, 4=Strongly Support)")
    plt.title("\n".join(textwrap.wrap(f"Support by awareness: {title_map[aware_col]}", 60)))
    plt.legend()
    plt.tight_layout()

    # Save the figure
    filename = output_dir / f"{aware_col}_support.png"
    print(f"filename downloaded: {filename}")
    plt.savefig(filename)
    plt.close()

print(f"Plots saved in folder: {output_dir}")
