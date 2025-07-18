import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import os
from census import Census

"""
This script pulls the distribution of Automated License Plate Reader (ALPR) cameras 
across census tracts in selected California counties (e.g., San Francisco, Santa Clara).

For each county, it:
- Fetches ALPR camera locations from OpenStreetMap via the Overpass API
- Loads Census tract shapefiles
- Retrieves tract-level demographic data from the U.S. Census API:
    - Median household income (ACS 5-Year Estimates)
    - Racial composition (Non-Hispanic White, Black, Asian, Hispanic/Latino)
- Assigns ALPR cameras to census tracts using spatial joins
- Aggregates the number of cameras per tract
- Merges income and racial data with ALPR counts
- Computes racial group percentages within each tract
- Saves a CSV file per county containing ALPR counts and demographic context

Output files are named like: 'san_francisco_alpr_race_income.csv'
"""

# Load Census API Key
CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")
if not CENSUS_API_KEY:
    raise ValueError("Census API key is missing! Set it as an environment variable.")
c = Census(CENSUS_API_KEY)

# === DATA FETCH FUNCTIONS ===

def fetch_census_income(county_fips):
    """Fetch median income data for Census Tracts from the Census API."""
    try:
        data = c.acs5.state_county_tract(
            fields=["B19013_001E"],  # Median household income
            state_fips="06",  # California
            county_fips=county_fips,
            tract="*",
            year=2021
        )
        return pd.DataFrame(data).rename(columns={"B19013_001E": "median_income"})
    except Exception as e:
        print(f"Error fetching Census income data for county {county_fips}: {e}")
        return pd.DataFrame()

def fetch_census_race_data(county_fips):
    """Fetch racial composition + Hispanic origin for Census Tracts."""
    try:
        data = c.acs5.state_county_tract(
            fields=[
                "B03002_001E",  # Total Population
                "B03002_003E",  # Non-Hispanic White
                "B03002_004E",  # Non-Hispanic Black
                "B03002_006E",  # Non-Hispanic Asian
                "B03002_012E",  # Hispanic/Latino (of any race)
            ],
            state_fips="06",
            county_fips=county_fips,
            tract="*",
            year=2021
        )
        df = pd.DataFrame(data).rename(columns={
            "B03002_001E": "total_pop",
            "B03002_003E": "white_non_hispanic",
            "B03002_004E": "black_pop",
            "B03002_006E": "asian_pop",
            "B03002_012E": "hispanic_pop"
        })
        return df
    except Exception as e:
        print(f"Error fetching extended race data: {e}")
        return pd.DataFrame()

def fetch_alpr_locations():
    """Fetch ALPR camera locations from OpenStreetMap (Overpass API)."""
    query = """
    [out:json];
    node["man_made"="surveillance"]["surveillance:type"="ALPR"];
    out body;
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    response = requests.get(overpass_url, params={"data": query})
    if response.status_code != 200:
        print(f"Overpass API request failed: {response.status_code}")
        return None
    data = response.json()
    locations = [
        {"id": element["id"], "latitude": element["lat"], "longitude": element["lon"]}
        for element in data.get("elements", [])
        if "lat" in element and "lon" in element
    ]
    print(f"Found {len(locations)} ALPR cameras.")
    return pd.DataFrame(locations)

def load_census_shapefile(file_path):
    """Load Census Tracts shapefile for a county."""
    try:
        census_gdf = gpd.read_file(file_path)
        census_gdf = census_gdf.to_crs("EPSG:4326")
        return census_gdf
    except Exception as e:
        print(f"Error loading Census shapefile: {e}")
        return None

# === SPATIAL JOIN + MERGE ===

def process_alpr_data(alpr_df, census_gdf, census_income_df):
    """Assign ALPR locations to Census Tracts and analyze camera distribution by income."""
    alpr_gdf = gpd.GeoDataFrame(
        alpr_df,
        geometry=gpd.points_from_xy(alpr_df.longitude, alpr_df.latitude),
        crs="EPSG:4326"
    )
    census_gdf = census_gdf.to_crs(alpr_gdf.crs)
    alpr_with_tracts = gpd.sjoin(alpr_gdf, census_gdf, how="left", predicate="within")

    # Identify tract column
    possible_tract_columns = ["tractce", "TRACT", "TRACTCE10", "GEOID", "tract"]
    for col in possible_tract_columns:
        if col in alpr_with_tracts.columns:
            tract_column = col
            break
    else:
        raise KeyError("No valid 'tract' column found in the Census shapefile!")

    alpr_with_tracts = alpr_with_tracts.rename(columns={tract_column: "tract"})
    alpr_with_tracts["tract"] = alpr_with_tracts["tract"].astype(str).str.zfill(6)

    alpr_counts = (
        alpr_with_tracts.groupby("tract").size()
        .reset_index(name="num_alpr_cameras")
    )
    merged_df = pd.merge(alpr_counts, census_income_df, on="tract", how="left")
    return merged_df

# === MAIN PROCESSING LOOP ===

counties = {
    "075": ("San_Francisco", "shapefiles/Census_2020_Tracts-for-San Francisco_20250305.zip"),
    "085": ("Santa_Clara", "shapefiles/CensusTract2020_20250320.zip"),
    # "001": ("Alameda", "shapefiles/Alameda_Census_Tracts.zip")  # Optional
}

def main():
    print("Fetching ALPR camera locations...")
    alpr_df = fetch_alpr_locations()
    if alpr_df is None or alpr_df.empty:
        print("No ALPR data retrieved. Exiting.")
        return

    for county_fips, (county_name, shapefile) in counties.items():
        print(f"\nProcessing {county_name} County...")

        census_income_df = fetch_census_income(county_fips)
        if census_income_df.empty:
            print(f"Failed to retrieve Census income data for {county_name}. Skipping.")
            continue

        race_df = fetch_census_race_data(county_fips)
        if race_df.empty:
            print(f"Failed to retrieve Census race data for {county_name}. Skipping.")
            continue

        census_gdf = load_census_shapefile(shapefile)
        if census_gdf is None or census_gdf.empty:
            print(f"Failed to load Census shapefile for {county_name}. Skipping.")
            continue

        alpr_result_df = process_alpr_data(alpr_df, census_gdf, census_income_df)

        # Merge race data
        alpr_result_df = alpr_result_df.merge(race_df, on="tract", how="left")
        alpr_result_df = alpr_result_df.rename(columns={"white_non_hispanic": "white_pop"})

        # Compute percentages
        alpr_result_df["white_pct"] = alpr_result_df["white_pop"] / alpr_result_df["total_pop"]
        alpr_result_df["black_pct"] = alpr_result_df["black_pop"] / alpr_result_df["total_pop"]
        alpr_result_df["asian_pct"] = alpr_result_df["asian_pop"] / alpr_result_df["total_pop"]
        alpr_result_df["hispanic_pct"] = alpr_result_df["hispanic_pop"] / alpr_result_df["total_pop"]

        # Save results
        file_path = f"{county_name.lower()}_alpr_race_income.csv"
        alpr_result_df.to_csv(file_path, index=False)
        print(f"Saved {county_name} ALPR + Census data to {file_path}")

if __name__ == "__main__":
    main()
