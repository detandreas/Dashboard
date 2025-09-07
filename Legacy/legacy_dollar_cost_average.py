import numpy as np

def DCA(df, buy_dates, buy_prices, buy_quantities):
    """
    Υπολογίζει τη χρονοσειρά του DCA (μέσο κόστος εισόδου) σε κάθε ημερομηνία του DataFrame.
    Για κάθε ημερομηνία του df:
      - Ελέγχουμε αν πραγματοποιήθηκε αγορά (σύμφωνα με τις buy_dates).
      - Αν ναι, ενημερώνουμε το συσσωρευμένο κόστος και τις συσσωρευμένες μετοχές.
      - Στη συνέχεια, το DCA υπολογίζεται ως το συσσωρευμένο κόστος διαιρεμένο με τις συσσωρευμένες μετοχές.
    Αν δεν έχει γίνει καμία αγορά μέχρι εκείνη την ημερομηνία, το DCA ορίζεται ως 0.
    """
    dca = [] 
    cumulative_cost = 0
    cumulative_shares = 0
    buy_idx = 0
    shares_per_day = []
    value_per_day = []

    # Διατρέχουμε όλες τις ημερομηνίες του DataFrame (π.χ. από το yfinance)
    for current_date in df.index:
        # Ελέγχουμε για αγορές στην τρέχουσα ημερομηνία
        while buy_idx < len(buy_dates) and current_date.date() == buy_dates[buy_idx].date():
            cumulative_cost += buy_prices[buy_idx] * buy_quantities[buy_idx]
            cumulative_shares += buy_quantities[buy_idx]
            buy_idx += 1

        # Αν έχουν γίνει αγορές, υπολογίζουμε το DCA, αλλιώς το αφήνουμε ως 0
        if cumulative_shares > 0:
            dca.append(cumulative_cost / cumulative_shares)
        else:
            dca.append(np.nan)
            
        shares_per_day.append(cumulative_shares)
        value_per_day.append(cumulative_cost)
            
          
    return dca,shares_per_day
