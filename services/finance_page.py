import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go
from dash import html, dcc
from datetime import datetime, timedelta
import re

def get_month_columns(df):
    """Dynamically detect month columns and return those up to one month before current month"""
    current_date = datetime.now()
    
    # Calculate cutoff date (one month before current month)
    if current_date.month == 1:
        cutoff_year = current_date.year - 1
        cutoff_month = 12
    else:
        cutoff_year = current_date.year
        cutoff_month = current_date.month - 1
    
    # Pattern to match month columns (e.g., "OCT 24", "NOV 24", "JAN 25")
    month_pattern = r'^(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{2}$'
    
    # Month name to number mapping
    month_mapping = {
        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    }
    
    valid_columns = []
    
    for col in df.columns:
        if re.match(month_pattern, col.strip()):
            # Extract month and year from column name
            parts = col.strip().split()
            month_name = parts[0]
            year_suffix = int(parts[1])
            
            # Convert 2-digit year to 4-digit year (assuming 24 = 2024, 25 = 2025, etc.)
            if year_suffix >= 24:  # Adjust this threshold as needed
                full_year = 2000 + year_suffix
            else:
                full_year = 2000 + year_suffix
            
            month_num = month_mapping[month_name]
            
            # Check if this month is before or equal to cutoff
            if (full_year < cutoff_year) or (full_year == cutoff_year and month_num <= cutoff_month):
                valid_columns.append((col, full_year, month_num))
    
    # Sort by year and month
    valid_columns.sort(key=lambda x: (x[1], x[2]))
    
    # Return just the column names
    return [col[0] for col in valid_columns]

def get_month_display_names(columns):
    """Convert column names to display-friendly month names"""
    month_mapping = {
        'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 
        'MAY': 'May', 'JUN': 'Jun', 'JUL': 'Jul', 'AUG': 'Aug', 
        'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DEC': 'Dec'
    }
    
    display_names = []
    for col in columns:
        parts = col.strip().split()
        if len(parts) == 2:
            month_name = parts[0]
            year_suffix = parts[1]
            
            # Convert to full year
            year_num = int(year_suffix)
            if year_num >= 24:
                full_year = 2000 + year_num
            else:
                full_year = 2000 + year_num
            
            display_month = month_mapping.get(month_name, month_name)
            display_names.append(f"{display_month} {full_year}")
        else:
            display_names.append(col)
    
    return display_names

def load_finance_data(finance_xlsx_path):
    """Load and prepare finance data from the Excel file"""
    try:
        df = pd.read_excel(finance_xlsx_path)
        df.columns = df.columns.str.strip()
        
        # Get dynamic month columns
        month_columns = get_month_columns(df)
        
        if len(month_columns) == 0:
            return None, "No valid month columns found in finance file."
        
        return df, None
    except Exception as e:
        return None, f"Error loading finance file: {str(e)}"

def build_finance_page(finance_xlsx_path, colors, card_style):
    """Build the Personal Finances page layout with data automatically loaded"""
    df, error = load_finance_data(finance_xlsx_path)
    
    if error:
        return html.Div([
            html.H2("📊 Personal Finances Dashboard", 
                    style={"textAlign": "center", "color": colors["accent"], "marginBottom": "30px"}),
            html.Div([
                html.H4("Error Loading Finance Data", style={"color": colors["red"]}),
                html.P(error, style={"color": colors["text_primary"]}),
                html.P(f"Please ensure the file exists at: {finance_xlsx_path}", 
                       style={"color": colors["text_secondary"]})
            ], style=card_style)
        ])
    
    return html.Div([
        html.H2("📊 Personal Finances Dashboard", 
                style={"textAlign": "center", "color": colors["accent"], "marginBottom": "30px"}),
        
        # Finance analysis
        create_finance_analysis(df, colors, card_style)
    ])

def create_finance_analysis(df, colors, card_style):
    """Create financial analysis visualizations and metrics"""
    # Get dynamic month columns
    required_cols = get_month_columns(df)
    
    if len(required_cols) == 0:
        return html.Div([
            html.Div([
                html.H4("No Data Available", style={"color": colors["red"]}),
                html.P("No valid month columns found for the specified time period.", 
                       style={"color": colors["text_primary"]})
            ], style=card_style)
        ])
    
    # Initialize regression model
    reg = LinearRegression()
    
    def datamanip(y):
        y = y.values
        x = np.arange(len(y)).reshape(-1,1)
        return x, y

    def regression_analysis(data_x, data_y):
        reg.fit(data_x, data_y)
        a = reg.coef_[0]
        b = reg.intercept_
        x = np.linspace(0, len(required_cols)-1, 100)
        y = a * x + b
        return x, y, a, b

    # Extract data
    income_data = df.loc[1][required_cols] if len(df) > 1 else pd.Series([0] * len(required_cols))
    expenses_data = df.loc[15][required_cols] if len(df) > 15 else pd.Series([0] * len(required_cols))
    investments_data = df.loc[23][required_cols] if len(df) > 23 else pd.Series([0] * len(required_cols))
    
    # Create metrics cards
    metrics_cards = html.Div([
        html.Div([
            html.H6("Avg Monthly Income", style={"color": colors["text_secondary"], "marginBottom": "10px"}),
            html.H4(f"€{income_data.mean():,.2f}", style={"margin": "0", "color": colors["green"]})
        ], style=card_style),
        
        html.Div([
            html.H6("Avg Monthly Expenses", style={"color": colors["text_secondary"], "marginBottom": "10px"}),
            html.H4(f"€{expenses_data.mean():,.2f}", style={"margin": "0", "color": colors["red"]})
        ], style=card_style),
        
        html.Div([
            html.H6("Avg Monthly Investments", style={"color": colors["text_secondary"], "marginBottom": "10px"}),
            html.H4(f"€{investments_data.mean():,.2f}", style={"margin": "0", "color": colors["accent"]})
        ], style=card_style),
        
        html.Div([
            html.H6("Last Updated", style={"color": colors["text_secondary"], "marginBottom": "10px"}),
            html.H4(datetime.now().strftime("%d %b %Y"), 
                    style={"margin": "0", "color": colors["text_primary"]})
        ], style=card_style)
    ], style={"display": "flex", "justifyContent": "center", "flexWrap": "wrap", "marginBottom": "30px"})
    
    # Create trend analysis figures
    months = list(range(len(required_cols)))
    month_labels = [col.replace(' ', '<br>') for col in required_cols]
    month_names = get_month_display_names(required_cols)
    
    # Combined overview chart (1st) - no trend lines here
    fig_overview = go.Figure([
        go.Scatter(
            x=months, 
            y=income_data.values, 
            mode='markers+lines', 
            name='Income', 
            line=dict(color='red', width=3), 
            marker=dict(size=8),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Month: %{customdata}<br>' +
                         'Amount: €%{y:,.2f}' +
                         '<extra></extra>',
            customdata=month_names
        ),
        go.Scatter(
            x=months, 
            y=expenses_data.values, 
            mode='markers+lines', 
            name='Expenses', 
            line=dict(color='blue', width=3), 
            marker=dict(size=8),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Month: %{customdata}<br>' +
                         'Amount: €%{y:,.2f}' +
                         '<extra></extra>',
            customdata=month_names
        ),
        go.Scatter(
            x=months, 
            y=investments_data.values, 
            mode='markers+lines', 
            name='Investments', 
            line=dict(color='green', width=3), 
            marker=dict(size=8),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Month: %{customdata}<br>' +
                         'Amount: €%{y:,.2f}' +
                         '<extra></extra>',
            customdata=month_names
        )
    ])
    
    fig_overview.update_layout(
        title="Financial Overview - All Categories",
        template="plotly_dark",
        height=500,
        xaxis_title="Months",
        yaxis_title="Amount (€)",
        xaxis=dict(tickvals=months, ticktext=month_labels),
        plot_bgcolor=colors["card_bg"],
        paper_bgcolor=colors["card_bg"],
        font=dict(color=colors["text_primary"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        hovermode="x unified"
    )
    
    return html.Div([
        metrics_cards,
        
        # Overview chart
        html.Div([
            dcc.Graph(figure=fig_overview)
        ], style={**card_style, "marginBottom": "20px"}),
    ])
