import dash_bootstrap_components as dbc
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State, callback_context
import pandas as pd
from project_n3.process_weather import get_forecast_by_lat_lon, get_coords_by_address
import plotly.graph_objects as go

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# Navbar
navbar = dbc.NavbarSimple(
    brand="Прогноз погоды по маршруту",
    brand_href="#",
    color="primary",
    dark=True,
    className="mb-4"
)

# Modal for entering intermediate points
modal = dbc.Modal(
    [
        dbc.ModalHeader("Введите промежуточные точки"),
        dbc.ModalBody(
            dbc.Input(id='intermediate-points-input', type='text', placeholder='Введите адреса через запятую')
        ),
        dbc.ModalFooter(
            dbc.Button("Сохранить", id='save-points-button', className='ml-auto', n_clicks=0)
        )
    ],
    id='intermediate-points-modal',
    is_open=False,
    size='lg',
)

# Input Section
input_section = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Label("Начальная точка:", style={'fontWeight': 'bold'}),
            dbc.Input(id='start-input', type='text', placeholder='Введите адрес'),
        ], width=6),
        dbc.Col([
            html.Label("Конечная точка:", style={'fontWeight': 'bold'}),
            dbc.Input(id='end-input', type='text', placeholder='Введите адрес'),
        ], width=6),
    ], className="mb-3"),
    dbc.Row([
        dbc.Col([
            html.Label("Количество дней для прогноза:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='days-selector',
                options=[
                    {'label': '1 день', 'value': 1},
                    {'label': '3 дня', 'value': 3},
                    {'label': '5 дней', 'value': 5}
                ],
                value=5,
                clearable=False,
                style={'color': '#000'}
            ),
        ], width=6),
        dbc.Col([
            dbc.Button("Добавить промежуточные точки", id='add-point-button', color='secondary', n_clicks=0)
        ], width=6),
    ], className="mb-3"),
    dbc.Row([
        dbc.Col([
            dbc.Button("Получить прогноз", id='submit-button', color='success', n_clicks=0, className='mt-2'),
        ], width={"size": 2, "offset": 5})
    ])
])

map_section = dbc.Row([dcc.Graph(id='route-map', style={'height': '600px', 'width': '100%'})])

# Layout
app.layout = dbc.Container([
    navbar,
    input_section,
    modal,
    dcc.Loading(
        id="loading-spinner",
        type="circle",
        children=[
            html.Div(id='output-weather', className="mt-4"),
            map_section,
            html.Div(id='graph-container', children=[
                dcc.Dropdown(
                    id='graph-selector',
                    options=[
                        {'label': 'Температура', 'value': 'temp'},
                        {'label': 'Скорость ветра', 'value': 'wind'},
                        {'label': 'Вероятность осадков', 'value': 'rain'}
                    ],
                    value='temp',
                    multi=False,
                    placeholder="Выберите параметр...",
                    style={'color': '#000'}
                ),
                dcc.Graph(id='weather-graph', style={'marginTop': '20px'})
            ], style={'display': 'none'})
        ]
    )
], fluid=True)

# Store addresses and weather data in hidden divs
app.layout.children.append(dcc.Store(id='weather-data-store'))


def generate_weather_card(address, weather_data, index, days):
    forecast = weather_data['forecast'][index]
    forecast_cards = []

    for day in range(days):
        temp_avg = round((forecast[day]['temp']['min'] + forecast[day]['temp']['max']) / 2)
        forecast_cards.append(
            html.Div([
                html.H5(f"День {day + 1}"),
                html.P(f"Средняя температура: {temp_avg}°C"),
                html.P(f"Скорость ветра: {forecast[day]['wind_speed']} м/с"),
                html.P(f"Вероятность осадков: {forecast[day]['rain_prob']}%"),
            ])
        )

    card = dbc.Card([dbc.CardHeader(f"Погода в {address}"), dbc.CardBody(forecast_cards)])
    return card


# Callback to open the modal
@app.callback(
    Output('intermediate-points-modal', 'is_open'),
    Input('add-point-button', 'n_clicks'),
    Input('save-points-button', 'n_clicks'),
    State('intermediate-points-modal', 'is_open'),
    State('intermediate-points-input', 'value')
)
def toggle_modal(add_clicks, save_clicks, is_open, intermediate_points_value):
    ctx = callback_context

    if not ctx.triggered:
        return is_open

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'add-point-button':
        return True
    elif trigger_id == 'save-points-button':
        return False

    return is_open


# Update weather data callback to include intermediate points
@app.callback(
    [Output('output-weather', 'children'), Output('weather-data-store', 'data'), Output('graph-container', 'style')],
    Input('submit-button', 'n_clicks'),
    [State('start-input', 'value'), State('end-input', 'value'), State('days-selector', 'value'),
     State('intermediate-points-input', 'value')]
)
def update_weather_data(n_clicks, start, end, days, intermediate_points):
    if n_clicks > 0:
        if not start or not end:
            return dbc.Alert("Ошибка: Не все поля заполнены!", color="danger"), {}, {'display': 'none'}

        addresses = [start]
        if intermediate_points:
            addresses += [point.strip() for point in intermediate_points.split(',')]
        addresses.append(end)

        weather_data = {'addresses': [], 'forecast': [], 'coordinates': []}

        for address in addresses:
            coords = get_coords_by_address(address)
            if coords != 'not a valid address':
                forecast = get_forecast_by_lat_lon(coords['lat'], coords['lon'])
                if forecast == 'cant access geodata(out of limit)':
                    return dbc.Alert("Ошибка: невозможно получить прогноз, превышен лимит доступа к геоданным.",
                                     color="danger"), {}, {'display': 'none'}

                # Assuming forecast is valid here
                weather_data['addresses'].append(coords['res_adr'])
                weather_data['coordinates'].append({'lat': coords['lat'], 'lon': coords['lon']})
                weather_data['forecast'].append(forecast[:days])
            else:
                return dbc.Alert("Ошибка: не корректный адрес", color="danger"), {}, {'display': 'none'}

        cards = [generate_weather_card(address, weather_data, i, days) for i, address in
                 enumerate(weather_data['addresses'])]

        return dbc.Row([dbc.Col(card, width=12) for card in cards]), weather_data, {'display': 'block'}

    return html.Div(), {}, {'display': 'none'}


@app.callback(
    Output('weather-graph', 'figure'),
    Input('weather-data-store', 'data'),
    Input('graph-selector', 'value')
)
def update_weather_graph(weather_data, selected_param):
    if not weather_data:
        # Return an empty chart while data is being fetched
        empty_df = pd.DataFrame({'addresses': [], 'values': []})
        return px.bar(empty_df, x='addresses', y='values', title="Загрузка данных...")

    # Create graph based on selected parameter
    addresses = weather_data['addresses']

    days = len(weather_data['forecast'][0])  # days for forecasting
    selected_data = []

    if selected_param == 'temp':
        for forecast in weather_data['forecast']:
            selected_data.append([round((day['temp']['min'] + day['temp']['max']) / 2) for day in forecast])
        title = "Температура (°C)"

    elif selected_param == 'wind':
        for forecast in weather_data['forecast']:
            selected_data.append([day['wind_speed'] for day in forecast])
        title = "Скорость ветра (м/с)"

    else:
        for forecast in weather_data['forecast']:
            selected_data.append([day['rain_prob'] for day in forecast])
        title = "Вероятность осадков (%)"

    # Create a DataFrame for the data
    data_df = pd.DataFrame({'addresses': addresses})

    for i in range(days):
        data_df[f'День {i + 1}'] = [forecast[i] for forecast in selected_data]

    # Create the graph
    fig = px.bar(data_df, x='addresses', y=[f'День {i + 1}' for i in range(days)], title=title)


    fig.update_layout(
        xaxis_title="Адрес",
        yaxis_title=title,
        legend_title_text='День',
        barmode='group',
        plot_bgcolor='rgb(64, 64, 64)',  # Dark background
        paper_bgcolor='rgb(64, 64, 64)',  # Dark background for paper
        font=dict(color='white'),  # White text color for better visibility on dark background
        title_font=dict(color='white')  # Title font color
    )


    return fig


@app.callback(
    [Output('route-map', 'figure'), Output('route-map', 'style')],
    Input('submit-button', 'n_clicks'),
    [State('start-input', 'value'), State('end-input', 'value'), State('intermediate-points-input', 'value'),
     State('days-selector', 'value')]
)
def update_map(n_clicks, start, end, intermediate_points, days):
    if n_clicks > 0:
        if not start or not end:
            return {}, {'display': 'none'}  # Hide map if fields are empty

        # Get addresses
        addresses = [start]
        if intermediate_points:
            addresses += [point.strip() for point in intermediate_points.split(',')]
        addresses.append(end)

        # Get coordinates and weather data for each address
        coordinates = []
        weather_data = {'addresses': [], 'forecast': [], 'coordinates': []}

        for address in addresses:
            coords = get_coords_by_address(address)
            if coords and all(k in coords for k in ('lat', 'lon')):
                coordinates.append({
                    "lat": coords['lat'],
                    "lon": coords['lon'],
                    "address": coords['res_adr']
                })
                weather_data['addresses'].append(coords['res_adr'])
                weather_data['coordinates'].append({'lat': coords['lat'], 'lon': coords['lon']})
                forecast = get_forecast_by_lat_lon(coords['lat'], coords['lon'])
                weather_data['forecast'].append(forecast[:days])
            else:
                return dbc.Alert(f"Не удалось получить координаты для адреса: {address}", color="danger"), {
                    'display': 'none'}

        # Ensure coordinates are in correct format: separate lat and lon
        df = pd.DataFrame(coordinates)

        # Check if lat/lon are numeric and filter out invalid coordinates (NaN values)
        df[['lat', 'lon']] = df[['lat', 'lon']].apply(pd.to_numeric, errors='coerce')
        df.dropna(subset=['lat', 'lon'], inplace=True)

        # Prepare the data for hover tool
        weather_info = []
        for i, address in enumerate(weather_data['addresses']):
            forecast_info = []
            for day in range(days):
                temp_avg = round((weather_data['forecast'][i][day]['temp']['min'] +
                                  weather_data['forecast'][i][day]['temp']['max']) / 2)
                forecast_info.append(f"День {day + 1}: Средняя температура: {temp_avg}°C,"
                                     f" Скорость ветра: {weather_data['forecast'][i][day]['wind_speed']} м/с,"
                                     f" Вероятность осадков: {weather_data['forecast'][i][day]['rain_prob']}%")
            weather_info.append(forecast_info)

        # Create the map figure
        fig = px.scatter_mapbox(
            df,
            lat='lat',
            lon='lon',
            hover_name='address',
            hover_data={'address': False},
            zoom=5,
            height=600,
            title="Маршрут и погодные условия"
        )

        # Add the route line (connecting the points)
        fig.add_trace(go.Scattermapbox(
            lat=df['lat'],
            lon=df['lon'],
            mode='lines+markers',
            marker=dict(size=10, color='red'),
            line=dict(width=2, color='blue'),
            name="Маршрут"
        ))

        # Add custom hover data (using the weather info)
        for i, info in enumerate(weather_info):
            fig.add_trace(go.Scattermapbox(
                lat=[df['lat'].iloc[i]],
                lon=[df['lon'].iloc[i]],
                text=[f"<b style='color: white;'>{weather_data['addresses'][i]}</b><br>{'<br>'.join(info)}"],
                mode='markers',
                marker=dict(size=10, color='blue'),
                name=weather_data['addresses'][i]
            ))

        fig.update_layout(mapbox_style='open-street-map',
                          plot_bgcolor='rgb(64, 64, 64)',  # Dark background
                          paper_bgcolor='rgb(64, 64, 64)',
                          title_font_color='white',
                          legend_font_color='white',
                          )

        return fig, {'display': 'block'}

    return {}, {'display': 'none'}


if __name__ == '__main__':
    app.run_server(debug=True)
