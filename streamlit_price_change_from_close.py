import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import base64

def calculate_stock_returns(stock_list, comparison_date=None, comparison_time=None):
    """
    Calculate returns for a list of stocks compared to previous day's close
    
    Parameters
    ----------
        comparison_time: str, optional
            Time to capture price with which to compare with the previous day's close. Format is "HH:mm" (only 30 minute mark each hour is allowed, as this corresponds to yfinance).
        comparison_date: str, optional
            Date to compare with the previous day's close. Format is MM-DD-YYYY.
    """
    print(f"Stock List: {stock_list}")
    print(f"Comparison Date: {comparison_date}")
    print(f"Comparison Time: {comparison_time}")
    if comparison_date is None:
        comparison_date = datetime.now(pytz.timezone('America/New_York')).strftime('%m-%d-%Y')
        
    if comparison_time is None:
        comparison_time = datetime.now(pytz.timezone('America/New_York')).strftime('%H:30')
    
    target_date = datetime.strptime(comparison_date, '%m-%d-%Y')
    
    if target_date.weekday() >= 5:
        st.warning("Selected date is a weekend. Please select a weekday.")
        return pd.DataFrame()
    
    if target_date.weekday() == 0:
        prev_day = target_date - timedelta(days=3)
    else:
        prev_day = target_date - timedelta(days=1)
    
    results = {
        'Symbol': [],
        'Previous Close': [],
        'Target Price': [],
        'Return (%)': []
    }
    
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, symbol in enumerate(stock_list):
        try:
            # Update progress bar and status
            progress = (idx + 1) / len(stock_list)
            progress_bar.progress(progress)
            status_text.text(f"Processing {symbol}... ({idx + 1}/{len(stock_list)})")
            
            
            # ticker = obb.equity.price.historical(symbol=symbol, start_date=prev_day.strftime('%Y-%m-%d'), end_date=(target_date + timedelta(days=1)).strftime('%Y-%m-%d'), interval='1h').to_df()
            ticker = yf.Ticker(symbol).history(start=prev_day, end=target_date + timedelta(days=1), interval='1h')
            
            
            # Get target date data
            target_date_data = ticker[ticker.index.strftime('%Y-%m-%d') == target_date.strftime('%Y-%m-%d')]
            target_date_data.index = target_date_data.index.tz_convert('America/New_York')
            target_time_price = target_date_data[target_date_data.index.strftime('%H:%M') == comparison_time]['Close'].values[0]
            
            # Get previous day data
            prev_day_data = ticker[ticker.index.strftime('%Y-%m-%d') == prev_day.strftime('%Y-%m-%d')]
            prev_day_close = prev_day_data.iloc[-1]['Close']
            
            returns_pct = ((target_time_price - prev_day_close) / prev_day_close) * 100
            
            results['Symbol'].append(symbol)
            results['Previous Close'].append(round(prev_day_close, 2))
            results['Target Price'].append(round(target_time_price, 2))
            results['Return (%)'].append(round(returns_pct, 2))
            
        except Exception as e:
            # st.warning(f"Error processing {symbol}: {str(e)}")
            continue
    
    # Clear progress bar and status text
    progress_bar.empty()
    status_text.empty()
    
    # check if no results were returned
    if not results['Symbol']:
        st.warning("No results retuned. This could be due to the date selected or the previous day being a holiday. Please try a different date.")
        return pd.DataFrame()
    
    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values('Return (%)', ascending=False)
    df_results.reset_index(drop=True, inplace=True)
    
    return df_results

def get_table_download_link(df):
    """Generates a link to download the DataFrame as CSV"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="stock_returns.csv">Download CSV file</a>'
    return href

def main():
    st.set_page_config(page_title="Stock Returns Calculator", layout="centered")
    
    # Custom CSS
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stButton>button {
            width: 100%;
        }
        .reportview-container .main .block-container {
            padding-top: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("📈 Stock Returns Calculator")
    
    # Sidebar
    st.sidebar.header("Settings")
    
    stocks_list = []
    stock_input = st.sidebar.text_area(
        "Enter stock symbols (one per line):",
        height=200,
        help="Enter stock symbols separated by newlines (e.g., AAPL\nMSFT\nGOOGL)"
    )
    if stock_input:
        stocks_list = [s.strip().upper() for s in stock_input.split('\n') if s.strip()]
    
    
    # Date Input
    comparison_date = None
    max_days_back = 730
    min_date = datetime.now() - timedelta(days=max_days_back)
    max_date = datetime.now()
    comparison_date = st.sidebar.date_input(
        "Select target date",
        max_date,
        min_value=min_date,
        max_value=max_date
    ).strftime('%m-%d-%Y')
    
    # Time input
    comparison_time = None
    comparison_time = st.sidebar.slider(
        "Select target hour",
        min_value=datetime(2023, 1, 1, 9, 30),
        max_value=datetime(2023, 1, 1, 15, 30),
        value=datetime(2023, 1, 1, 9, 30),
        step=timedelta(minutes=60),
        format="HH:mm"
    ).strftime('%H:%M')
    
    # Main content

    st.sidebar.write(f"Number of stocks loaded: {len(stocks_list)}")
    
    if st.sidebar.button("Calculate Returns"):
        if not stocks_list:
            st.warning("Please enter stock symbols to begin.")
            return
        with st.spinner('Calculating returns...'):
            df = calculate_stock_returns(stocks_list, comparison_date, comparison_time)
            
            # Display results in tabs
            tab1, tab2, tab3 = st.tabs(["📊 Table View", "📈 Top Performers", "📉 Bottom Performers"])
            
            with tab1:
                st.dataframe(df, use_container_width=True)
                st.markdown(get_table_download_link(df), unsafe_allow_html=True)
            
            with tab2:
                st.subheader("Top 10 Performers")
                top_10 = df.head(10)
                st.dataframe(top_10, use_container_width=True)
                
            
            with tab3:
                st.subheader("Bottom 10 Performers")
                bottom_10 = df.tail(10).iloc[::-1]
                st.dataframe(bottom_10, use_container_width=True)

            
            # Summary statistics
            st.subheader("Summary Statistics")
            col1, col2, col3, col4 = st.columns(4)
            try: 
                with col1:
                    st.metric("Average Return", f"{df['Return (%)'].mean():.2f}%")
                with col2:
                    st.metric("Median Return", f"{df['Return (%)'].median():.2f}%")
                with col3:
                    st.metric("Best Return", f"{df['Return (%)'].max():.2f}%")
                with col4:
                    st.metric("Worst Return", f"{df['Return (%)'].min():.2f}%")
            except:
                pass
    
    else:
        st.info("Please enter stock symbols to begin.")
        
    # Footer
    st.markdown("---")

if __name__ == "__main__":
    main()
    # results = calculate_stock_returns(['mstr'], "12-18-2024", '10:30') #12-30-2024
    # print(results)
    
# streamlit run app.py