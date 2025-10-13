from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Load CSV
file_path = Path(__file__).parent / "alpr_survey_results.csv"
df = pd.read_csv(file_path)

# Columns for ALPR awareness facts
awareness_cols = {
    "Storage of plate & vehicle info up to 12 months": 
        "In some Bay Area cities, Automatic License Plate Reader (ALPR) cameras store an image of your license plate, vehicle make and model, and location in a searchable database for up to 12 months every time you drive past one. Before today, how aware were you of that fact? (6s6r3ex)",
    "Police can search ALPR data without a warrant": 
        "Police can search the Automatic License Plate Reader (ALPR) database for your data without a warrant or approval from any other organization. Before today, how aware were you of that fact? (zke2ete)",
    "Police can share ALPR data freely in CA": 
        "Police can legally share your license plate Automatic License Plate Reader (ALPR) data with other local governments/police departments within California at any time without a warrant. Before today, how aware were you of that fact? (skzr4a8)"
}

# Race column
race_col = "What is your race or ethnicity? (Select all that apply) (d8morv7)"
main_races = ["White", "Asian or Pacific Islander", "Black or African American", 
              "Hispanic or Latino", "Native American or Indigenous", "Middle Eastern or North African"]

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

# Apply recoding
for col in awareness_cols.values():
    df[col + "_num"] = df[col].apply(recode_awareness)

# Plot each fact by racial background
for title, col in awareness_cols.items():
    avg_by_race = {}
    for race in main_races:
        # Include all rows that mention this race, even in combinations
        group_rows = df[df[race_col].str.contains(race, case=False, na=False)]
        avg_support = group_rows[col + "_num"].mean()
        avg_by_race[race] = avg_support

    # Plot
    plt.figure(figsize=(8,5))
    plt.bar(avg_by_race.keys(), avg_by_race.values(), color='skyblue')
    plt.title(f"Average Awareness of: {title} by Race/Ethnicity")
    plt.ylabel("Average Awareness (0=Not aware, 2=Very aware)")
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0,2)
    plt.tight_layout()
    plt.show()
