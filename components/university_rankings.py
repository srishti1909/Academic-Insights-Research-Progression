import base64
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px

from dash import dcc, html, Input, Output, State, no_update
from io import BytesIO
from fuzzywuzzy import process
from services.mysql_service import mysql_engine, update_university_rank
from sqlalchemy import text, exc

layout = html.Div([
    dbc.Card([
        dbc.CardHeader("University Rankings based on Citations per Faculty"),
        dbc.CardBody([
            dbc.Tabs([
                dbc.Tab([
                    dbc.Row([
                        dbc.Col(html.H5("Upload XLSX File"), width=4)
                    ]),
                    dbc.Row([
                        dbc.Col(
                            dcc.Upload(
                                id='file-upload',
                                children=html.Div([
                                    'Drag and Drop to Upload File OR ',
                                    html.Br(),
                                    html.Button('Browse File', className='btn btn-primary')
                                ]),
                                style={
                                    'width': '25%',
                                    'height': '100px',
                                    'lineHeight': '40px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    'margin': '10px 0'
                                }
                            ),
                            width=12
                        )
                    ]),
                    dbc.Row([
                        dbc.Col(
                            html.Div(id='output'),
                            width=12
                        )
                    ]),
                    dbc.Row([
                        dbc.Col(
                            html.Div(id="file-name-display"),
                            width=12
                        )
                    ]),
                    dbc.Row([
                        dbc.Col(
                            html.Button('Submit', id='submit-button-upload', n_clicks=0, className='btn btn-primary'),
                            width=4
                        )
                    ]),
                ], label="Upload Rankings Data"),
                dbc.Tab([
                    dcc.Dropdown(
                        id='university-dropdown',
                        options=[],
                        placeholder="Select a University",
                        style={'width': '100%'}
                    ),
                    html.Br(),
                    dbc.Input(
                        id='rank-input',
                        placeholder='Enter University Rank',
                        type='number',
                        min=1,
                        step=1,
                        style={'width': '15%'}
                    ),
                    html.Br(),
                    html.Button('Submit', id='submit-button-update', n_clicks=0, className='btn btn-primary'),
                    html.Div(id='query-status'),
                ], label="Update University Rank"),
            ]),
        ]),
    ]),
    html.Br(),
    html.Div([
        dcc.Graph(id='university-ranks-dashboard')
    ]),
    html.Button('Refresh Chart', id='refresh-button', className='btn btn-primary'),
    dcc.Store(id='store-uploaded-data'),
])


def register_callbacks(app):
    @app.callback(
        [Output('file-name-display', 'children'),
         Output('submit-button-upload', 'disabled')],
        Input('file-upload', 'filename')
    )
    def display_file_name_and_update_submit_button(filename):
        if filename is not None:
            if filename.lower().endswith('.xlsx'):
                return [html.Span(f"Uploaded File: {filename} ", style={'color': 'green'}),
                        html.Span("✅", style={'color': 'green'})], False
            else:
                return [html.Span(f"File: {filename} with type {filename.split('.')[-1].upper()} not supported ",
                                  style={'color': 'red'}), html.Span("❌", style={'color': 'red'})], True
        else:
            return "", True

    # update university dropdown
    @app.callback(
        Output('university-dropdown', 'options'),
        Input('university-dropdown', 'search_value')
    )
    def update_university_dropdown(search_value):
        with mysql_engine.connect() as connection:
            result = connection.execute(text('SELECT id AS uid, name FROM university'))
            universities = pd.DataFrame(result.fetchall(), columns=["uid", "name"])
        return [{'label': row['name'], 'value': row['name']} for _, row in universities.iterrows()]

    @app.callback(
        [Output('query-status', 'children'),
         Output('intermediate-value', 'children')],
        Input('submit-button-update', 'n_clicks'),
        State('university-dropdown', 'value'),
        State('rank-input', 'value'),
        State('refresh-button', 'n_clicks')
    )
    def update_university_rank_from_textinput(n_clicks, selected_university, new_rank, refresh_n_clicks):
        if selected_university is None or new_rank is None:
            return "\nPlease fill in all fields before submitting. ⚠️", no_update
        try:
            if n_clicks > 0:
                with mysql_engine.connect() as connection:
                    old_rank_query = text("SELECT university_rank FROM university WHERE name = :name")
                    old_rank = connection.execute(old_rank_query, {"name": selected_university}).scalar()

                    if old_rank == int(new_rank):
                        return [html.Span(f"{selected_university}'s Rank is already {old_rank}. \
                        Enter a different rank to update.", style={'color': 'orange'}),
                                html.Span("⚠️", style={'color': 'orange'})], \
                            no_update

                uni_query = text("UPDATE university SET university_rank = :new_rank WHERE name = :name")
                uni_data = {'new_rank': int(new_rank), 'name': selected_university}

                with mysql_engine.connect() as connection:
                    trans = connection.begin()
                    try:
                        connection.execute(uni_query, uni_data)
                        trans.commit()
                    except exc.SQLAlchemyError:
                        trans.rollback()
                        raise

                refresh_n_clicks = 0 if refresh_n_clicks is None else refresh_n_clicks

                return [html.Span(
                    f"University {selected_university}'s Rank is updated successfully from {old_rank} to {new_rank}",
                    style={'color': 'green'}), html.Span("✅", style={'color': 'green'})], refresh_n_clicks + 1

        except exc.SQLAlchemyError as e:
            error = str(e)
            print("the error is:" + error)
            return error, no_update

    app.layout.children.append(html.Div(id='intermediate-value', style={'display': 'none'}))

    # Scatter-plot to show university rankings
    @app.callback(
        Output('university-ranks-dashboard', 'figure'),
        [Input('refresh-button', 'n_clicks'),
         Input('intermediate-value', 'children'),
         Input('store-uploaded-data', 'data')]
    )
    def show_university_rankings(n_clicks, intermediate_value, uploaded_data):
        with mysql_engine.connect() as connection:
            result = connection.execute(text(
                'SELECT name, university_rank FROM university'))
            result_df = pd.DataFrame(result.fetchall(),
                                     columns=["name", "university_rank"])

            result_df = result_df.dropna(subset=['university_rank'])

            result_df['y'] = np.arange(len(result_df))

            result_df['inverted_rank'] = result_df['university_rank'].max() - result_df['university_rank'] + 1

            fig = px.scatter(result_df, x='university_rank', custom_data=['name', 'university_rank'],
                             color='university_rank', color_continuous_scale=px.colors.diverging.Geyser,
                             size='inverted_rank',
                             size_max=20
                             )

            fig.update_traces(
                hovertemplate="<b>%{customdata[0]}</b><br>Rank: %{customdata[1]}<extra></extra>"
            )

            fig.update_layout(
                height=800,
                title='University Rankings based on Citations per Faculty',
                title_font=dict(size=20),
                title_x=0.5,
                xaxis_title='Rank',
                xaxis_title_font=dict(size=18),
                xaxis_tickfont=dict(size=14),
                yaxis_title='',
                yaxis=dict(showticklabels=False),
                coloraxis_colorbar_title='Rank',
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=16,
                    font_family="PT Root UI"
                )
            )

        return fig

    def read_excel_file(contents):
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(BytesIO(decoded), skiprows=3, header=None)
        return df

    def filter_and_process_dataframe(df):
        # check if the first col in the dataframe is "rank display" for 2023 file | "rank in country" for 2022 file
        if df.iloc[0, 0] == 'rank display':
            institution_col = 2  # C
            cpf_rank_col = 17  # R
            cpf_score_col = 16  # Q
            country_col = 4  # E
        elif df.iloc[0, 0] == 'rank in country':
            institution_col = 4  # E
            cpf_rank_col = 19  # T
            cpf_score_col = 18  # S
            country_col = 6  # G

        filtered_df = df.iloc[:, [institution_col, cpf_rank_col, cpf_score_col, country_col]].copy()

        filtered_df.columns = ['institution', 'cpf rank', 'cpf score', 'country']

        filtered_df.loc[:, 'cpf rank'] = filtered_df['cpf rank'].replace('+', 1000)

        filtered_df.loc[:, 'Citations per Faculty Rank'] = pd.to_numeric(filtered_df['cpf rank'], errors='coerce')

        average_score_601 = filtered_df.loc[
            filtered_df['Citations per Faculty Rank'] >= 601, 'cpf score'].mean()

        filtered_df.loc[
            filtered_df['Citations per Faculty Rank'] >= 601, 'Citations per Faculty Rank'] = average_score_601

        filtered_df = filtered_df.dropna()

        filtered_df = filtered_df.loc[filtered_df['country'] == 'United States']

        filtered_df = filtered_df.sort_values(by='Citations per Faculty Rank')

        filtered_df = filtered_df[['institution', 'Citations per Faculty Rank', 'cpf score']].rename(
            columns={'institution': 'University Name', 'cpf score': 'Score'})

        return filtered_df

    def update_university_rankings(df, min_match_score=88):
        with mysql_engine.connect() as connection:
            # Start a transaction
            trans = connection.begin()

            # Get the existing university data
            result = connection.execute(text('SELECT id, name FROM university'))
            df_university = pd.DataFrame(result.fetchall(), columns=["id", "name"])

            sql_universities = {name: idx for idx, name in df_university[['id', 'name']].itertuples(index=False)}
            csv_universities = {row['University Name']: row['Citations per Faculty Rank'] for index, row in
                                df.iterrows()}

            # Update the university rankings
            for csv_university_name, citations_rank in csv_universities.items():
                best_match, match_score = process.extractOne(csv_university_name, sql_universities.keys())
                if match_score >= min_match_score:
                    university_id = sql_universities[best_match]
                    update_university_rank(university_id, citations_rank, connection)

            specific_universities = [
                'University of Florida',
                'Purdue University--West Lafayette',
                'University of San Diego',
            ]

            for university_name in specific_universities:
                best_match, match_score = process.extractOne(university_name, csv_universities.keys())
                if match_score >= min_match_score:
                    university_id = sql_universities[university_name]
                    update_university_rank(university_id, csv_universities[best_match], connection)

            # Manual updates for universities that aren't matched by fuzzywuzzy
            manual_updates = {
                'Virginia Tech': 362,
                'Stony Brook University--SUNY': 395,
                'Brigham Young University--Provo': 582,
                'University of Denver': 595
            }

            for university_name, university_rank in manual_updates.items():
                if university_name in sql_universities:
                    university_id = sql_universities[university_name]
                    update_university_rank(university_id, university_rank, connection)

            # Commit the transaction
            trans.commit()

            # Count the updated rows and return the result
            updated_universities_count_query = text("SELECT COUNT(*) FROM university WHERE university_rank IS NOT NULL")
            updated_universities_count = connection.execute(updated_universities_count_query).scalar()

        return updated_universities_count

    @app.callback(
        [Output('output', 'children'),
         Output('store-uploaded-data', 'data')],
        Input('submit-button-upload', 'n_clicks'),
        State('file-upload', 'contents'),
        State('file-upload', 'filename')
    )
    def handle_file_upload(n_clicks_upload=0, contents=None, filename=None):
        if n_clicks_upload:
            if contents is not None and filename is not None:
                if filename.lower().endswith('.xlsx'):
                    df = read_excel_file(contents)
                    filtered_df = filter_and_process_dataframe(df)
                    updated_universities_count = update_university_rankings(filtered_df)

                    return [html.Div([html.Span(
                        f'File uploaded and processed: {filename}. {updated_universities_count} university rankings updated.',
                        style={'color': 'green'}), html.Span("✅", style={'color': 'green'})]),
                        updated_universities_count]
                else:
                    return [html.Div([html.Span(
                        f"File: {filename} with type {filename.split('.')[-1].upper()} not supported ",
                        style={'color': 'red'}), html.Span("❌", style={'color': 'red'})]), None]
            else:
                return [html.Div('No file uploaded.'), None]
        else:
            return [None, None]

    @app.callback(
        Output('dummy-output', 'children'),
        Input('submit-button-update', 'n_clicks')
    )
    def handle_submit_button_update(n_clicks_update):
        pass

    app.layout.children.append(html.Div(id='dummy-output', style={'display': 'none'}))
    # MYSQL university_rankings.py
