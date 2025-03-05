
import requests
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import os
from census import Census

# Load API Key
CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")

# Validate API key
if not CENSUS_API_KEY:
    raise ValueError("Census API key is missing! Set it as an environment variable.")

c = Census(CENSUS_API_KEY)


def fetch_census_income():
    """Fetch median income data for SF Census Tracts from the Census API."""
    tracts = "*"  # Get all tracts
    try:
        data = c.acs5.state_county_tract(
            fields=["B19013_001E"],  # Median household income
            state_fips="06",  # California
            county_fips="075",  # San Francisco
            tract=tracts,
            year=2021
        )
        return pd.DataFrame(data).rename(columns={"B19013_001E": "median_income"})
    except Exception as e:
        print(f"Error fetching Census data: {e}")
        return pd.DataFrame()


def fetch_alpr_locations():
    """Fetch ALPR camera locations from OpenStreetMap (Overpass API)."""
    query = """
    [out:json];
    node["man_made"="surveillance"]["surveillance:type"="ALPR"]["operator"="San Francisco Police Department"];
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


def load_census_shapefile():
    """Load Census Tracts shapefile for SF."""
    try:
        census_gdf = gpd.read_file("Census_2020_Tracts-for-San Francisco_20250305.zip")
        census_gdf = census_gdf.to_crs("EPSG:4326")  # Ensure WGS84 coordinate system
        return census_gdf
    except Exception as e:
        print(f"Error loading Census shapefile: {e}")
        return None


def process_alpr_data(alpr_df, census_gdf, census_income_df):
    """Assign ALPR locations to Census Tracts and analyze camera distribution by income."""
    
    # Convert ALPR DataFrame to GeoDataFrame
    alpr_gdf = gpd.GeoDataFrame(
        alpr_df,
        geometry=gpd.points_from_xy(alpr_df.longitude, alpr_df.latitude),
        crs="EPSG:4326"
    )

    # Spatial join: Assign each ALPR camera to a Census Tract
    alpr_with_tracts = gpd.sjoin(alpr_gdf, census_gdf, how="left", predicate="within")
    alpr_with_tracts = alpr_with_tracts.rename(columns={"tractce": "tract"})

    # Ensure tract column matches Census income data format
    alpr_with_tracts["tract"] = alpr_with_tracts["tract"].astype(str).str.zfill(6)

    # Count ALPR cameras per Census Tract
    alpr_counts = (
        alpr_with_tracts.groupby("tract").size()
        .reset_index(name="num_alpr_cameras")
    )

    # Merge ALPR camera counts with Census income data
    merged_df = pd.merge(alpr_counts, census_income_df, on="tract", how="left")

    return merged_df


def main():
    """Main function to execute data processing."""
    print("Fetching ALPR camera locations...")
    alpr_df = fetch_alpr_locations()
    if alpr_df is None or alpr_df.empty:
        print("No ALPR data retrieved. Exiting.")
        return

    print("Fetching Census median income data...")
    census_income_df = fetch_census_income()
    if census_income_df.empty:
        print("Failed to retrieve Census income data. Exiting.")
        return

    print("Loading Census tract shapefile...")
    census_gdf = load_census_shapefile()
    if census_gdf is None or census_gdf.empty:
        print("Failed to load Census shapefile. Exiting.")
        return

    print("Processing ALPR data with Census Tracts...")
    result_df = process_alpr_data(alpr_df, census_gdf, census_income_df)

    # Save results
    result_df.to_csv("alpr_by_income.csv", index=False)
    print("Analysis complete! Results saved to 'alpr_by_income.csv'.")

    # Display results
    print(result_df.head())


if __name__ == "__main__":
    main()
