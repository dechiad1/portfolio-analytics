"""
Streamlit Dashboard for Portfolio Analytics
"""

import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Portfolio Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Database connection
@st.cache_resource
def get_db_connection():
    """Get DuckDB connection"""
    db_path = Path(__file__).parent / 'data' / 'portfolio.duckdb'
    return duckdb.connect(str(db_path), read_only=True)

@st.cache_data
def load_performance_data():
    """Load performance metrics from database"""
    con = get_db_connection()
    query = """
    SELECT 
        ticker,
        total_return_pct,
        annualized_return_pct,
        volatility_pct,
        sharpe_ratio,
        vs_benchmark_pct
    FROM main_marts.fct_performance
    ORDER BY total_return_pct DESC
    """
    return con.execute(query).df()

@st.cache_data
def load_asset_class_data():
    """Load asset class distribution"""
    con = get_db_connection()
    query = """
    SELECT 
        ticker,
        name,
        asset_class,
        sector,
        total_return_pct,
        volatility_pct,
        sharpe_ratio,
        vs_benchmark_pct
    FROM main_marts.dim_asset_classes
    WHERE total_return_pct IS NOT NULL
    """
    return con.execute(query).df()

@st.cache_data
def load_fund_metadata():
    """Load fund metadata from dim_funds"""
    con = get_db_connection()
    query = """
    SELECT
        ticker,
        fund_name,
        quote_type,
        asset_class,
        sector,
        expense_ratio_pct,
        mandate
    FROM main_marts.dim_funds
    ORDER BY ticker
    """
    return con.execute(query).df()

@st.cache_data
def load_price_history(ticker):
    """Load price history for a specific ticker"""
    con = get_db_connection()
    query = f"""
    SELECT date, price
    FROM main_staging.stg_prices
    WHERE ticker = '{ticker}'
    ORDER BY date
    """
    return con.execute(query).df()

# Main dashboard
def main():
    st.title("📊 Portfolio Analytics Dashboard")
    st.markdown("---")

    try:
        # Load data
        performance_df = load_performance_data()
        asset_class_df = load_asset_class_data()
        fund_metadata_df = load_fund_metadata()

        # Portfolio Holdings Metadata (Collapsible)
        with st.expander("📋 View Portfolio Holdings Details", expanded=False):
            st.markdown("### Holdings Metadata")

            # Create display dataframe with simplified asset types
            metadata_display = fund_metadata_df.copy()

            # Simplify asset type based on quote_type and asset_class
            def get_asset_type(row):
                if pd.notna(row['quote_type']):
                    if row['quote_type'] == 'EQUITY':
                        return 'Stock'
                    elif row['quote_type'] == 'MUTUALFUND':
                        return 'Mutual Fund'
                    elif row['quote_type'] == 'ETF':
                        return 'ETF'
                # Fallback to asset_class if quote_type is not available
                if pd.notna(row['asset_class']):
                    return row['asset_class']
                return 'Unknown'

            metadata_display['Asset Type'] = metadata_display.apply(get_asset_type, axis=1)

            # Select and rename columns for display
            display_cols = metadata_display[['ticker', 'fund_name', 'Asset Type', 'sector', 'expense_ratio_pct']]
            display_cols.columns = ['Ticker', 'Name', 'Asset Type', 'Sector', 'Expense Ratio (%)']

            # Format expense ratio
            display_cols['Expense Ratio (%)'] = display_cols['Expense Ratio (%)'].apply(
                lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
            )

            # Display the table
            st.dataframe(display_cols, use_container_width=True, hide_index=True)

            # Show additional details for selected ticker
            st.markdown("---")
            st.markdown("**View Detailed Information:**")
            selected_ticker = st.selectbox(
                "Select a holding to view full details:",
                options=metadata_display['ticker'].tolist(),
                key='metadata_ticker_select'
            )

            if selected_ticker:
                ticker_details = metadata_display[metadata_display['ticker'] == selected_ticker].iloc[0]

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Ticker:** {ticker_details['ticker']}")
                    st.markdown(f"**Name:** {ticker_details['fund_name']}")
                    st.markdown(f"**Asset Type:** {ticker_details['Asset Type']}")
                    st.markdown(f"**Sector:** {ticker_details['sector'] if pd.notna(ticker_details['sector']) else 'N/A'}")

                with col2:
                    expense_ratio = f"{ticker_details['expense_ratio_pct']:.2f}%" if pd.notna(ticker_details['expense_ratio_pct']) else 'N/A'
                    st.markdown(f"**Expense Ratio:** {expense_ratio}")
                    st.markdown(f"**Security Type:** {ticker_details['quote_type'] if pd.notna(ticker_details['quote_type']) else 'N/A'}")

                # Show mandate/description if available
                if pd.notna(ticker_details['mandate']) and ticker_details['mandate']:
                    st.markdown("**Description:**")
                    st.info(ticker_details['mandate'])

        st.markdown("---")
        
        # Top-level metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_return = performance_df['total_return_pct'].mean()
            st.metric("Avg Total Return", f"{avg_return:.1f}%")
        
        with col2:
            best_performer = performance_df.iloc[0]
            st.metric("Best Performer", 
                     best_performer['ticker'],
                     f"{best_performer['total_return_pct']:.1f}%")
        
        with col3:
            avg_sharpe = performance_df['sharpe_ratio'].mean()
            st.metric("Avg Sharpe Ratio", f"{avg_sharpe:.2f}")
        
        with col4:
            beat_benchmark = (performance_df['vs_benchmark_pct'] > 0).sum()
            st.metric("Beat S&P 500", f"{beat_benchmark} / {len(performance_df)}")
        
        st.markdown("---")
        
        # Two column layout
        l2_col1, l2_col2 = st.columns(2)
        
        with l2_col1:
            st.subheader("📈 Performance Overview")
            
            # Performance table
            display_df = performance_df[['ticker', 'total_return_pct', 'annualized_return_pct', 'sharpe_ratio', 'vs_benchmark_pct']]
            display_df.columns = ['Ticker', 'Total Return (%)', 'Annual Return (%)', 'Sharpe', 'vs. S&P 500 (%)']
            
            # Color code vs benchmark
            def color_benchmark(val):
                if pd.isna(val):
                    return ''
                color = 'green' if val > 0 else 'red'
                return f'color: {color}; font-weight: bold'
            
            styled_df = display_df.style.applymap(color_benchmark, subset=['vs. S&P 500 (%)'])
            st.dataframe(styled_df, use_container_width=True)
        
        with l2_col2:
            st.subheader("🎯 Risk vs Return")

            # Scatter plot: Risk vs Return (exclude money markets)
            # Filter out money market funds for meaningful comparison
            risk_return_df = asset_class_df[
                (asset_class_df['asset_class'] != 'Cash & Equivalents')
            ].copy()

            # Merge with performance to get the data
            risk_return_plot = performance_df[
                performance_df['ticker'].isin(risk_return_df['ticker'])
            ].fillna(0)

            fig = px.scatter(
                risk_return_plot,
                x='volatility_pct',
                y='annualized_return_pct',
                color="sharpe_ratio",
                color_continuous_scale="RdYlGn",
                hover_name='ticker',
                labels={
                    'volatility_pct': 'Volatility (%)',
                    'annualized_return_pct': 'Annualized Return (%)',
                    'sharpe_ratio': 'Sharpe Ratio'
                },
                title='Risk-Return Profile (excl. Money Markets)',
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")

        # Asset class and sector analysis
        l3_col1, l3_col2 = st.columns(2)

        with l3_col1:
            st.subheader("🏛️ Asset Class Distribution")

            # Group by asset class
            asset_summary = asset_class_df.groupby('asset_class').agg({
                'ticker': 'count',
                'total_return_pct': 'mean',
                'volatility_pct': 'mean',
                'sharpe_ratio': 'mean'
            }).reset_index()
            asset_summary.columns = ['Asset Class', 'Count', 'Avg Return (%)', 'Avg Volatility', 'Avg Sharpe']

            st.dataframe(asset_summary, use_container_width=True)

            # Pie chart
            fig = px.pie(
                asset_summary,
                values='Count',
                names='Asset Class',
                title='Holdings by Asset Class'
            )
            st.plotly_chart(fig, use_container_width=True)

        with l3_col2:
            st.subheader("🏢 Sector Distribution")

            # Group by sector (filter out NaN sectors)
            sector_df = asset_class_df[asset_class_df['sector'].notna()].copy()

            sector_summary = sector_df.groupby('sector').agg({
                'ticker': 'count',
                'total_return_pct': 'mean',
                'volatility_pct': 'mean',
                'sharpe_ratio': 'mean'
            }).reset_index()
            sector_summary.columns = ['Sector', 'Count', 'Avg Return (%)', 'Avg Volatility', 'Avg Sharpe']

            st.dataframe(sector_summary, use_container_width=True)

            # Pie chart
            fig = px.pie(
                sector_summary,
                values='Count',
                names='Sector',
                title='Holdings by Sector'
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # Benchmark comparison (full width)
        st.subheader("📊 Benchmark Comparison")

        # Bar chart: vs benchmark (exclude money markets)
        # Filter out money market funds - not meaningful to compare to S&P 500
        non_money_market_tickers = asset_class_df[
            asset_class_df['asset_class'] != 'Cash & Equivalents'
        ]['ticker'].tolist()

        benchmark_df = performance_df[
            performance_df['ticker'].isin(non_money_market_tickers)
        ].sort_values('vs_benchmark_pct', ascending=True)

        fig = go.Figure()

        colors = ['green' if x > 0 else 'red' for x in benchmark_df['vs_benchmark_pct']]

        fig.add_trace(go.Bar(
            x=benchmark_df['vs_benchmark_pct'],
            y=benchmark_df['ticker'],
            orientation='h',
            marker_color=colors,
            text=benchmark_df['vs_benchmark_pct'].round(1),
            textposition='auto',
        ))

        fig.update_layout(
            title='Performance vs. S&P 500 Benchmark (excl. Money Markets)',
            xaxis_title='Excess Return (%)',
            yaxis_title='Ticker',
            showlegend=False,
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Make sure you've run the data ingestion scripts and DBT models first!")
        st.code("""
# Run these commands first:
python scripts/ingest_prices.py
python scripts/ingest_benchmarks.py
cd dbt && dbt seed && dbt run
        """)

if __name__ == "__main__":
    main()
