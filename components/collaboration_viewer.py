import dash_bootstrap_components as dbc
import pandas as pd

from dash import dcc, html, Input, Output
from services.mysql_service import mysql_engine
from sqlalchemy import text

layout = html.Div([
    dbc.Card([
        dbc.CardHeader("Faculty Publication Collaboration Viewer", className="card-header"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(placeholder='Select University:', id='university-id', className='mb-3')
                ], width=6),
                dbc.Col([
                    dcc.Dropdown(placeholder='Select Faculty', id='faculty-id', className='mb-3')
                ], width=6)
            ]),
            dbc.RadioItems(
                id='data-radio',
                options=[
                    {'label': ' Within University', 'value': 0},
                    {'label': ' Outside University', 'value': 1}
                ],
                value=0,
                inline=True,
                className='mb-3 custom-radio'
            ),
            dbc.Row([
                dbc.Col([
                    dbc.InputGroup([
                        dbc.InputGroupText("Enter the number of records to display:",
                                           className='input-group-text-collab mb-2'),
                        dbc.Input(
                            id='num-records-input',
                            type='number',
                            min=1,
                            value=10,
                            step=1,
                            className='mb-2'
                        ),
                    ]),
                ], width=4)
            ], className='mb-3'),
            html.Div(id='coauthors', className='mt-3'),
        ], className="card-body")
    ])
])


# MYSQL collaboration_viewer.py
def register_callbacks(app):
    @app.callback(
        Output('university-id', 'options'),
        Input('university-id', 'search_value')
    )
    def update_university_dropdown(selected_university):
        with mysql_engine.connect() as connection:
            result = connection.execute(text('SELECT id as uid, name FROM university'))
            universities = pd.DataFrame(result.fetchall(), columns=["uid", "name"])
        return [{'label': row['name'], 'value': row['uid']} for _, row in universities.iterrows()]

    @app.callback(
        Output('faculty-id', 'options'),
        Input('university-id', 'value')
    )
    def update_faculty_dropdown(selected_university):
        if selected_university is None:
            return []
        with mysql_engine.connect() as connection:
            result = connection.execute(text('SELECT id, name FROM faculty WHERE university_id = :uid'),
                                        {"uid": selected_university})
            faculty_list = pd.DataFrame(result.fetchall(), columns=["id", "name"])
        return [{'label': row['name'], 'value': row['id']} for _, row in faculty_list.iterrows()]

    @app.callback(
        Output('coauthors', 'children'),
        Input('university-id', 'value'),
        Input('faculty-id', 'value'),
        Input('data-radio', 'value'),
        Input('num-records-input', 'value')
    )
    def show_coauthors(selected_university, selected_faculty, selected_radio, num_records):
        if selected_faculty is None or selected_university is None or num_records is None:
            return []
        with mysql_engine.connect() as connection:
            base_query = '''
            SELECT DISTINCT f1.name AS faculty1, f2.name AS faculty2, u2.name AS university,
            p.title AS publication, p.year, p.num_citations
            FROM faculty f1
            JOIN faculty_publication fp ON fp.faculty_id = f1.id
            JOIN faculty_publication fp1 ON fp.publication_id = fp1.publication_id AND fp.faculty_id <> fp1.faculty_id
            JOIN publication p ON p.id = fp.publication_id AND p.id = fp1.publication_id
            JOIN faculty f2 ON f2.id = fp1.faculty_id
            JOIN university u1 ON u1.id = f1.university_id
            JOIN university u2 ON u2.id = f2.university_id
            AND f1.id = :faculty_id
            AND u1.id = :university_id
            '''

            if selected_radio == 0:
                query = base_query + 'AND u1.id = u2.id'
            else:
                query = base_query + 'AND u1.id <> u2.id'

            query = query + '''
            ORDER BY p.num_citations ASC
            LIMIT :limit
            '''

            result = connection.execute(text(query),
                                        {"faculty_id": selected_faculty, "university_id": selected_university,
                                         "limit": num_records})

            recent_publications = pd.DataFrame(result.fetchall(),
                                               columns=["Faculty1", "Faculty2", "University", "Publication", "Year",
                                                        "num_citations"])

            recent_publications.rename(columns={
                'Faculty1': 'Faculty',
                'Faculty2': 'Co-Author',
                'num_citations': 'Number of citations',
                'created_at': 'Created at'
            }, inplace=True)

            recent_publications.reset_index(drop=True, inplace=True)
            recent_publications.index += 1
            recent_publications.reset_index(inplace=True)
            recent_publications.rename(columns={"index": "#"}, inplace=True)
        
        return dbc.Table.from_dataframe(recent_publications, striped=True, bordered=True, hover=True)
# MYSQL collaboration_viewer.py
