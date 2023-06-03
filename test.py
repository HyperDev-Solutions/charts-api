#Importing Libraries
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import yahoo_fin.stock_info as si
from pytictoc import TicToc
import numpy as np
import matplotlib.pyplot as plt
import stumpy


#**********************
#THIS IS THE INPUT!!!!!
Analyzed_ticker = 'DUK'
#**********************

print(Analyzed_ticker)
t=TicToc()
#Defining Start and End Date
end_date = date.today().strftime('%m/%d/%Y') #'01/01/2023'
#start_date = '01/01/2010'
start_date = '01/01/1990'
#Importing Data.  La part AAPL serveix per poder mirar contra altres patterns, a part de la propia.  Caldria fer bucle i agafar les millors
accum_results = pd.DataFrame()

#today = date.today()
sel_start = (date.today() - relativedelta(months=5))
#print(sel_start)

#ticker_list = ['^STOXX50E', 'cat', 'cop', 'xom', 'v', 'jpm', 'wfc', 'lvs', 'f', 'ups', 'unp', 'ELE.MC', 'ITX.MC', 'DUK', 'o', 'LIN']
#add_list = [5, 20, 40]
add_list = [30]
ticker_list = ['^GSPC']

for ticker in ticker_list:
  for add in add_list:
    #mestre
    master_ticker = si.get_data(Analyzed_ticker, start_date = start_date , end_date = end_date)["close"].to_frame().round(1)
    master_ticker.head()
    master_ticker["1DMA"] = master_ticker["close"].rolling(1).mean().round(1)
    master_ticker["5DMA"] = master_ticker["close"].rolling(5).mean().round(1)
    master_ticker = master_ticker.dropna()

    #Comparat
    compared_ticker =si.get_data(ticker, start_date = start_date , end_date = end_date)["close"].to_frame().round(1)
    compared_ticker.head()
    compared_ticker["1DMA"] = compared_ticker["close"].rolling(1).mean().round(1)
    compared_ticker["5DMA"] = compared_ticker["close"].rolling(5).mean().round(1)
    compared_ticker = compared_ticker.dropna()

    #Partitioning the data
    #sel_start = date(2022,8,1)
    master_data = master_ticker[sel_start:end_date]
    #print(master_data.head())
    compared_data = compared_ticker[:sel_start]
    #print(compared_data.tail())
    #print(compared_data)

    #Calculating distance profile
    distance_profile = stumpy.mass(master_data["1DMA"], compared_data["1DMA"],normalize=True)
    #Getting index position with the minimum distance score
    idx = np.argmin(distance_profile)
    #print(f"The nearest pattern to {Analyzed_ticker} is the period between {str(compared_data.iloc[idx].name.strftime('%m/%d/%Y'))} and {str(compared_data.iloc[idx+len(master_data)].name.strftime('%m/%d/%Y'))} of {ticker}")

    # Since MASS computes z-normalized Euclidean distances, we should z-normalize our subsequences before plotting
    master_data_z_norm = stumpy.core.z_norm(master_data["1DMA"].values)
    mostra_i = len(master_data)
    compared_data_z_norm = stumpy.core.z_norm(compared_data["1DMA"].values[idx:idx+len(master_data)+add])


    #Top 10 matches
    matches = stumpy.match(master_data["1DMA"],compared_data["1DMA"],max_matches=10,normalize= True)
    #print(matches)
    matches_df= pd.DataFrame(matches, columns=["Score","Position"])
    a=[]
    cv_list=[]
    fc_list=[]
    returns=[]
    pos=[]
    pos = matches_df["Position"]


    #print(pos)
    for i in matches_df["Position"]:
      try:
        close_value = compared_data.iloc[i+mostra_i].loc['close']
        cv_list.append(close_value)
      except:
        cv_list.append(0)

      try:
        future_close = compared_data.iloc[i + mostra_i + add].loc['close']
        fc_list.append(future_close)
      except:
        fc_list.append(0)

      try:
        rets = (compared_data.iloc[i + mostra_i + add].loc['close'] / compared_data.iloc[i + mostra_i].loc['close']) - 1
        returns.append(rets)
      except:
        returns.append(0)
      x = compared_data.iloc[i].name.strftime('%m/%d/%Y')
      a.append(x)
    matches_df["Match_Start_Dates"]= a
    matches_df["Norm_Score"] = (matches_df["Score"]-matches_df["Score"].mean())/matches_df["Score"].std()
    matches_df["Ini_CValue"] = cv_list
    matches_df["Fin_CValue"] = fc_list
    matches_df["Returns"] = returns
    matches_df["tck"] = ticker
    matches_df["add"] = add
    #print(matches_df)
    print("matches_df",matches_df,"master_data_z_norm",master_data_z_norm,"compared_data_z_norm",compared_data_z_norm)

    first_returns ="{:.2%}".format(returns[0])
    plt.figure(figsize=(15,5))
    plt.suptitle(f"The most similar pattern in the last 50 years of data happened in "+str(compared_data.iloc[idx].name.strftime('%m/%d/%Y'))+" and after "+str(add)+" days yielded "+first_returns, fontsize='15')
    plt.xlabel('Time', fontsize ='20')
    plt.ylabel('Price', fontsize='20')
    plt.plot(master_data_z_norm, lw=3, color="red", label=(Analyzed_ticker)+":  "+sel_start.strftime("%Y-%m-%d")+" - Today")
    plt.plot(compared_data_z_norm, lw=2, label=(ticker)+":  "+str(compared_data.iloc[idx].name.strftime('%m/%d/%Y'))+"-" +str(compared_data.iloc[idx+len(master_data)+add].name.strftime('%m/%d/%Y')))
    plt.legend()
    plt.show()