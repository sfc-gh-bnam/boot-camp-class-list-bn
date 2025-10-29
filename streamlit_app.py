import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Brandon - Report Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Generate sample data
@st.cache_data
def load_data():
    # Sample sales data
    dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
    sales_data = pd.DataFrame({
        'Date': dates,
        'Sales': np.random.randint(1000, 5000, len(dates)),
        'Region': np.random.choice(['North', 'South', 'East', 'West'], len(dates)),
        'Product': np.random.choice(['Product A', 'Product B', 'Product C'], len(dates))
    })
    return sales_data

# Load data
df = load_data()

# Title
st.title("📊 Brandon - Report Dashboard")
st.markdown("---")

# Key Metrics
st.header("Key Metrics")
col1, col2, col3, col4 = st.columns(4)

total_sales = df['Sales'].sum()
avg_sales = df['Sales'].mean()
max_sales = df['Sales'].max()
num_transactions = len(df)

col1.metric("Total Sales", f"${total_sales:,.0f}")
col2.metric("Average Sales", f"${avg_sales:,.0f}")
col3.metric("Max Sales", f"${max_sales:,.0f}")
col4.metric("Transactions", f"{num_transactions:,}")

st.markdown("---")

# Charts Section
st.header("Sales Analysis")

# Time series chart
st.subheader("Sales Over Time")
fig_line = px.line(
    df.groupby('Date')['Sales'].sum().reset_index(),
    x='Date',
    y='Sales',
    title='Daily Sales Trend',
    labels={'Sales': 'Sales ($)'}
)
fig_line.update_layout(height=400)
st.plotly_chart(fig_line, use_container_width=True)

# Charts in columns
col1, col2 = st.columns(2)

# Sales by Region
with col1:
    st.subheader("Sales by Region")
    region_sales = df.groupby('Region')['Sales'].sum().reset_index()
    fig_bar = px.bar(
        region_sales,
        x='Region',
        y='Sales',
        title='Total Sales by Region',
        labels={'Sales': 'Sales ($)'},
        color='Sales',
        color_continuous_scale='Blues'
    )
    fig_bar.update_layout(height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

# Sales by Product
with col2:
    st.subheader("Sales by Product")
    product_sales = df.groupby('Product')['Sales'].sum().reset_index()
    fig_pie = px.pie(
        product_sales,
        values='Sales',
        names='Product',
        title='Sales Distribution by Product'
    )
    fig_pie.update_layout(height=400)
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# Data Table
st.header("Data Overview")
st.dataframe(
    df.head(100),
    use_container_width=True,
    hide_index=True
)

# Sidebar filters
st.sidebar.header("Filters")
selected_regions = st.sidebar.multiselect(
    "Select Regions",
    options=df['Region'].unique(),
    default=df['Region'].unique()
)

selected_products = st.sidebar.multiselect(
    "Select Products",
    options=df['Product'].unique(),
    default=df['Product'].unique()
)

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(df['Date'].min(), df['Date'].max()),
    min_value=df['Date'].min(),
    max_value=df['Date'].max()
)

# Apply filters
if selected_regions and selected_products:
    filtered_df = df[
        (df['Region'].isin(selected_regions)) &
        (df['Product'].isin(selected_products))
    ]
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['Date'] >= pd.to_datetime(date_range[0])) &
            (filtered_df['Date'] <= pd.to_datetime(date_range[1]))
        ]
    
    if len(filtered_df) > 0:
        st.sidebar.success(f"Showing {len(filtered_df)} records")
    else:
        st.sidebar.warning("No data matches the selected filters")

# Footer
st.markdown("---")
st.caption(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
