import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import logging
from typing import List, Tuple
import re
from datetime import datetime
import plotly.graph_objects as go

from config.settings import Config

logger = logging.getLogger(__name__)

class FinanceAnalysisService:
    """Service for financial analysis and calculations."""
    
    def __init__(self, config: Config):
        self.config = config
        self.regression_model = LinearRegression()
    
    def load_finance_data(self) -> Tuple[pd.DataFrame, List[str]]:
        """Load finance data and extract valid month columns."""
        try:
            df = pd.read_excel(self.config.database.finance_xlsx_path)
            df.columns = df.columns.str.strip()
            
            month_columns = self._get_month_columns(df)
            
            if len(month_columns) == 0:
                raise ValueError("No valid month columns found in finance file")
            
            logger.info(f"Loaded finance data with {len(month_columns)} month columns")
            return df, month_columns
            
        except Exception as e:
            logger.error(f"Error loading finance data: {e}")
            raise
    
    def _get_month_columns(self, df: pd.DataFrame) -> List[str]:
        """Extract valid month columns from dataframe."""
        current_date = datetime.now()
        
        # Calculate cutoff date (one month before current month)
        if current_date.month == 1:
            cutoff_year = current_date.year - 1
            cutoff_month = 12
        else:
            cutoff_year = current_date.year
            cutoff_month = current_date.month - 1
        
        # Pattern to match month columns
        month_pattern = r'^(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{2}$'
        
        # Month mapping
        month_mapping = {
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }
        
        valid_columns = []
        
        for col in df.columns:
            if re.match(month_pattern, col.strip()):
                parts = col.strip().split()
                month_name = parts[0]
                year_suffix = int(parts[1])
                
                # Convert 2-digit year to 4-digit year
                full_year = 2000 + year_suffix if year_suffix >= 24 else 2000 + year_suffix
                month_num = month_mapping[month_name]
                
                # Check if this month is before or equal to cutoff
                if (full_year < cutoff_year) or (full_year == cutoff_year and month_num <= cutoff_month):
                    valid_columns.append((col, full_year, month_num))
        
        # Sort by year and month
        valid_columns.sort(key=lambda x: (x[1], x[2]))
        return [col[0] for col in valid_columns]
    
    def extract_financial_data(self, df: pd.DataFrame, month_columns: List[str]) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Extract income, expenses, and investments data from specific rows."""
        income_data = df.loc[1][month_columns] if len(df) > 1 else pd.Series([0] * len(month_columns))
        expenses_data = df.loc[15][month_columns] if len(df) > 15 else pd.Series([0] * len(month_columns))
        investments_data = df.loc[23][month_columns] if len(df) > 23 else pd.Series([0] * len(month_columns))
        
        return income_data, expenses_data, investments_data
    
    def calculate_regression_analysis(self, data: pd.Series, months: List[int]) -> Tuple[np.ndarray, np.ndarray, float, float]:
        """Calculate regression analysis for financial data."""
        try:
            # Prepare data for regression
            X = np.array(months).reshape(-1, 1)
            y = data.values
            
            # Fit regression model
            self.regression_model.fit(X, y)
            slope = self.regression_model.coef_[0]
            intercept = self.regression_model.intercept_
            
            # Generate trend line
            x_trend = np.linspace(0, len(months)-1, 100)
            y_trend = self.regression_model.predict(x_trend.reshape(-1, 1))
            
            logger.debug(f"Regression analysis: slope={slope:.2f}, intercept={intercept:.2f}")
            return x_trend, y_trend, slope, intercept
            
        except Exception as e:
            logger.error(f"Error in regression analysis: {e}")
            raise
    
    def calculate_financial_metrics(self, income_data: pd.Series, expenses_data: pd.Series, 
                                  investments_data: pd.Series) -> dict:
        """Calculate key financial metrics."""
        try:
            avg_income = income_data.mean()
            avg_expenses = expenses_data.mean()
            avg_investments = investments_data.mean()
            
            # Calculate savings rate
            net_savings = avg_income - avg_expenses
            savings_rate = (net_savings / avg_income * 100) if avg_income > 0 else 0
            
            # Calculate investment rate
            investment_rate = (avg_investments / avg_income * 100) if avg_income > 0 else 0
            
            # Calculate expense ratio
            expense_ratio = (avg_expenses / avg_income * 100) if avg_income > 0 else 0
            
            metrics = {
                'avg_income': avg_income,
                'avg_expenses': avg_expenses,
                'avg_investments': avg_investments,
                'savings_rate': savings_rate,
                'investment_rate': investment_rate,
                'expense_ratio': expense_ratio,
                'net_savings': net_savings
            }
            
            logger.info(f"Financial metrics calculated: savings_rate={savings_rate:.1f}%")
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating financial metrics: {e}")
            raise
    
    def get_month_display_names(self, month_columns: List[str]) -> List[str]:
        """Convert month column names to display-friendly format."""
        month_mapping = {
            'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 
            'MAY': 'May', 'JUN': 'Jun', 'JUL': 'Jul', 'AUG': 'Aug', 
            'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DEC': 'Dec'
        }
        
        display_names = []
        for col in month_columns:
            parts = col.strip().split()
            if len(parts) == 2:
                month_name = parts[0]
                year_suffix = parts[1]
                
                # Convert to full year
                year_num = int(year_suffix)
                full_year = 2000 + year_num if year_num >= 24 else 2000 + year_num
                
                display_month = month_mapping.get(month_name, month_name)
                display_names.append(f"{display_month} {full_year}")
            else:
                display_names.append(col)
        
        return display_names
    
    def analyze_trends(self, income_data: pd.Series, expenses_data: pd.Series, 
                      investments_data: pd.Series, months: List[int]) -> dict:
        """Analyze trends for all financial categories."""
        try:
            trends = {}
            
            # Analyze income trend
            _, _, income_slope, _ = self.calculate_regression_analysis(income_data, months)
            trends['income'] = {
                'slope': income_slope,
                'direction': '↗' if income_slope > 0 else '↘',
                'trend_text': f"€{income_slope:.2f}/month"
            }
            
            # Analyze expenses trend
            _, _, expenses_slope, _ = self.calculate_regression_analysis(expenses_data, months)
            trends['expenses'] = {
                'slope': expenses_slope,
                'direction': '↗' if expenses_slope > 0 else '↘',
                'trend_text': f"€{expenses_slope:.2f}/month"
            }
            
            # Analyze investments trend
            _, _, investments_slope, _ = self.calculate_regression_analysis(investments_data, months)
            trends['investments'] = {
                'slope': investments_slope,
                'direction': '↗' if investments_slope > 0 else '↘',
                'trend_text': f"€{investments_slope:.2f}/month"
            }
            
            logger.info("Trend analysis completed for all categories")
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            raise

    def create_income_chart(self, income_data: pd.Series, month_columns: List[str], colors: dict) -> go.Figure:
        """Create income chart with regression line."""
        display_names = self.get_month_display_names(month_columns)
        months = list(range(len(month_columns)))
        
        # Calculate regression
        x_trend, y_trend, slope, intercept = self.calculate_regression_analysis(income_data, months)
        
        fig = go.Figure()
        
        # Add income line
        fig.add_trace(go.Scatter(
            x=display_names,
            y=income_data.values,
            mode='lines+markers',
            name='Income',
            line=dict(color=colors["green"], width=3),
            marker=dict(size=8)
        ))
        
        # Add regression line
        fig.add_trace(go.Scatter(
            x=[display_names[0], display_names[-1]],
            y=[intercept, intercept + slope * (len(months) - 1)],
            mode='lines',
            name=f'Trend (€{slope:.2f}/month)',
            line=dict(color=colors["accent"], width=2, dash='dash')
        ))
        
        fig.update_layout(
            title="Monthly Income",
            xaxis_title="Month",
            yaxis_title="Income (€)",
            template="plotly_dark",
            height=400,
            plot_bgcolor=colors["card_bg"],
            paper_bgcolor=colors["card_bg"]
        )
        
        return fig
    
    def create_expenses_chart(self, expenses_data: pd.Series, month_columns: List[str], colors: dict) -> go.Figure:
        """Create expenses chart with regression line."""
        display_names = self.get_month_display_names(month_columns)
        months = list(range(len(month_columns)))
        
        # Calculate regression
        x_trend, y_trend, slope, intercept = self.calculate_regression_analysis(expenses_data, months)
        
        fig = go.Figure()
        
        # Add expenses line
        fig.add_trace(go.Scatter(
            x=display_names,
            y=expenses_data.values,
            mode='lines+markers',
            name='Expenses',
            line=dict(color=colors["red"], width=3),
            marker=dict(size=8)
        ))
        
        # Add regression line
        fig.add_trace(go.Scatter(
            x=[display_names[0], display_names[-1]],
            y=[intercept, intercept + slope * (len(months) - 1)],
            mode='lines',
            name=f'Trend (€{slope:.2f}/month)',
            line=dict(color=colors["accent"], width=2, dash='dash')
        ))
        
        fig.update_layout(
            title="Monthly Expenses",
            xaxis_title="Month",
            yaxis_title="Expenses (€)",
            template="plotly_dark",
            height=400,
            plot_bgcolor=colors["card_bg"],
            paper_bgcolor=colors["card_bg"]
        )
        
        return fig
    
    def create_investments_chart(self, investments_data: pd.Series, month_columns: List[str], colors: dict) -> go.Figure:
        """Create investments chart with regression line."""
        display_names = self.get_month_display_names(month_columns)
        months = list(range(len(month_columns)))
        
        # Calculate regression
        x_trend, y_trend, slope, intercept = self.calculate_regression_analysis(investments_data, months)
        
        fig = go.Figure()
        
        # Add investments line
        fig.add_trace(go.Scatter(
            x=display_names,
            y=investments_data.values,
            mode='lines+markers',
            name='Investments',
            line=dict(color=colors["accent"], width=3),
            marker=dict(size=8)
        ))
        
        # Add regression line
        fig.add_trace(go.Scatter(
            x=[display_names[0], display_names[-1]],
            y=[intercept, intercept + slope * (len(months) - 1)],
            mode='lines',
            name=f'Trend (€{slope:.2f}/month)',
            line=dict(color=colors["green"], width=2, dash='dash')
        ))
        
        fig.update_layout(
            title="Monthly Investments",
            xaxis_title="Month",
            yaxis_title="Investments (€)",
            template="plotly_dark",
            height=400,
            plot_bgcolor=colors["card_bg"],
            paper_bgcolor=colors["card_bg"]
        )
        
        return fig
