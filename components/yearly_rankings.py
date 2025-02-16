import dash_bootstrap_components as dbc
import functools
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import dcc, html, Input, Output
from services.neo4j_service import neo4j_driver


# Preload the year options:
def get_year_options():
    query = """MATCH (pub:PUBLICATION) RETURN DISTINCT pub.year AS year ORDER BY year DESC"""
    with neo4j_driver.session() as session:
        result = session.run(query)
        years = pd.DataFrame([r.data() for r in result])

    return [{'label': row['year'], 'value': row['year']} for _, row in years.iterrows()]


year_options = get_year_options()

layout = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Yearly Ranking: Top 10 Universities by Faculty and Publications"),
                        dbc.CardBody(
                            [
                                dcc.Dropdown(
                                    id='year-dropdown',
                                    options=year_options,
                                    placeholder="Select a Year",
                                    style={'fontSize': '16px'},
                                ),
                                dcc.Graph(id='faculty-publications-chart'),
                            ]
                        ),
                    ],
                    style={'marginBottom': '1rem'},
                )
            )
        ),
    ]
)


def register_callbacks(app):
    @app.callback(
        Output('faculty-publications-chart', 'figure'),
        [Input('year-dropdown', 'value')]
    )
    @functools.lru_cache()
    def update_faculty_publications_chart(selected_year):
        if selected_year is None:
            return go.Figure()

        with neo4j_driver.session() as session:
            query = """
                MATCH (u:INSTITUTE)<-[:AFFILIATION_WITH]-(f:FACULTY)-[:PUBLISH]->(pub:PUBLICATION)
                WHERE pub.year = $year
                RETURN u.name AS university, COUNT(DISTINCT f) AS faculty_count, COUNT(DISTINCT pub) AS publication_count
                ORDER BY publication_count DESC, faculty_count DESC
                LIMIT 10
            """
            result = session.run(query, {"year": int(selected_year)})
            faculty_count = pd.DataFrame([r.data() for r in result])

        fig = px.bar(
            faculty_count,
            x=['faculty_count', 'publication_count'],
            y='university',
            labels={'university': 'University', 'value': 'Count', 'variable': 'Category'},
            barmode='group',
            custom_data=['university'],
            text_auto=True,
            color_discrete_map={'faculty_count': '#00A0B0', 'publication_count': '#EDC951'},
            category_orders={'Category': ['faculty_count', 'publication_count']},
        )

        fig.for_each_trace(
            lambda trace: trace.update(
                name='Faculty Count' if trace.name == 'faculty_count' else 'Publication Count',
                hovertemplate=(
                    f"{'Faculty Count' if trace.name == 'faculty_count' else 'Publication Count'} = {trace.x[0]}<extra></extra>"
                )
            )
        )

        fig.update_layout(
            barmode='stack',
            title_font=dict(size=20),
            yaxis=dict(autorange="reversed", title=None, tickfont={'size': 14}),
            xaxis=dict(title='Count', tickfont={'size': 14}),
            xaxis_title_font=dict(size=18),
            legend=dict(font={'size': 14}, title=dict(text='Category', font=dict(size=14)), itemsizing='constant'),
            hovermode='y unified',
            title={
                'text': f'Top 10 Universities Faculty and Publications in {selected_year}',
                'x': 0.5,  # Centered title
                'xanchor': 'center'
            },
            hoverlabel=dict(
                bgcolor="white",
                font_size=16,
                font_family="PT Root UI"
            )
        )

        fig.update_yaxes(automargin=True)

        return fig
# NEO4J yearly_rankings.py
