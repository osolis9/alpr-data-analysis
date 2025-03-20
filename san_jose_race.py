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


def fetch_census_race_data():
    """Fetch racial demographics for Census Tracts in Santa Clara County."""
    try:
        data = c.acs5.state_county_tract(
            fields=[
                "B02001_001E",  # Total Population
                "B02001_002E",  # White
                "B02001_003E",  # Black or African American
                "B02001_004E",  # American Indian/Alaska Native
                "B02001_005E",  # Asian
                "B02001_006E",  # Native Hawaiian/Pacific Islander
                "B02001_007E",  # Some other race
                "B02001_008E",  # Two or more races
            ],
            state_fips="06",  # California
            county_fips="085",  # Santa Clara County
            tract="*",  # Get all tracts in Santa Clara County
            year=2021
        )

        df = pd.DataFrame(data)

        # Rename columns for clarity
        df = df.rename(columns={
            "B02001_001E": "total_population",
            "B02001_002E": "white",
            "B02001_003E": "black",
            "B02001_004E": "native_american",
            "B02001_005E": "asian",
            "B02001_006E": "pacific_islander",
            "B02001_007E": "other_race",
            "B02001_008E": "two_or_more"
        })

        # Convert tract column to match shapefile format
        df["tract"] = df["tract"].astype(str).str.zfill(6)

        # Calculate percentage for each race
        race_columns = ["white", "black", "native_american", "asian", "pacific_islander", "other_race", "two_or_more"]
        for col in race_columns:
            df[f"{col}_pct"] = (df[col] / df["total_population"]) * 100

        return df

    except Exception as e:
        print(f"Error fetching Census race data: {e}")
        return pd.DataFrame()


def fetch_alpr_locations_sj():
    """Fetch ALPR camera locations from OpenStreetMap for San Jose."""
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

    print(f"Found {len(locations)} ALPR cameras in San Jose.")
    return pd.DataFrame(locations)


def load_census_shapefile():
    """Load Census Tracts shapefile for Santa Clara County."""
    try:
        census_gdf = gpd.read_file("santa_clara_2020_census_tract.zip")
        census_gdf = census_gdf.to_crs("EPSG:4326")  # Ensure WGS84 coordinate system
        return census_gdf
    except Exception as e:
        print(f"Error loading Census shapefile: {e}")
        return None


def process_alpr_data(alpr_df, census_gdf, census_race_df):
    """Assign ALPR locations to Census Tracts and analyze camera distribution by race."""
    
    # Convert ALPR DataFrame to GeoDataFrame
    alpr_gdf = gpd.GeoDataFrame(
        alpr_df,
        geometry=gpd.points_from_xy(alpr_df.longitude, alpr_df.latitude),
        crs="EPSG:4326"
    )

    # Spatial join: Assign each ALPR camera to a Census Tract
    alpr_with_tracts = gpd.sjoin(alpr_gdf, census_gdf, how="left", predicate="within")
    alpr_with_tracts = alpr_with_tracts.rename(columns={"tractce": "tract"})

    # Ensure tract column matches Census race data format
    alpr_with_tracts["tract"] = alpr_with_tracts["tract"].astype(str).str.zfill(6)

    # Count ALPR cameras per Census Tract
    alpr_counts = (
        alpr_with_tracts.groupby("tract").size()
        .reset_index(name="num_alpr_cameras")
    )

    # Merge ALPR camera counts with Census race data
    merged_df = pd.merge(alpr_counts, census_race_df, on="tract", how="left")

    return merged_df


def main():
    """Main function to execute data processing."""
    print("Fetching ALPR camera locations for San Jose...")
    alpr_df = fetch_alpr_locations_sj()
    if alpr_df is None or alpr_df.empty:
        print("No ALPR data retrieved. Exiting.")
        return

    print("Fetching Census race data for Santa Clara County...")
    census_race_df = fetch_census_race_data()
    if census_race_df.empty:
        print("Failed to retrieve Census race data. Exiting.")
        return

    print("Loading Census tract shapefile for Santa Clara County...")
    census_gdf = load_census_shapefile()
    if census_gdf is None or census_gdf.empty:
        print("Failed to load Census shapefile. Exiting.")
        return

    print("Processing ALPR data with Census Tracts...")
    result_df = process_alpr_data(alpr_df, census_gdf, census_race_df)

    # Save results
    result_df.to_csv("alpr_by_race.csv", index=False)
    print("Analysis complete! Results saved to 'alpr_by_race.csv'.")

    # Display results
    print(result_df.head())


if __name__ == "__main__":
    main()
