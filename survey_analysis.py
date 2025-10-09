import pandas as pd

# Load San Francisco ZIPs
sf_zip_path = "San_Francisco_ZIP_Codes_20250901.csv"
df_zip = pd.read_csv(sf_zip_path)
sf_zip_codes = list(map(str, df_zip["zip_code"].dropna().unique()))  # ensure string format

oakland_zip_codes = [
    "94552", "94546", "94605", "94621", "94619" ,"94577", "94501", 
    "94607", "94578", "94602", "94516", "94705", "94708", "94611",
    "94580", "94601", "94579", "94608", "94603", "94502", "94618"
]

for zip in oakland_zip_codes:
   print(zip)

for zip in sf_zip_codes:
   print(zip)
# Load your survey data
survey_path = "ALPR General Survey Results v2.csv"
df_survey = pd.read_csv(survey_path)

# Clean up ZIP column in survey data
zip_col = "What is your ZIP code? (7bepp7b)"
df_survey[zip_col] = df_survey[zip_col].astype(str).str.strip()

zip_code_list = [(oakland_zip_codes, 'Oakland'), (sf_zip_codes, 'San Francisco')]
# Filter for San Francisco participants

for city_zip_codes, city in zip_code_list:

    df_city = df_survey[df_survey[zip_col].isin(city_zip_codes)]
    #save df_city to csv
    df_city.to_csv(f"{city}_survey_data.csv", index=False)

    print(f"Number of {city} respondents:", len(df_city))
    print(df_city.head())

    # Identify ALPR awareness columns
    awareness_cols = [col for col in df_city.columns if any(k in col for k in [
        #"50mnfkf",  # aware of Flock Safety installing ALPRs
        "6s6r3ex",  # aware of vehicle info stored for 12 months
        # "zke2ete",  # aware police can search data without warrant
        # "skzr4a8",  # aware police can share data without warrant
        # "3eg0nl6"   # aware of ALPR camera counts
    ])]
    city_answer_count = total = len(df_city)
    # Mark as unaware if they answered "1 = Not at all aware" to all
    def is_unaware(row):
        return all(str(row[col]).strip().startswith(("1", "2")) for col in awareness_cols)

    df_city["unaware_of_alpr"] = df_city.apply(is_unaware, axis=1)

    def get_45_count(question_id):
        id_col = [col for col in df_city.columns if question_id in col][0]
        df_city[f'results for {question_id} 4/5'] = df_city[id_col].astype(str).str.strip().str.startswith(("4", "5"))
        count = df_city[f'results for {question_id} 4/5'].sum()
        return count

    def get_12_count(question_id):
        id_col = [col for col in df_city.columns if question_id in col][0]
        df_city[f'results for {question_id} 1/2'] = df_city[id_col].astype(str).str.strip().str.startswith(("1", "2"))
        count = df_city[f'results for {question_id} 1/2'].sum()
        return count


    # sentiment_col = [col for col in df_city.columns if "ttzmqna" in col][0]
    # likey_share_with_fed_col = [col for col in df_city.columns if "gnnu4ft" in col][0]
    # # Mark negative sentiment: "1 = Strongly oppose" or "2 = Somewhat oppose"
    # df_city["public_should_have_insight"] = df_city[sentiment_col].astype(str).str.strip().str.startswith(("4", "5"))

    # df_city["how_likely_shared_with_fed"] = df_city[likey_share_with_fed_col].astype(str).str.strip().str.startswith(("4", "5"))
    # Calculate statistics
    total = len(df_city)
    unaware_count = df_city["unaware_of_alpr"].sum()
    # public_should_have_insight_count = df_city["public_should_have_insight"].sum()
    # share_with_fed_count = df_city["how_likely_shared_with_fed"].sum()
    # both_count = df_sf[df_sf["unaware_of_alpr"] & df_sf["public_should_have_insight"]].shape[0]
    public_should_have_insight_count = get_45_count("ttzmqna")
    share_with_fed_count = get_45_count("gnnu4ft")
    ok_for_police_to_track_count = get_12_count("nd9oynf")
    # Percentages
    print(f"📊 Total {city} respondents: {total}")
    print(f"🙈 Unaware of ALPRs: {unaware_count} ({unaware_count / total:.1%})")
    print(f"😠 Public should have imput or oversight before new tech is adopted: {public_should_have_insight_count} ({public_should_have_insight_count / total:.1%})")
    print(f"🤝 How likely to share ALPR data with federal agencies: {share_with_fed_count} ({share_with_fed_count / total:.1%})")
    print(f"** Not OK for police to track non-criminal vehicles with ALPRs: {ok_for_police_to_track_count} ({ok_for_police_to_track_count / total:.1%})")
    # print(f"🔻 Both unaware and negative: {both_count} ({both_count / total:.1%})")