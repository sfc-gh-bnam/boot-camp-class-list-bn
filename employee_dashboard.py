import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import io

# Page configuration
st.set_page_config(
    page_title="Brandon - Report Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'employee_df' not in st.session_state:
    st.session_state.employee_df = pd.DataFrame()

@st.cache_data(show_spinner="Loading file...")
def process_uploaded_file(uploaded_file):
    """Process uploaded Excel or CSV file with caching"""
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'xlsx':
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        elif file_extension == 'xls':
            df = pd.read_excel(uploaded_file, engine='xlrd')
        elif file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
        else:
            return None, f"Unsupported file type: {file_extension}. Please use .xlsx, .xls, or .csv"
        
        df.columns = df.columns.str.strip()
        
        # Only process Hire Date column if it exists
        if 'Hire Date' in df.columns:
            df['Hire Date'] = pd.to_datetime(df['Hire Date'], errors='coerce')
        
        return df, None
    except Exception as e:
        return None, str(e)

def get_default_columns():
    """Return list of default employee columns"""
    return [
        'Boot Camp In-Person', 'VILT', 'Region', 'Role', 'Preferred Name',
        'Work Email', 'Personal', 'Hire Date', 'Business Title', 'Business Unit',
        'Manager Name', 'Manager Email', 'Location', 'Cost Center #', 'Cost Center Name',
        'Employee Type', 'Management VP', 'Management RVP', 'Transfer/Promo',
        'SE Capstone', 'Capstone Channel', 'BOOTCAMP_MOD', 'VILT_MOD',
        'Duplicate Check', 'Load OB_NEW_HIRES', 'NewHire Loaded?', 'Load CAPSTONE_AUDIT',
        'Capstone Loaded'
    ]

def compute_metrics(df):
    """Compute key metrics efficiently"""
    total = len(df)
    
    # Use vectorized operations
    recent_hires = 0
    if 'Hire Date' in df.columns:
        cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=90)
        recent_hires = df['Hire Date'].notna() & (df['Hire Date'] >= cutoff_date)
        recent_hires = recent_hires.sum()
    
    bootcamp_completed = 0
    if 'Boot Camp In-Person' in df.columns:
        bootcamp_completed = df['Boot Camp In-Person'].notna().sum()
    
    vilt_completed = 0
    if 'VILT' in df.columns:
        vilt_completed = df['VILT'].notna().sum()
    
    return total, recent_hires, bootcamp_completed, vilt_completed

def apply_filters_fast(df, regions=None, roles=None, business_units=None, employee_types=None):
    """Apply filters efficiently using vectorized operations"""
    mask = pd.Series([True] * len(df), index=df.index)
    
    if regions and 'Region' in df.columns:
        mask &= df['Region'].isin(regions)
    if roles and 'Role' in df.columns:
        mask &= df['Role'].isin(roles)
    if business_units and 'Business Unit' in df.columns:
        mask &= df['Business Unit'].isin(business_units)
    if employee_types and 'Employee Type' in df.columns:
        mask &= df['Employee Type'].isin(employee_types)
    
    return df[mask]

# Title
st.title("📊 Brandon - Report Dashboard")
st.markdown("---")

# Sidebar - Data Management
st.sidebar.header("Data Management")
uploaded_file = st.sidebar.file_uploader(
    "Upload Employee Data File",
    type=['xlsx', 'xls', 'csv'],
    help="Upload an Excel (.xlsx, .xls) or CSV file with employee training data"
)

# Initialize file tracking in session state
if 'last_uploaded_file_id' not in st.session_state:
    st.session_state.last_uploaded_file_id = None

if uploaded_file is not None:
    # Create unique file identifier (name + size should be unique enough)
    try:
        file_position = uploaded_file.tell()
    except:
        file_position = 0
    file_id = f"{uploaded_file.name}_{uploaded_file.size}_{file_position}"
    
    # Only process if this is a new file
    if file_id != st.session_state.last_uploaded_file_id:
        with st.spinner("Loading file..."):
            df, error = process_uploaded_file(uploaded_file)
            if error:
                st.sidebar.error(f"Error loading file: {error}")
            else:
                st.session_state.employee_df = df
                st.session_state.last_uploaded_file_id = file_id
                st.sidebar.success(f"✓ File loaded: {uploaded_file.name}")
                st.success(f"✅ Loaded {len(df)} records!")

if st.sidebar.button("Clear All Data", type="secondary"):
    st.session_state.employee_df = pd.DataFrame()
    st.session_state.last_uploaded_file_id = None
    st.success("Data cleared!")

# Tabs for Dashboard and Add Employee
tab1, tab2 = st.tabs(["📊 Dashboard", "➕ Add Employee"])

with tab1:
    # Check if data exists - always read fresh from session state
    if 'employee_df' not in st.session_state or st.session_state.employee_df.empty:
        st.info("👆 Please upload a file or add employee data using the 'Add Employee' tab")
        st.stop()
    
    # Always get fresh copy from session state to ensure we have latest data
    df = st.session_state.employee_df.copy()
    
    # Compute metrics once
    total_employees, recent_hires, bootcamp_completed, vilt_completed = compute_metrics(df)
    
    # Key Metrics
    st.header("Overview Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total Employees", f"{total_employees:,}")
    col2.metric("Recent Hires (90 days)", f"{recent_hires:,}")
    col3.metric("Boot Camp Completed", f"{bootcamp_completed:,}")
    col4.metric("VILT Completed", f"{vilt_completed:,}")
    
    st.markdown("---")
    
    # Filters Section
    st.sidebar.markdown("---")
    st.sidebar.header("Filters")
    
    # Get unique values only once
    selected_regions = []
    selected_roles = []
    selected_business_units = []
    selected_employee_types = []
    
    if 'Region' in df.columns and len(df) > 0:
        regions = df['Region'].dropna().unique()
        regions = sorted([r for r in regions if pd.notna(r)])
        if regions:
            selected_regions = st.sidebar.multiselect(
                "Select Regions",
                options=regions,
                default=regions if len(regions) <= 20 else regions[:20]
            )
    
    if 'Role' in df.columns and len(df) > 0:
        roles = df['Role'].dropna().unique()
        roles = sorted([r for r in roles if pd.notna(r)])
        if roles:
            selected_roles = st.sidebar.multiselect(
                "Select Roles",
                options=roles,
                default=roles if len(roles) <= 20 else roles[:20]
            )
    
    if 'Business Unit' in df.columns and len(df) > 0:
        business_units = df['Business Unit'].dropna().unique()
        business_units = sorted([bu for bu in business_units if pd.notna(bu)])
        if business_units:
            selected_business_units = st.sidebar.multiselect(
                "Select Business Units",
                options=business_units,
                default=business_units if len(business_units) <= 20 else business_units[:20]
            )
    
    if 'Employee Type' in df.columns and len(df) > 0:
        employee_types = df['Employee Type'].dropna().unique()
        employee_types = sorted([et for et in employee_types if pd.notna(et)])
        if employee_types:
            selected_employee_types = st.sidebar.multiselect(
                "Select Employee Types",
                options=employee_types,
                default=employee_types
            )
    
    # Apply filters efficiently
    filtered_df = apply_filters_fast(
        df, 
        selected_regions if selected_regions else None,
        selected_roles if selected_roles else None,
        selected_business_units if selected_business_units else None,
        selected_employee_types if selected_employee_types else None
    )
    
    st.sidebar.success(f"Showing {len(filtered_df)} of {len(df)} records")
    
    # Charts Section - only show if we have filtered data
    if len(filtered_df) > 0:
        st.header("Employee Analysis")
        
        if 'Region' in filtered_df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Employees by Region")
                region_counts = filtered_df['Region'].value_counts().reset_index()
                region_counts.columns = ['Region', 'Count']
                if len(region_counts) > 0:
                    fig_region = px.bar(
                        region_counts,
                        x='Region',
                        y='Count',
                        title='Employee Count by Region',
                        color='Count',
                        color_continuous_scale='Blues'
                    )
                    fig_region.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig_region, use_container_width=True)
            
            with col2:
                st.subheader("Employees by Role")
                if 'Role' in filtered_df.columns:
                    role_counts = filtered_df['Role'].value_counts().reset_index()
                    role_counts.columns = ['Role', 'Count']
                    role_counts = role_counts.head(10)
                    if len(role_counts) > 0:
                        fig_role = px.bar(
                            role_counts,
                            x='Role',
                            y='Count',
                            title='Top 10 Roles',
                            color='Count',
                            color_continuous_scale='Greens'
                        )
                        fig_role.update_layout(height=400, xaxis_tickangle=-45, showlegend=False)
                        st.plotly_chart(fig_role, use_container_width=True)
        
        st.markdown("---")
        
        # Training Completion Analysis
        st.header("Training Completion Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Boot Camp Completion")
            if 'Boot Camp In-Person' in filtered_df.columns:
                completed = filtered_df['Boot Camp In-Person'].notna().sum()
                not_completed = len(filtered_df) - completed
                if completed + not_completed > 0:
                    bootcamp_df = pd.DataFrame({
                        'Status': ['Completed', 'Not Completed'],
                        'Count': [completed, not_completed]
                    })
                    fig_bootcamp = px.pie(
                        bootcamp_df,
                        values='Count',
                        names='Status',
                        title='Boot Camp In-Person Completion',
                        color_discrete_map={'Completed': '#1f77b4', 'Not Completed': '#ff7f0e'}
                    )
                    fig_bootcamp.update_layout(height=400, showlegend=True)
                    st.plotly_chart(fig_bootcamp, use_container_width=True)
        
        with col2:
            st.subheader("VILT Completion")
            if 'VILT' in filtered_df.columns:
                completed = filtered_df['VILT'].notna().sum()
                not_completed = len(filtered_df) - completed
                if completed + not_completed > 0:
                    vilt_df = pd.DataFrame({
                        'Status': ['Completed', 'Not Completed'],
                        'Count': [completed, not_completed]
                    })
                    fig_vilt = px.pie(
                        vilt_df,
                        values='Count',
                        names='Status',
                        title='VILT Completion',
                        color_discrete_map={'Completed': '#2ca02c', 'Not Completed': '#d62728'}
                    )
                    fig_vilt.update_layout(height=400, showlegend=True)
                    st.plotly_chart(fig_vilt, use_container_width=True)
        
        st.markdown("---")
        
        # VILT Class Visualization Module
        # Use full df (unfiltered) for VILT class grouping to get accurate counts
        if 'VILT' in df.columns:
            st.header("📚 VILT Class List")
            
            # Prepare VILT class data from FULL dataset (not filtered) for accurate counts
            # But apply filters if any are selected for display purposes
            vilt_base_data = df[df['VILT'].notna()].copy()
            
            # Apply same filters to VILT data for display
            if len(vilt_base_data) > 0:
                vilt_filtered = apply_filters_fast(
                    vilt_base_data,
                    selected_regions if selected_regions else None,
                    selected_roles if selected_roles else None,
                    selected_business_units if selected_business_units else None,
                    selected_employee_types if selected_employee_types else None
                )
                # Use filtered for display
                vilt_data = vilt_filtered.copy()
            else:
                vilt_data = pd.DataFrame()
            
            if len(vilt_data) > 0:
                # Use VILT value directly as class identifier (treat as text/string)
                vilt_data['VILT Class'] = vilt_data['VILT'].astype(str)
                
                # Get unique VILT classes
                vilt_classes = sorted(vilt_data['VILT Class'].unique(), reverse=True)
                vilt_class_summary = vilt_data.groupby('VILT Class').agg({
                    'Preferred Name': 'count',
                    'VILT': 'first'
                }).reset_index()
                vilt_class_summary.columns = ['VILT Class', 'Total Students', 'Class Name']
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.subheader("VILT Classes Overview")
                    # Display summary by class
                    class_summary = vilt_data.groupby('VILT Class').agg({
                        'Preferred Name': 'count'
                    }).reset_index()
                    class_summary.columns = ['VILT Class', 'Students']
                    class_summary = class_summary.sort_values('Students', ascending=False).head(20)
                    
                    if len(class_summary) > 0:
                        fig_vilt_classes = px.bar(
                            class_summary,
                            x='VILT Class',
                            y='Students',
                            title='Students by VILT Class',
                            color='Students',
                            color_continuous_scale='Purples'
                        )
                        fig_vilt_classes.update_layout(height=400, xaxis_tickangle=-45, showlegend=False)
                        st.plotly_chart(fig_vilt_classes, use_container_width=True)
                    
                    # VILT Class selector
                    selected_vilt_class = st.selectbox(
                        "Select VILT Class to View",
                        options=["All Classes"] + vilt_classes,
                        index=0
                    )
                
                with col2:
                        st.subheader("Students by VILT Class")
                        
                        # Filter by selected class
                        if selected_vilt_class == "All Classes":
                            display_vilt_data = vilt_data
                            st.info(f"Showing all {len(display_vilt_data)} students across {len(vilt_classes)} VILT classes")
                        else:
                            display_vilt_data = vilt_data[vilt_data['VILT Class'] == selected_vilt_class]
                            st.info(f"Showing {len(display_vilt_data)} students in VILT class: {selected_vilt_class}")
                        
                        # Display students grouped by class
                        if len(display_vilt_data) > 0:
                            # Key columns to display
                            display_columns = ['Preferred Name', 'Work Email', 'Region', 'Role', 
                                             'Business Unit', 'VILT Class', 'VILT_MOD']
                            available_columns = [col for col in display_columns if col in display_vilt_data.columns]
                            
                            # Prepare display dataframe
                            display_df = display_vilt_data[available_columns].copy()
                            display_df = display_df.sort_values('VILT Class', ascending=False)
                            
                            st.dataframe(
                                display_df,
                                use_container_width=True,
                                hide_index=True,
                                height=500
                            )
                            
                            # Download button for VILT class data
                            vilt_csv = display_vilt_data.to_csv(index=False)
                            st.download_button(
                                label=f"📥 Download {selected_vilt_class if selected_vilt_class != 'All Classes' else 'All'} VILT Class Data",
                                data=vilt_csv,
                                file_name=f"vilt_class_{selected_vilt_class if selected_vilt_class != 'All Classes' else 'all'}_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                        
                        # Grouped view by class
                        st.markdown("### Grouped by Class")
                        for vilt_class in sorted(vilt_classes, reverse=True)[:10]:  # Show top 10
                            class_students = vilt_data[vilt_data['VILT Class'] == vilt_class]
                            
                            with st.expander(f"📅 {vilt_class} ({len(class_students)} students)", expanded=False):
                                cols_to_show = ['Preferred Name', 'Work Email', 'Region', 'Role']
                                cols_to_show = [c for c in cols_to_show if c in class_students.columns]
                                st.dataframe(
                                    class_students[cols_to_show],
                                    use_container_width=True,
                                    hide_index=True
                                )
            else:
                st.info("No VILT class data available. Users need to have VILT class values assigned.")
        
        st.markdown("---")
        
        # Hire Date Trends
        if 'Hire Date' in filtered_df.columns:
            hire_trends = filtered_df[filtered_df['Hire Date'].notna()]
            if len(hire_trends) > 0:
                st.subheader("Hiring Trends Over Time")
                hire_trends = hire_trends.copy()
                hire_trends['Hire Month'] = hire_trends['Hire Date'].dt.to_period('M').astype(str)
                monthly_hires = hire_trends.groupby('Hire Month', observed=False).size().reset_index()
                monthly_hires.columns = ['Month', 'Count']
                
                if len(monthly_hires) > 0:
                    fig_hire_trend = px.line(
                        monthly_hires,
                        x='Month',
                        y='Count',
                        title='Monthly Hires Over Time',
                        markers=True
                    )
                    fig_hire_trend.update_layout(height=400, showlegend=False)
                    fig_hire_trend.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_hire_trend, use_container_width=True)
        
        st.markdown("---")
        
        # Edit Employee Section
        st.header("✏️ Edit Employee")
        if 'Work Email' not in df.columns or df['Work Email'].isna().all():
            st.warning("No employee email addresses found. Cannot edit employees.")
        else:
            employees_with_email = df[df['Work Email'].notna()].copy()
            if len(employees_with_email) == 0:
                st.warning("No employees with email addresses found.")
            else:
                # Create display names for selectbox
                employee_options = []
                for idx, row in employees_with_email.iterrows():
                    name = row.get('Preferred Name', 'Unknown')
                    email = row.get('Work Email', 'No Email')
                    display_name = f"{name} ({email})" if name and name != 'Unknown' else email
                    employee_options.append((idx, display_name))
                
                employee_options.sort(key=lambda x: x[1])
                
                if employee_options:
                    selected_display = st.selectbox(
                        "Select Employee to Edit",
                        options=[opt[1] for opt in employee_options],
                        index=0,
                        key="edit_employee_select"
                    )
                    
                    selected_idx = [opt[0] for opt in employee_options if opt[1] == selected_display][0]
                    selected_employee = df.loc[selected_idx].copy()
                    
                    # Helper functions for dropdowns
                    def get_dropdown_options(column_name, current_value=""):
                        if column_name not in df.columns:
                            return [""]
                        options = [""] + sorted([str(v) for v in df[column_name].dropna().unique() if pd.notna(v) and str(v).strip()])
                        if current_value and current_value not in options:
                            current_str = str(current_value) if pd.notna(current_value) else ""
                            if current_str:
                                options.append(current_str)
                        return options
                    
                    def get_dropdown_index(options, current_value):
                        if pd.isna(current_value) or current_value == "":
                            return 0
                        current_str = str(current_value)
                        if current_str in options:
                            return options.index(current_str)
                        return 0
                    
                    # Edit Form
                    with st.form("edit_employee_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            preferred_name = st.text_input("Preferred Name *", value=str(selected_employee.get('Preferred Name', '')) if pd.notna(selected_employee.get('Preferred Name', '')) else "", key="edit_pref_name")
                            work_email = st.text_input("Work Email *", value=str(selected_employee.get('Work Email', '')) if pd.notna(selected_employee.get('Work Email', '')) else "", key="edit_email")
                            personal = st.text_input("Personal", value=str(selected_employee.get('Personal', '')) if pd.notna(selected_employee.get('Personal', '')) else "", key="edit_personal")
                            
                            hire_date_value = selected_employee.get('Hire Date')
                            if pd.notna(hire_date_value) and pd.api.types.is_datetime64_any_dtype(type(hire_date_value)):
                                hire_date = st.date_input("Hire Date", value=hire_date_value.date() if hasattr(hire_date_value, 'date') else hire_date_value, key="edit_hire_date")
                            elif pd.notna(hire_date_value):
                                try:
                                    hire_date = st.date_input("Hire Date", value=pd.to_datetime(hire_date_value).date(), key="edit_hire_date2")
                                except:
                                    hire_date = st.date_input("Hire Date", value=None, key="edit_hire_date3")
                            else:
                                hire_date = st.date_input("Hire Date", value=None, key="edit_hire_date4")
                            
                            business_title_options = get_dropdown_options('Business Title', selected_employee.get('Business Title', ''))
                            business_title_idx = get_dropdown_index(business_title_options, selected_employee.get('Business Title', ''))
                            business_title = st.selectbox("Business Title", business_title_options, index=business_title_idx, key="edit_business_title")
                            
                            business_unit_options = get_dropdown_options('Business Unit', selected_employee.get('Business Unit', ''))
                            business_unit_idx = get_dropdown_index(business_unit_options, selected_employee.get('Business Unit', ''))
                            business_unit = st.selectbox("Business Unit", business_unit_options, index=business_unit_idx, key="edit_business_unit")
                            
                            region_options = get_dropdown_options('Region', selected_employee.get('Region', ''))
                            region_idx = get_dropdown_index(region_options, selected_employee.get('Region', ''))
                            region = st.selectbox("Region", region_options, index=region_idx, key="edit_region")
                            
                            role_options = get_dropdown_options('Role', selected_employee.get('Role', ''))
                            role_idx = get_dropdown_index(role_options, selected_employee.get('Role', ''))
                            role = st.selectbox("Role", role_options, index=role_idx, key="edit_role")
                            
                            location_options = get_dropdown_options('Location', selected_employee.get('Location', ''))
                            location_idx = get_dropdown_index(location_options, selected_employee.get('Location', ''))
                            location = st.selectbox("Location", location_options, index=location_idx, key="edit_location")
                            
                            manager_name_options = get_dropdown_options('Manager Name', selected_employee.get('Manager Name', ''))
                            manager_name_idx = get_dropdown_index(manager_name_options, selected_employee.get('Manager Name', ''))
                            manager_name = st.selectbox("Manager Name", manager_name_options, index=manager_name_idx, key="edit_manager_name")
                            
                            manager_email_options = get_dropdown_options('Manager Email', selected_employee.get('Manager Email', ''))
                            manager_email_idx = get_dropdown_index(manager_email_options, selected_employee.get('Manager Email', ''))
                            manager_email = st.selectbox("Manager Email", manager_email_options, index=manager_email_idx, key="edit_manager_email")
                            
                            cost_center_num_options = get_dropdown_options('Cost Center #', selected_employee.get('Cost Center #', ''))
                            cost_center_num_idx = get_dropdown_index(cost_center_num_options, selected_employee.get('Cost Center #', ''))
                            cost_center_num = st.selectbox("Cost Center #", cost_center_num_options, index=cost_center_num_idx, key="edit_cost_center_num")
                            
                            cost_center_name_options = get_dropdown_options('Cost Center Name', selected_employee.get('Cost Center Name', ''))
                            cost_center_name_idx = get_dropdown_index(cost_center_name_options, selected_employee.get('Cost Center Name', ''))
                            cost_center_name = st.selectbox("Cost Center Name", cost_center_name_options, index=cost_center_name_idx, key="edit_cost_center_name")
                            
                            employee_type_options = ["", "Full Time", "Part Time", "Contract", "Intern"]
                            current_employee_type = str(selected_employee.get('Employee Type', '')) if pd.notna(selected_employee.get('Employee Type', '')) else ""
                            employee_type_index = employee_type_options.index(current_employee_type) if current_employee_type in employee_type_options else 0
                            employee_type = st.selectbox("Employee Type", employee_type_options, index=employee_type_index, key="edit_employee_type")
                            
                            management_vp_options = get_dropdown_options('Management VP', selected_employee.get('Management VP', ''))
                            management_vp_idx = get_dropdown_index(management_vp_options, selected_employee.get('Management VP', ''))
                            management_vp = st.selectbox("Management VP", management_vp_options, index=management_vp_idx, key="edit_management_vp")
                            
                            management_rvp_options = get_dropdown_options('Management RVP', selected_employee.get('Management RVP', ''))
                            management_rvp_idx = get_dropdown_index(management_rvp_options, selected_employee.get('Management RVP', ''))
                            management_rvp = st.selectbox("Management RVP", management_rvp_options, index=management_rvp_idx, key="edit_management_rvp")
                        
                        with col2:
                            bootcamp_options = get_dropdown_options('Boot Camp In-Person', selected_employee.get('Boot Camp In-Person', ''))
                            bootcamp_idx = get_dropdown_index(bootcamp_options, selected_employee.get('Boot Camp In-Person', ''))
                            bootcamp_in_person = st.selectbox("Boot Camp In-Person", bootcamp_options, index=bootcamp_idx, key="edit_bootcamp")
                            
                            vilt_options = get_dropdown_options('VILT', selected_employee.get('VILT', ''))
                            vilt_idx = get_dropdown_index(vilt_options, selected_employee.get('VILT', ''))
                            vilt = st.selectbox("VILT", vilt_options, index=vilt_idx, key="edit_vilt")
                            
                            transfer_promo_options = get_dropdown_options('Transfer/Promo', selected_employee.get('Transfer/Promo', ''))
                            transfer_promo_idx = get_dropdown_index(transfer_promo_options, selected_employee.get('Transfer/Promo', ''))
                            transfer_promo = st.selectbox("Transfer/Promo", transfer_promo_options, index=transfer_promo_idx, key="edit_transfer_promo")
                            
                            se_capstone_value = selected_employee.get('SE Capstone')
                            if pd.notna(se_capstone_value) and pd.api.types.is_datetime64_any_dtype(type(se_capstone_value)):
                                se_capstone = st.date_input("SE Capstone Date", value=se_capstone_value.date() if hasattr(se_capstone_value, 'date') else se_capstone_value, key="edit_se_capstone")
                            elif pd.notna(se_capstone_value):
                                try:
                                    se_capstone = st.date_input("SE Capstone Date", value=pd.to_datetime(se_capstone_value).date(), key="edit_se_capstone2")
                                except:
                                    se_capstone = st.date_input("SE Capstone Date", value=None, key="edit_se_capstone3")
                            else:
                                se_capstone = st.date_input("SE Capstone Date", value=None, key="edit_se_capstone4")
                            
                            capstone_channel_options = get_dropdown_options('Capstone Channel', selected_employee.get('Capstone Channel', ''))
                            capstone_channel_idx = get_dropdown_index(capstone_channel_options, selected_employee.get('Capstone Channel', ''))
                            capstone_channel = st.selectbox("Capstone Channel", capstone_channel_options, index=capstone_channel_idx, key="edit_capstone_channel")
                            
                            bootcamp_mod_options = get_dropdown_options('BOOTCAMP_MOD', selected_employee.get('BOOTCAMP_MOD', ''))
                            bootcamp_mod_idx = get_dropdown_index(bootcamp_mod_options, selected_employee.get('BOOTCAMP_MOD', ''))
                            bootcamp_mod = st.selectbox("BOOTCAMP_MOD", bootcamp_mod_options, index=bootcamp_mod_idx, key="edit_bootcamp_mod")
                            
                            vilt_mod_options = get_dropdown_options('VILT_MOD', selected_employee.get('VILT_MOD', ''))
                            vilt_mod_idx = get_dropdown_index(vilt_mod_options, selected_employee.get('VILT_MOD', ''))
                            vilt_mod = st.selectbox("VILT_MOD", vilt_mod_options, index=vilt_mod_idx, key="edit_vilt_mod")
                            
                            duplicate_check_options = get_dropdown_options('Duplicate Check', selected_employee.get('Duplicate Check', ''))
                            duplicate_check_idx = get_dropdown_index(duplicate_check_options, selected_employee.get('Duplicate Check', ''))
                            duplicate_check = st.selectbox("Duplicate Check", duplicate_check_options, index=duplicate_check_idx, key="edit_duplicate_check")
                            
                            yes_no_options = ["", "Yes", "No"]
                            
                            load_ob_new_hires_default = str(selected_employee.get('Load OB_NEW_HIRES', '')) if pd.notna(selected_employee.get('Load OB_NEW_HIRES', '')) else ""
                            load_ob_new_hires_index = yes_no_options.index(load_ob_new_hires_default) if load_ob_new_hires_default in yes_no_options else 0
                            load_ob_new_hires = st.selectbox("Load OB_NEW_HIRES", yes_no_options, index=load_ob_new_hires_index, key="edit_load_ob_new_hires")
                            
                            newhire_loaded_default = str(selected_employee.get('NewHire Loaded?', '')) if pd.notna(selected_employee.get('NewHire Loaded?', '')) else ""
                            newhire_loaded_index = yes_no_options.index(newhire_loaded_default) if newhire_loaded_default in yes_no_options else 0
                            newhire_loaded = st.selectbox("NewHire Loaded?", yes_no_options, index=newhire_loaded_index, key="edit_newhire_loaded")
                            
                            load_capstone_audit_default = str(selected_employee.get('Load CAPSTONE_AUDIT', '')) if pd.notna(selected_employee.get('Load CAPSTONE_AUDIT', '')) else ""
                            load_capstone_audit_index = yes_no_options.index(load_capstone_audit_default) if load_capstone_audit_default in yes_no_options else 0
                            load_capstone_audit = st.selectbox("Load CAPSTONE_AUDIT", yes_no_options, index=load_capstone_audit_index, key="edit_load_capstone_audit")
                            
                            capstone_loaded_default = str(selected_employee.get('Capstone Loaded', '')) if pd.notna(selected_employee.get('Capstone Loaded', '')) else ""
                            capstone_loaded_index = yes_no_options.index(capstone_loaded_default) if capstone_loaded_default in yes_no_options else 0
                            capstone_loaded = st.selectbox("Capstone Loaded", yes_no_options, index=capstone_loaded_index, key="edit_capstone_loaded")
                        
                        submitted = st.form_submit_button("💾 Save Changes", type="primary")
                        
                        if submitted:
                            if not preferred_name or not work_email:
                                st.error("⚠️ Please fill in required fields: Preferred Name and Work Email")
                            else:
                                original_email = selected_employee.get('Work Email', '')
                                updated_employee = {
                                    'Preferred Name': preferred_name,
                                    'Work Email': work_email,
                                    'Personal': personal if personal else None,
                                    'Hire Date': pd.to_datetime(hire_date) if hire_date else None,
                                    'Business Title': business_title if business_title else None,
                                    'Business Unit': business_unit if business_unit else None,
                                    'Region': region if region else None,
                                    'Role': role if role else None,
                                    'Location': location if location else None,
                                    'Manager Name': manager_name if manager_name else None,
                                    'Manager Email': manager_email if manager_email else None,
                                    'Cost Center #': cost_center_num if cost_center_num else None,
                                    'Cost Center Name': cost_center_name if cost_center_name else None,
                                    'Employee Type': employee_type if employee_type else None,
                                    'Management VP': management_vp if management_vp else None,
                                    'Management RVP': management_rvp if management_rvp else None,
                                    'Boot Camp In-Person': bootcamp_in_person if bootcamp_in_person else None,
                                    'VILT': vilt if vilt else None,
                                    'Transfer/Promo': transfer_promo if transfer_promo else None,
                                    'SE Capstone': pd.to_datetime(se_capstone) if se_capstone else None,
                                    'Capstone Channel': capstone_channel if capstone_channel else None,
                                    'BOOTCAMP_MOD': bootcamp_mod if bootcamp_mod else None,
                                    'VILT_MOD': vilt_mod if vilt_mod else None,
                                    'Duplicate Check': duplicate_check if duplicate_check else None,
                                    'Load OB_NEW_HIRES': load_ob_new_hires if load_ob_new_hires else None,
                                    'NewHire Loaded?': newhire_loaded if newhire_loaded else None,
                                    'Load CAPSTONE_AUDIT': load_capstone_audit if load_capstone_audit else None,
                                    'Capstone Loaded': capstone_loaded if capstone_loaded else None
                                }
                                
                                for col in st.session_state.employee_df.columns:
                                    if col not in updated_employee:
                                        updated_employee[col] = selected_employee.get(col, None)
                                
                                mask = st.session_state.employee_df['Work Email'] == original_email
                                if mask.sum() == 0:
                                    actual_idx = selected_idx
                                else:
                                    actual_idx = st.session_state.employee_df[mask].index[0]
                                
                                original_df = st.session_state.employee_df.copy(deep=True)
                                
                                for col in original_df.columns:
                                    if col not in updated_employee:
                                        updated_employee[col] = selected_employee.get(col, original_df.loc[actual_idx, col] if actual_idx in original_df.index else None)
                                
                                for key in updated_employee.keys():
                                    if key not in original_df.columns:
                                        original_df[key] = None
                                
                                for key, value in updated_employee.items():
                                    if value == '' or (isinstance(value, str) and value.strip() == ''):
                                        updated_employee[key] = None
                                
                                row_data = {}
                                for col in original_df.columns:
                                    if col in updated_employee:
                                        row_data[col] = updated_employee[col]
                                    else:
                                        if actual_idx in original_df.index:
                                            row_data[col] = original_df.loc[actual_idx, col]
                                        else:
                                            row_data[col] = None
                                
                                for col in original_df.columns:
                                    original_df.loc[actual_idx, col] = row_data.get(col, None)
                                
                                updated_df = original_df.reset_index(drop=True).copy(deep=True)
                                
                                original_count = len(st.session_state.employee_df)
                                new_count = len(updated_df)
                                
                                if new_count != original_count:
                                    st.error(f"⚠️ Error: Row count mismatch! Expected {original_count}, got {new_count}. Update cancelled to prevent data loss.")
                                else:
                                    # Clear any cached data
                                    st.cache_data.clear()
                                    
                                    # Replace the entire dataframe in session state
                                    st.session_state.employee_df = updated_df.copy()
                                    
                                    # Force a complete refresh by updating timestamp
                                    st.session_state.last_update = datetime.now().isoformat()
                                    st.session_state.data_version = st.session_state.get('data_version', 0) + 1
                                    
                                    st.success(f"✅ Employee '{preferred_name}' updated successfully! Total employees: {new_count}")
                                    st.balloons()
                                    
                                    # Rerun immediately to refresh all metrics and charts
                                    st.rerun()
        
        st.markdown("---")
        
        # Data Table - limit display
        st.header("Employee Data")
        display_limit = st.slider("Rows to display", 10, min(500, len(filtered_df)), 100, step=10)
        st.dataframe(
            filtered_df.head(display_limit),
            use_container_width=True,
            hide_index=True,
            height=400
        )
    else:
        st.warning("No data matches the selected filters")
    
    # Export Button
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"bootcamp_class_list_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    with col2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Boot Camp Class List')
        excel_data = output.getvalue()
        st.download_button(
            label="📥 Download as Excel",
            data=excel_data,
            file_name=f"bootcamp_class_list_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

with tab2:
    st.header("Add New Employee")
    
    with st.form("add_employee_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            preferred_name = st.text_input("Preferred Name *", "")
            work_email = st.text_input("Work Email *", "")
            personal = st.text_input("Personal", "")
            hire_date = st.date_input("Hire Date")
            business_title = st.text_input("Business Title", "")
            business_unit = st.text_input("Business Unit", "")
ennettuna<｜tool▁call▁begin｜>
grep
                
                if not employee_options:
                    st.warning("No employees available to edit.")
                else:
                    selected_display = st.selectbox(
                        "Select Employee to Edit",
                        options=[opt[1] for opt in employee_options],
                        index=0
                    )
                    
                    # Get the selected index
                    selected_idx = [opt[0] for opt in employee_options if opt[1] == selected_display][0]
                    selected_employee = df.loc[selected_idx].copy()
                    
                    # Helper function to get unique values for dropdown
                    def get_dropdown_options(column_name, current_value=""):
                        """Get unique values from dataframe column for dropdown, including current value"""
                        if column_name not in df.columns:
                            return [""]
                        options = [""] + sorted([str(v) for v in df[column_name].dropna().unique() if pd.notna(v) and str(v).strip()])
                        # Add current value if it's not in options
                        if current_value and current_value not in options:
                            current_str = str(current_value) if pd.notna(current_value) else ""
                            if current_str:
                                options.append(current_str)
                        return options
                    
                    # Helper function to get index for dropdown
                    def get_dropdown_index(options, current_value):
                        """Get index of current value in options list"""
                        if pd.isna(current_value) or current_value == "":
                            return 0
                        current_str = str(current_value)
                        if current_str in options:
                            return options.index(current_str)
                        return 0
                    
                    # Edit Form
                    with st.form("edit_employee_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            preferred_name = st.text_input("Preferred Name *", value=str(selected_employee.get('Preferred Name', '')) if pd.notna(selected_employee.get('Preferred Name', '')) else "")
                            work_email = st.text_input("Work Email *", value=str(selected_employee.get('Work Email', '')) if pd.notna(selected_employee.get('Work Email', '')) else "")
                            personal = st.text_input("Personal", value=str(selected_employee.get('Personal', '')) if pd.notna(selected_employee.get('Personal', '')) else "")
                            
                            # Handle Hire Date
                            hire_date_value = selected_employee.get('Hire Date')
                            if pd.notna(hire_date_value) and pd.api.types.is_datetime64_any_dtype(type(hire_date_value)):
                                hire_date = st.date_input("Hire Date", value=hire_date_value.date() if hasattr(hire_date_value, 'date') else hire_date_value)
                            elif pd.notna(hire_date_value):
                                try:
                                    hire_date = st.date_input("Hire Date", value=pd.to_datetime(hire_date_value).date())
                                except:
                                    hire_date = st.date_input("Hire Date", value=None)
                            else:
                                hire_date = st.date_input("Hire Date", value=None)
                            
                            # Business Title dropdown
                            business_title_options = get_dropdown_options('Business Title', selected_employee.get('Business Title', ''))
                            business_title_idx = get_dropdown_index(business_title_options, selected_employee.get('Business Title', ''))
                            business_title = st.selectbox("Business Title", business_title_options, index=business_title_idx)
                            
                            # Business Unit dropdown
                            business_unit_options = get_dropdown_options('Business Unit', selected_employee.get('Business Unit', ''))
                            business_unit_idx = get_dropdown_index(business_unit_options, selected_employee.get('Business Unit', ''))
                            business_unit = st.selectbox("Business Unit", business_unit_options, index=business_unit_idx)
                            
                            # Region dropdown
                            region_options = get_dropdown_options('Region', selected_employee.get('Region', ''))
                            region_idx = get_dropdown_index(region_options, selected_employee.get('Region', ''))
                            region = st.selectbox("Region", region_options, index=region_idx)
                            
                            # Role dropdown
                            role_options = get_dropdown_options('Role', selected_employee.get('Role', ''))
                            role_idx = get_dropdown_index(role_options, selected_employee.get('Role', ''))
                            role = st.selectbox("Role", role_options, index=role_idx)
                            
                            # Location dropdown
                            location_options = get_dropdown_options('Location', selected_employee.get('Location', ''))
                            location_idx = get_dropdown_index(location_options, selected_employee.get('Location', ''))
                            location = st.selectbox("Location", location_options, index=location_idx)
                            
                            # Manager Name dropdown
                            manager_name_options = get_dropdown_options('Manager Name', selected_employee.get('Manager Name', ''))
                            manager_name_idx = get_dropdown_index(manager_name_options, selected_employee.get('Manager Name', ''))
                            manager_name = st.selectbox("Manager Name", manager_name_options, index=manager_name_idx)
                            
                            # Manager Email dropdown
                            manager_email_options = get_dropdown_options('Manager Email', selected_employee.get('Manager Email', ''))
                            manager_email_idx = get_dropdown_index(manager_email_options, selected_employee.get('Manager Email', ''))
                            manager_email = st.selectbox("Manager Email", manager_email_options, index=manager_email_idx)
                            
                            # Cost Center # dropdown
                            cost_center_num_options = get_dropdown_options('Cost Center #', selected_employee.get('Cost Center #', ''))
                            cost_center_num_idx = get_dropdown_index(cost_center_num_options, selected_employee.get('Cost Center #', ''))
                            cost_center_num = st.selectbox("Cost Center #", cost_center_num_options, index=cost_center_num_idx)
                            
                            # Cost Center Name dropdown
                            cost_center_name_options = get_dropdown_options('Cost Center Name', selected_employee.get('Cost Center Name', ''))
                            cost_center_name_idx = get_dropdown_index(cost_center_name_options, selected_employee.get('Cost Center Name', ''))
                            cost_center_name = st.selectbox("Cost Center Name", cost_center_name_options, index=cost_center_name_idx)
                            # Handle Employee Type selectbox
                            employee_type_options = ["", "Full Time", "Part Time", "Contract", "Intern"]
                            current_employee_type = str(selected_employee.get('Employee Type', '')) if pd.notna(selected_employee.get('Employee Type', '')) else ""
                            employee_type_index = employee_type_options.index(current_employee_type) if current_employee_type in employee_type_options else 0
                            employee_type = st.selectbox("Employee Type", employee_type_options, index=employee_type_index)
                            # Management VP dropdown
                            management_vp_options = get_dropdown_options('Management VP', selected_employee.get('Management VP', ''))
                            management_vp_idx = get_dropdown_index(management_vp_options, selected_employee.get('Management VP', ''))
                            management_vp = st.selectbox("Management VP", management_vp_options, index=management_vp_idx)
                            
                            # Management RVP dropdown
                            management_rvp_options = get_dropdown_options('Management RVP', selected_employee.get('Management RVP', ''))
                            management_rvp_idx = get_dropdown_index(management_rvp_options, selected_employee.get('Management RVP', ''))
                            management_rvp = st.selectbox("Management RVP", management_rvp_options, index=management_rvp_idx)
                        
                        with col2:
                            # Boot Camp In-Person dropdown
                            bootcamp_options = get_dropdown_options('Boot Camp In-Person', selected_employee.get('Boot Camp In-Person', ''))
                            bootcamp_idx = get_dropdown_index(bootcamp_options, selected_employee.get('Boot Camp In-Person', ''))
                            bootcamp_in_person = st.selectbox("Boot Camp In-Person", bootcamp_options, index=bootcamp_idx)
                            
                            # VILT dropdown
                            vilt_options = get_dropdown_options('VILT', selected_employee.get('VILT', ''))
                            vilt_idx = get_dropdown_index(vilt_options, selected_employee.get('VILT', ''))
                            vilt = st.selectbox("VILT", vilt_options, index=vilt_idx)
                            
                            # Transfer/Promo dropdown
                            transfer_promo_options = get_dropdown_options('Transfer/Promo', selected_employee.get('Transfer/Promo', ''))
                            transfer_promo_idx = get_dropdown_index(transfer_promo_options, selected_employee.get('Transfer/Promo', ''))
                            transfer_promo = st.selectbox("Transfer/Promo", transfer_promo_options, index=transfer_promo_idx)
                            
                            # Handle SE Capstone Date
                            se_capstone_value = selected_employee.get('SE Capstone')
                            if pd.notna(se_capstone_value) and pd.api.types.is_datetime64_any_dtype(type(se_capstone_value)):
                                se_capstone = st.date_input("SE Capstone Date", value=se_capstone_value.date() if hasattr(se_capstone_value, 'date') else se_capstone_value)
                            elif pd.notna(se_capstone_value):
                                try:
                                    se_capstone = st.date_input("SE Capstone Date", value=pd.to_datetime(se_capstone_value).date())
                                except:
                                    se_capstone = st.date_input("SE Capstone Date", value=None)
                            else:
                                se_capstone = st.date_input("SE Capstone Date", value=None)
                            
                            # Capstone Channel dropdown
                            capstone_channel_options = get_dropdown_options('Capstone Channel', selected_employee.get('Capstone Channel', ''))
                            capstone_channel_idx = get_dropdown_index(capstone_channel_options, selected_employee.get('Capstone Channel', ''))
                            capstone_channel = st.selectbox("Capstone Channel", capstone_channel_options, index=capstone_channel_idx)
                            
                            # BOOTCAMP_MOD dropdown
                            bootcamp_mod_options = get_dropdown_options('BOOTCAMP_MOD', selected_employee.get('BOOTCAMP_MOD', ''))
                            bootcamp_mod_idx = get_dropdown_index(bootcamp_mod_options, selected_employee.get('BOOTCAMP_MOD', ''))
                            bootcamp_mod = st.selectbox("BOOTCAMP_MOD", bootcamp_mod_options, index=bootcamp_mod_idx)
                            
                            # VILT_MOD dropdown
                            vilt_mod_options = get_dropdown_options('VILT_MOD', selected_employee.get('VILT_MOD', ''))
                            vilt_mod_idx = get_dropdown_index(vilt_mod_options, selected_employee.get('VILT_MOD', ''))
                            vilt_mod = st.selectbox("VILT_MOD", vilt_mod_options, index=vilt_mod_idx)
                            
                            # Duplicate Check dropdown
                            duplicate_check_options = get_dropdown_options('Duplicate Check', selected_employee.get('Duplicate Check', ''))
                            duplicate_check_idx = get_dropdown_index(duplicate_check_options, selected_employee.get('Duplicate Check', ''))
                            duplicate_check = st.selectbox("Duplicate Check", duplicate_check_options, index=duplicate_check_idx)
                            
                            # Handle selectbox defaults
                            yes_no_options = ["", "Yes", "No"]
                            
                            load_ob_new_hires_default = str(selected_employee.get('Load OB_NEW_HIRES', '')) if pd.notna(selected_employee.get('Load OB_NEW_HIRES', '')) else ""
                            load_ob_new_hires_index = yes_no_options.index(load_ob_new_hires_default) if load_ob_new_hires_default in yes_no_options else 0
                            load_ob_new_hires = st.selectbox("Load OB_NEW_HIRES", yes_no_options, index=load_ob_new_hires_index)
                            
                            newhire_loaded_default = str(selected_employee.get('NewHire Loaded?', '')) if pd.notna(selected_employee.get('NewHire Loaded?', '')) else ""
                            newhire_loaded_index = yes_no_options.index(newhire_loaded_default) if newhire_loaded_default in yes_no_options else 0
                            newhire_loaded = st.selectbox("NewHire Loaded?", yes_no_options, index=newhire_loaded_index)
                            
                            load_capstone_audit_default = str(selected_employee.get('Load CAPSTONE_AUDIT', '')) if pd.notna(selected_employee.get('Load CAPSTONE_AUDIT', '')) else ""
                            load_capstone_audit_index = yes_no_options.index(load_capstone_audit_default) if load_capstone_audit_default in yes_no_options else 0
                            load_capstone_audit = st.selectbox("Load CAPSTONE_AUDIT", yes_no_options, index=load_capstone_audit_index)
                            
                            capstone_loaded_default = str(selected_employee.get('Capstone Loaded', '')) if pd.notna(selected_employee.get('Capstone Loaded', '')) else ""
                            capstone_loaded_index = yes_no_options.index(capstone_loaded_default) if capstone_loaded_default in yes_no_options else 0
                            capstone_loaded = st.selectbox("Capstone Loaded", yes_no_options, index=capstone_loaded_index)
                        
                        submitted = st.form_submit_button("💾 Save Changes", type="primary")
                        
                        if submitted:
                            if not preferred_name or not work_email:
                                st.error("⚠️ Please fill in required fields: Preferred Name and Work Email")
                            else:
                                # Get the original email to find the employee (in case email was changed)
                                original_email = selected_employee.get('Work Email', '')
                                
                                # Update the employee record
                                updated_employee = {
                                    'Preferred Name': preferred_name,
                                    'Work Email': work_email,
                                    'Personal': personal if personal else None,
                                    'Hire Date': pd.to_datetime(hire_date) if hire_date else None,
                                    'Business Title': business_title if business_title else None,
                                    'Business Unit': business_unit if business_unit else None,
                                    'Region': region if region else None,
                                    'Role': role if role else None,
                                    'Location': location if location else None,
                                    'Manager Name': manager_name if manager_name else None,
                                    'Manager Email': manager_email if manager_email else None,
                                    'Cost Center #': cost_center_num if cost_center_num else None,
                                    'Cost Center Name': cost_center_name if cost_center_name else None,
                                    'Employee Type': employee_type if employee_type else None,
                                    'Management VP': management_vp if management_vp else None,
                                    'Management RVP': management_rvp if management_rvp else None,
                                    'Boot Camp In-Person': bootcamp_in_person if bootcamp_in_person else None,
                                    'VILT': vilt if vilt else None,
                                    'Transfer/Promo': transfer_promo if transfer_promo else None,
                                    'SE Capstone': pd.to_datetime(se_capstone) if se_capstone else None,
                                    'Capstone Channel': capstone_channel if capstone_channel else None,
                                    'BOOTCAMP_MOD': bootcamp_mod if bootcamp_mod else None,
                                    'VILT_MOD': vilt_mod if vilt_mod else None,
                                    'Duplicate Check': duplicate_check if duplicate_check else None,
                                    'Load OB_NEW_HIRES': load_ob_new_hires if load_ob_new_hires else None,
                                    'NewHire Loaded?': newhire_loaded if newhire_loaded else None,
                                    'Load CAPSTONE_AUDIT': load_capstone_audit if load_capstone_audit else None,
                                    'Capstone Loaded': capstone_loaded if capstone_loaded else None
                                }
                                
                                # Preserve all existing columns from the selected employee
                                for col in st.session_state.employee_df.columns:
                                    if col not in updated_employee:
                                        updated_employee[col] = selected_employee.get(col, None)
                                
                                # Find the employee in the session state using original email as identifier
                                # This is more reliable than using index
                                mask = st.session_state.employee_df['Work Email'] == original_email
                                if mask.sum() == 0:
                                    # Fallback to index if email match fails
                                    actual_idx = selected_idx
                                else:
                                    actual_idx = st.session_state.employee_df[mask].index[0]
                                
                                # Get the original dataframe - make a deep copy to avoid reference issues
                                original_df = st.session_state.employee_df.copy(deep=True)
                                
                                # Ensure all columns exist in updated_employee dict
                                for col in original_df.columns:
                                    if col not in updated_employee:
                                        # Get the original value from the selected employee
                                        updated_employee[col] = selected_employee.get(col, original_df.loc[actual_idx, col] if actual_idx in original_df.index else None)
                                
                                # Ensure all updated_employee keys exist as columns
                                for key in updated_employee.keys():
                                    if key not in original_df.columns:
                                        original_df[key] = None
                                
                                # Convert empty strings to None for consistency
                                for key, value in updated_employee.items():
                                    if value == '' or (isinstance(value, str) and value.strip() == ''):
                                        updated_employee[key] = None
                                
                                # Update the row by replacing it entirely
                                # This ensures all data is preserved correctly
                                row_data = {}
                                for col in original_df.columns:
                                    if col in updated_employee:
                                        row_data[col] = updated_employee[col]
                                    else:
                                        # Preserve existing value
                                        if actual_idx in original_df.index:
                                            row_data[col] = original_df.loc[actual_idx, col]
                                        else:
                                            row_data[col] = None
                                
                                # Update the specific row using .loc with a single assignment
                                # This is more reliable than updating cell by cell
                                for col in original_df.columns:
                                    original_df.loc[actual_idx, col] = row_data.get(col, None)
                                
                                # Reset index and create a completely fresh dataframe
                                # This ensures Streamlit recognizes it as a new object
                                updated_df = original_df.reset_index(drop=True).copy(deep=True)
                                
                                # Verify the update maintained row count
                                original_count = len(st.session_state.employee_df)
                                new_count = len(updated_df)
                                
                                if new_count != original_count:
                                    st.error(f"⚠️ Error: Row count mismatch! Expected {original_count}, got {new_count}. Update cancelled to prevent data loss.")
                                else:
                                    # Replace session state dataframe - this ensures Streamlit recognizes the change
                                    st.session_state.employee_df = updated_df.copy()
                                    
                                    # Force Streamlit to recognize the change by updating a timestamp
                                    st.session_state.last_update = datetime.now().isoformat()
                                    
                                    st.success(f"✅ Employee '{preferred_name}' updated successfully! Total employees: {new_count}")
                                    
                                    # Rerun to refresh all tabs immediately
                                    st.rerun()
    st.header("Add New Employee")
    
    with st.form("add_employee_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            preferred_name = st.text_input("Preferred Name *", "")
            work_email = st.text_input("Work Email *", "")
            personal = st.text_input("Personal", "")
            hire_date = st.date_input("Hire Date")
            business_title = st.text_input("Business Title", "")
            business_unit = st.text_input("Business Unit", "")
            region = st.text_input("Region", "")
            role = st.text_input("Role", "")
            location = st.text_input("Location", "")
            manager_name = st.text_input("Manager Name", "")
            manager_email = st.text_input("Manager Email", "")
            cost_center_num = st.text_input("Cost Center #", "")
            cost_center_name = st.text_input("Cost Center Name", "")
            employee_type = st.selectbox("Employee Type", ["", "Full Time", "Part Time", "Contract", "Intern"])
            management_vp = st.text_input("Management VP", "")
            management_rvp = st.text_input("Management RVP", "")
        
        with col2:
            bootcamp_in_person = st.text_input("Boot Camp In-Person", "")
            vilt = st.text_input("VILT", "")
            transfer_promo = st.text_input("Transfer/Promo", "")
            se_capstone = st.date_input("SE Capstone Date")
            capstone_channel = st.text_input("Capstone Channel", "")
            bootcamp_mod = st.text_input("BOOTCAMP_MOD", "")
            vilt_mod = st.text_input("VILT_MOD", "")
            duplicate_check = st.text_input("Duplicate Check", "")
            load_ob_new_hires = st.selectbox("Load OB_NEW_HIRES", ["", "Yes", "No"])
            newhire_loaded = st.selectbox("NewHire Loaded?", ["", "Yes", "No"])
            load_capstone_audit = st.selectbox("Load CAPSTONE_AUDIT", ["", "Yes", "No"])
            capstone_loaded = st.selectbox("Capstone Loaded", ["", "Yes", "No"])
        
        submitted = st.form_submit_button("Add Employee", type="primary")
        
        if submitted:
            if not preferred_name or not work_email:
                st.error("⚠️ Please fill in required fields: Preferred Name and Work Email")
            else:
                # Create new employee record
                new_employee = {
                    'Preferred Name': preferred_name,
                    'Work Email': work_email,
                    'Personal': personal if personal else None,
                    'Hire Date': pd.to_datetime(hire_date) if hire_date else None,
                    'Business Title': business_title if business_title else None,
                    'Business Unit': business_unit if business_unit else None,
                    'Region': region if region else None,
                    'Role': role if role else None,
                    'Location': location if location else None,
                    'Manager Name': manager_name if manager_name else None,
                    'Manager Email': manager_email if manager_email else None,
                    'Cost Center #': cost_center_num if cost_center_num else None,
                    'Cost Center Name': cost_center_name if cost_center_name else None,
                    'Employee Type': employee_type if employee_type else None,
                    'Management VP': management_vp if management_vp else None,
                    'Management RVP': management_rvp if management_rvp else None,
                    'Boot Camp In-Person': bootcamp_in_person if bootcamp_in_person else None,
                    'VILT': vilt if vilt else None,
                    'Transfer/Promo': transfer_promo if transfer_promo else None,
                    'SE Capstone': pd.to_datetime(se_capstone) if se_capstone else None,
                    'Capstone Channel': capstone_channel if capstone_channel else None,
                    'BOOTCAMP_MOD': bootcamp_mod if bootcamp_mod else None,
                    'VILT_MOD': vilt_mod if vilt_mod else None,
                    'Duplicate Check': duplicate_check if duplicate_check else None,
                    'Load OB_NEW_HIRES': load_ob_new_hires if load_ob_new_hires else None,
                    'NewHire Loaded?': newhire_loaded if newhire_loaded else None,
                    'Load CAPSTONE_AUDIT': load_capstone_audit if load_capstone_audit else None,
                    'Capstone Loaded': capstone_loaded if capstone_loaded else None
                }
                
                # Add to dataframe more efficiently
                new_df = pd.DataFrame([new_employee])
                if st.session_state.employee_df.empty:
                    st.session_state.employee_df = new_df
                else:
                    # Ensure columns exist and concatenate
                    all_cols = set(st.session_state.employee_df.columns) | set(new_df.columns)
                    for col in all_cols:
                        if col not in st.session_state.employee_df.columns:
                            st.session_state.employee_df[col] = None
                        if col not in new_df.columns:
                            new_df[col] = None
                    st.session_state.employee_df = pd.concat(
                        [st.session_state.employee_df, new_df],
                        ignore_index=True
                    )
                
                st.success(f"✅ Employee '{preferred_name}' added successfully!")
                st.info(f"Total employees: {len(st.session_state.employee_df)}")

# Footer
st.markdown("---")
st.caption(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
