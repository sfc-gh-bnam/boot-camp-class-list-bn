import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Brandon - Report Dashboard TEST 2",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Region mapping to coordinates (major US cities)
REGION_COORDS = {
    'North': {'lat': 40.7128, 'lon': -74.0060, 'city': 'New York'},
    'South': {'lat': 33.7490, 'lon': -84.3880, 'city': 'Atlanta'},
    'East': {'lat': 42.3601, 'lon': -71.0589, 'city': 'Boston'},
    'West': {'lat': 34.0522, 'lon': -118.2437, 'city': 'Los Angeles'}
}

# Generate sample data
@st.cache_data
def load_sample_data():
    # Sample sales data
    dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
    regions = np.random.choice(['North', 'South', 'East', 'West'], len(dates))
    
    sales_data = pd.DataFrame({
        'Date': dates,
        'Sales': np.random.randint(1000, 5000, len(dates)),
        'Region': regions,
        'Product': np.random.choice(['Product A', 'Product B', 'Product C'], len(dates))
    })
    
    # Add geographic coordinates
    sales_data['lat'] = sales_data['Region'].map(lambda x: REGION_COORDS[x]['lat'])
    sales_data['lon'] = sales_data['Region'].map(lambda x: REGION_COORDS[x]['lon'])
    sales_data['City'] = sales_data['Region'].map(lambda x: REGION_COORDS[x]['city'])
    
    return sales_data

def process_uploaded_file(uploaded_file):
    """Process uploaded Excel or CSV file and add geographic coordinates if needed"""
    try:
        # Determine file type and read accordingly
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension in ['xlsx', 'xls']:
            # Read Excel file
            df = pd.read_excel(uploaded_file)
        elif file_extension == 'csv':
            # Read CSV file
            df = pd.read_csv(uploaded_file)
        else:
            return None, f"Unsupported file type: {file_extension}. Please use .xlsx, .xls, or .csv"
        
        # Ensure Date column is datetime
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        
        # Add geographic coordinates if not present
        if 'lat' not in df.columns and 'Region' in df.columns:
            df['lat'] = df['Region'].map(lambda x: REGION_COORDS.get(x, {}).get('lat', 0))
            df['lon'] = df['Region'].map(lambda x: REGION_COORDS.get(x, {}).get('lon', 0))
            df['City'] = df['Region'].map(lambda x: REGION_COORDS.get(x, {}).get('city', 'Unknown'))
        elif 'City' not in df.columns and 'lat' in df.columns and 'lon' in df.columns:
            # If coordinates exist but no City, try to match or set Unknown
            df['City'] = 'Unknown'
        
        return df, None
    except Exception as e:
        return None, str(e)

# Sidebar - File Upload
st.sidebar.header("Data Source")
uploaded_file = st.sidebar.file_uploader(
    "Upload File",
    type=['xlsx', 'xls', 'csv'],
    help="Upload an Excel (.xlsx, .xls) or CSV file with columns: Date, Sales, Region, Product (optional: City, lat, lon)"
)

# Load data
if uploaded_file is not None:
    df, error = process_uploaded_file(uploaded_file)
    if error:
        st.sidebar.error(f"Error loading file: {error}")
        st.sidebar.info("Using sample data instead")
        df = load_sample_data()
    else:
        st.sidebar.success(f"✓ File loaded: {uploaded_file.name}")
        st.sidebar.info(f"Rows: {len(df)}")
else:
    df = load_sample_data()

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

# Geographic Chart
st.subheader("Sales by Geographic Location")
geo_data = df.groupby(['City', 'Region', 'lat', 'lon'])['Sales'].sum().reset_index().sort_values('Sales', ascending=False)

fig_geo = px.scatter_geo(
    geo_data,
    lat='lat',
    lon='lon',
    size='Sales',
    text='City',
    hover_name='City',
    hover_data={'Region': True, 'Sales': ':,', 'lat': False, 'lon': False},
    title='Sales Distribution by Geographic Location',
    color='Sales',
    color_continuous_scale='Viridis',
    projection='orthographic',
    size_max=50
)
fig_geo.update_traces(
    textposition='top center',
    textfont=dict(size=12, color='black')
)
fig_geo.update_layout(
    height=600,
    geo=dict(
        projection_type='orthographic',
        showland=True,
        landcolor='rgb(243, 243, 243)',
        countrycolor='rgb(204, 204, 204)',
        showocean=True,
        oceancolor='rgb(230, 245, 255)',
        showcountries=True,
        showlakes=True,
        lakecolor='rgb(230, 245, 255)',
        showframe=False
    )
)
st.plotly_chart(fig_geo, use_container_width=True)

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
