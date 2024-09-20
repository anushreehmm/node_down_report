#!/usr/bin/env python
# coding: utf-8

# In[25]:


import pandas as pd
import dash
import os
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_table
import dash_bootstrap_components as dbc

# Data Cleaning Functions
def data1_clean(file1_path):
    df = pd.read_excel(file1_path, skiprows=5)
    df = df.rename(columns={
        'Unnamed: 0': 'Sl.no',
        'Unnamed: 1': 'IP Address',
        'Unnamed: 4': 'Event',
        'Unnamed: 6': 'Alarm Time',
        'Unnamed: 2': 'Node Alias'  # Rename Host Name to Node Alias
    })
    df = df.drop(columns=['Sl.no', 'Clear Time', 'Duration', 'Description', 'Host Name'], errors='ignore')  # Dropping unnecessary columns
    df = df.dropna(subset=['Node Alias', 'Alarm Time'])  # Dropping rows with NaN in important columns
    df['Alarm Time'] = pd.to_datetime(df['Alarm Time'], errors='coerce')
    df = df.dropna(subset=['Alarm Time'])  # Ensure Alarm Time is datetime
    return df

def data2_clean(file2_path):
    df = pd.read_excel(file2_path)
    df = df.drop([0, 1, 2, 3, 4], axis=0).reset_index(drop=True)
    df = df.drop(columns=['Unnamed: 2', 'Unnamed: 3'], errors='ignore')
    df = df.rename(columns={
        'Unnamed: 0': 'Node Alias',
        'Unnamed: 1': 'IP Address',
        'Unnamed: 4': 'Availability(%)',
        'Unnamed: 5': 'Latency(msec)',
        'Unnamed: 6': 'Packet Loss(%)'
    })
    df['Packet Loss(%)'] = pd.to_numeric(df['Packet Loss(%)'], errors='coerce')
    df['Availability(%)'] = pd.to_numeric(df['Availability(%)'], errors='coerce')
    df['Latency(msec)'] = pd.to_numeric(df['Latency(msec)'], errors='coerce')
    df = df.dropna(subset=['Packet Loss(%)', 'Availability(%)', 'Latency(msec)'])
    return df

# File Paths
file1_path = 'data.xlsx'
file2_path = 'data2.xlsx'

# Cleaned DataFrames
df1_cleaned = data1_clean(file1_path)
df2_cleaned = data2_clean(file2_path)

# Merge DataFrames on 'IP Address', adding 'Availability(%)' to df1
merged_df = pd.merge(df1_cleaned, df2_cleaned[['IP Address', 'Availability(%)']], on='IP Address', how='left')

# Initialize Dash App with Bootstrap Theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

# Determine min and max dates for DatePickerRange
min_date = merged_df['Alarm Time'].min()
max_date = merged_df['Alarm Time'].max()

# Fallback in case merged_df is empty
if pd.isnull(min_date):
    min_date = pd.to_datetime('2020-01-01')  # Example default date
if pd.isnull(max_date):
    max_date = pd.to_datetime('2020-12-31')  # Example default date

# Layout
custom_label_style = {
    "color": "#ffffff",  # Set to white for visibility
    "fontWeight": "bold",
    "marginBottom": "5px"
}

custom_dropdown_style = {
    "backgroundColor": "#212529",  # Dark background color
    "color": "#fff",  # White text color
    "border": "1px solid #444",  # Dark border
    "borderRadius": "5px",  # Rounded corners
    "padding": "5px 10px"  # Add some padding
}

app.layout = dbc.Container(
    fluid=True,
    style={
        "backgroundColor": "#f5f5f5",  # Light gray background
        "minHeight": "100vh",
        "padding": "20px"
    },
    children=[
        # Header
        dbc.Row(
            dbc.Col(
                html.H1(
                    "Node Availability Report",
                    className="text-center text-light bg-primary p-4 mb-4 rounded",
                    style={"fontSize": "36px", "font-family": "Roboto, sans-serif"}
                ),
                width=12
            )
        ),
        # Filters Section
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Select Date Range:", style=custom_label_style),
                        dcc.DatePickerRange(
                            id='date-range',
                            start_date=min_date.date(),
                            end_date=max_date.date(),
                            min_date_allowed=min_date.date(),
                            max_date_allowed=max_date.date(),
                            display_format='YYYY-MM-DD',
                            style=custom_dropdown_style
                        )
                    ],
                    width=4
                ),
                dbc.Col(
                    [
                        html.Label("Select Downtime Criteria:", style=custom_label_style),
                        dcc.Dropdown(
                            id='downtime-dropdown',
                            options=[
                                {'label': '<= 3', 'value': '<=3'},
                                {'label': '> 3', 'value': '>3'},
                                {'label': '> 5', 'value': '>5'},
                                {'label': '> 10', 'value': '>10'}
                            ],
                            value='<=3',
                            placeholder='Select downtime criteria',
                            style=custom_dropdown_style
                        )
                    ],
                    width=4
                ),
                dbc.Col(
                    [
                        html.Br(),  # For spacing
                        dbc.Button(
                            "Apply Filters",
                            id='filter-button',
                            color="success"
                        )
                    ],
                    width=4
                )
            ],
            className="mb-4"
        ),
        # Data Table Section
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Filtered Node Availability")),
                        dbc.CardBody(
                            dash_table.DataTable(
                                id='filtered-table',
                                columns=[
                                    {'name': 'Node Alias', 'id': 'Node Alias'},
                                    {'name': 'Availability (%)', 'id': 'Availability(%)'}
                                ],
                                style_table={'overflowX': 'auto'},
                                style_cell={
                                    'textAlign': 'left',
                                    'padding': '10px',
                                    'backgroundColor': '#2c2c2c',
                                    'color': 'white'
                                },
                                style_header={
                                    'backgroundColor': '#1a1a1a',
                                    'color': 'white',
                                    'fontWeight': 'bold'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {
                                            'filter_query': '{Availability(%)} > 99.5',
                                            'column_id': 'Availability(%)'
                                        },
                                        'backgroundColor': '#28a745',
                                        'color': 'white'
                                    },
                                    {
                                        'if': {
                                            'filter_query': '{Availability(%)} > 98.5 && {Availability(%)} <= 99.5',
                                            'column_id': 'Availability(%)'
                                        },
                                        'backgroundColor': '#ffc107',
                                        'color': 'black'
                                    },
                                    {
                                        'if': {
                                            'filter_query': '{Availability(%)} <= 98.5',
                                            'column_id': 'Availability(%)'
                                        },
                                        'backgroundColor': '#dc3545',
                                        'color': 'white'
                                    }
                                ],
                                page_size=20,  # Optional: limit number of rows per page
                                sort_action='native',
                                filter_action='native',
                                style_as_list_view=True
                            )
                        )
                    ],
                    className="shadow-lg"
                ),
                width=12
            )
        )
    ]
)

# Callback Function
@app.callback(
    Output('filtered-table', 'data'),
    [
        Input('filter-button', 'n_clicks')
    ],
    [
        State('date-range', 'start_date'),
        State('date-range', 'end_date'),
        State('downtime-dropdown', 'value')
    ]
)
def update_table(n_clicks, start_date, end_date, downtime_criteria):
    # Validate and parse dates
    try:
        if start_date:
            start_date = pd.to_datetime(start_date).date()
        else:
            start_date = merged_df['Alarm Time'].min().date()
        
        if end_date:
            end_date = pd.to_datetime(end_date).date()
        else:
            end_date = merged_df['Alarm Time'].max().date()
    except Exception as e:
        # If dates are invalid, return empty data
        print(f"Date parsing error: {e}")
        return []
    
    # Ensure 'Alarm Time' is datetime
    if not pd.api.types.is_datetime64_any_dtype(merged_df['Alarm Time']):
        merged_df['Alarm Time'] = pd.to_datetime(merged_df['Alarm Time'], errors='coerce')
    
    # Filter merged DataFrame based on date range
    mask = (merged_df['Alarm Time'].dt.date >= start_date) & (merged_df['Alarm Time'].dt.date <= end_date)
    filtered_df = merged_df.loc[mask]
    
    if filtered_df.empty:
        return []
    
    # Count occurrences of each Node Alias
    counts = filtered_df['Node Alias'].value_counts().reset_index()
    counts.columns = ['Node Alias', 'Count']
    
    # Merge counts with availability
    result = pd.merge(counts, df2_cleaned[['Node Alias', 'Availability(%)']], on='Node Alias', how='left')
    
    # Apply downtime criteria filter
    downtime_limit = int(downtime_criteria.split()[-1])
    if downtime_criteria.startswith('<='):
        result = result[result['Count'] <= downtime_limit]
    else:
        result = result[result['Count'] > downtime_limit]
    
    return result.to_dict('records')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))  # Get the port from the environment variable
    app.run_server(host="0.0.0.0", port=port, debug=True)


# In[ ]:




