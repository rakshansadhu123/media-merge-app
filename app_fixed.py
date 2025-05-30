
import streamlit as st
import pandas as pd

# Must be the first Streamlit command
st.set_page_config(page_title="MediaMerge", layout="wide")

st.title("📊 Media Merge App")
st.write("Upload benchmark data first, then upload media performance files to generate metrics and compare against benchmarks.")

# --- Benchmark File Upload ---
st.header("📉 Upload Benchmark File")

if 'benchmark_df' not in st.session_state:
    st.session_state['benchmark_df'] = None

if st.session_state['benchmark_df'] is None:
    benchmark_file = st.file_uploader(
        "Upload your benchmark Excel file (must include 'Channel', 'Benchmark CPM', 'Benchmark ROAS')",
        type=["xlsx"],
        key="benchmark"
    )
    if benchmark_file:
        try:
            benchmark_df = pd.read_excel(benchmark_file)
            benchmark_df.columns = [c.strip().lower() for c in benchmark_df.columns]
            benchmark_df.rename(columns={
                'channel': 'Channel',
                'benchmark cpm': 'Benchmark CPM',
                'benchmark roas': 'Benchmark ROAS'
            }, inplace=True)
            st.session_state['benchmark_df'] = benchmark_df
            st.success("✅ Benchmark file loaded!")
        except Exception as e:
            st.error(f"❌ Error loading benchmark file: {e}")

# --- Media Files Upload ---
st.header("📁 Upload Media Performance Files")

uploaded_files = st.file_uploader("Upload media Excel files", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    benchmark_df = st.session_state.get('benchmark_df', None)

    for uploaded_file in uploaded_files:
        try:
            df = pd.read_excel(uploaded_file)

            # Normalize and rename columns to match expected metric calculations
            df.columns = [col.strip().lower() for col in df.columns]
            col_map = {
                'spend (£)': 'Spend (£)',
                'cost': 'Spend (£)',
                'impressions': 'Impressions',
                'views': 'Impressions',
                'clicks': 'Clicks',
                'conversions': 'Conversions',
                'revenue (£)': 'Revenue (£)'
            }
            df.rename(columns=col_map, inplace=True)

            # Ensure all expected columns exist
            for col in ['Spend (£)', 'Impressions', 'Clicks', 'Conversions', 'Revenue (£)']:
                if col not in df.columns:
                    df[col] = 0

            # Metric calculations
            df['CPM (£)'] = df['Spend (£)'] / (df['Impressions'] / 1000).replace(0, pd.NA)
            df['CTR (%)'] = (df['Clicks'] / df['Impressions']).replace(0, pd.NA) * 100
            df['CPC (£)'] = df['Spend (£)'] / df['Clicks'].replace(0, pd.NA)
            df['ROAS'] = df['Revenue (£)'] / df['Spend (£)'].replace(0, pd.NA)
            df['Conversion Rate (%)'] = df['Conversions'] / df['Clicks'].replace(0, pd.NA) * 100

            # Benchmark comparison
            if 'channel' in [c.lower() for c in df.columns] and benchmark_df is not None:
                df.rename(columns={c: 'Channel' for c in df.columns if c.lower() == 'channel'}, inplace=True)
                df = df.merge(benchmark_df[['Channel', 'Benchmark CPM', 'Benchmark ROAS']], on='Channel', how='left')

                df['CPM vs Benchmark'] = df['CPM (£)'] - df['Benchmark CPM']
                df['CPM Status'] = df.apply(
                    lambda row: 'Above Benchmark' if pd.notna(row['Benchmark CPM']) and row['CPM (£)'] > row['Benchmark CPM']
                    else ('Below Benchmark' if pd.notna(row['Benchmark CPM']) and row['CPM (£)'] <= row['Benchmark CPM']
                    else 'No Benchmark'),
                    axis=1
                )
                df['ROAS Status'] = df.apply(
                    lambda row: 'Above Benchmark' if pd.notna(row['Benchmark ROAS']) and row['ROAS'] > row['Benchmark ROAS']
                    else ('Below Benchmark' if pd.notna(row['Benchmark ROAS']) and row['ROAS'] <= row['Benchmark ROAS']
                    else 'No Benchmark'),
                    axis=1
                )
            else:
                df['CPM vs Benchmark'] = pd.NA
                df['CPM Status'] = 'No Benchmark'
                df['ROAS Status'] = 'No Benchmark'

            df['Source File'] = uploaded_file.name
            all_data.append(df)

        except Exception as e:
            st.error(f"❌ Error processing {uploaded_file.name}: {e}")

    if all_data:
        merged_df = pd.concat(all_data, ignore_index=True)
        st.success("✅ Files merged successfully!")
        st.dataframe(merged_df)

        csv = merged_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Merged File",
            data=csv,
            file_name='merged_media_data.csv',
            mime='text/csv',
        )
