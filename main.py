import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="Department Research Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- Custom Styling ---
st.markdown("""
    <style>
    .main {
        background-color: #f9f9f9;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .stHeader {
        color: #2c3e50;
    }
    </style>
""", unsafe_allow_html=True)

# --- Data Loading Helper ---
def load_file(file_obj):
    """
    Robust file loader that handles encoding issues, engine errors,
    and format mismatches (CSV vs Excel).
    """
    
    # Helper to wrap the file logic whether it's a path (str) or uploaded file
    def read_with_options(source):
        # 1. Try Standard UTF-8
        try:
            if hasattr(source, 'seek'): source.seek(0)
            return pd.read_csv(source, encoding='utf-8')
        except:
            pass
            
        # 2. Try Latin-1 (Common for Excel exports)
        try:
            if hasattr(source, 'seek'): source.seek(0)
            return pd.read_csv(source, encoding='latin1')
        except:
            pass

        # 3. Try Python Engine with Auto-Separator (Fixes 'Expected 1 fields' error)
        try:
            if hasattr(source, 'seek'): source.seek(0)
            return pd.read_csv(source, sep=None, engine='python', encoding='utf-8')
        except:
            pass
            
        # 4. Try Python Engine with Latin-1
        try:
            if hasattr(source, 'seek'): source.seek(0)
            return pd.read_csv(source, sep=None, engine='python', encoding='latin1')
        except:
            pass

        # 5. Last Resort: Try Excel
        try:
            if hasattr(source, 'seek'): source.seek(0)
            return pd.read_excel(source)
        except Exception as e:
            raise ValueError(f"All parsing attempts failed. Last error: {e}")

    return read_with_options(file_obj)

# --- Main Data Function ---
@st.cache_data
def load_and_clean_data(ece_file, cse_file):
    try:
        # Load files using the robust loader
        df_ece = load_file(ece_file)
        df_cse = load_file(cse_file)
        
        # Add Department Tag
        df_ece['Department'] = 'ECE'
        df_cse['Department'] = 'CSE'
        
        # Standardize Columns for ECE
        ece_rename_map = {
            'Name of Professor': 'Name',
            'Number of Journal Publications': 'Journal Publications',
            'Number of Conference Publications': 'Conference Publications',
            'Number of Publications (Total)': 'Total Publications',
            'Books/Chapters Count': 'Books/Chapters',
            'Patents Count': 'Patents',
            'Projects Count': 'Projects',
            'Citations Count': 'Citations',
            'H Index Count': 'H Index'
        }
        df_ece = df_ece.rename(columns=ece_rename_map)
        
        # Standardize Columns for CSE
        cse_rename_map = {
            'Name of professor': 'Name',
            'Number of Journal Publications': 'Journal Publications',
            'Number of Conference Publications': 'Conference Publications',
            'Number of Publications (Total)': 'Total Publications',
            'Books/Chapters (Count)': 'Books/Chapters',
            'Patents (Count)': 'Patents',
            'Projects (Count)': 'Projects',
            'Citations': 'Citations',
            'H index': 'H Index'
        }
        df_cse = df_cse.rename(columns=cse_rename_map)
        
        # Select common columns to ensure clean merge
        common_columns = ['Name', 'Designation', 'Journal Publications', 
                          'Conference Publications', 'Total Publications', 
                          'Books/Chapters', 'Patents', 'Projects', 
                          'Citations', 'H Index', 'Department']
        
        # Combine
        combined_df = pd.concat([df_ece[common_columns], df_cse[common_columns]], ignore_index=True)
        
        # List of columns that MUST be numbers
        numeric_cols = ['Journal Publications', 'Conference Publications', 
                        'Total Publications', 'Books/Chapters', 'Patents', 
                        'Projects', 'Citations', 'H Index']
        
        # --- FIX: FORCE TO NUMERIC ---
        # This converts strings like "10 " to 10, and garbage like "NA" to NaN
        for col in numeric_cols:
            combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce')
        
        # Now fill the NaNs (errors) with 0
        combined_df[numeric_cols] = combined_df[numeric_cols].fillna(0)
        
        return combined_df
        
    except Exception as e:
        st.error(f"Error processing files: {e}")
        return None

# --- Main App Logic ---

st.title("📊 Research Performance Dashboard")
st.markdown("Compare research metrics between *ECE* and *CSE* departments.")

# Sidebar for Navigation and Files
with st.sidebar:
    st.header("Settings")
    
    data = None
    
    # File Uploader
    uploaded_files = st.file_uploader("Upload CSV files (Select both ECE & CSE)", 
                                      type=['csv', 'xlsx'], 
                                      accept_multiple_files=True)
    
    file_ece = None
    file_cse = None

    # Logic to handle uploaded files
    if uploaded_files:
        for f in uploaded_files:
            fname = f.name.upper()
            if "ECE" in fname:
                file_ece = f
            elif "CSE" in fname:
                file_cse = f
        
        if file_ece and file_cse:
            st.success("✅ Both files identified!")
            data = load_and_clean_data(file_ece, file_cse)
        elif len(uploaded_files) < 2:
            st.warning("⚠ Please upload TWO files (one for ECE, one for CSE).")
        else:
            st.error("❌ Could not distinguish files. Ensure filenames contain 'ECE' and 'CSE'.")
    else:
        st.info("Waiting for upload...")

if data is not None:
    # Sidebar Navigation
    page = st.sidebar.radio("Go to", ["Overview", "Department Comparison", "Faculty Rankings", "Teacher Profile"])
    
    # Global Filters (Optional)
    filtered_data = data # Use full data for now
    
    # --- PAGE 1: OVERVIEW ---
    if page == "Overview":
        st.header("General Overview")
        
        # Key Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Faculty", len(filtered_data))
        c2.metric("Total Publications", int(filtered_data['Total Publications'].sum()))
        c3.metric("Total Citations", int(filtered_data['Citations'].sum()))
        c4.metric("Avg H-Index", f"{filtered_data['H Index'].mean():.2f}")
        
        st.markdown("### Department Split")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart for Faculty count
            dept_counts = filtered_data['Department'].value_counts().reset_index()
            dept_counts.columns = ['Department', 'Count']
            fig_pie = px.pie(dept_counts, values='Count', names='Department', title="Faculty Distribution", color='Department', 
                             color_discrete_map={'ECE':'#EF553B', 'CSE':'#636EFA'})
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col2:
             # Total Journals per Dept
            dept_journals = filtered_data.groupby('Department')['Journal Publications'].sum().reset_index()
            fig_bar = px.bar(dept_journals, x='Department', y='Journal Publications', color='Department', 
                             title="Total Journal Publications by Dept", text_auto=True,
                             color_discrete_map={'ECE':'#EF553B', 'CSE':'#636EFA'})
            st.plotly_chart(fig_bar, use_container_width=True)

    # --- PAGE 2: DEPARTMENT COMPARISON ---
    elif page == "Department Comparison":
        st.header("Inter-Department Comparison")
        
        # User Selection for Comparison
        feature = st.selectbox("Select Feature to Compare", 
                               ['Journal Publications', 'Citations', 'Patents', 'Projects', 'H Index', 'Total Publications'])
        
        col1, col2 = st.columns(2)
        
        # 1. Total Count Comparison
        with col1:
            st.subheader(f"Total {feature}")
            dept_sum = filtered_data.groupby('Department')[feature].sum().reset_index()
            fig_sum = px.bar(dept_sum, x='Department', y=feature, color='Department', 
                             title=f"Total {feature} (Sum)", text_auto=True,
                             color_discrete_map={'ECE':'#EF553B', 'CSE':'#636EFA'})
            st.plotly_chart(fig_sum, use_container_width=True)
            
        # 2. Average Comparison
        with col2:
            st.subheader(f"Average {feature}")
            dept_avg = filtered_data.groupby('Department')[feature].mean().reset_index()
            fig_avg = px.bar(dept_avg, x='Department', y=feature, color='Department', 
                             title=f"Average {feature} per Faculty", text_auto='.2f',
                             color_discrete_map={'ECE':'#EF553B', 'CSE':'#636EFA'})
            st.plotly_chart(fig_avg, use_container_width=True)
            
        # 3. Distribution (Box Plot)
        st.subheader(f"Distribution of {feature}")
        fig_box = px.box(filtered_data, x='Department', y=feature, color='Department', points="all",
                         title=f"Statistical Distribution of {feature}",
                         color_discrete_map={'ECE':'#EF553B', 'CSE':'#636EFA'})
        st.plotly_chart(fig_box, use_container_width=True)
        
        # Correlation Heatmap (Bonus)
        st.subheader("Correlation Heatmap (Numeric Features)")
        numeric_df = filtered_data[['Journal Publications', 'Conference Publications', 'Total Publications', 'Citations', 'H Index', 'Patents', 'Projects']]
        corr = numeric_df.corr()
        fig_corr = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='RdBu_r')
        st.plotly_chart(fig_corr, use_container_width=True)

    # --- PAGE 3: FACULTY RANKINGS ---
    elif page == "Faculty Rankings":
        st.header("🏆 Faculty Rankings")
        
        c1, c2, c3 = st.columns([1, 1, 1])
        
        with c1:
            target_dept = st.selectbox("Select Department", ["All", "ECE", "CSE"])
        with c2:
            ranking_metric = st.selectbox("Rank By", ['Journal Publications', 'Citations', 'Patents', 'Projects', 'H Index'])
        with c3:
            top_n = st.slider("Show Top", 5, 20, 10)
            
        # Filter Data
        if target_dept != "All":
            ranking_data = filtered_data[filtered_data['Department'] == target_dept]
        else:
            ranking_data = filtered_data
            
        # Sort
        ranking_data = ranking_data.sort_values(by=ranking_metric, ascending=False).head(top_n)
        
        # Plot
        fig_rank = px.bar(ranking_data, x=ranking_metric, y='Name', orientation='h', 
                          color='Department', text_auto=True,
                          title=f"Top {top_n} Faculty by {ranking_metric}",
                          color_discrete_map={'ECE':'#EF553B', 'CSE':'#636EFA'})
        fig_rank.update_layout(yaxis={'categoryorder':'total ascending'}) # Ensure sorted order in chart
        st.plotly_chart(fig_rank, use_container_width=True)
        
        # Data Table
        # Fix: Create a list of columns to display and remove duplicates to avoid ValueError
        display_cols = ['Name', 'Department', 'Designation', ranking_metric, 'Citations', 'H Index']
        unique_cols = list(dict.fromkeys(display_cols)) # Removes duplicates while preserving order
        
        st.dataframe(ranking_data[unique_cols])

    # --- PAGE 4: TEACHER PROFILE ---
    elif page == "Teacher Profile":
        st.header("🧑‍🏫 Individual Teacher Profile")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            selected_dept = st.selectbox("Select Department", ["ECE", "CSE"])
            dept_profs = filtered_data[filtered_data['Department'] == selected_dept]['Name'].unique()
            selected_prof = st.selectbox("Select Professor", sorted(dept_profs))
            
        # Get Prof Data
        prof_data = filtered_data[filtered_data['Name'] == selected_prof].iloc[0]
        
        with col2:
            st.subheader(f"{prof_data['Name']}")
            st.markdown(f"*Designation:* {prof_data['Designation']}")
            st.markdown(f"*Department:* {prof_data['Department']}")
            
        st.markdown("---")
        
        # Metrics Row
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Journals", int(prof_data['Journal Publications']))
        m2.metric("Conferences", int(prof_data['Conference Publications']))
        m3.metric("Citations", int(prof_data['Citations']))
        m4.metric("H-Index", int(prof_data['H Index']))
        m5.metric("Patents", int(prof_data['Patents']))
        
        # Chart for this professor
        st.subheader("Publication Composition")
        
        # Pie chart of their work
        labels = ['Journals', 'Conferences', 'Books/Chapters']
        values = [prof_data['Journal Publications'], prof_data['Conference Publications'], prof_data['Books/Chapters']]
        
        c_chart1, c_chart2 = st.columns(2)
        
        with c_chart1:
            fig_prof_pie = px.pie(values=values, names=labels, title="Publication Types")
            st.plotly_chart(fig_prof_pie, use_container_width=True)
            
        with c_chart2:
            # Radar Chart
            categories = ['Journals', 'Conferences', 'Projects', 'Patents']
            r_values = [prof_data['Journal Publications'], prof_data['Conference Publications'], prof_data['Projects'], prof_data['Patents']]
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=r_values,
                theta=categories,
                fill='toself',
                name=prof_data['Name']
            ))
            fig_radar.update_layout(title="Activity Radar", polar=dict(radialaxis=dict(visible=True)))
            st.plotly_chart(fig_radar, use_container_width=True)

else:
    st.info("Waiting for data... Please upload your CSV files using the sidebar.")