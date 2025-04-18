def buys(df, ticker):
    buy_signals = []
    buy_dates = []
    buy_price = []
    buy_quantity = []  # νέα λίστα για τις ποσότητες
    number_of_buys = 0
    shares = 0
    bought_amount = 0

    for i in range(len(df)):
        date = df.index[i]
        Quantity = df[('Quantity', ticker)].iloc[i].item()
        Direction = df[[('Direction', ticker)]].iloc[i].item()
        Price = df[[('Price', ticker)]].iloc[i].item()

        if Direction == ' Buy ':
            buy_price.append(Price)
            buy_signals.append(Price)
            buy_dates.append(date)
            buy_quantity.append(Quantity)  # καταγράφουμε και την ποσότητα
            number_of_buys += 1
            shares += Quantity
            bought_amount += Price * Quantity
            if ticker!='USD/EUR':
                print(f"Αγορά: {ticker} | {date.strftime('%Y-%m-%d')} | Τιμή: ${Price:.2f} | Μετοχές: {Quantity}")
            else:
                print(f"Αγορά: {ticker} | {date.strftime('%Y-%m-%d')} | Τιμή: ${Price:.2f} | Δολάρια: {Quantity}")
        else:
            buy_signals.append(0)
            
    avg_buy = bought_amount / shares if shares > 0 else 0
    print(f'Τιμή Εισόδου {ticker} : {avg_buy:.2f}')
    return buy_signals, buy_dates, buy_price, buy_quantity, shares, avg_buy
