import dash_bootstrap_components as dbc
import pandas as pd
import requests

from dash import dcc, html, Input, Output, State, no_update
from services.mysql_service import mysql_engine
from sqlalchemy import text, exc


def is_image_url_valid(image_url):
    if image_url is None:
        return False
    try:
        response = requests.head(image_url, timeout=5)
        return response.status_code == 200 and 'image' in response.headers['Content-Type']
    except (requests.exceptions.RequestException, KeyError):
        return False


# layout of the view
# 1. University Dropdown
# 2. Faculty Dropdown
# 3. Enter Publication details
# 4. Faculty Photo and number of publications
# 5. Recent Publications


layout = html.Div([
    dbc.Card([
        dbc.CardHeader("Enter New Publications", className="card-header"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(placeholder='Select University:', id='pub-university-id', className='mb-3')
                ], width=6),
                dbc.Col([
                    dcc.Dropdown(placeholder='Select Faculty', id='pub-faculty-id', className='mb-3')
                ], width=6)
            ]),
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.InputGroup([
                                        dbc.InputGroupText("Enter publication ID:", className='mb-2'),
                                        dbc.Input(id='Input-pub_id', type='number', className='mb-2')
                                    ]),
                                ], width=8)
                            ], className='mb-3'),
                            dbc.Row([
                                dbc.Col([
                                    dbc.InputGroup([
                                        dbc.InputGroupText("Enter title:", className='mb-2'),
                                        dbc.Input(id='Input-title', type='text', className='mb-2')
                                    ]),
                                ], width=8)
                            ], className='mb-3'),
                            dbc.Row([
                                dbc.Col([
                                    dbc.InputGroup([
                                        dbc.InputGroupText("Enter venue:", className='mb-2'),
                                        dbc.Input(id='Input-venue', type='text', className='mb-2')
                                    ]),
                                ], width=8)
                            ], className='mb-3'),
                            dbc.Row([
                                dbc.Col([
                                    dbc.InputGroup([
                                        dbc.InputGroupText("Enter year:", className='mb-2'),
                                        dbc.Input(id='Input-year', type='number', className='mb-2')
                                    ]),
                                ], width=8)
                            ], className='mb-3'),
                            dbc.Row([
                                dbc.Col([
                                    dbc.InputGroup([
                                        dbc.InputGroupText("Enter number of citations:", className='mb-2'),
                                        dbc.Input(id='Input-num_cit', type='number', className='mb-2')
                                    ]),
                                ], width=8)
                            ], className='mb-3'),
                            dbc.Button('Submit', id='button-submit', color="primary", className="mt-3", n_clicks=0),
                            html.Div(id='pub-query-status', className='mt-3'),
                            html.Div(id='pub-intermediate-value', style={'display': 'none'}),
                            dcc.Store(id='refresh-counter', data={'count': 0})
                        ], className="card-body")
                    ], className="mb-4"),
                    xs=12, sm=12, md=6, lg=8, xl=6
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.Div(
                                html.Img(id='faculty-photo', className='faculty-photo'),
                                className='faculty-photo-container'
                            ),
                            html.Div(id='fac-pub-cnt', className='mt-3',
                                     style={'font-size': '24px', 'text-align': 'center'}),
                            html.Br()
                        ], style={'height': '100%'})
                    ]),
                    xs=12, sm=12, md=6, lg=6, xl=6
                )
            ]),
            dbc.Card([
                dbc.CardHeader("Recently Added Publications", className="card-header"),
                dbc.CardBody([
                    html.Div(id='recent-publications'),
                    dbc.Button('Refresh Table', id='pub-refresh-button', color="primary", className="mt-3")
                ], className="card-body")
            ])
        ])
    ])
])


# MYSQL new_publications.py
def register_callbacks(app):
    # update the university dropdown
    @app.callback(
        Output('pub-university-id', 'options'),
        Input('pub-university-id', 'search_value')
    )
    def update_university_dropdown(selected_university):
        with mysql_engine.connect() as connection:
            result = connection.execute(text('SELECT id AS uid, name FROM university'))
            universities = pd.DataFrame(result.fetchall(), columns=["uid", "name"])
        return [{'label': row['name'], 'value': row['uid']} for _, row in universities.iterrows()]

    # update faculty dropdown list from selected university
    @app.callback(
        Output('pub-faculty-id', 'options'),
        Input('pub-university-id', 'value')
    )
    def update_faculty_dropdown(selected_university):
        if selected_university is None:
            return []
        with mysql_engine.connect() as connection:
            result = connection.execute(text('SELECT id, name FROM faculty WHERE university_id = :uid'),
                                        {"uid": selected_university})
            faculty_list = pd.DataFrame(result.fetchall(), columns=["id", "name"])
        return [{'label': row['name'], 'value': row['id']} for _, row in faculty_list.iterrows()]

    # update faculty publication counts
    def update_faculty_publication_cnt(selected_faculty):
        if selected_faculty is None:
            return []
        with mysql_engine.connect() as connection:
            result = connection.execute(text('SELECT publication_count, name FROM faculty WHERE id = :fid'),
                                        {"fid": selected_faculty}).fetchone()
            return "Faculty " + result[1] + " has " + str(result[0]) + " publications \n"

    # display faculty photo using photo_url
    @app.callback(
        Output('faculty-photo', 'src'),
        Output('fac-pub-cnt', 'children', allow_duplicate=True),
        Input('pub-faculty-id', 'value'),
        prevent_initial_call=True
    )
    def get_faculty_photo(selected_faculty):
        if selected_faculty is None:
            return None, None
        with mysql_engine.connect() as connection:
            result = connection.execute(text('SELECT photo_url FROM faculty WHERE id = :fid'),
                                        {"fid": selected_faculty}).fetchone()
            photo_url = result[0]
            if not is_image_url_valid(photo_url):
                photo_url = 'https://user-images.githubusercontent.com/8846884/232245136-e2a3e0f0-fd8c-4aa8-a18b-6e83848d9de3.jpeg'
            return photo_url, update_faculty_publication_cnt(selected_faculty)

    # Insert a new publication into publication table using the details entered in the form
    # and display the new faculty publication count after successful insert
    @app.callback(
        [Output('pub-query-status', 'children'),
         Output('fac-pub-cnt', 'children'),
         Output('refresh-counter', 'data')],
        Input('button-submit', 'n_clicks'),
        State('Input-pub_id', 'value'),
        State('Input-title', 'value'),
        State('Input-venue', 'value'),
        State('Input-year', 'value'),
        State('Input-num_cit', 'value'),
        State('pub-faculty-id', 'value'),
        State('refresh-counter', 'data')
    )
    def insert_publication(button_click, pub_id, title, venue, year, num_cit, fac_id, refresh_counter):
        if pub_id is None or title is None or venue is None or year is None or num_cit is None or fac_id is None:
            return "\nPlease fill in all fields before submitting. ⚠️", None, no_update
        elif fac_id is not None and (
                pub_id is None or title is None or venue is None or year is None or num_cit is None):
            result = update_faculty_publication_cnt(fac_id)
            return "\nPlease fill in all fields before submitting. ⚠️", result, no_update

        with mysql_engine.connect() as connection:
            existing_pub = connection.execute(text("SELECT id FROM publication WHERE id = :pub_id"),
                                              {"pub_id": int(pub_id)}).fetchone()

        if existing_pub:
            return html.Span([
                html.Span("Publication ID: ", style={'color': 'red'}),
                html.Span(f"{pub_id} ", style={'color': 'red'}),
                html.Span(" already exists ", style={'color': 'red'}),
                html.Span("❌", style={'color': 'red'})
            ]), no_update, no_update

        try:
            pub_query = text("INSERT INTO publication VALUES(:pub_id, :title, :venue, :year, :num_cit, NOW())")
            pub_data = {'pub_id': int(pub_id), 'title': title, 'venue': venue, 'year': int(year),
                        'num_cit': int(num_cit)}
            fac_pub_query = text("INSERT INTO faculty_publication VALUES(:fac_id, :pub_id)")
            fac_pub_data = {'fac_id': int(fac_id), 'pub_id': int(pub_id)}
            with mysql_engine.connect() as connection:
                trans = connection.begin()
                try:
                    connection.execute(pub_query, pub_data)
                    connection.execute(fac_pub_query, fac_pub_data)
                    trans.commit()
                    result = update_faculty_publication_cnt(fac_id)
                except exc.SQLAlchemyError:
                    trans.rollback()
                    raise

            return html.Span([
                html.Span("Publication ID: ", style={'color': 'green'}),
                html.Span(f"{pub_id} ", style={'color': 'green'}),
                html.Span(" was inserted successfully ", style={'color': 'green'}),
                html.Span("✅", style={'color': 'green'})
            ]), result, {'count': refresh_counter['count'] + 1}

        except exc.SQLAlchemyError as e:
            error = str(e)
            print("the error is:" + error)
            return error, no_update

    # display top 10 publications that are recently added which includes the latest one
    # that is just added by entering in the form
    @app.callback(
        Output('recent-publications', 'children'),
        [Input('pub-refresh-button', 'n_clicks'),
         Input('refresh-counter', 'data')]
    )
    def update_recent_publications(n_clicks, refresh_counter):
        with mysql_engine.connect() as connection:
            result = connection.execute(text(
                'SELECT f.name AS faculty, p.id, title, venue, year, num_citations, created_at '
                'FROM publication p '
                'INNER JOIN faculty_publication fp ON fp.publication_id = p.id '
                'INNER JOIN faculty f ON fp.faculty_id = f.id '
                'WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 10'))
            recent_publications = pd.DataFrame(result.fetchall(),
                                               columns=["faculty", "id", "title", "venue", "year", "num_citations",
                                                        "created_at"])

            # Rename the columns
            recent_publications.rename(columns={
                'faculty': 'Faculty',
                'id': 'Publication ID',
                'title': 'Title',
                'venue': 'Venue',
                'year': 'Year',
                'num_citations': 'Number of citations',
                'created_at': 'Created at'
            }, inplace=True)

        return dbc.Table.from_dataframe(recent_publications, striped=True, bordered=True, hover=True)
# MYSQL new_publications.py
