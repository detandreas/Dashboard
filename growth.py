import pandas as pd
import numpy as np

def growth(last_close_price,avg_buy,buy_price,buy_quantity):
    Growth = (last_close_price - avg_buy)/avg_buy
    Invested = 0
    for i in range(len(buy_price)):
        
        Invested += buy_price[i]*buy_quantity[i]
    
    Value = Invested*(1+Growth)
    Profit = Value - Invested 
    print(f'Επένδυση: ${Invested:.2f} | Απόδοση: { 100*Growth:.2f}% | Αγοραία Αξία: ${Value:.2f} | Κέρδος: ${Profit:.2f}')
    
    return Growth
    

def portfolio_growth(df,dca,shares_per_day):
    Profit = []
    
    for i in range(len(df)):
        close_price = df.loc[df.index[i],'Close'].item()
        if dca[i] == 0:
            Profit.append(0)
        else:
            Profit.append((close_price - dca[i])*shares_per_day[i])
            
        
    return np.array(Profit)
        
        
def Portfolio_Yield(dca_EQAC,shares_EQAC,dca_VUAA,shares_VUAA,profit):
    invested_per_day = []
    Yield_per_day = []
    
    for i in range(len(profit)):
        invested = dca_EQAC[i]*shares_EQAC[i] + dca_VUAA[i]*shares_VUAA[i]
        if invested != 0:
            Yield = profit[i]/invested
            Yield_per_day.append(Yield)
        else:
            Yield_per_day.append(0)
        
   
    Yield_per_day = np.array(Yield_per_day)
    return 100*Yield_per_day
        
        
        
        
        
    
    
    