"""
Name: Seichi Shinozaki
CS230: Section 2
Data: LEGO Store locations in the USA and Canada
URL: Link to your web application on Streamlit Cloud (if posted)

Description:
LEGO Store Explorer is a Streamlit application that helps users find LEGO store
locations across the USA and Canada. It uses store data from a CSV file, lets
users filter results by country and state/province, and calculates distances
from a user-entered location to each store. The app also includes charts,
tables, and an interactive map to make the store data easier to explore.
"""

import math
import matplotlib.pyplot as plt
import pandas as pd
import pydeck as pdk
import streamlit as st


@st.cache_data
def load_data(file_name):
    """Load LEGO store data into a DataFrame."""
    df = pd.read_csv(file_name)
    return df


def clean_data(df):
    """Prepare the data for analysis."""
    df = df.copy()
    df["Store Count"] = 1
    df = df.dropna(subset=["Store Name", "City", "State", "Country", "Latitude", "Longitude"])
    return df


def filter_data(df, country="USA", state="All"):
    """Filter the data by country and state/province."""
    filtered = df[df["Country"] == country]

    if state != "All":
        filtered = filtered[filtered["State"] == state]

    return filtered, len(filtered)


def get_state_counts(df):
    """Create a pivot table of store counts by state/province."""
    state_counts = pd.pivot_table(
        df,
        values="Store Count",
        index="State",
        aggfunc="sum"
    ).reset_index()

    state_counts = state_counts.sort_values(by="Store Count", ascending=False)
    return state_counts


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in miles between two latitude/longitude points."""
    radius = 3958.8

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    distance = radius * c
    return distance


def add_distance_column(df, user_lat, user_lon):
    """Add a distance column showing miles from the user to each store."""
    df = df.copy()

    df["Distance_Miles"] = df.apply(
        lambda row: haversine(user_lat, user_lon, row["Latitude"], row["Longitude"]),
        axis=1
    )

    df = df.sort_values(by="Distance_Miles")
    return df


def get_nearest_store(df):
    """Return the nearest and farthest store."""
    nearest = df.loc[df["Distance_Miles"].idxmin()]
    farthest = df.loc[df["Distance_Miles"].idxmax()]
    return nearest, farthest


def build_store_summaries(df, top_n):
    """Create a list of dictionaries for the nearest stores."""
    nearest_rows = df.head(top_n)
    store_list = []

    for _, row in nearest_rows.iterrows():
        store_info = {
            "Store Name": row["Store Name"],
            "City": row["City"],
            "State": row["State"],
            "Country": row["Country"],
            "Distance_Miles": round(row["Distance_Miles"], 2)
        }
        store_list.append(store_info)

    return store_list


def display_store_summaries(store_list):
    """Display nearest store summaries."""
    st.write("### Nearest Stores Summary")

    for store in store_list:
        name = store.get("Store Name", "Unknown Store")
        city = store.get("City", "Unknown City")
        state = store.get("State", "Unknown State")
        country = store.get("Country", "Unknown Country")
        distance = store.get("Distance_Miles", 0)

        st.write(f"**{name}** - {city}, {state}, {country} ({distance} miles)")


def make_state_bar_chart(state_counts):
    """Display a bar chart of states/provinces with the most LEGO stores."""
    top_states = state_counts.head(10)

    fig, ax = plt.subplots()
    ax.bar(top_states["State"], top_states["Store Count"])
    ax.set_title("Top 10 States/Provinces by Number of LEGO Stores")
    ax.set_xlabel("State/Province")
    ax.set_ylabel("Number of Stores")
    plt.xticks(rotation=45)
    st.pyplot(fig)


def make_country_chart(df):
    """Display a pie chart comparing USA and Canada."""
    country_counts = df.groupby("Country")["Store Count"].sum()

    fig, ax = plt.subplots()
    ax.pie(country_counts, labels=country_counts.index, autopct="%1.1f%%")
    ax.set_title("LEGO Store Distribution by Country")
    st.pyplot(fig)


def make_map(df):
    """Display LEGO stores on an interactive map."""
    st.pydeck_chart(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=pdk.ViewState(
                latitude=df["Latitude"].mean(),
                longitude=df["Longitude"].mean(),
                zoom=3,
                pitch=35,
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=df,
                    get_position="[Longitude, Latitude]",
                    get_radius=50000,
                    pickable=True,
                )
            ],
            tooltip={
                "text": "{Store Name}\n{City}, {State}\n{Country}\nDistance: {Distance_Miles:.2f} miles"
            },
        )
    )


def main():
    st.set_page_config(page_title="LEGO Store Explorer", layout="wide")
    st.title("LEGO Store Explorer")
    st.write("This app explores LEGO store locations across the USA and Canada.")
    st.write("It filters stores, compares store counts, and finds the nearest location.")

    # Make sure this CSV file is in the same folder as this Python file
    df = load_data("LegoUSACanada(in).csv")
    df = clean_data(df)

    st.sidebar.header("Filter Options")

    country = st.sidebar.selectbox(
        "Select Country",
        sorted(df["Country"].dropna().unique())
    )

    state_values = df[df["Country"] == country]["State"].dropna().unique().tolist()
    state_list = ["All"] + sorted([state for state in state_values])

    state = st.sidebar.selectbox("Select State/Province", state_list)

    user_lat = st.sidebar.number_input("Enter your latitude", value=42.3601, format="%.4f")
    user_lon = st.sidebar.number_input("Enter your longitude", value=-71.0589, format="%.4f")
    top_n = st.sidebar.slider("How many nearest stores to show", 3, 15, 5)

    filtered_df, total_stores = filter_data(df, country, state)

    if filtered_df.empty:
        st.warning("No stores match your selected filters.")
        return

    filtered_df = add_distance_column(filtered_df, user_lat, user_lon)

    st.subheader(f"Filtered Store Count: {total_stores}")

    nearest, farthest = get_nearest_store(filtered_df)

    st.write("### Closest Store")
    st.write(f"**{nearest['Store Name']}**")
    st.write(f"{nearest['City']}, {nearest['State']} - {nearest['Country']}")
    st.write(f"Distance: {nearest['Distance_Miles']:.2f} miles")

    st.write("### Farthest Store")
    st.write(f"**{farthest['Store Name']}**")
    st.write(f"{farthest['City']}, {farthest['State']} - {farthest['Country']}")
    st.write(f"Distance: {farthest['Distance_Miles']:.2f} miles")

    state_counts = get_state_counts(filtered_df)

    make_state_bar_chart(state_counts)
    make_country_chart(df)
    make_map(filtered_df)

    st.write("### Nearest Stores Table")
    st.dataframe(
        filtered_df[["Store Name", "City", "State", "Country", "Distance_Miles"]].head(top_n)
    )

    store_list = build_store_summaries(filtered_df, top_n)
    display_store_summaries(store_list)

    st.write("### State/Province Summary")
    st.dataframe(state_counts)


if __name__ == "__main__":
    main()