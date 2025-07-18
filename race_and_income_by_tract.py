"""
This script fetches Census ACS 5-Year 2021 data for selected counties in California (San Francisco, Alameda, San Mateo),
including median household income and racial/ethnic demographics at the census tract level.

Specifically, it:
- Retrieves total population, White (non-Hispanic), Black, Asian, Hispanic, and median income data using the Census API.
- Calculates the percentage of people of color (POC) per tract as: (Total Population - White Population) / Total Population.
- Constructs a full GEOID for each tract.
- Saves the resulting dataset to a CSV file for each county (e.g., 'san_francisco_race_income_by_tract.csv').

Useful for analyzing spatial patterns of racial demographics and income.
"""

from census import Census
import pandas as pd
import os

# Load Census API key from environment
CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")
c = Census(CENSUS_API_KEY)

def fetch_race_income_data(state_fips, county_fips, county_name):
    data = c.acs5.state_county_tract(
        fields=[
            "B03002_001E",  # Total Population
            "B03002_003E",  # White (Non-Hispanic)
            "B03002_004E",  # Black
            "B03002_006E",  # Asian
            "B03002_012E",  # Hispanic or Latino
            "B19013_001E",  # Median Household Income
        ],
        state_fips=state_fips,
        county_fips=county_fips,
        tract="*",
        year=2021
    )

    df = pd.DataFrame(data).rename(columns={
        "B03002_001E": "total_pop",
        "B03002_003E": "white_pop",
        "B03002_004E": "black_pop",
        "B03002_006E": "asian_pop",
        "B03002_012E": "hispanic_pop",
        "B19013_001E": "median_income"
    })

    # Format GEOID
    df["tract"] = df["tract"].astype(str).str.zfill(6)
    df["county"] = df["county"].astype(str).str.zfill(3)
    df["GEOID"] = "06" + df["county"] + df["tract"]

    # Calculate Percent POC
    df["POC_pct"] = ((df["total_pop"] - df["white_pop"]) / df["total_pop"]) * 100

    # Save
    filename = f"{county_name.lower().replace(' ', '_')}_race_income_by_tract.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Saved: {filename}")

    return df

# Run for each county
sf_df = fetch_race_income_data("06", "075", "San Francisco")
alameda_df = fetch_race_income_data("06", "001", "Alameda")
san_mateo_df = fetch_race_income_data("06", "081", "San Mateo")
