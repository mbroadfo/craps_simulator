# File: dashboard.py

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import time
from main import main  # Import the main function
from config import ACTIVE_PLAYERS, SESSION_MODE, HOUSE_RULES  # Import config values

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Craps Simulator Dashboard"

# Layout of the dashboard
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Craps Simulator Dashboard"), width=12, className="text-center my-4")
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Button("Run Simulation", id="run-button", color="primary", className="mb-3"),
            html.Div(id="play-by-play", style={"height": "300px", "overflowY": "scroll", "border": "1px solid #ddd", "padding": "10px"})
        ], width=3),
        dbc.Col([
            html.Img(src="/assets/craps_table_layout.png", style={"width": "100%", "height": "auto"}),  # Craps layout image
        ], width=5),
        dbc.Col([
            dcc.Graph(id="bankroll-graph"),
            html.Div(id="stats-display", style={"marginTop": "20px"})
        ], width=4)
    ])
])

# Callback to run the simulation
@app.callback(
    [Output("play-by-play", "children"),
     Output("bankroll-graph", "figure"),
     Output("stats-display", "children")],
    [Input("run-button", "n_clicks")],
    [State("play-by-play", "children")]
)
def run_simulation(n_clicks, existing_logs):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate

    # Initialize logs and stats
    logs = existing_logs or []
    bankroll_data = []
    stats = {"total_rolls": 0, "player_bankroll": 1000}

    # Run the simulation using the main function
    logs.append(html.P("Starting simulation..."))
    main()  # Call the main function from main.py
    logs.append(html.P("Simulation completed."))

    # Placeholder for bankroll data (replace with actual data from the simulation)
    for roll in range(1, 11):
        bankroll_data.append({"Roll": roll, "Bankroll": random.randint(800, 1200)})

    # Create the bankroll graph
    df = pd.DataFrame(bankroll_data)
    fig = px.line(df, x="Roll", y="Bankroll", title="Player Bankroll Over Time")

    # Display stats
    stats_text = [
        html.P(f"Total Rolls: {stats['total_rolls']}"),
        html.P(f"Player Bankroll: ${stats['player_bankroll']}")
    ]

    return logs, fig, stats_text

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)