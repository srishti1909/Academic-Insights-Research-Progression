import dash
import dash_bootstrap_components as dbc

from dash import html
from components import (
    keyword_trends,
    yearly_rankings,
    top_keywords,
    university_rankings,
    new_publications,
    collaboration_viewer,
)

custom_css = "static/custom_theme.css"
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY, custom_css])

navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavbarBrand("Academic Insights & Research Progression", href="#"),
        ],
        fluid=True,
    ),
    color="primary",
    dark=True,
)


# Function to create tabs
def create_tab(label, children, tab_style, active_tab_style):
    return dbc.Tab(
        label=label,
        children=children,
        tab_style=tab_style,
        active_tab_style=active_tab_style,
    )


# Define the list of dictionaries for each tab
tabs_info = [
    {"label": "Yearly Rankings", "component": yearly_rankings},
    {"label": "University Rankings", "component": university_rankings},
    {"label": "New Publications", "component": new_publications},
    {"label": "Collaboration Viewer", "component": collaboration_viewer},
    {"label": "Top Keywords", "component": top_keywords},
    {"label": "Keyword Trends", "component": keyword_trends},
]

# Generate tabs using the create_tab function and list of dictionaries
tabs = dbc.Tabs(
    [
        create_tab(
            label=tab["label"],
            children=tab["component"].layout,
            tab_style={"padding": "1rem", "backgroundColor": "#f8f9fa"},
            active_tab_style={"borderTop": "3px solid #007bff"},
        )
        for tab in tabs_info
    ],
    style={"marginTop": "1rem"},
)

app.layout = html.Div(
    [
        navbar,
        dbc.Container(
            [
                tabs,
            ],
            fluid=True,
        ),
    ]
)

# Register callbacks for each component
for tab in tabs_info:
    tab["component"].register_callbacks(app)

if __name__ == "__main__":
    app.run_server(debug=False)
