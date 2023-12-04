import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Load your data
df_clubs = pd.read_csv("./data/clubs.csv")
df_competitions = pd.read_csv("./data/competitions.csv")
df_player_valuations = pd.read_csv("./data/player_valuations.csv")
df_players = pd.read_csv("./data/players.csv")
df_appearances = pd.read_csv('./data/appearances.csv')

# Merge the club data with the competition data
df_merged = pd.merge(df_clubs, df_competitions[['competition_id', 'country_name']], how='left', left_on='domestic_competition_id', right_on='competition_id')

# Merge the player information
df_merged = pd.merge(df_merged, df_players[df_players['last_season'] == 2023][['current_club_id', 'name', 'date_of_birth', 'player_id']], how='left', left_on='club_id', right_on='current_club_id', suffixes=('_club','_player'))

# Merge with player valuations for the selected season (e.g., last_season = 2023)
df_merged = pd.merge(df_merged, df_player_valuations[df_player_valuations['last_season'] == 2023][['market_value_in_eur', 'player_id']], how='left', left_on='player_id', right_on='player_id')

# Calculate age based on date of birth
df_merged['dob'] = pd.to_datetime(df_merged['date_of_birth'])
df_merged['age'] = np.round((datetime.now() - df_merged['dob']).dt.days/365, 2)

# Compute the total market value based on individual player market value
total_market_value_per_club = df_merged.groupby('name_club').agg({'market_value_in_eur': 'sum'}).reset_index()
avg_minutes_played = df_appearances.groupby('player_id').agg(avg_played_minutes=('minutes_played', 'mean'), total_played_minutes=('minutes_played','sum')).reset_index()

df_merged['market_value_in_eur'] = df_merged['market_value_in_eur'].fillna(0)

df_merged = pd.merge(df_merged, avg_minutes_played[['avg_played_minutes', 'total_played_minutes', 'player_id']], how='left', left_on='player_id', right_on='player_id')


# Set app title and description
st.title("Club Analysis Dashboard")
st.sidebar.header("Settings")

# Sidebar: Country and Competition Selection
selected_country = st.sidebar.selectbox("Select Country", df_merged['country_name'].unique())
competitions_in_country = df_merged[df_merged['country_name'] == selected_country]['domestic_competition_id'].unique()
selected_competition = st.sidebar.selectbox("Select Competition", competitions_in_country)



# Filter the DataFrame based on user selection
filtered_df = df_merged[(df_merged['country_name'] == selected_country) & (df_merged['domestic_competition_id'] == selected_competition)]

# Sidebar: Club Selection
selected_clubs = st.sidebar.multiselect("Select Clubs", filtered_df['name_club'].unique())

# Sidebar: Metrics Selection
selected_metrics = st.sidebar.multiselect(
    "Select Metrics",
    ["squad_size", "average_age", "foreigners_percentage"]
)


# Player Market Value Section
st.header("Player Market Value Analysis")

if selected_clubs:
    for club in selected_clubs:
        # Create a DataFrame for the current club
        club_data = filtered_df[filtered_df['name_club'] == club]

        # Plotly Express Box Plot for player market value
        fig = px.bar(
            club_data,
            x="market_value_in_eur",
            y="age",
            title=f"Distribution of Player Market Value",
            hover_name="country_name",
        )
        fig.update_layout(showlegend=True)
        st.plotly_chart(fig)

        # Display descriptive statistics for player market value
        st.subheader(f"Descriptive Statistics for Player Market Value - {club}:")
        st.write("Note: Values are in EUR")
        st.write(club_data['market_value_in_eur'].describe())

else:
    st.warning("Select at least one club for analysis.")

# Comparison Section
st.header("Club Comparison")

if selected_clubs and selected_metrics:
    for club in selected_clubs:
        st.subheader(f"{club} Statistics:")
        club_data = filtered_df[filtered_df['name_club'] == club]
        summary_stats = pd.DataFrame({
            'Metric': selected_metrics,
            'Mean': [club_data[metric].mean() for metric in selected_metrics],
            'Median': [club_data[metric].median() for metric in selected_metrics],
            'Max': [club_data[metric].max() for metric in selected_metrics],
            'Min': [club_data[metric].min() for metric in selected_metrics],
            'Std Dev': [club_data[metric].std() for metric in selected_metrics],
        })

        # Apply custom styling to the dataframe
        summary_stats_styled = summary_stats.style.bar(subset=['Mean', 'Median'], color='#d65f5f')\
            .bar(subset=['Max', 'Min'], color='#5fba7d')\
            .bar(subset=['Std Dev'], color='#5fba7d', align='mid')

        # Display the styled dataframe
        st.dataframe(summary_stats_styled)

else:
    st.warning("Select at least one club and one metric for analysis.")


# Comparison Section -------------------- SCATTER
st.write(filtered_df['market_value_in_eur'].describe())


total_market_value_per_club

st.header("Club Comparison -- SCATTER")

fig = px.scatter(
    filtered_df,
    x="avg_played_minutes",
    y="age",
    color="name_player",
    size="market_value_in_eur",
    title="Club Comparison",
    log_x=True
)
st.plotly_chart(fig)


fig = px.scatter(
    filtered_df,
    x="total_played_minutes",
    y="age",
    color="name_club",
    size="market_value_in_eur",
    title="Club Comparison",
    log_x=True
)
st.plotly_chart(fig)

# Seasonal Performance Section
st.header("Seasonal Performance")
# Add a line chart or other relevant visualizations for seasonal performance

# Geographical Data Section
st.header("Geographical Data")
# Assuming you have a DataFrame df_geographical_data with geographical data
# Display a map or other relevant visualization
if "latitude" in df_clubs.columns and "longitude" in df_clubs.columns:
    fig_map = px.scatter_geo(
        filtered_df,
        lat="latitude",
        lon="longitude",
        text="name",
        title="Club Locations",
        template="plotly",
    )
    st.plotly_chart(fig_map)
else:
    st.warning("Geographical data not available for selected clubs.")


# Coach Analysis Section
st.header("Coach Analysis")
# Assuming you have a DataFrame df_coach_analysis with coach data
# Display relevant coach information
if "coach_name" in df_clubs.columns:
    st.write("Current Coaches of Selected Clubs:")
    st.write(filtered_df[["name_club", "coach_name"]].drop_duplicates())
else:
    st.warning("Coach data not available for selected clubs.")

# Add more sections as needed...

# Finalize the app