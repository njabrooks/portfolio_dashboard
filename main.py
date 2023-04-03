import os
import pandas as pd
from datetime import datetime
from dash import dash, html, dcc, dash_table, Input, Output
from dash.dash_table import FormatTemplate
import plotly.express as px
from config import summary_folder, font_style1, font_style2

# Read and combine CSV files
csv_files = [f for f in os.listdir(summary_folder) if f.endswith(".csv")]
dataframes = []

for file in csv_files:
    df = pd.read_csv(os.path.join(summary_folder, file))
    datetime_str = file[:15]
    datetime_obj = datetime.strptime(datetime_str, "%Y%m%d.%H%M%S")
    df["Datetime"] = datetime_obj
    df["DatetimeSort"] = datetime_obj.strftime("%Y%m%d%H00")
    dataframes.append(df)

combined_df = pd.concat(dataframes).reset_index(drop=True)
combined_df = combined_df[combined_df["Account"] != "Total"]

# Add "Type" column to the combined_df
cash_accounts = [
    "HSBC Credit", "NatWest", "Monzo", "HSBC USD", "HSBC HKD", "HSBC Savings",
    "HSBC Credit", "Monzo", "HSBC GBP", "BA Amex", "Monzo", "John Lewis"
]

property_accounts = ["35B Lancaster Rd", "Tesla Model Y"]


def determine_type(account):
    if account in cash_accounts:
        return "Cash"
    elif account in property_accounts:
        return "Property"
    else:
        return "Risk"


combined_df["Type"] = combined_df["Account"].apply(determine_type)

# Import money format template
money = FormatTemplate.money(2)


# Initialise the Dash app
app = dash.Dash(__name__, external_stylesheets=['/assets/custom_styles.css'])


# Establish app layout
app.layout = html.Div(
    children=[
        # Header
        html.H1("Portfolio Dashboard", style={"textAlign": "center", "color": "white",
            "font-family": font_style1, "fontWeight": "normal", "fontSize": "2.5rem", "margin-top": "20px"}),

        # Checklists
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Type:", style={"color": "white", "font-family": font_style2,
                                                   "font-size": "1.25rem"}),
                        dcc.Checklist(
                            id="type-checklist",
                            options=[{"label": t, "value": t} for t in combined_df["Type"].unique()],
                            value=combined_df["Type"].unique(),
                            inline=True,
                            labelStyle={"color": "white", "font-family": font_style1, "margin-top": "5px",
                                        "margin-left": "18px"},
                        ),
                    ],
                    style={"width": "50%", "display": "flex", "backgroundColor": "#333333"},
                ),
                html.Div(
                    [
                        html.Label("Owner:", style={"color": "white", "font-family": font_style2,
                                                    "font-size": "1.25rem"}),
                        dcc.Checklist(
                            id="owner-checklist",
                            options=[{"label": o, "value": o} for o in combined_df["Owner"].unique()],
                            value=combined_df["Owner"].unique(),
                            inline=True,
                            labelStyle={"color": "white", "font-family": font_style1, "margin-top": "5px",
                                        "margin-left": "18px"},
                        ),
                    ],
                    style={"width": "50%", "display": "flex", "backgroundColor": "#333333"},
                ),
            ],
            style={"backgroundColor": "#333333", "padding": "10px", "display": "flex"},
        ),

        # Chart
        html.Div(
            [
                dcc.Graph(id="line-chart", config={"displayModeBar": False}),
            ],
            style={"backgroundColor": "#444444", "padding": "10px"},
        ),

        # Table
        html.Div(
            [
                dash_table.DataTable(
                    id="summary-table",
                    data=[],
                    columns=[
                        {"name": "Owner", "id": "Owner"},
                        {"name": "Type", "id": "Type"},
                        {"name": "Account", "id": "Account"},
                        {"name": "USD Value", "id": "USD Value", "type": "numeric", "format": money}
                    ],
                    style_header={
                        "backgroundColor": "#333333",
                        "color": "white",
                        "fontSize": "1.1rem",
                        "fontFamily": font_style2,
                    },
                    sort_action="native",
                    sort_mode="single",
                    style_data_conditional=[
                        {
                            "if": {"row_index": "odd"},
                            "backgroundColor": "#666666",
                            "color": "white",
                        },
                        {
                            "if": {"row_index": "even"},
                            "backgroundColor": "#444444",
                            "color": "white",
                        },
                        {
                            "if": {"filter_query": "{Type} = 'Total'"},
                            "fontFamily": font_style2,
                            "backgroundColor": "#007BFF"
                        },
                    ],
                    style_cell={
                        "backgroundColor": "#444444",
                        "color": "white",
                        "textAlign": "left",
                        "fontFamily": font_style1,
                        "padding-left": "8px",
                        "padding-right": "8px",
                    },
                    style_cell_conditional=[
                        {"if": {"column_id": "USD Value"}, "textAlign": "right"},
                        {'if': {'column_id': 'Type'}, 'width': '25%'},
                        {'if': {'column_id': 'Account'}, 'width': '25%'},
                        {'if': {'column_id': 'Owner'}, 'width': '25%'},
                    ],
                ),
            ],
            style={"width": "50%", "margin": "auto", "padding": "10px"},
        ),

        # Latest data text
        html.Div(
            [html.Small(id="latest-data-text", children="Latest data: {}".format(combined_df["Datetime"].max()),
                        style={"float": "left", "color": "white"},
                        )
             ],
            style={"padding": "10px"},
        ),
    ],
    style={"backgroundColor": "#333333", "font-family": font_style2},
)


# Step 5: Create callbacks
@app.callback(
    Output("line-chart", "figure"),
    [
        Input("type-checklist", "value"),
        Input("owner-checklist", "value"),
    ],
)
def update_chart(selected_types, selected_owners):
    chart_data = combined_df[
        (combined_df["Type"].isin(selected_types)) & (combined_df["Owner"].isin(selected_owners))
        ]

    # Group data by Datetime and calculate the sum of USD Value
    aggregated_data = chart_data.groupby("Datetime")["USD Value"].sum().reset_index()

    # Create a line chart using aggregated data
    fig = px.line(
        aggregated_data,
        x="Datetime",
        y="USD Value",
        title="Portfolio Value",
    )

    # Update the chart styling
    fig.update_layout(
        font={"color": "white", "family": font_style2},
        plot_bgcolor="#444444",
        paper_bgcolor="#444444",
    )
    fig.update_xaxes(
        title="Datetime",
        gridcolor="#666666",
        tickformat="%d%b",
        tickangle=0,
        showspikes=False,
        spikemode='across',
        spikethickness=1,
        spikecolor='#666666',
        spikedash='solid',
    )
    fig.update_yaxes(
        title="USD",
        gridcolor="#666666",
        tickformat=".3s",
        hoverformat=".2f",
        showspikes=False,
        spikemode='across',
        spikethickness=1,
        spikecolor='#666666',
        spikedash='solid',
    )

    fig.update_traces(line=dict(color='#007BFF', width=4))

    # Set the hovertemplate
    fig.update_traces(hovertemplate="Date: %{x|%d %b %Y %H:%M}<br>USD Value: $%{y:,.0f}")

    return fig


@app.callback(
    Output("summary-table", "data"),
    [
        Input("type-checklist", "value"),
        Input("owner-checklist", "value"),
    ],
)
def update_table(selected_types, selected_owners):
    table_data = combined_df[
        (combined_df["Type"].isin(selected_types)) & (combined_df["Owner"].isin(selected_owners))
        ]

    max_datetime_sort = table_data['DatetimeSort'].max()
    table_data = table_data[table_data['DatetimeSort'] == max_datetime_sort]

    summary_df = (
        table_data.groupby(["Owner", "Type", "Account"])
        .agg({"USD Value": "sum"})
        .reset_index()
    )

    # Calculate the total row
    total_row = summary_df.sum(numeric_only=True)
    total_row["Owner"] = "Total"
    total_row["Type"] = "Total"
    total_row["Account"] = "Total"

    # Add the total row to the summary_df
    total_row_df = pd.DataFrame(total_row).T
    summary_df = pd.concat([summary_df, total_row_df], ignore_index=True)

    # Custom sort function to ensure the total row remains at the bottom
    def custom_sort(row):
        if row["Account"] == "Total":
            return float("inf")
        return row["USD Value"]

    summary_df["sort_column"] = summary_df.apply(custom_sort, axis=1)
    summary_df = summary_df.sort_values(by=["sort_column"]).drop(columns=["sort_column"]).reset_index(drop=True)

    return summary_df.to_dict("records")


if __name__ == '__main__':
    app.run_server(debug=True)