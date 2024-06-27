import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_datareader.data as web
import datetime
import func

st.set_page_config(page_title="CAPM Analysis", 
                   page_icon="chart_with_upwards_trend",
                   layout="wide")

st.title("Capital Asset Pricing Model")

with st.expander("What is CAPM?"):
    st.image("CAPMEq.png", use_column_width=True)
    st.write("""
    The Capital Asset Pricing Model (CAPM) is used to calculate the expected return of an asset based on its risk relative to the market.
    It helps investors assess the relationship between risk and potential return for stocks.
    
    - **ri** = expected return on a stock (%)
    - **rf** = risk free return rate (%)
    - **Bi** = Beta between the stock and the market
    - **rm** = expected return of the market (%) (e.g., SP500)
    """)

# Initialize session state for stocks list if it doesn't exist
if 'stocks_list' not in st.session_state:
    st.session_state.stocks_list = ['NVDA', 'MSFT', 'GOOGL', 'AAPL']

col1, col2 = st.columns([1,1])

with col1:
    new_stock = st.text_input("Enter a stock ticker symbol (e.g., TSLA, AMZN)")
    if st.button("Add Stock"):
        if new_stock and new_stock not in st.session_state.stocks_list:
            st.session_state.stocks_list.append(new_stock)
            st.success(f"Added {new_stock} to the list.")
        elif new_stock in st.session_state.stocks_list:
            st.warning(f"{new_stock} is already in the list.")
        else:
            st.warning("Please enter a valid stock ticker.")
    st.write("Current list of stocks:", ", ".join(st.session_state.stocks_list))
    stocks_to_remove = st.multiselect("Select stocks to remove", st.session_state.stocks_list)
    if st.button("Remove Selected Stocks"):
        for stock in stocks_to_remove:
            st.session_state.stocks_list.remove(stock)
        st.success("Selected stocks removed.")

with col2:
    year = st.number_input("Number of years", 1, 10, value=5)
    with st.expander("Why does the Time Period matter?"):
        st.write("""
        The number of years determines the historical data range for the analysis. 
        A longer period provides more data but may include outdated market conditions.
        """)

# Proceed with the analysis
try:
    end = datetime.date.today()
    start = end - datetime.timedelta(days=365*year)

    SP500 = web.DataReader(['sp500'], 'fred', start, end)

    stocks_df = pd.DataFrame()
    for stock in st.session_state.stocks_list:
        data = yf.download(stock, start=start, end=end)
        stocks_df[f'{stock}'] = data['Close']
    stocks_df.reset_index(inplace=True)
    stocks_df.rename(columns={'index': 'Date'}, inplace=True)

    SP500.reset_index(inplace=True)
    SP500.columns = ['Date','sp500']

    stocks_df = pd.merge(stocks_df, SP500, on='Date', how='inner')

    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown("### Start of the Period")
        st.dataframe(stocks_df.head(), use_container_width=True)
    with col2:
        st.markdown("### End of the Period (Most Recent)")
        st.dataframe(stocks_df.tail(), use_container_width=True)

    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown("### Price of all the Stocks")
        st.plotly_chart(func.interactive_plot(stocks_df))
    with col2:
        st.markdown("### Price of all the Stocks (After Normalizing)")
        st.plotly_chart(func.interactive_plot(func.normalize(stocks_df)))

    with st.expander("About The Charts"):
        st.write("""
        The first chart shows the actual price movements of the stocks over time. 
        The second chart normalizes these prices, setting their initial value to 1 at the start of the period. 
        This normalization process helps in comparing performance by eliminating the effect of different price scales, making it easier to see relative growth or decline.
        """)

    stocks_daily_return = func.daily_return(stocks_df)

    beta = {}
    alpha = {}
    for i in stocks_daily_return.columns:
        if i != 'Date' and i != 'sp500':
            b, a = func.calculate_beta(stocks_daily_return, i)
            beta[i] = b
            alpha[i] = a

    beta_df = pd.DataFrame(columns=['Stock', 'Beta Value'])
    beta_df['Stock'] = beta.keys()
    beta_df['Beta Value'] = [str(round(i, 2)) for i in beta.values()]

    rf = 0
    rm = stocks_daily_return['sp500'].mean() * 252

    return_df = pd.DataFrame()
    return_value = []
    for stock, value in beta.items():
        return_value.append(str(round(rf + (value * (rm - rf)), 2)))
    return_df['Stock'] = st.session_state.stocks_list
    return_df['Return Value'] = return_value

    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown('### Calculated Beta Value')
        st.dataframe(beta_df, use_container_width=True)
        with st.expander("What is Beta?"):
            st.write("""
            Beta measures a stock's volatility relative to the market (S&P 500). 
            A beta > 1 indicates higher volatility than the market, while < 1 indicates lower volatility. 
            This helps in assessing the stock's risk and potential returns.
            """)

    with col2:
        st.markdown('### Calculated Return Using CAPM')
        st.dataframe(return_df, use_container_width=True)
        with st.expander("Understanding CAPM Returns"):
            st.write("""
            This table shows the expected return for each stock according to CAPM. 
            It considers the risk-free rate, the stock's beta, and the market return. 
            Higher expected returns often come with higher risk.
            """)

    col1, col2 = st.columns(2)
    with col1:
        st.write("Daily Returns (Start of Period):")
        st.dataframe(stocks_daily_return.head(), use_container_width=True)
    with col2:
        st.write("Daily Returns (End of Period):")
        st.dataframe(stocks_daily_return.tail(), use_container_width=True)

    with st.expander("About Daily Returns"):
        st.write("""
        These tables show the daily percentage changes in stock prices at the beginning and end of the period. 
        Daily returns are crucial for understanding short-term volatility and can be used to calculate various risk metrics.
        """)

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.write("Please ensure all inputs are valid and try again.")
