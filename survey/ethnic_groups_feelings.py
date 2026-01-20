from pathlib import Path
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Load CSV
file_path = Path(__file__).parent / "alpr_survey_results.csv"
df = pd.read_csv(file_path)

# Columns
text_col = "How did surveillance make you feel or impact you? (urjiu1g)"
race_col = "What is your race or ethnicity? (Select all that apply) (d8morv7)"

# Optional: pick main racial groups to analyze
groups = ["Asian", "Black or African American", "White", "Hispanic or Latino"]

for group in groups:
    # Filter rows where race contains the group
    group_text = df[df[race_col].str.contains(group, na=False)][text_col].dropna()
    combined_text = " ".join(group_text)

    if combined_text.strip() == "":
        continue

    # Generate word cloud
    wc = WordCloud(width=800, height=400, background_color="white").generate(combined_text)

    plt.figure(figsize=(10,5))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.title(f"Common Words for {group}")
    plt.show()
