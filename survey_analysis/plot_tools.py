from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Relative path to CSV (same folder as script)
file_path = Path(__file__).parent / "bay_responses.csv"

# Update the column name exactly as in your CSV
col = 'Which of the following surveillance tools have you heard of or seen in your city? (Select all that apply) (8dl9hmt)'

# Process survey responses
tools_data = df[col].dropna()
tools_split = tools_data.str.split(',')
all_tools = [tool.strip() for sublist in tools_split for tool in sublist]

# Count occurrences
tools_counts = pd.Series(all_tools).value_counts()

# Plot horizontal bar chart
plt.figure(figsize=(14, 8))  # make bigger so labels fit
tools_counts.plot(kind='barh')

plt.xlabel("Number of Respondents")
plt.ylabel("Surveillance Tool")
plt.title("Most Recognized Surveillance Tools in the Community")

plt.gca().invert_yaxis()  # biggest at top
plt.yticks(fontsize=9)    # smaller font for long labels

plt.tight_layout()        # auto-adjust so nothing is cut off
plt.show()
