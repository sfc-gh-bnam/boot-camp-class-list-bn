import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import io

st.set_page_config(
    page_title="Boot Camp Class List - BN",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'employee_df' not in st.session_state:
    st.session_state.employee_df = pd.DataFrame()

@st.cache_data(show_spinner="Loading file...")
def process_uploaded_file(uploaded_file):
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
        
        if 'Hire Date' in df.columns:
            df['Hire Date'] = pd.to_datetime(df['Hire Date'], errors='coerce')
        
        if 'Course Completion' in df.columns:
            df['Course Completion'] = pd.to_datetime(df['Course Completion'], errors='coerce')
        
        return df, None
    except Exception as e:
        return None, str(e)

def get_default_columns():
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
    total = len(df)
    
    recent_hires = 0
    if 'Hire Date' in df.columns:
        cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=90)
        recent_hires = df['Hire Date'].notna() & (df['Hire Date'] >= cutoff_date)
        recent_hires = recent_hires.sum()
    
    # Calculate unique Boot Camp classes
    total_bootcamp_classes = 0
    if 'Boot Camp In-Person' in df.columns:
        bootcamp_data = df[df['Boot Camp In-Person'].notna()]
        if len(bootcamp_data) > 0:
            total_bootcamp_classes = bootcamp_data['Boot Camp In-Person'].nunique()
    
    total_vilt_classes = 0
    if 'VILT' in df.columns:
        vilt_data = df[df['VILT'].notna()]
        if len(vilt_data) > 0:
            total_vilt_classes = vilt_data['VILT'].nunique()
    
    return total, recent_hires, total_bootcamp_classes, total_vilt_classes

def apply_filters_fast(df, regions=None, roles=None, business_units=None, employee_types=None):
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

st.title("👥 Boot Camp Class List - BN")
st.markdown("---")

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
    try:
        file_position = uploaded_file.tell()
    except:
        file_position = 0
    file_id = f"{uploaded_file.name}_{uploaded_file.size}_{file_position}"
    
    if file_id != st.session_state.last_uploaded_file_id:
        with st.spinner("Loading file..."):
            df, error = process_uploaded_file(uploaded_file)
            if error:
                st.sidebar.error(f"Error loading file: {error}")
            else:
                st.session_state.employee_df = df
                st.session_state.last_uploaded_file_id = file_id
                st.session_state.original_employee_count = len(df)
                st.sidebar.success(f"✓ File loaded: {uploaded_file.name}")
                st.success(f"✅ Loaded {len(df)} records!")

if st.sidebar.button("Clear All Data", type="secondary"):
    st.session_state.employee_df = pd.DataFrame()
    st.session_state.last_uploaded_file_id = None
    st.session_state.original_employee_count = 0
    st.success("Data cleared!")

tab1, tab2 = st.tabs(["📊 Dashboard", "➕ Add Employee"])

with tab1:
    if 'employee_df' not in st.session_state or st.session_state.employee_df.empty:
        st.info("👆 Please upload a file or add employee data using the 'Add Employee' tab")
        st.stop()
    
    df = st.session_state.employee_df
    
    if 'refresh_trigger' in st.session_state:
        st.session_state.data_refresh_time = st.session_state.refresh_trigger
        del st.session_state.refresh_trigger
    
    total_employees, recent_hires, total_bootcamp_classes, total_vilt_classes = compute_metrics(df)
    
    st.header("Overview Metrics")
    
    if 'data_refresh_time' in st.session_state:
        st.success(f"🔄 Data refreshed at {st.session_state.data_refresh_time}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total Employees", f"{total_employees:,}")
    col2.metric("Recent Hires (90 days)", f"{recent_hires:,}")
    col3.metric("Total Boot Camp Classes", f"{total_bootcamp_classes:,}")
    col4.metric("Total VILT Classes", f"{total_vilt_classes:,}")
    
    st.markdown("---")
    
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
    
    filtered_df = apply_filters_fast(
        df, 
        selected_regions if selected_regions else None,
        selected_roles if selected_roles else None,
        selected_business_units if selected_business_units else None,
        selected_employee_types if selected_employee_types else None
    )
    
    st.sidebar.success(f"Showing {len(filtered_df)} of {len(df)} records")
    
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
        
        if 'Boot Camp In-Person' in st.session_state.employee_df.columns:
            st.header("🏕️ Boot Camp In-Person Class List")
            
            if 'data_refresh_time' in st.session_state:
                st.caption(f"Last updated: {st.session_state.data_refresh_time}")
            
            bootcamp_base_data = st.session_state.employee_df[st.session_state.employee_df['Boot Camp In-Person'].notna()].copy()
            
            col1, col2 = st.columns([1, 3])
            with col1:
                apply_filters_to_bootcamp = st.checkbox("Apply Sidebar Filters to Boot Camp Classes", value=False, help="Check this to apply the sidebar filters to the Boot Camp Class List")
            with col2:
                if apply_filters_to_bootcamp:
                    st.info("🏕️ Boot Camp Classes are filtered by sidebar selections")
                else:
                    st.info("🏕️ Boot Camp Classes shows ALL Boot Camp data")
            
            if len(bootcamp_base_data) > 0:
                if apply_filters_to_bootcamp:
                    bootcamp_data = apply_filters_fast(
                        bootcamp_base_data,
                        selected_regions if selected_regions else None,
                        selected_roles if selected_roles else None,
                        selected_business_units if selected_business_units else None,
                        selected_employee_types if selected_employee_types else None
                    )
                else:
                    bootcamp_data = bootcamp_base_data.copy()
            else:
                bootcamp_data = pd.DataFrame()
            
            if len(bootcamp_data) > 0:
                total_bootcamp_students = len(bootcamp_base_data)
                displayed_bootcamp_students = len(bootcamp_data)
                
                if displayed_bootcamp_students == total_bootcamp_students:
                    st.success(f"🏕️ Showing ALL {displayed_bootcamp_students} Boot Camp students")
                else:
                    st.info(f"🏕️ Showing {displayed_bootcamp_students} of {total_bootcamp_students} Boot Camp students")
                
                bootcamp_data['Boot Camp Class'] = bootcamp_data['Boot Camp In-Person'].astype(str)
                
                bootcamp_classes = sorted(bootcamp_data['Boot Camp Class'].unique(), reverse=True)
                bootcamp_class_summary = bootcamp_data.groupby('Boot Camp Class').agg({
                    'Preferred Name': 'count',
                    'Boot Camp In-Person': 'first'
                }).reset_index()
                bootcamp_class_summary.columns = ['Boot Camp Class', 'Total Students', 'Class Name']
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.subheader("Boot Camp Classes Overview")
                    # Display summary by class
                    class_summary = bootcamp_data.groupby('Boot Camp Class').agg({
                        'Preferred Name': 'count'
                    }).reset_index()
                    class_summary.columns = ['Boot Camp Class', 'Students']
                    class_summary = class_summary.sort_values('Students', ascending=False).head(20)
                    
                    if len(class_summary) > 0:
                        fig_bootcamp_classes = px.bar(
                            class_summary,
                            x='Boot Camp Class',
                            y='Students',
                            title='Students by Boot Camp Class',
                            color='Students',
                            color_continuous_scale='Oranges'
                        )
                        fig_bootcamp_classes.update_layout(height=400, xaxis_tickangle=-45, showlegend=False)
                        st.plotly_chart(fig_bootcamp_classes, use_container_width=True)
                    
                    selected_bootcamp_class = st.selectbox(
                        "Select Boot Camp Class to View",
                        options=["All Classes"] + bootcamp_classes,
                        index=0
                    )
                
                with col2:
                    st.subheader("Students by Boot Camp Class")
                    
                    if selected_bootcamp_class == "All Classes":
                        display_bootcamp_data = bootcamp_data
                        st.info(f"Showing all {len(display_bootcamp_data)} students across {len(bootcamp_classes)} Boot Camp classes")
                    else:
                        display_bootcamp_data = bootcamp_data[bootcamp_data['Boot Camp Class'] == selected_bootcamp_class]
                        st.info(f"Showing {len(display_bootcamp_data)} students in Boot Camp class: {selected_bootcamp_class}")
                    
                    # Display students grouped by class
                    if len(display_bootcamp_data) > 0:
                        # Key columns to display
                        display_columns = ['Preferred Name', 'Work Email', 'Region', 'Role', 
                                         'Business Unit', 'Boot Camp Class', 'BOOTCAMP_MOD']
                        available_columns = [col for col in display_columns if col in display_bootcamp_data.columns]
                        
                        display_df = display_bootcamp_data[available_columns].copy()
                        display_df = display_df.sort_values('Boot Camp Class', ascending=False)
                        
                        st.dataframe(
                            display_df,
                            use_container_width=True,
                            hide_index=True,
                            height=500
                        )
                        
                        bootcamp_csv = display_bootcamp_data.to_csv(index=False)
                        st.download_button(
                            label=f"📥 Download {selected_bootcamp_class if selected_bootcamp_class != 'All Classes' else 'All'} Boot Camp Class Data",
                            data=bootcamp_csv,
                            file_name=f"bootcamp_class_{selected_bootcamp_class if selected_bootcamp_class != 'All Classes' else 'all'}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    
                    # Grouped view by class
                    st.markdown("### Grouped by Class")
                    for bootcamp_class in sorted(bootcamp_classes, reverse=True)[:10]:  # Show top 10
                        class_students = bootcamp_data[bootcamp_data['Boot Camp Class'] == bootcamp_class]
                        
                        with st.expander(f"🏕️ {bootcamp_class} ({len(class_students)} students)", expanded=False):
                            cols_to_show = ['Preferred Name', 'Work Email', 'Region', 'Role']
                            cols_to_show = [c for c in cols_to_show if c in class_students.columns]
                            st.dataframe(
                                class_students[cols_to_show],
                                use_container_width=True,
                                hide_index=True
                            )
                    
                    with st.expander("🔍 Boot Camp Debug Information", expanded=False):
                        st.write(f"Total Boot Camp students in session state: {len(bootcamp_base_data)}")
                        st.write(f"Displayed Boot Camp students: {len(bootcamp_data)}")
                        st.write(f"Filters applied to Boot Camp: {apply_filters_to_bootcamp}")
                        st.write(f"Number of Boot Camp classes: {len(bootcamp_classes)}")
                        if len(bootcamp_data) > 0:
                            st.write("Boot Camp classes and student counts:")
                            class_counts = bootcamp_data['Boot Camp Class'].value_counts().head(10)
                            st.write(class_counts)
            else:
                st.info("No Boot Camp class data available. Users need to have Boot Camp In-Person class values assigned.")
        
        st.markdown("---")
        
        if 'VILT' in st.session_state.employee_df.columns:
            st.header("📚 VILT Class List")
            
            if 'data_refresh_time' in st.session_state:
                st.caption(f"Last updated: {st.session_state.data_refresh_time}")
            
            vilt_base_data = st.session_state.employee_df[st.session_state.employee_df['VILT'].notna()].copy()
            
            col1, col2 = st.columns([1, 3])
            with col1:
                apply_filters_to_vilt = st.checkbox("Apply Sidebar Filters to VILT Classes", value=False, help="Check this to apply the sidebar filters to the VILT Class List")
            with col2:
                if apply_filters_to_vilt:
                    st.info("📚 VILT Classes are filtered by sidebar selections")
                else:
                    st.info("📚 VILT Classes shows ALL VILT data")
            
            if len(vilt_base_data) > 0:
                if apply_filters_to_vilt:
                    vilt_data = apply_filters_fast(
                        vilt_base_data,
                        selected_regions if selected_regions else None,
                        selected_roles if selected_roles else None,
                        selected_business_units if selected_business_units else None,
                        selected_employee_types if selected_employee_types else None
                    )
                else:
                    vilt_data = vilt_base_data.copy()
            else:
                vilt_data = pd.DataFrame()
            
            if len(vilt_data) > 0:
                total_vilt_students = len(vilt_base_data)
                displayed_vilt_students = len(vilt_data)
                
                if displayed_vilt_students == total_vilt_students:
                    st.success(f"📚 Showing ALL {displayed_vilt_students} VILT students")
                else:
                    st.info(f"📚 Showing {displayed_vilt_students} of {total_vilt_students} VILT students")
                
                vilt_data['VILT Class'] = vilt_data['VILT'].astype(str)
                
                vilt_classes = sorted(vilt_data['VILT Class'].unique(), reverse=True)
                vilt_class_summary = vilt_data.groupby('VILT Class').agg({
                    'Preferred Name': 'count',
                    'VILT': 'first'
                }).reset_index()
                vilt_class_summary.columns = ['VILT Class', 'Total Students', 'Class Name']
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.subheader("VILT Classes Overview")
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
                    
                    selected_vilt_class = st.selectbox(
                        "Select VILT Class to View",
                        options=["All Classes"] + vilt_classes,
                        index=0
                    )
                
                with col2:
                    st.subheader("Students by VILT Class")
                    
                    if selected_vilt_class == "All Classes":
                        display_vilt_data = vilt_data
                        st.info(f"Showing all {len(display_vilt_data)} students across {len(vilt_classes)} VILT classes")
                    else:
                        display_vilt_data = vilt_data[vilt_data['VILT Class'] == selected_vilt_class]
                        st.info(f"Showing {len(display_vilt_data)} students in VILT class: {selected_vilt_class}")
                    
                    if len(display_vilt_data) > 0:
                        display_columns = ['Preferred Name', 'Work Email', 'Region', 'Role', 
                                         'Business Unit', 'VILT Class', 'VILT_MOD']
                        available_columns = [col for col in display_columns if col in display_vilt_data.columns]
                        
                        display_df = display_vilt_data[available_columns].copy()
                        display_df = display_df.sort_values('VILT Class', ascending=False)
                        
                        st.dataframe(
                            display_df,
                            use_container_width=True,
                            hide_index=True,
                            height=500
                        )
                        
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
                    
                    with st.expander("🔍 VILT Debug Information", expanded=False):
                        st.write(f"Total VILT students in session state: {len(vilt_base_data)}")
                        st.write(f"Displayed VILT students: {len(vilt_data)}")
                        st.write(f"Filters applied to VILT: {apply_filters_to_vilt}")
                        st.write(f"Number of VILT classes: {len(vilt_classes)}")
                        if len(vilt_data) > 0:
                            st.write("VILT classes and student counts:")
                            class_counts = vilt_data['VILT Class'].value_counts().head(10)
                            st.write(class_counts)
            else:
                st.info("No VILT class data available. Users need to have VILT class values assigned.")
        
        st.markdown("---")
        
        st.header("Training Completion Status")
        
        training_completion_base_data = df.copy()
        
        st.subheader("Filters for Training Completion Status")
        
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        
        training_selected_regions = []
        training_selected_roles = []
        training_selected_business_units = []
        training_selected_employee_types = []
        
        with filter_col1:
            if 'Region' in training_completion_base_data.columns and len(training_completion_base_data) > 0:
                training_regions = training_completion_base_data['Region'].dropna().unique()
                training_regions = sorted([r for r in training_regions if pd.notna(r)])
                if training_regions:
                    training_selected_regions = st.multiselect(
                        "Filter by Region",
                        options=training_regions,
                        default=[],
                        key="training_region_filter"
                    )
        
        with filter_col2:
            if 'Role' in training_completion_base_data.columns and len(training_completion_base_data) > 0:
                training_roles = training_completion_base_data['Role'].dropna().unique()
                training_roles = sorted([r for r in training_roles if pd.notna(r)])
                if training_roles:
                    training_selected_roles = st.multiselect(
                        "Filter by Role",
                        options=training_roles,
                        default=[],
                        key="training_role_filter"
                    )
        
        with filter_col3:
            if 'Business Unit' in training_completion_base_data.columns and len(training_completion_base_data) > 0:
                training_business_units = training_completion_base_data['Business Unit'].dropna().unique()
                training_business_units = sorted([bu for bu in training_business_units if pd.notna(bu)])
                if training_business_units:
                    training_selected_business_units = st.multiselect(
                        "Filter by Business Unit",
                        options=training_business_units,
                        default=[],
                        key="training_business_unit_filter"
                    )
        
        with filter_col4:
            if 'Employee Type' in training_completion_base_data.columns and len(training_completion_base_data) > 0:
                training_employee_types = training_completion_base_data['Employee Type'].dropna().unique()
                training_employee_types = sorted([et for et in training_employee_types if pd.notna(et)])
                if training_employee_types:
                    training_selected_employee_types = st.multiselect(
                        "Filter by Employee Type",
                        options=training_employee_types,
                        default=[],
                        key="training_employee_type_filter"
                    )
        
        training_completion_data = apply_filters_fast(
            training_completion_base_data,
            training_selected_regions if training_selected_regions else None,
            training_selected_roles if training_selected_roles else None,
            training_selected_business_units if training_selected_business_units else None,
            training_selected_employee_types if training_selected_employee_types else None
        )
        
        total_training_employees = len(training_completion_base_data)
        displayed_training_employees = len(training_completion_data)
        
        if displayed_training_employees == total_training_employees:
            st.success(f"📊 Showing Training Completion Status for ALL {displayed_training_employees} employees")
        else:
            st.info(f"📊 Showing Training Completion Status for {displayed_training_employees} of {total_training_employees} employees")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Boot Camp Completion")
            if 'Boot Camp In-Person' in training_completion_data.columns:
                completed = training_completion_data['Boot Camp In-Person'].notna().sum()
                not_completed = len(training_completion_data) - completed
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
            if 'VILT' in training_completion_data.columns:
                completed = training_completion_data['VILT'].notna().sum()
                not_completed = len(training_completion_data) - completed
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
        
        st.subheader("Employee Training Completion Details")
        
        if len(training_completion_data) > 0:
            completion_display_columns = ['Preferred Name', 'Work Email', 'Region', 'Role', 'Business Unit']
            
            if 'Boot Camp In-Person' in training_completion_data.columns:
                completion_display_columns.append('Boot Camp In-Person')
            
            if 'VILT' in training_completion_data.columns:
                completion_display_columns.append('VILT')
            
            if 'SE Capstone' in training_completion_data.columns:
                completion_display_columns.append('SE Capstone')
            
            if 'Course Completion' in training_completion_data.columns:
                completion_display_columns.append('Course Completion')
            
            available_completion_columns = [col for col in completion_display_columns if col in training_completion_data.columns]
            
            completion_display_df = training_completion_data[available_completion_columns].copy()
            
            def format_completion_date(value):
                if pd.isna(value):
                    return None
                try:
                    if pd.api.types.is_datetime64_any_dtype(type(value)):
                        return value.strftime('%Y-%m-%d')
                    date_val = pd.to_datetime(value, errors='coerce')
                    if pd.notna(date_val):
                        return date_val.strftime('%Y-%m-%d')
                except:
                    pass
                return None
            
            if 'Boot Camp In-Person' in completion_display_df.columns:
                completion_display_df['Boot Camp Status'] = completion_display_df['Boot Camp In-Person'].apply(
                    lambda x: '✅ Completed' if pd.notna(x) else '❌ Not Completed'
                )
            
            if 'VILT' in completion_display_df.columns:
                completion_display_df['VILT Status'] = completion_display_df['VILT'].apply(
                    lambda x: '✅ Completed' if pd.notna(x) else '❌ Not Completed'
                )
            
            if 'Course Completion' in completion_display_df.columns:
                completion_display_df['Course Completion Date'] = completion_display_df['Course Completion'].apply(format_completion_date)
            
            if 'SE Capstone' in training_completion_data.columns:
                completion_display_df['SE Capstone Date'] = training_completion_data['SE Capstone'].apply(format_completion_date)
            
            status_columns = []
            date_columns = []
            
            if 'Boot Camp Status' in completion_display_df.columns:
                status_columns.append('Boot Camp Status')
            
            if 'VILT Status' in completion_display_df.columns:
                status_columns.append('VILT Status')
            
            if 'Course Completion Date' in completion_display_df.columns:
                date_columns.append('Course Completion Date')
            
            if 'SE Capstone Date' in completion_display_df.columns:
                date_columns.append('SE Capstone Date')
            
            final_columns = ['Preferred Name', 'Work Email', 'Region', 'Role', 'Business Unit'] + status_columns + date_columns
            final_columns = [col for col in final_columns if col in completion_display_df.columns]
            
            completion_display_df = completion_display_df[final_columns].copy()
            completion_display_df = completion_display_df.sort_values('Preferred Name', ascending=True)
            
            st.dataframe(
                completion_display_df,
                use_container_width=True,
                hide_index=True,
                height=400
            )
            
            completion_csv = completion_display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Training Completion Data",
                data=completion_csv,
                file_name=f"training_completion_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No data available to display.")
        
        st.markdown("---")
        
        if 'Transfer/Promo' in st.session_state.employee_df.columns:
            st.header("🔄 Transfer/Promo Analysis")
            
            if 'data_refresh_time' in st.session_state:
                st.caption(f"Last updated: {st.session_state.data_refresh_time}")
            
            transfer_promo_base_data = st.session_state.employee_df[st.session_state.employee_df['Transfer/Promo'].notna()].copy()
            
            col1, col2 = st.columns([1, 3])
            with col1:
                apply_filters_to_transfer = st.checkbox("Apply Sidebar Filters to Transfer/Promo", value=False, help="Check this to apply the sidebar filters to the Transfer/Promo section")
            with col2:
                if apply_filters_to_transfer:
                    st.info("🔄 Transfer/Promo data is filtered by sidebar selections")
                else:
                    st.info("🔄 Transfer/Promo shows ALL transfer/promo data")
            
            # Only apply filters if user explicitly requests it
            if len(transfer_promo_base_data) > 0:
                if apply_filters_to_transfer:
                    transfer_promo_data = apply_filters_fast(
                        transfer_promo_base_data,
                        selected_regions if selected_regions else None,
                        selected_roles if selected_roles else None,
                        selected_business_units if selected_business_units else None,
                        selected_employee_types if selected_employee_types else None
                    )
                else:
                    transfer_promo_data = transfer_promo_base_data.copy()
            else:
                transfer_promo_data = pd.DataFrame()
            
            if len(transfer_promo_data) > 0:
                total_transfer_promo = len(transfer_promo_base_data)
                displayed_transfer_promo = len(transfer_promo_data)
                
                if displayed_transfer_promo == total_transfer_promo:
                    st.success(f"🔄 Showing ALL {displayed_transfer_promo} Transfer/Promo records")
                else:
                    st.info(f"🔄 Showing {displayed_transfer_promo} of {total_transfer_promo} Transfer/Promo records")
                
                transfer_promo_data['Transfer/Promo Type'] = transfer_promo_data['Transfer/Promo'].astype(str)
                transfer_promo_types = transfer_promo_data['Transfer/Promo Type'].value_counts()
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.subheader("Transfer/Promo Overview")
                    
                    if len(transfer_promo_types) > 0:
                        fig_transfer_promo = px.pie(
                            values=transfer_promo_types.values,
                            names=transfer_promo_types.index,
                            title='Transfer/Promo Distribution',
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        fig_transfer_promo.update_layout(height=400, showlegend=True)
                        st.plotly_chart(fig_transfer_promo, use_container_width=True)
                    
                    transfer_promo_options = ["All Types"] + list(transfer_promo_types.index)
                    selected_transfer_promo_type = st.selectbox(
                        "Select Transfer/Promo Type to View",
                        options=transfer_promo_options,
                        index=0
                    )
                
                with col2:
                    st.subheader("Transfer/Promo Details")
                    
                    if selected_transfer_promo_type == "All Types":
                        display_transfer_promo_data = transfer_promo_data
                        st.info(f"Showing all {len(display_transfer_promo_data)} Transfer/Promo records")
                    else:
                        display_transfer_promo_data = transfer_promo_data[transfer_promo_data['Transfer/Promo Type'] == selected_transfer_promo_type]
                        st.info(f"Showing {len(display_transfer_promo_data)} records for: {selected_transfer_promo_type}")
                    
                    if len(display_transfer_promo_data) > 0:
                        display_columns = ['Preferred Name', 'Work Email', 'Region', 'Role', 
                                         'Business Unit', 'Transfer/Promo', 'Hire Date', 'Business Title']
                        available_columns = [col for col in display_columns if col in display_transfer_promo_data.columns]
                        
                        # Prepare display dataframe
                        display_df = display_transfer_promo_data[available_columns].copy()
                        display_df = display_df.sort_values('Transfer/Promo', ascending=False)
                        
                        st.dataframe(
                            display_df,
                            use_container_width=True,
                            hide_index=True,
                            height=500
                        )
                        
                        transfer_promo_csv = display_transfer_promo_data.to_csv(index=False)
                        st.download_button(
                            label=f"📥 Download {selected_transfer_promo_type if selected_transfer_promo_type != 'All Types' else 'All'} Transfer/Promo Data",
                            data=transfer_promo_csv,
                            file_name=f"transfer_promo_{selected_transfer_promo_type if selected_transfer_promo_type != 'All Types' else 'all'}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    
                    # Grouped view by Transfer/Promo type
                    st.markdown("### Grouped by Type")
                    for transfer_promo_type in sorted(transfer_promo_types.index, reverse=True):
                        type_records = transfer_promo_data[transfer_promo_data['Transfer/Promo Type'] == transfer_promo_type]
                        
                        with st.expander(f"🔄 {transfer_promo_type} ({len(type_records)} records)", expanded=False):
                            cols_to_show = ['Preferred Name', 'Work Email', 'Region', 'Role', 'Business Title']
                            cols_to_show = [c for c in cols_to_show if c in type_records.columns]
                            st.dataframe(
                                type_records[cols_to_show],
                                use_container_width=True,
                                hide_index=True
                            )
                    
                    with st.expander("🔍 Transfer/Promo Debug Information", expanded=False):
                        st.write(f"Total Transfer/Promo records in session state: {len(transfer_promo_base_data)}")
                        st.write(f"Displayed Transfer/Promo records: {len(transfer_promo_data)}")
                        st.write(f"Filters applied to Transfer/Promo: {apply_filters_to_transfer}")
                        st.write(f"Number of Transfer/Promo types: {len(transfer_promo_types)}")
                        if len(transfer_promo_data) > 0:
                            st.write("Transfer/Promo types and counts:")
                            st.write(transfer_promo_types)
            else:
                st.info("No Transfer/Promo data available. Users need to have Transfer/Promo values assigned.")
        
        st.markdown("---")
        #     hire_trends = filtered_df[filtered_df['Hire Date'].notna()]
        #     if len(hire_trends) > 0:
        #         st.subheader("Hiring Trends Over Time")
        #         hire_trends = hire_trends.copy()
        #         hire_trends['Hire Month'] = hire_trends['Hire Date'].dt.to_period('M').astype(str)
        #         monthly_hires = hire_trends.groupby('Hire Month', observed=False).size().reset_index()
        #         monthly_hires.columns = ['Month', 'Count']
        #         
        #         if len(monthly_hires) > 0:
        #             fig_hire_trend = px.line(
        #                 monthly_hires,
        #                 x='Month',
        #                 y='Count',
        #                 title='Monthly Hires Over Time',
        #                 markers=True
        #             )
        #             fig_hire_trend.update_layout(height=400, showlegend=False)
        #             fig_hire_trend.update_xaxes(tickangle=45)
        #             st.plotly_chart(fig_hire_trend, use_container_width=True)
        
        st.markdown("---")
        
        # Edit Employee Section - Now integrated in Dashboard
        st.header("✏️ Edit Employee")
        if 'Work Email' not in st.session_state.employee_df.columns or st.session_state.employee_df['Work Email'].isna().all():
            st.warning("No employee email addresses found. Cannot edit employees.")
        else:
            employees_with_email = st.session_state.employee_df[st.session_state.employee_df['Work Email'].notna()].copy()
            if len(employees_with_email) == 0:
                st.warning("No employees with email addresses found.")
            else:
                # Create display names for selectbox using email as unique identifier
                employee_options = []
                for idx, row in employees_with_email.iterrows():
                    name = row.get('Preferred Name', 'Unknown')
                    email = row.get('Work Email', 'No Email')
                    display_name = f"{name} ({email})" if name and name != 'Unknown' else email
                    employee_options.append((email, display_name))  # Use email as key instead of index
                
                employee_options.sort(key=lambda x: x[1])
                
                if employee_options:
                    selected_display = st.selectbox(
                        "Select Employee to Edit",
                        options=[opt[1] for opt in employee_options],
                        index=0,
                        key="edit_employee_select"
                    )
                    
                    selected_email = [opt[0] for opt in employee_options if opt[1] == selected_display][0]
                    # Find employee by email in session state dataframe
                    selected_employee = st.session_state.employee_df[st.session_state.employee_df['Work Email'] == selected_email].iloc[0].copy()
                    
                    # Helper functions for dropdowns
                    def get_dropdown_options(column_name, current_value=""):
                        if column_name not in st.session_state.employee_df.columns:
                            return [""]
                        options = [""] + sorted([str(v) for v in st.session_state.employee_df[column_name].dropna().unique() if pd.notna(v) and str(v).strip()])
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
                                
                                # Find the employee by email in the session state dataframe
                                email_mask = st.session_state.employee_df['Work Email'] == selected_email
                                if email_mask.sum() == 0:
                                    st.error("Employee not found in database. Please refresh and try again.")
                                    st.stop()
                                
                                actual_idx = st.session_state.employee_df[email_mask].index[0]
                                
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
                                
                                # Update the row directly using .loc
                                for col in original_df.columns:
                                    if col in updated_employee:
                                        original_df.loc[actual_idx, col] = updated_employee[col]
                                
                                updated_df = original_df.reset_index(drop=True).copy(deep=True)
                                
                                original_count = len(st.session_state.employee_df)
                                new_count = len(updated_df)
                                
                                # For updates, we should maintain the same count
                                if new_count != original_count:
                                    st.error(f"⚠️ Error: Row count mismatch! Expected {original_count}, got {new_count}. Update cancelled to prevent data loss.")
                                    st.error("This usually means the employee index was not found. Please try refreshing the page and editing again.")
                                    st.error(f"Selected email: {selected_email}")
                                    st.error(f"Found employee at index: {actual_idx}")
                                else:
                                    # Clear any cached data
                                    st.cache_data.clear()
                                    
                                    # Replace the entire dataframe in session state
                                    st.session_state.employee_df = updated_df.copy()
                                    
                                    # Force a complete refresh by updating timestamp
                                    st.session_state.last_update = datetime.now().isoformat()
                                    st.session_state.data_version = st.session_state.get('data_version', 0) + 1
                                    
                                    # Verify the employee still exists after update
                                    updated_employee_check = st.session_state.employee_df[st.session_state.employee_df['Work Email'] == work_email]
                                    if len(updated_employee_check) > 0:
                                        st.success(f"✅ Employee '{preferred_name}' updated successfully! Total employees: {new_count}")
                                        st.info(f"Employee count: {original_count} → {new_count} (should be the same)")
                                        st.info(f"✅ Verification: Employee found in database after update")
                                    else:
                                        st.error(f"❌ CRITICAL ERROR: Employee '{preferred_name}' not found in database after update!")
                                    
                                    st.balloons()
                                    
                                    # Force a complete page refresh to ensure all data is updated
                                    st.session_state.refresh_trigger = datetime.now().isoformat()
                                    st.rerun()
        
        st.markdown("---")
        
        # Data Table - limit display
        st.header("Employee Data")
        
        # Search functionality
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_term = st.text_input("🔍 Search employees", placeholder="Search by name, email, role, region, etc...", key="employee_search")
        with col2:
            st.metric("Total Employees", len(st.session_state.employee_df))
        with col3:
            if 'original_employee_count' in st.session_state:
                st.metric("Original Count", st.session_state.original_employee_count)
            else:
                st.metric("Original Count", "Not set")
        
        # Show ALL employees by default in Employee Data section
        display_df = st.session_state.employee_df.copy()
        
        # Add filter toggle for Employee Data section
        col1, col2 = st.columns([1, 3])
        with col1:
            apply_filters_to_table = st.checkbox("Apply Sidebar Filters to Table", value=False, help="Check this to apply the sidebar filters to the Employee Data table")
        with col2:
            if apply_filters_to_table:
                st.info("📊 Table is filtered by sidebar selections")
            else:
                st.info("📊 Table shows ALL employees")
        
        if len(display_df) > 0:
            # Only apply filters if user explicitly requests it
            if apply_filters_to_table:
                display_df = apply_filters_fast(
                    display_df,
                    selected_regions if selected_regions else None,
                    selected_roles if selected_roles else None,
                    selected_business_units if selected_business_units else None,
                    selected_employee_types if selected_employee_types else None
                )
            
            # Apply search filter if search term is provided
            if search_term and search_term.strip():
                search_mask = pd.Series([False] * len(display_df), index=display_df.index)
                search_columns = ['Preferred Name', 'Work Email', 'Personal', 'Role', 'Region', 'Business Unit', 'Business Title', 'Manager Name']
                
                for col in search_columns:
                    if col in display_df.columns:
                        search_mask |= display_df[col].astype(str).str.contains(search_term, case=False, na=False)
                
                display_df = display_df[search_mask]
        
        if len(display_df) > 0:
            # Show employee count information
            total_in_session = len(st.session_state.employee_df)
            total_in_display = len(display_df)
            
            if total_in_display == total_in_session:
                st.success(f"📊 Showing ALL {total_in_display} employees")
            else:
                st.info(f"📊 Showing {total_in_display} of {total_in_session} employees")
            
            display_limit = st.slider("Rows to display", 10, min(500, len(display_df)), 100, step=10)
            st.dataframe(
                display_df.head(display_limit),
                use_container_width=True,
                hide_index=True,
                height=400
            )
            
            if search_term and search_term.strip():
                st.info(f"Found {len(display_df)} employees matching '{search_term}'")
        else:
            if search_term and search_term.strip():
                st.warning(f"No employees found matching '{search_term}'")
            else:
                st.warning("No data matches the selected filters")
        
        # Debug information
        with st.expander("🔍 Debug Information", expanded=False):
            st.write(f"Session state dataframe shape: {st.session_state.employee_df.shape}")
            st.write(f"Display dataframe shape: {display_df.shape}")
            st.write(f"Total employees in session state: {len(st.session_state.employee_df)}")
            st.write(f"Total employees in display: {len(display_df)}")
            st.write(f"Filters applied to table: {apply_filters_to_table}")
            st.write(f"Search term: '{search_term}'")
            if len(st.session_state.employee_df) > 0:
                st.write("First few employees in session state:")
                st.dataframe(st.session_state.employee_df[['Preferred Name', 'Work Email']].head())
            
            # Show filter details
            if apply_filters_to_table:
                st.write("**Active Filters:**")
                st.write(f"- Regions: {selected_regions if selected_regions else 'All'}")
                st.write(f"- Roles: {selected_roles if selected_roles else 'All'}")
                st.write(f"- Business Units: {selected_business_units if selected_business_units else 'All'}")
                st.write(f"- Employee Types: {selected_employee_types if selected_employee_types else 'All'}")
    
    # Export Button
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        csv = st.session_state.employee_df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"bootcamp_class_list_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    with col2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.employee_df.to_excel(writer, index=False, sheet_name='Boot Camp Class List')
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
                
                # Add to dataframe
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
                st.rerun()

# Footer
st.markdown("---")
st.caption(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
