from dash import Input, Output, State, dcc, html, no_update, callback_context
from flask import session
from db import verify_user
from db import fetch_data
from db import insert_data
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State, MATCH
import pandas as pd
import plotly.express as px
import base64
import io
import datetime
from sqlalchemy import create_engine
from sqlalchemy import text
import base64
import os


def dashboard_callbacks(dash_app):
    @dash_app.callback(
        Output("resolve-issues-modal", "is_open"),
        [Input("open-issues-button", "n_clicks"), Input("close-issues-modal", "n_clicks")],
        [State("resolve-issues-modal", "is_open")]
    )
    def toggle_issues_modal(open_clicks, close_clicks, is_open):
        if open_clicks or close_clicks:
            return not is_open
        return is_open

    # Callback to open/close the issue modal
    @dash_app.callback(
        Output("issue-modal", "is_open"),
        [Input("open-modal-button", "n_clicks"), Input("submit-issue-button", "n_clicks")],
        [State("issue-modal", "is_open")]
    )
    def toggle_modal(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open
    

    @dash_app.callback(
    [Output('output-image-upload', 'children'), Output('output-image-path', 'value')],
    [Input('upload-image', 'contents')],
    [State('upload-image', 'filename'), State('upload-image', 'last_modified')]
    )
    def upload_image(contents, filename, last_modified):
        # print(contents)
        if contents:
            # print("contents is true")
            # Decode the image data
            data = contents.split(',')[1]
            image_data = base64.b64decode(data)
            assets_path = 'assets/uploads'


            # Ensure 'uploads' directory exists
            if not os.path.exists(assets_path):
                os.makedirs(assets_path)
            
            # Define the file path
            file_path = os.path.join(assets_path, filename)
                        
            # Save the file
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            # Display uploaded image as feedback
            return html.Img(src=contents, style={'width': '100%'}), file_path

        return "", ""


    # Callback pour gérer la modale
    @dash_app.callback(
        [Output("logout-modal", "is_open"),
        Output("url-redirect", "href")],
        [Input("logout-link", "n_clicks"), Input("confirm-logout", "n_clicks"), Input("cancel-logout", "n_clicks")],
        [State("logout-modal", "is_open"), State("nclicks-store", "data")]
    )
    def toggle_logout_modal(logout_click, confirm_click, cancel_click, is_open, nclicks_data):
        if nclicks_data is None:
            nclicks_data = {"logout_clicks": 0, "confirm_clicks": 0, "cancel_clicks": 0}

        if logout_click and logout_click > nclicks_data["logout_clicks"]:
            nclicks_data["logout_clicks"] = logout_click
            return not is_open, no_update  # Ouvrir la modale

        if cancel_click and cancel_click > nclicks_data["cancel_clicks"]:
            nclicks_data["cancel_clicks"] = cancel_click
            return False, no_update  # Fermer la modale

        if confirm_click and confirm_click > nclicks_data["confirm_clicks"]:
            nclicks_data["confirm_clicks"] = confirm_click
            # return dcc.Location(href="/logout", id="logout-redirect")
            return False, "/logout"
        return is_open, no_update

    # Callback pour stocker les n_clicks
    @dash_app.callback(
        Output('nclicks-store', 'data'),
        [Input("logout-link", "n_clicks"), Input("confirm-logout", "n_clicks"), Input("cancel-logout", "n_clicks")],
        [State('nclicks-store', 'data')]
    )
    def update_nclicks_store(logout_click, confirm_click, cancel_click, nclicks_data):
        if nclicks_data is None:
            nclicks_data = {"logout_clicks": 0, "confirm_clicks": 0, "cancel_clicks": 0}
        return {"logout_clicks": logout_click or 0, "confirm_clicks": confirm_click or 0, "cancel_clicks": cancel_click or 0}

            # Callback to toggle the sidebar
    @dash_app.callback(
        Output("sidebar", "is_open"),
        Input("open-sidebar", "n_clicks"),
        State("sidebar", "is_open"),
    )
    def toggle_sidebar(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open

    def parse_contents(contents, filename):

        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        try:
            if 'xls' in filename:
                df = pd.read_excel(io.BytesIO(decoded))
            else:
                return html.Div(
                    'File format not supported.',
                    className='alert alert-danger'
                )
        except Exception as e:
            return html.Div(
                f'There was an error processing this file: {str(e)}',
                className='alert alert-danger'
            )
        
        try:
            # Créez la colonne "unique_id" en combinant les valeurs de six colonnes
            df['unique_id'] = (
            df['OFFICE'].astype(str) + '_' +
            df['FISCAL_YEAR'].astype(str) + '_' +
            df['MONTH'].astype(str) + '_' +
            df['SOLD_TO'].astype(str) + '_' +
            df['FIRST_NAME'].astype(str) + '_' +
            df['LAST_NAME'].astype(str)
            )
            # Récupérer les unique_id existants dans la base de données
            fetch_data_query = "SELECT unique_id FROM DATA"
            existing_ids = fetch_data(fetch_data_query)
            existing_ids_set = set(existing_ids['unique_id'])
            
            # Filtrer le DataFrame pour ne conserver que les nouveaux enregistrements
            df_to_insert = df[~df['unique_id'].isin(existing_ids_set)]
            
            if not df_to_insert.empty:
                # Insérer les nouveaux enregistrements
                insert_data(df_to_insert, 'DATA', 'append')
            else:
                return html.Div(
                    'No new data to insert. All records already exist in the database.',
                        className='alert alert-info'
                    )
        except Exception as e:
            return html.Div(
                f'An error occurred while inserting data into the database: {str(e)}',
                className='alert alert-danger'
            )
        return html.Div(
            'Data successfully inserted into the database.',
            className='alert alert-success'
        )

    @dash_app.callback(Output('output-data-upload', 'children'),
        [Input('upload-data', 'contents')],
        [State('upload-data', 'filename')])

    def update_output(contents, filename):
        if contents is not None:
            children = parse_contents(contents, filename)
            return children
        # Combined callback to open the modal, load data, and save changes
    @dash_app.callback(
        Output("edit-modal", "is_open"),
        Output("edit-table", "data"),
        Input("edit-button", "n_clicks"),
        Input("save-changes", "n_clicks"),
        State("edit-modal", "is_open"),
        State("edit-table", "data")
    )
    def toggle_modal_edit(edit_n_clicks, save_n_clicks, is_open, table_data):
        ctx = callback_context

        if not ctx.triggered:
            return is_open, no_update

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "edit-button":
            if edit_n_clicks:
                # Load data from database
                query = "SELECT * FROM data"
                
                df = fetch_data(query)
                return not is_open, df.to_dict('records')
            return is_open, no_update
        
        elif button_id == "save-changes":
            if save_n_clicks:
                df = pd.DataFrame(table_data)
                insert_data(df, 'DATA', 'replace')
                return not is_open, no_update
        
        return is_open, no_update

        # Toggle Export Modal
    @dash_app.callback(
        Output("export-modal", "is_open"),
        Input("export-button", "n_clicks"),
        State("export-modal", "is_open")
    )
    def toggle_export_modal(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open

        # Show/Hide Inputs Based on Export Option
    @dash_app.callback(
        [Output('fiscal-year-input', 'style'),
        Output('month-dropdown', 'style')],
        Input('export-option', 'value')
    )
    def toggle_export_inputs(option):
        if option == 'fiscal_year':
            return {'display': 'block'}, {'display': 'none'}  # Show fiscal year input, hide month dropdown
        elif option == 'month':
            return {'display': 'block'}, {'display': 'block'}  # Hide fiscal year input, show month dropdown
        return {'display': 'none'}, {'display': 'none'}  # Hide both by default
    # Export Data
    @dash_app.callback(
        Output("download-dataframe-xlsx", "data"),
        Input('confirm-export', 'n_clicks'),
        State('export-option', 'value'),
        State('fiscal-year-input', 'value'),
        State('month-dropdown', 'value'),
        prevent_initial_call=True
    )
    def export_data(n_clicks, export_option, fiscal_year, month):
        if n_clicks is None:
            return no_update
        if export_option == 'fiscal_year' and fiscal_year:
            if not fiscal_year.isdigit():
                return html.Div(['Please enter a valid fiscal year.'])
            query = f"SELECT * FROM DATA WHERE FISCAL_YEAR = '{fiscal_year}'"
            filename = f"CSI_Data_{fiscal_year}.xlsx"

        elif export_option == 'month' and month and fiscal_year:
            if not fiscal_year.isdigit():
                return html.Div(['Please enter a valid fiscal year.'])

            months_str = ', '.join([f"'{month}'" for month in month])
            query = f"SELECT * FROM DATA WHERE MONTH IN ({months_str}) AND FISCAL_YEAR = '{fiscal_year}'"
            filename = f"CSI_Data_{months_str}_{fiscal_year}.xlsx"
        else:
            query = "SELECT * FROM DATA"
            today = datetime.datetime.today().strftime('%Y-%m-%d')
            filename = f"CSI_All_Data_{today}.xlsx"

        # Retrieve and export data from the database
        try:
            df = fetch_data(query)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            output.seek(0)
            return dcc.send_bytes(output.getvalue(), filename)
        
        except Exception as e:
            return html.Div([
                f'An error occurred while exporting data: {str(e)}'
            ])

    # Callback pour mettre à jour les graphiques en fonction des filtres
    @dash_app.callback(
        [
            Output('line-graph', 'figure'),
            Output('bar-graph', 'figure'),
            Output('pie-graph', 'figure'),
            Output('treemap-graph', 'figure'),
            Output('bar-evolution-graph', 'figure'),
            Output('comments-table', 'data')  # Output to update the table

        ],
        [
            Input('filter-dropdown', 'value'),
            Input('fiscal-year-input-filter', 'value'),
            Input('interval-component', 'n_intervals')
        ]
    )

    def update_graphs(filter_value, fiscal_year, n_intervals):
        fiscal_year_query = f"((FISCAL_YEAR = '{fiscal_year - 1}' and MONTH in ('OCTOBER', 'NOVEMBER', 'DECEMBER') ) OR (FISCAL_YEAR= '{fiscal_year}' and MONTH in ('JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER')))"

        # Dictionnaire pour convertir les mois en nombres
        month_order = {
            'OCTOBER': 1,
            'NOVEMBER': 2,
            'DECEMBER': 3,
            'JANUARY': 4,  
            'FEBRUARY': 5,
            'MARCH': 6,
            'APRIL': 7,
            'MAY': 8,
            'JUNE': 9,
            'JULY': 10,
            'AUGUST': 11,
            'SEPTEMBER': 12
        }

        #Pie graph
        query_pie = f"SELECT OVERALL_SATISFACTION, COUNT(OVERALL_SATISFACTION) AS 'Rating'FROM DATA WHERE OVERALL_SATISFACTION IS NOT NULL AND {fiscal_year_query} GROUP BY OVERALL_SATISFACTION;"
        df = fetch_data(query_pie)
        custom_colors = ['#ff7700', '#ff910c', '#ffaa17', '#ffc322', '#ffdc2d']
        pie_fig = px.pie(df, names='OVERALL_SATISFACTION', values='Rating', title="Overall Satisfaction", color_discrete_sequence=custom_colors )
        pie_fig.update_traces(textfont=dict(color='black')  # Set the font color inside the pie chart to black
        )
        pie_fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
            paper_bgcolor='#1B2131',       # Light gray background for the entire chart
            title_font=dict(size=20, color='white', family="Trebuchet MS"),  # Title font settings
            legend_font=dict(color='white', family="Trebuchet MS"),
            font=dict(color='white', family="Trebuchet MS")
        )
        

        #Tree map
        query_treemap = f"SELECT GLOBAL_CUSTOMER, AVG(CAST(CUSTOMER_SATISFACTION_INDEX AS FLOAT)) 'CSI' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX is not null and {fiscal_year_query} GROUP BY GLOBAL_CUSTOMER;"
        df = fetch_data(query_treemap)
        df['color'] = df['CSI'].apply(lambda x: '#05D5FA' if x > 14 else '#ff7700')
        treemap_fig = px.treemap(df, path=['GLOBAL_CUSTOMER'], values='CSI',
            color='color',  # Use the color column for coloring
            color_discrete_map={'#05D5FA': '#05D5FA', '#ff7700': '#ff7700'},  # Define color mapping
            title="Customer Satisfaction Index Treemap")
        treemap_fig.update_traces(textfont=dict(color='black'))
        treemap_fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
            paper_bgcolor='#1B2131',       # Light gray background for the entire chart
            title_font=dict(size=20,color='white', family="Trebuchet MS"),  # Title font settings
            legend_font=dict(color='black'),
            font=dict(color='black')
        )
            # Query for the comments
        query_comments = f"SELECT OFFICE, FISCAL_YEAR, MONTH, GLOBAL_CUSTOMER, concat(FIRST_NAME, ' ',LAST_NAME) as name, ADDITIONNAL_COMMENTS from DATA WHERE ADDITIONNAL_COMMENTS is not null  AND {fiscal_year_query};"
        comments_df = fetch_data(query_comments)

        # Convert the DataFrame to a list of dictionaries for the DataTable
        table_data = comments_df.to_dict('records')

        if filter_value == 'global':
            #Line graph BY GLOBAL CUSTOMER
            query_line = f"SELECT GLOBAL_CUSTOMER, COUNT(CUSTOMER_SATISFACTION_INDEX) * 100.0 / COUNT(*) AS 'RES-RATE' FROM DATA WHERE {fiscal_year_query} GROUP BY GLOBAL_CUSTOMER;"

            df = fetch_data(query_line)

            area_fig = px.area(
                df, 
                x='GLOBAL_CUSTOMER', 
                y='RES-RATE', 
                labels={'RES-RATE': 'Response Rate (%)'},
                title="Response Rate by Global Customer"
            )
            area_fig.update_traces(line_color='#05D5FA',  marker=dict(color='#05D5FA', size=8, symbol='circle') )
            area_fig.update_layout(
                xaxis_title='',  # Remove the x-axis label 
                plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
                paper_bgcolor='#1B2131',       # Light gray background for the entire chart
                title_font=dict(size=20,color='white', family="Trebuchet MS"),  # Title font settings
                legend_font=dict(color='white'),
                font=dict(color='white')
            )

            #Bar graph BY GLOBAL CUSTOMER
            query_bar = f"SELECT GLOBAL_CUSTOMER, AVG(CAST(CUSTOMER_SATISFACTION_INDEX AS FLOAT)) 'CSI Average' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX is not null and {fiscal_year_query} GROUP BY GLOBAL_CUSTOMER;"
            df = fetch_data(query_bar)

            df['color'] = df['CSI Average'].apply(lambda x: '#05D5FA' if x > 14 else '#ff7700')

            bar_fig = px.bar(df, 
                x='GLOBAL_CUSTOMER', 
                y='CSI Average', 
                color='color',  # Use the color column for coloring
                color_discrete_map={'#05D5FA': '#05D5FA', '#ff7700': '#ff7700'},  # Define color mapping
                title="Customer Satisfaction Index by Global Customer"
            )
            bar_fig.for_each_trace(lambda t: t.update(name='> 14' if t.name == '#05D5FA' else '<= 14'))

            bar_fig.update_layout(
                xaxis_title='',  # Remove the x-axis label 
                plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
                paper_bgcolor='#1B2131',       # Light gray background for the entire chart
                title_font=dict(size=20,color='white', family="Trebuchet MS"),  # Title font settings
                legend_font=dict(color='white'),
                font=dict(color='white')
            )
            #Evolution bar graph BY GLOBAL CUSTOMER
            query_bar = f"SELECT MONTH, GLOBAL_CUSTOMER, AVG(CAST(CUSTOMER_SATISFACTION_INDEX AS FLOAT)) AS 'CSI' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX IS NOT NULL AND {fiscal_year_query} GROUP BY GLOBAL_CUSTOMER, MONTH;"
            df = fetch_data(query_bar)

            df['color'] = df['CSI'].apply(lambda x: 'blue' if x > 14 else 'red')
            df['MONTH_ORDER'] = df['MONTH'].map(month_order)

            # Trier les données par ordre des mois
            df_sorted = df.sort_values(by='MONTH_ORDER')

            bar_evolution_fig = px.bar(df_sorted, 
                x='MONTH', 
                y='CSI', 
                color='GLOBAL_CUSTOMER',  # Use the color column for coloring
                color_discrete_map={'blue': 'blue', 'red': 'red'},  # Define color mapping
                barmode='group',
                title="Customer Satisfaction Index by Global Customer"
            )
            bar_evolution_fig.update_layout(
                xaxis_title='',
                yaxis_title='Customer Satisfaction Index',
                legend_title='Global Customer',
                xaxis_tickangle=-45,
                bargap=0.05,
                plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
                paper_bgcolor='#1B2131',       # Light gray background for the entire chart
                title_font=dict(size=20,color='white', family="Trebuchet MS"),  # Title font settings
                legend_font=dict(color='white'),
                font=dict(color='white')
            )
        elif filter_value == 'ship_to':
            #Line graph
            query_line = f"SELECT SOLD_TO_NAME, COUNT(CUSTOMER_SATISFACTION_INDEX) * 100.0 / COUNT(*) AS 'RES-RATE' FROM DATA WHERE {fiscal_year_query} GROUP BY SOLD_TO_NAME;"
            df = fetch_data(query_line)
            area_fig = px.area(
                df, 
                x='SOLD_TO_NAME', 
                y='RES-RATE', 
                labels={'RES-RATE': 'Response Rate (%)'},
                title="Response Rate by Ship To"
            )
            area_fig.update_traces(line_color='#05D5FA',  marker=dict(color='#05D5FA', size=8, symbol='circle') )
            area_fig.update_layout(
                xaxis_title='',  # Remove the x-axis label 
                plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
                paper_bgcolor='#1B2131',       # Light gray background for the entire chart
                title_font=dict(size=20,color='white', family="Trebuchet MS"),  # Title font settings
                legend_font=dict(color='white'),
                font=dict(color='white')
            )

            #Bar graph
            query_bar = f"SELECT SOLD_TO_NAME, AVG(CAST(CUSTOMER_SATISFACTION_INDEX AS FLOAT)) 'CSI Average' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX is not null and {fiscal_year_query} GROUP BY SOLD_TO_NAME;"
            df = fetch_data(query_bar)
            df['color'] = df['CSI Average'].apply(lambda x: '#05D5FA' if x > 14 else '#ff7700')

            bar_fig = px.bar(df, 
                x='SOLD_TO_NAME', 
                y='CSI Average', 
                color='color',  # Use the color column for coloring
                color_discrete_map={'#05D5FA': '#05D5FA', '#ff7700': '#ff7700'},  # Define color mapping
                title="Customer Satisfaction Index by Ship To"
            )
            bar_fig.for_each_trace(lambda t: t.update(name='> 14' if t.name == '#05D5FA' else '<= 14'))

            bar_fig.update_layout(
                xaxis_title='',  # Remove the x-axis label
                yaxis_title='CSI Average',
                legend_title='Color',
                xaxis_tickangle=-45,
                bargap=0.05,
                plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
                paper_bgcolor='#1B2131',       # Light gray background for the entire chart
                title_font=dict(size=20,color='white', family="Calibri"),  # Title font settings
                legend_font=dict(color='white'),
                font=dict(color='white')
            )
            
            #Evolution bar graph
            query_bar = f"SELECT MONTH, SOLD_TO_NAME, CAST(CUSTOMER_SATISFACTION_INDEX AS FLOAT) AS 'CSI' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX is not null and {fiscal_year_query};"
            df = fetch_data(query_bar)
            # Ajouter une colonne avec l'ordre des mois
            df['MONTH_ORDER'] = df['MONTH'].map(month_order)

            # Trier les données par ordre des mois
            df_sorted = df.sort_values(by='MONTH_ORDER')

            bar_evolution_fig = px.bar(df_sorted, 
                x='MONTH', 
                y= 'CSI',            
                color='SOLD_TO_NAME',  # Use the color column for coloring
                barmode='group',
                title="Customer Satisfaction Index by Ship To"
            )
            bar_evolution_fig.update_layout(
                xaxis_title='Month',
                yaxis_title='Customer Satisfaction Index',
                legend_title='Ship To',
                xaxis_tickangle=-45,
                bargap=0.05,
                plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
                paper_bgcolor='#1B2131',       # Light gray background for the entire chart
                title_font=dict(size=20,color='white', family="Calibri"),  # Title font settings
                legend_font=dict(color='white'),
                font=dict(color='white')  
            ) 
        elif filter_value == 'office':
            #Line graph BY OFFICE
            
            query_line = f"SELECT OFFICE, MONTH, COUNT(CUSTOMER_SATISFACTION_INDEX) * 100.0 / COUNT(*) AS 'RES-RATE' FROM DATA WHERE {fiscal_year_query} GROUP BY MONTH, OFFICE;"
            df = fetch_data(query_line)
            # Ajouter une colonne avec l'ordre des mois
            df['MONTH_ORDER'] = df['MONTH'].map(month_order)

            # Trier les données par ordre des mois
            df_sorted = df.sort_values(by='MONTH_ORDER')

            area_fig = px.area(
                df_sorted, 
                x='MONTH', 
                y='RES-RATE', 
                color='OFFICE',  # Colors will be assigned to each office
                labels={'RES-RATE': 'Response Rate (%)'},
                title="Response Rate by Office",
                color_discrete_sequence=['#00BFFF', '#FFDC2D'],  # Custom color sequence
            )

            area_fig.update_layout(
                xaxis_title='',  # Remove the x-axis label 
                legend_title='Office',
                plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
                paper_bgcolor='#1B2131',       # Dark background for the entire chart
                title_font=dict(size=20, color='white', family="Trebuchet MS"),  # Title font settings
                legend_font=dict(color='white'),
                font=dict(color='white')
            )

            #Bar graph BY OFFICE

            query_bar = f"SELECT OFFICE, AVG(CAST(CUSTOMER_SATISFACTION_INDEX AS FLOAT)) 'CSI' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX is not null and {fiscal_year_query} GROUP BY OFFICE;"
            df = fetch_data(query_bar)
            df['color'] = df['CSI'].apply(lambda x: '#05D5FA' if x > 14 else '#ff7700')

            bar_fig = px.bar(df, 
                x='OFFICE', 
                y='CSI', 
                color='color', 
                color_discrete_map={'#05D5FA': '#05D5FA', '#ff7700': '#ff7700'}, 
                title="Customer Satisfaction Index Average by Office"
            )
            bar_fig.for_each_trace(lambda t: t.update(name='> 14' if t.name == '#05D5FA' else '<= 14'))

            bar_fig.update_layout(
                xaxis_title='',  # Remove the x-axis label
                yaxis_title='CSI',
                legend_title='Color',
                xaxis_tickangle=-45,
                bargap=0.05,
                plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
                paper_bgcolor='#1B2131',       # Light gray background for the entire chart
                title_font=dict(size=20,color='white', family="Calibri"),  # Title font settings
                legend_font=dict(color='white'),
                font=dict(color='white') 
            )
            
            #Evolution bar graph BY OFFICE
            query_bar = f"SELECT MONTH, OFFICE, AVG(CAST(CUSTOMER_SATISFACTION_INDEX AS FLOAT)) AS 'CSI' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX IS NOT NULL AND {fiscal_year_query} GROUP BY OFFICE, MONTH;"
            df = fetch_data(query_bar)
            # Ajouter une colonne avec l'ordre des mois
            df['MONTH_ORDER'] = df['MONTH'].map(month_order)

            # Trier les données par ordre des mois
            df_sorted = df.sort_values(by='MONTH_ORDER')
            bar_evolution_fig = px.bar(df_sorted, 
                x='MONTH', 
                y='CSI', 
                color='OFFICE',  # Use the color column for coloring
                barmode='group',
                title="Customer Satisfaction Index by Office",
                color_discrete_sequence=['#00BFFF', '#ffaa17'],
            )
            bar_evolution_fig.update_layout(
                xaxis_title='Month',
                yaxis_title='Customer Satisfaction Index',
                legend_title='Office',
                xaxis_tickangle=-45,
                bargap=0.05,
                plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
                paper_bgcolor='#1B2131',       # Light gray background for the entire chart
                title_font=dict(size=20,color='white', family="Calibri"),  # Title font settings
                legend_font=dict(color='white'),
                font=dict(color='white') 

            )    



        return area_fig, bar_fig, pie_fig, treemap_fig, bar_evolution_fig, table_data

    @dash_app.callback(
        Output("download-graphs-dataframe-xlsx", "data"),
        [Input("export-pie", "n_clicks"),
        Input("export-line", "n_clicks"),
        Input("export-bar", "n_clicks"),
        Input("export-treemap", "n_clicks"),
        Input("export-evolution-bar", "n_clicks"),
        Input("export-comments", "n_clicks")],
        [State('line-graph', 'figure'),
        State('bar-graph', 'figure'),
        State('pie-graph', 'figure'),
        State('treemap-graph', 'figure'),
        State('bar-evolution-graph', 'figure'),
        State('comments-table', 'data'),
        State('filter-dropdown', 'value'),
        State('fiscal-year-input-filter', 'value')],
        prevent_initial_call=True
    )
    def export_graph_data(export_pie, export_line, export_bar, export_treemap, export_evolution_bar, export_comments,
                        area_fig, bar_fig, pie_fig, treemap_fig, bar_evolution_fig, table_data,
                        filter_value, fiscal_year):
        
        # Déterminer quel bouton a été cliqué
        ctx = callback_context

        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        
        month_order = {
            'JANUARY': 1,
            'FEBRUARY': 2,
            'MARCH': 3,
            'APRIL': 4,
            'MAY': 5,
            'JUNE': 6,
            'JULY': 7,
            'AUGUST': 8,
            'SEPTEMBER': 9,
            'OCTOBER': 10,
            'NOVEMBER': 11,
            'DECEMBER': 12
        }
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        fiscal_year_query = f"((FISCAL_YEAR = '{fiscal_year - 1}' and MONTH in ('OCTOBER', 'NOVEMBER', 'DECEMBER') ) OR (FISCAL_YEAR= '{fiscal_year}' and MONTH in ('JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER')))"

        # Construire la condition WHERE basée sur les filtres
        if filter_value == 'office':
            filter_column = 'OFFICE'
            line_query = f"SELECT OFFICE, MONTH, COUNT(CUSTOMER_SATISFACTION_INDEX) * 100.0 / COUNT(*) AS 'RESPONSE_RATE' FROM DATA WHERE {fiscal_year_query} GROUP BY MONTH, OFFICE ORDER BY OFFICE;"
            bar_query = f"SELECT OFFICE, AVG(CAST(CUSTOMER_SATISFACTION_INDEX AS FLOAT)) 'CSI' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX is not null and {fiscal_year_query} GROUP BY OFFICE;"
            evolution_bar_query = f"SELECT MONTH, OFFICE, AVG(CUSTOMER_SATISFACTION_INDEX) AS 'CSI' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX IS NOT NULL AND {fiscal_year_query} GROUP BY OFFICE, MONTH;"

        elif filter_value == 'ship_to':
            filter_column = 'SOLD_TO_NAME'
            line_query = f"SELECT {filter_column}, COUNT(CUSTOMER_SATISFACTION_INDEX) * 100.0 / COUNT(*) AS 'RESPONSE_RATE' FROM DATA WHERE {fiscal_year_query} GROUP BY {filter_column}"
            bar_query = f"SELECT {filter_column}, AVG(CAST(CUSTOMER_SATISFACTION_INDEX AS FLOAT)) AS 'CSI Average' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX is not null and {fiscal_year_query} GROUP BY {filter_column}"
            evolution_bar_query = f"SELECT MONTH, {filter_column}, CUSTOMER_SATISFACTION_INDEX AS 'CSI' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX is not null and {fiscal_year_query} ORDER {filter_column};"

        elif filter_value == 'global':
            filter_column = 'GLOBAL_CUSTOMER'
            line_query = f"SELECT {filter_column}, COUNT(CUSTOMER_SATISFACTION_INDEX) * 100.0 / COUNT(*) AS 'RESPONSE_RATE' FROM DATA WHERE {fiscal_year_query} GROUP BY {filter_column}"
            bar_query = f"SELECT {filter_column}, AVG(CAST(CUSTOMER_SATISFACTION_INDEX AS FLOAT)) AS 'CSI Average' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX is not null and {fiscal_year_query} GROUP BY {filter_column}"
            evolution_bar_query = f"SELECT MONTH, {filter_column}, CUSTOMER_SATISFACTION_INDEX AS 'CSI' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX is not null and {fiscal_year_query} ORDER BY {filter_column};"

        else:
            filter_column = None
        

        
        # Sélectionner les données en fonction du bouton cliqué et du filtre
        if button_id == "export-pie":
            pie_query = f"SELECT OVERALL_SATISFACTION, COUNT(OVERALL_SATISFACTION) AS 'Rating' FROM DATA WHERE OVERALL_SATISFACTION IS NOT NULL AND {fiscal_year_query} GROUP BY OVERALL_SATISFACTION;"
            df = fetch_data(pie_query)
            filename = f"Pie_Graph_Data_{fiscal_year}.xlsx"
        
        elif button_id == "export-treemap":
            treemap_query = f"SELECT GLOBAL_CUSTOMER, AVG(CAST(CUSTOMER_SATISFACTION_INDEX AS FLOAT)) 'CSI' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX is not null and {fiscal_year_query} GROUP BY GLOBAL_CUSTOMER;"
            df = fetch_data(treemap_query)
            filename = f"Treemap_Graph_Data_{fiscal_year}.xlsx"
        
        elif button_id == "export-comments":
            comments_query = f"SELECT OFFICE, FISCAL_YEAR, MONTH, GLOBAL_CUSTOMER, concat(FIRST_NAME, ' ',LAST_NAME) as name, ADDITIONNAL_COMMENTS from DATA WHERE ADDITIONNAL_COMMENTS is not null  AND {fiscal_year_query};"
            df = fetch_data(comments_query)
            df['MONTH_ORDER'] = df['MONTH'].map(month_order)
            df = df.sort_values(by='MONTH_ORDER')

            filename = f"Comments_{fiscal_year}.xlsx"
        
        elif button_id == "export-line":
            df = fetch_data(line_query)
            if filter_value == 'office':
                df['MONTH_ORDER'] = df['MONTH'].map(month_order)
                df = df.sort_values(by='MONTH_ORDER')

            filename = f"Line_Graph_Data_{filter_column}_{fiscal_year}.xlsx"
        
        elif button_id == "export-bar":
            df = fetch_data(bar_query)
            filename = f"Bar_Graph_Data_{filter_column}_{fiscal_year}.xlsx"


        elif button_id == "export-evolution-bar":
            df = fetch_data(evolution_bar_query)
            df['MONTH_ORDER'] = df['MONTH'].map(month_order)
            df = df.sort_values(by='MONTH_ORDER')
            filename = f"Evolution_Bar_Graph_Data_{filter_column}_{fiscal_year}.xlsx"
        
        # Exporter les données au format Excel
        return dcc.send_data_frame(df.to_excel, filename, sheet_name="Sheet1", index=False)


