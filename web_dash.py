import dash_bootstrap_components as dbc
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State
import pandas as pd
from process_weather import get_forecast_by_lat_lon, get_coords_by_address


app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server  # Expose server for deployment

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
            dbc.Button("Сохранить", id='save-points-button', className='ml-auto')
        )
    ],
    id='intermediate-points-modal',
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
app.layout.children.append(
    dcc.Store(id='weather-data-store')
)

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

    card = dbc.Card([
        dbc.CardHeader(f"Погода в {address}"),
        dbc.CardBody(forecast_cards)
    ])
    return card


# Callback to open the modal
@app.callback(
    Output('intermediate-points-modal', 'is_open'),
    Input('add-point-button', 'n_clicks'),
    Input('save-points-button', 'n_clicks'),
    State('intermediate-points-modal', 'is_open'),
    State('intermediate-points-input', 'value')
)
def toggle_modal(add_clicks, save_clicks, is_open, points_input):
    if add_clicks:
        return True
    if save_clicks:
        return False
    return is_open


# Update weather data callback to include intermediate points
@app.callback(
    [Output('output-weather', 'children'),
     Output('weather-data-store', 'data'),
     Output('graph-container', 'style')],
    Input('submit-button', 'n_clicks'),
    [State('start-input', 'value'),
     State('end-input', 'value'),
     State('days-selector', 'value'),
     State('intermediate-points-input', 'value')]
)
def update_weather_data(n_clicks, start, end, days, intermediate_points):
    if n_clicks > 0:
        if not start or not end:
            return dbc.Alert("Ошибка: Не все поля заполнены!", color="danger"), {}, {'display': 'none'}

        addresses = [start, end]

        # Process intermediate points entered by the user
        if intermediate_points:
            addresses += [point.strip() for point in intermediate_points.split(',')]

        weather_data = {'addresses': [], 'forecast': []}

        for address in addresses:
            coords = get_coords_by_address(address)
            forecast = get_forecast_by_lat_lon(coords['lat'], coords['lon'])
            weather_data['addresses'].append(coords['res_adr'])
            weather_data['forecast'].append(forecast[:days])


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
    days = len(weather_data['forecast'][0])  # Количество дней, на которое получен прогноз
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

    # Для каждого дня добавляем столбцы с данными (для каждого параметра)
    for i in range(days):
        data_df[f'Day {i + 1}'] = [forecast[i] for forecast in selected_data]

    # Create the graph
    fig = px.bar(data_df, x='addresses', y=[f'Day {i + 1}' for i in range(days)], title=title)
    fig.update_layout(
        xaxis_title="Адрес",
        yaxis_title=title,
        barmode='group',  # Устанавливаем, чтобы бары были расположены рядом
    )

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)