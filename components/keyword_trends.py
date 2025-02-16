import dash_bootstrap_components as dbc

from dash import dcc, html, Input, Output
from services.mongodb_service import get_keyword_options, get_keyword_trends_data

layout = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Keyword Trends Over Time"),
                        dbc.CardBody(
                            [
                                dcc.Dropdown(
                                    id='keyword-trends-dropdown',
                                    options=get_keyword_options(),
                                    multi=True,
                                    placeholder="Select Keywords",
                                    className="mb-3",
                                ),
                                dcc.Graph(id='keyword-trends-chart'),
                            ]
                        ),
                    ],
                    style={"marginTop": "1rem"},
                )
            )
        ),
    ]
)


# MONGODB keyword_trends.py
def register_callbacks(app):
    @app.callback(
        Output('keyword-trends-chart', 'figure'),
        Input('keyword-trends-dropdown', 'value'))
    def update_keyword_trends_chart(selected_keywords):
        if not selected_keywords:
            return {'data': []}

        trends_data = get_keyword_trends_data(selected_keywords)

        # Define a custom color palette
        color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
                         '#bcbd22', '#17becf']

        figure = {
            'data': [
                {
                    'x': trend['years'],
                    'y': trend['counts'],
                    'name': keyword,
                    'mode': 'lines+markers',
                    'line': {'color': color_palette[i % len(color_palette)]},
                    'marker': {'symbol': 'circle', 'size': 10},
                    'hovertemplate': f"<b>{keyword}</b><br>Keyword Count: %{{y}}<extra></extra>",
                }
                for i, (keyword, trend) in enumerate(trends_data.items())
            ],
            'layout': {
                'title': 'Keyword Trends Over Time',
                'height': 600,
                'xaxis': {
                    'title': 'Year',
                    'gridcolor': '#e1e1e1',
                    'zerolinecolor': '#e1e1e1',
                    'showgrid': True,
                    'tickfont': {'size': 12},
                },
                'yaxis': {
                    'title': 'Keyword Count',
                    'gridcolor': '#e1e1e1',
                    'zerolinecolor': '#e1e1e1',
                    'showgrid': True,
                    'tickfont': {'size': 12},
                },
                'legend': {
                    'font': {'size': 12},
                },
                'hovermode': 'x unified',
            },
        }

        return figure
# MONGODB keyword_trends.py
