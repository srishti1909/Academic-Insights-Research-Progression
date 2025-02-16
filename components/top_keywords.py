import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

from dash import dcc, html, Input, Output
from services.mysql_service import mysql_engine, get_top_keywords_by_university
from sqlalchemy import text

layout = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Top Keywords in Different Universities"),
                        dbc.CardBody(
                            [
                                dcc.Dropdown(
                                    id='university-keywords-dropdown',
                                    options=[],
                                    placeholder="Select a University",
                                    style={'fontSize': '16px'},
                                ),
                                # html.H4(id='unique-keywords', style={'text-align': 'center'}),
                                html.Br(),
                                html.Div([
                                    dbc.Col(
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.Img(id='university-logo',
                                                                 style={'height': '250px', 'width': '100%',
                                                                        'object-fit': 'contain'}),
                                                        html.H4(id='university-name', className='card-title',
                                                                style={'text-align': 'center'})
                                                    ]
                                                ),
                                            ],
                                            style={'marginRight': '1rem'},
                                        ),
                                        width=4,
                                    ),
                                    dbc.Col(
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        dcc.Graph(id='top-keywords-chart')
                                                    ]
                                                ),
                                            ],
                                        ),
                                        width=8,
                                    ),
                                ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                            ]
                        ),
                    ],
                    style={'marginBottom': '1rem'},
                )
            )
        ),
    ]
)


# MYSQL top_keywords.py
def register_callbacks(app):
    @app.callback(
        Output('university-keywords-dropdown', 'options'),
        Input('university-keywords-dropdown', 'search_value')
    )
    def update_university_keywords_dropdown_options(search_value):
        with mysql_engine.connect() as connection:
            universities = pd.read_sql_query(text("SELECT name FROM university ORDER BY name"), connection)

        return [{'label': row['name'], 'value': row['name']} for _, row in universities.iterrows()]

    @app.callback(
        Output('university-logo', 'src'),
        Output('top-keywords-chart', 'figure'),
        Output('university-name', 'children'),
        Input('university-keywords-dropdown', 'value')
    )
    def update_university_logo_and_keywords_chart(university_name):
        if not university_name:
            empty_chart = px.treemap(title="Please select a university to display the chart. ⚠️")
            empty_chart.update_layout(title_x=0.5)
            return '', empty_chart, ''

        query = f"SELECT photo_url FROM university WHERE name = '{university_name}'"
        with mysql_engine.connect() as connection:
            logo_url = connection.scalar(text(query))

        logo_src = logo_url

        data = get_top_keywords_by_university(university_name)

        fig = px.treemap(data, path=['keyword'], values='total_score',
                         color_discrete_sequence=px.colors.diverging.Geyser)

        query = f"""
            SELECT COUNT(DISTINCT k.id) as unique_keywords_count
            FROM keyword k
            JOIN faculty_keyword fk ON k.id = fk.keyword_id
            JOIN faculty f ON fk.faculty_id = f.id
            JOIN university u ON f.university_id = u.id
            WHERE u.name = '{university_name}'
            LIMIT 10
        """

        with mysql_engine.connect() as connection:
            unique_keywords_count = connection.scalar(text(query))

        fig.update_layout(
            title=f'Top 10 Keywords for {university_name} — Number of Unique Keywords: {unique_keywords_count}',
            title_font=dict(size=20),
            title_x=0.5
        )

        return logo_src, fig, university_name
# MYSQL top_keywords.py
