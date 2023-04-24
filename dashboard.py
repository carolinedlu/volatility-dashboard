import streamlit as st
import pandas_ta as ta
import pandas as pd
import yfinance as yf
import pandas as pd; import numpy as np

st.title("Volatility Dashboard")
st.sidebar.title("selection")
option = st.sidebar.selectbox("options",('long signal', 'short signal', 'data frame', 'Important dates', 'implinks'))
st.subheader(option)

df = yf.download('BTC-USD', period='6mo', interval='1h')
df = df.reset_index()
# Step: Change data type of Date to Datetime
df = df.rename(columns={'index': 'Date'})
df['Volatility Open'] = df['Open'].rolling(window=10).std()
df['Volatility High'] = df['High'].rolling(window=10).std()
df['Volatility Low'] = df['Low'].rolling(window=10).std()
df['Volatility Close'] = df['Close'].rolling(window=10).std()

newdf=df[['Datetime','Volatility Open','Volatility High','Volatility Low','Volatility Close']]
newdf=newdf.set_index('Datetime')
newdf=newdf.dropna()


newdf = newdf.rename_axis('Date')
newdf.index = pd.to_datetime(newdf.index)
newdf.index = newdf.index.tz_localize(None)
newdf.tail()
f = pd.read_csv('https://raw.githubusercontent.com/suparn2304/volatility-dashboard/main/vol1%20harmonic.csv', index_col=0)
f = f.rename_axis('Date')
f.index = pd.to_datetime(f.index)
f = f.rename(columns={'0.0000000': 'forier'})

new_dates = pd.date_range(start=newdf.index.min(), end='2023-05-23 10:00:00', freq='1h')
updated_index = newdf.index.append(new_dates)
newdf = newdf[~newdf.index.duplicated(keep='first')]
newdf = newdf.reindex(updated_index)
newdf.index = pd.to_datetime(newdf.index)

merged_df = pd.merge(newdf, f, how='left', left_index=True, right_index=True)
merged_df.tail()
merged_df.index = pd.to_datetime(merged_df.index, infer_datetime_format=True)
merged_df = merged_df.rename(columns={'Volatility Open': 'Open', 'Volatility Close': 'Close', 'Volatility High': 'High', 'Volatility Low': 'Low'})
merged_df = merged_df.fillna(method='ffill')
merged_df = merged_df[~merged_df.index.duplicated(keep='first')]
merged_df['fut1'] = merged_df['forier'].shift(-1)
merged_df['fut2'] = merged_df['forier'].shift(-2)
merged_df['fut3'] = merged_df['forier'].shift(-3)
merged_df['fut4'] = merged_df['forier'].shift(-4)
merged_df['fut5'] = merged_df['forier'].shift(-5)
merged_df['zscore'] = ta.zscore(merged_df['Close'], length=20, std=1)
merged_df = merged_df.rename_axis('Date')
merged_df['forier_plot'] = merged_df['forier']*100
merged_df['fut1'] = merged_df['forier'].shift(-1)
merged_df['fut2'] = merged_df['forier'].shift(-2)
merged_df['fut3'] = merged_df['forier'].shift(-3)
merged_df['fut4'] = merged_df['forier'].shift(-4)
merged_df['fut5'] = merged_df['forier'].shift(-5)


entry_points = pd.DataFrame(columns=['Date', 'Entry_Price'])

# Set the threshold for the z-score
zscore_threshold = -0.7999

# Loop through the rows in the DataFrame
for i in range(len(merged_df)):
    # Check if the conditions are met for entering a trade
    if (merged_df.iloc[i].fut3 > merged_df.iloc[i].fut2 > merged_df.iloc[i].fut1) and \
            (merged_df.iloc[i].zscore > zscore_threshold) and \
            (merged_df.iloc[i-1].zscore < zscore_threshold):
        # Record the entry point
        entry_points = entry_points.append({'Date': merged_df.iloc[i].name, 
                                             'Entry_Price': merged_df.iloc[i].Close}, 
                                             ignore_index=True)
        


ohlc_df = pd.DataFrame()
ohlc_df.index = merged_df.index
ohlc_df['Open'] = merged_df['Open']
ohlc_df['High'] = merged_df['High']
ohlc_df['Low'] = merged_df['Low']
ohlc_df['Close'] = merged_df['Close']


if option == 'data frame':
    st.dataframe(ohlc_df)


df_callendar = pd.read_csv('https://raw.githubusercontent.com/suparn2304/volatility-dashboard/main/calendar-event-list.csv', index_col=0)
df_callendar.index = pd.to_datetime(df_callendar.index)
calllendar_df = pd.merge(ohlc_df, df_callendar, how='left', left_index=True, right_index=True)
calllendar_df = calllendar_df.dropna()

if option == 'Important dates':
    st.dataframe(df_callendar)


import plotly.graph_objects as go
fig =  go.Figure(data= [go. Candlestick (
                 x = ohlc_df.index,
                 open = ohlc_df.Open,
                 high = ohlc_df.High,
                 low = ohlc_df.Low,
                 close = ohlc_df.Close
)]) 

fig.add_trace(go.Scatter(
                x=entry_points.Date,
                y=entry_points.Entry_Price,
                mode= "markers",
                marker_symbol="diamond-dot",
                marker_size = 13,
                marker_line_width = 2,
                marker_line_color= "rgba(0, 0, 0, 0.7)",
                marker_color="rgba(0,255,0,0.7)", 
))

fig.add_trace(go.Scatter(
                x=calllendar_df.index,
                y=calllendar_df.Close,
                mode= "markers",
                marker_symbol="x",
                marker_size = 10,
                marker_line_width = 2,
                marker_line_color= "rgba(0, 0, 0, 0.7)",
                marker_color="rgba(205, 13, 0, 1)", 
))


fig.update_layout (xaxis_rangeslider_visible=False)

if option == 'long signal':
    st.plotly_chart(fig)
    st.dataframe(entry_points)

entry_points_short = pd.DataFrame(columns=['Date', 'Entry_Price'])

# Set the threshold for the z-score
zscore_threshold = 0.7999

# Loop through the rows in the DataFrame
for i in range(len(merged_df)):
    # Check if the conditions are met for entering a trade
    if (merged_df.iloc[i].fut3 < merged_df.iloc[i].fut2 < merged_df.iloc[i].fut1) and \
            (merged_df.iloc[i].zscore < zscore_threshold) and \
            (merged_df.iloc[i-1].zscore > zscore_threshold):
        # Record the entry point
        entry_points_short = entry_points_short.append({'Date': merged_df.iloc[i].name, 
                                             'Entry_Price': merged_df.iloc[i].Close}, 
                                             ignore_index=True)
        



import plotly.graph_objects as go
fig =  go.Figure(data= [go. Candlestick (
                 x = ohlc_df.index,
                 open = ohlc_df.Open,
                 high = ohlc_df.High,
                 low = ohlc_df.Low,
                 close = ohlc_df.Close
)]) 

fig.add_trace(go.Scatter(
                x=entry_points_short.Date,
                y=entry_points_short.Entry_Price,
                mode= "markers",
                marker_symbol="diamond-dot",
                marker_size = 10,
                marker_line_width = 2,
                marker_line_color= "rgba(0, 0, 0, 0.7)",
                marker_color="rgba(205, 13, 0, 1)", 
))

fig.add_trace(go.Scatter(
                x=calllendar_df.index,
                y=calllendar_df.Close,
                mode= "markers",
                marker_symbol="x",
                marker_size = 10,
                marker_line_width = 2,
                marker_line_color= "rgba(0, 0, 0, 0.7)",
                marker_color="rgba(205, 13, 0, 1)", 
))



fig.update_layout (xaxis_rangeslider_visible=False)
if option == 'short signal':
    st.plotly_chart(fig)
    st.dataframe(entry_points_short)

if option == 'implinks':
    st.write("gmx top trader account [link](https://www.gmx.house/arbitrum/account/0x48202a51c0d5d81b3ebed55016408a0e0a0afaae)")
    st.write("gmx top trader account 2 [link](https://www.gmx.house/arbitrum/account/0xe8c19db00287e3536075114b2576c70773e039bd)")
    st.write("bookmap [link](https://web.bookmap.com/?duration=10m)")
    st.write("tradinglite [link](https://www.tradinglite.com/)")
