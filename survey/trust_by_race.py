from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import textwrap

# Load CSV
file_path = Path(__file__).parent / "alpr_survey_results.csv"
df = pd.read_csv(file_path)

# Column names
trust_col = "Who do you trust to make decisions about how surveillance is used in your city? (Select all that apply) (w02ux9i)"
race_col = "What is your race or ethnicity? (Select all that apply) (d8morv7)"

# Ensure columns exist
if trust_col not in df.columns or race_col not in df.columns:
    raise ValueError("Columns not found in CSV!")

# Drop rows with missing data
df_subset = df[[trust_col, race_col]].dropna()

# Split multiple responses and explode
df_subset[trust_col] = df_subset[trust_col].str.split(',')
df_subset[race_col] = df_subset[race_col].str.split(',')

df_exploded = df_subset.explode(trust_col).explode(race_col)

# Strip whitespace
df_exploded[trust_col] = df_exploded[trust_col].str.strip()
df_exploded[race_col] = df_exploded[race_col].str.strip()

# Count occurrences
trust_counts = df_exploded.groupby(race_col)[trust_col].value_counts().unstack(fill_value=0)

# Plot horizontal stacked bar chart
plt.figure(figsize=(14,8), constrained_layout=True)
ax = trust_counts.plot(
    kind='barh', 
    stacked=True, 
    colormap='tab20', 
    ax=plt.gca()
)

plt.xlabel("Number of Respondents")
plt.ylabel("Racial Background")
plt.title("\n".join(textwrap.wrap(
    "Who Do People Trust Most to Make Surveillance Decisions? by Racial Background", 60
)))

# Move legend far enough outside to show all labels
plt.legend(
    title="Decision-Maker", 
    bbox_to_anchor=(1.3, 1),  # move further right
    loc='upper left',
    fontsize=10
)
plt.yticks(rotation=0)

# Save figure
output_dir = Path(__file__).parent / "plots"
output_dir.mkdir(exist_ok=True)
plt.savefig(output_dir / "trust_surveillance_by_race.png", bbox_inches='tight')
plt.close()
