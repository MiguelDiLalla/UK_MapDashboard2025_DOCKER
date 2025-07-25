# Function to get colorable columns (categorical or numeric, not lists/dicts)
def get_colorable_columns(df):
    """
    Purpose: Return columns suitable for coloring in visualizations.
    Input: DataFrame
    Output: List of valid column names
    Only includes columns that are categorical or numeric and not lists/dicts.
    """
    base_cols = ["Pension", "Tipo_Habitacion", "GastoTotal", "Noches", "Repetidor", "Antelacion_Range", "G_Etario", "Agencia"]
    valid_cols = []
    for col in base_cols:
        if col not in df.columns:
            continue
        if df[col].dtype.kind not in {'O', 'i', 'f'}:
            continue
        sample = df[col].dropna().iloc[:10]
        if any(isinstance(v, (list, tuple, dict, np.ndarray)) for v in sample):
            continue
        try:
            if df[col].nunique() > 1:
                valid_cols.append(col)
        except TypeError:
            continue
    return valid_cols
# Purpose: Streamlit dashboard for UK & Ireland hotel reservations analysis (Q1/Q2 2025)
# - Sidebar controls for hotel, canal filter, and color column selection
# - Map visualization using Plotly (dark theme, bright palette)
# - Rich logging for status and errors
# - Data sources: data/UK_2025_s1_GeoData.parquet and data/IE_2025_s1_GeoData.parquet
# - Style emulates the attached dashboard (black background, white text, bold colors)

import streamlit as st
st.set_page_config(layout="wide")
from rich.console import Console
from rich import print as rprint
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio

# Fixed category orders for certain columns so legends are always consistent
CATEGORY_ORDERS = {
    "G_Etario": [
        "De 15 a 24 años",
        "De 25 a 44 años",
        "De 45 a 64 años",
        "65 años o más",
    ],
    "Antelacion_Range": [
        "0-7 días",
        "8-14 días",
        "15-30 días",
        "31-60 días",
        "61-90 días",
        "91-365 días",
        "366+ días",
    ],
    "Repetidor": ["SI", "NO"],
}


def apply_category_orders(df):
    for col, order in CATEGORY_ORDERS.items():
        if col in df.columns:
            df[col] = pd.Categorical(df[col], categories=order, ordered=True)
    return df


# Set Plotly dark theme and bright color palette
def set_plotly_style():
    pio.templates.default = "plotly_dark"

def rich_log(msg):
    console = Console()
    console.log(msg)

set_plotly_style()



# Load data before sidebar controls
@st.cache_data
def load_data():
    """Load and combine UK and Ireland reservation data."""
    try:
        uk_df = pd.read_parquet("data/UK_2025_s1_GeoData.parquet")
        ie_df = pd.read_parquet("data/IE_2025_s1_GeoData.parquet")

        # Align columns between both datasets
        uk_cols = set(uk_df.columns)
        ie_cols = set(ie_df.columns)
        for col in uk_cols - ie_cols:
            ie_df[col] = np.nan
        for col in ie_cols - uk_cols:
            uk_df[col] = np.nan

        common_cols = uk_df.columns.tolist()
        ie_df = ie_df[common_cols]

        df = pd.concat([uk_df, ie_df], ignore_index=True)

        rich_log("[bold green]Loaded UK and Ireland datasets[/bold green]")
        return df
    except Exception as e:
        rich_log(f"[bold red]Failed to load data: {e}[/bold red]")
        st.error(f"Failed to load data: {e}")
        return pd.DataFrame()

df = apply_category_orders(load_data())

# Build color mappings after loading data to ensure categories are
# consistent across hotels. These mappings are used when coloring by
# 'Pension' or 'Tipo_Habitacion'.
def build_color_mapping(column):
    palette = px.colors.qualitative.Bold
    unique_vals = sorted(df[column].dropna().unique()) if column in df.columns else []
    return {val: palette[i % len(palette)] for i, val in enumerate(unique_vals)}

COLOR_MAPPINGS = {
    "Pension": build_color_mapping("Pension"),
    "Tipo_Habitacion": build_color_mapping("Tipo_Habitacion"),
}

# Helper to build Plotly color arguments based on column type. For
# categorical columns that have predefined mappings we provide the map
# so colors remain constant across plots.
def get_color_args(column):
    if df[column].dtype.kind in "fi":
        return {"color_continuous_scale": px.colors.sequential.Viridis}
    args = {"color_discrete_sequence": px.colors.qualitative.Bold}
    if column in COLOR_MAPPINGS:
        args["color_discrete_map"] = COLOR_MAPPINGS[column]
    return args


# Sidebar controls
st.sidebar.markdown(
    """
    <div style='text-align: center; margin-bottom: 2rem;'>
        <img src=\"https://hello.springhoteles.com/assets/Spring_Logo_White-3b27c43e.jpg\"
             width=\"220\" style=\"max-width: 90%; height: auto; margin-bottom: 0.5rem; border-radius: 18px; border: 2px solid #fff; box-shadow: 0 2px 12px rgba(0,0,0,0.25);\" />
    </div>
    """,
    unsafe_allow_html=True
)
st.sidebar.markdown("""
<style>
.sidebar .sidebar-content {background-color: #111111; color: white;}
</style>
<b style='color:white;font-size:20px;'>UK &amp; Ireland Hotel Reservations Dashboard</b>
""", unsafe_allow_html=True)

hotel_mode = st.sidebar.radio("Hotel Selection Mode", ["Todos", "Single"], index=0)
all_hotels = sorted(df["Hotel"].dropna().unique())
selected_hotels = []
if hotel_mode == "Todos":
    selected_hotels = all_hotels
    colorable = get_colorable_columns(df)
else:
    selected_hotels = st.sidebar.multiselect("Select Hotel(s)", all_hotels, default=all_hotels[:1])
    colorable = get_colorable_columns(df[df["Hotel"].isin(selected_hotels)])
default_idx = colorable.index("G_Etario") if "G_Etario" in colorable else 0
color_col = st.sidebar.selectbox("Color by", colorable, index=default_idx)

# Filtering controls for other columns
st.sidebar.markdown("---")

if hotel_mode == "Single" and len(selected_hotels) == 1:
    filter_cols = [
        "Pension",
        "Tipo_Habitacion",
        "GastoTotal",
        "Noches",
        "Repetidor",
        "Antelacion_Range",
        "G_Etario",
    ]
else:
    filter_cols = [
        "GastoTotal",
        "Noches",
        "Repetidor",
        "Antelacion_Range",
        "G_Etario",
    ]

filtered_df = df.copy()
for col in filter_cols:
    if col == color_col or col not in df.columns:
        continue
    if df[col].dtype.kind in {"i", "f"}:
        min_val = int(df[col].min())
        max_val = int(df[col].max())
        selected = st.sidebar.slider(col, min_val, max_val, (min_val, max_val))
        filtered_df = filtered_df[(filtered_df[col] >= selected[0]) & (filtered_df[col] <= selected[1])]
    else:
        options = sorted(df[col].dropna().unique())
        selected = st.sidebar.multiselect(col, options, default=options)
        filtered_df = filtered_df[filtered_df[col].isin(selected)]

# Map visualization
st.markdown("""
<style>
body {background-color: #000000; color: white;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='color:white;'>Reservations Map</h2>", unsafe_allow_html=True)

import streamlit.components.v1 as components



# Always use two columns: OCEAN (left), Non-OCEAN (right)
col_ocean, col_agency = st.columns(2)

if hotel_mode == "Todos":
    # Plot all OCEAN and Non-OCEAN reservations together
    with col_ocean:
        st.markdown("<h3 style='color:white;'>All Hotels | Canal: OCEAN</h3>", unsafe_allow_html=True)
        df_ocean = filtered_df[filtered_df["Canal"] == "OCEAN"]
        try:
            color_args = get_color_args(color_col)
            category_args = {}
            if color_col in CATEGORY_ORDERS:
                category_args = {"category_orders": {color_col: CATEGORY_ORDERS[color_col]}}
            fig_ocean = px.scatter_map(
                df_ocean,
                lat="lat",
                lon="lon",
                hover_name="reservation_id" if "reservation_id" in df_ocean.columns else None,
                hover_data=[color_col, "Codigo_Postal", "GastoTotal", "Edad"] if "GastoTotal" in df_ocean.columns else [color_col, "Codigo_Postal", "Edad"],
                color=color_col,
                zoom=5,
                center={"lat": 54.5, "lon": -5},
                height=800,
                width=900,
                title=f"All Hotels Reservations Colored by '{color_col}' (Q1/Q2 2025) | Canal OCEAN",
                **color_args,
                **category_args
            )
            fig_ocean.update_layout(
                mapbox_style="carto-darkmatter",
                paper_bgcolor="black",
                plot_bgcolor="black",
                font_color="white",
                legend=dict(bgcolor="black", font_color="white"),
            )
            st.plotly_chart(fig_ocean, use_container_width=True)
            rich_log(f"[bold green]All Hotels OCEAN reservations plotted on UK & Ireland map, colored by '{color_col}'.[/bold green]")
            rich_log(f"[bold yellow]Total plotted OCEAN reservations: {len(df_ocean)}[/bold yellow]")
        except Exception as e:
            rich_log(f"[bold red]Failed to plot All Hotels OCEAN reservations: {e}[/bold red]")
            st.error(f"Failed to plot OCEAN reservations: {e}")
    with col_agency:
        st.markdown("<h3 style='color:white;'>All Hotels | Canal: Non-OCEAN</h3>", unsafe_allow_html=True)
        df_agency = filtered_df[filtered_df["Canal"] != "OCEAN"]
        try:
            color_args = get_color_args(color_col)
            category_args = {}
            if color_col in CATEGORY_ORDERS:
                category_args = {"category_orders": {color_col: CATEGORY_ORDERS[color_col]}}
            fig_agency = px.scatter_map(
                df_agency,
                lat="lat",
                lon="lon",
                hover_name="reservation_id" if "reservation_id" in df_agency.columns else None,
                hover_data=[color_col, "Codigo_Postal", "GastoTotal", "Edad"] if "GastoTotal" in df_agency.columns else [color_col, "Codigo_Postal", "Edad"],
                color=color_col,
                zoom=5,
                center={"lat": 54.5, "lon": -5},
                height=800,
                width=900,
                title=f"All Hotels Reservations Colored by '{color_col}' (Q1/Q2 2025) | Canal Non-OCEAN",
                **color_args,
                **category_args
            )
            fig_agency.update_layout(
                mapbox_style="carto-darkmatter",
                paper_bgcolor="black",
                plot_bgcolor="black",
                font_color="white",
                legend=dict(bgcolor="black", font_color="white"),
            )
            st.plotly_chart(fig_agency, use_container_width=True)
            rich_log(f"[bold green]All Hotels Non-OCEAN reservations plotted on UK & Ireland map, colored by '{color_col}'.[/bold green]")
            rich_log(f"[bold yellow]Total plotted Non-OCEAN reservations: {len(df_agency)}[/bold yellow]")
        except Exception as e:
            rich_log(f"[bold red]Failed to plot All Hotels Non-OCEAN reservations: {e}[/bold red]")
            st.error(f"Failed to plot Non-OCEAN reservations: {e}")
else:
    # Stack each hotel's plot vertically in each column
    for hotel_name in selected_hotels:
        with col_ocean:
            st.markdown(f"<h3 style='color:white;'>Hotel: {hotel_name} | Canal: OCEAN</h3>", unsafe_allow_html=True)
            df_ocean_h = filtered_df[(filtered_df["Hotel"] == hotel_name) & (filtered_df["Canal"] == "OCEAN")]
            try:
                color_args = get_color_args(color_col)
                category_args = {}
                if color_col in CATEGORY_ORDERS:
                    category_args = {"category_orders": {color_col: CATEGORY_ORDERS[color_col]}}
                fig_ocean = px.scatter_map(
                    df_ocean_h,
                    lat="lat",
                    lon="lon",
                    hover_name="reservation_id" if "reservation_id" in df_ocean_h.columns else None,
                    hover_data=[color_col, "Codigo_Postal", "GastoTotal", "Edad"] if "GastoTotal" in df_ocean_h.columns else [color_col, "Codigo_Postal", "Edad"],
                    color=color_col,
                    zoom=5,
                    center={"lat": 54.5, "lon": -5},
                    height=800,
                    width=900,
                    title=f"{hotel_name} Reservations Colored by '{color_col}' (Q1/Q2 2025) | Canal OCEAN",
                    **color_args,
                    **category_args
                )
                fig_ocean.update_layout(
                    mapbox_style="carto-darkmatter",
                    paper_bgcolor="black",
                    plot_bgcolor="black",
                    font_color="white",
                    legend=dict(bgcolor="black", font_color="white"),
                )
                st.plotly_chart(fig_ocean, use_container_width=True)
                rich_log(f"[bold green]{hotel_name} OCEAN reservations plotted on UK & Ireland map, colored by '{color_col}'.[/bold green]")
                rich_log(f"[bold yellow]Total plotted OCEAN reservations: {len(df_ocean_h)}[/bold yellow]")
            except Exception as e:
                rich_log(f"[bold red]Failed to plot {hotel_name} OCEAN reservations: {e}[/bold red]")
                st.error(f"Failed to plot OCEAN reservations: {e}")
        with col_agency:
            st.markdown(f"<h3 style='color:white;'>Hotel: {hotel_name} | Canal: Non-OCEAN</h3>", unsafe_allow_html=True)
            df_agency_h = filtered_df[(filtered_df["Hotel"] == hotel_name) & (filtered_df["Canal"] != "OCEAN")]
            try:
                color_args = get_color_args(color_col)
                category_args = {}
                if color_col in CATEGORY_ORDERS:
                    category_args = {"category_orders": {color_col: CATEGORY_ORDERS[color_col]}}
                fig_agency = px.scatter_map(
                    df_agency_h,
                    lat="lat",
                    lon="lon",
                    hover_name="reservation_id" if "reservation_id" in df_agency_h.columns else None,
                    hover_data=[color_col, "Codigo_Postal", "GastoTotal", "Edad"] if "GastoTotal" in df_agency_h.columns else [color_col, "Codigo_Postal", "Edad"],
                    color=color_col,
                    zoom=5,
                    center={"lat": 54.5, "lon": -5},
                    height=800,
                    width=900,
                    title=f"{hotel_name} Reservations Colored by '{color_col}' (Q1/Q2 2025) | Canal Non-OCEAN",
                    **color_args,
                    **category_args
                )
                fig_agency.update_layout(
                    mapbox_style="carto-darkmatter",
                    paper_bgcolor="black",
                    plot_bgcolor="black",
                    font_color="white",
                    legend=dict(bgcolor="black", font_color="white"),
                )
                st.plotly_chart(fig_agency, use_container_width=True)
                rich_log(f"[bold green]{hotel_name} Non-OCEAN reservations plotted on UK & Ireland map, colored by '{color_col}'.[/bold green]")
                rich_log(f"[bold yellow]Total plotted Non-OCEAN reservations: {len(df_agency_h)}[/bold yellow]")
            except Exception as e:
                rich_log(f"[bold red]Failed to plot {hotel_name} Non-OCEAN reservations: {e}[/bold red]")
                st.error(f"Failed to plot Non-OCEAN reservations: {e}")
