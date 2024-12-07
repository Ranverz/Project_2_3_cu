from flask import Flask, render_template, request
from process_weather import get_forecast_by_lat_lon, define_if_weather_is_bad, get_coords_by_address

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('main.html')

@app.route('/weather-result', methods=['POST'])
def submit_route():
    # Получаем данные из формы
    start = request.form.get('start')
    end = request.form.get('end')

    cords_start = get_coords_by_address(start)
    lon_start = cords_start['lon']
    lat_start = cords_start['lat']
    adr_start = cords_start['res_adr']

    cords_end = get_coords_by_address(end)
    lon_end = cords_end['lon']
    lat_end = cords_end['lat']
    adr_end = cords_end['res_adr']

    forecast_start = get_forecast_by_lat_lon(lat_start, lon_start)
    forecast_end = get_forecast_by_lat_lon(lat_end, lon_end)

    if forecast_start == 'cant access geodata' or forecast_start == 'cant get forecast data':
        return f"<h1>Ошибка: {forecast_start}</h1>"
    else:
        temp_start = round((forecast_start['temp']['min'] + forecast_start['temp']['max']) / 2)
        wind_speed_start = forecast_start['wind_speed']
        rain_prob_start = forecast_start['rain_prob']
        result_start = define_if_weather_is_bad(temp_start, wind_speed_start, rain_prob_start)

    if forecast_end == 'cant access geodata' or forecast_end == 'cant get forecast data':
        return f"<h1>Ошибка: {forecast_end}</h1>"
    else:
        temp_end = round((forecast_end['temp']['min'] + forecast_end['temp']['max']) / 2)
        wind_speed_end = forecast_end['wind_speed']
        rain_prob_end = forecast_end['rain_prob']
        result_end = define_if_weather_is_bad(temp_end, wind_speed_end, rain_prob_end)

    # Обрабатываем данные
    if start and end:
        if result_start == 'weather is good':
            text_res_start = f'хорошая'
        else:
            text_res_start = f'плохая'

        if result_end == 'weather is good':
            text_res_end = f'хорошая'
        else:
            text_res_end = f'плохая'


        return render_template('weather.html',
                               start=adr_start, end=adr_end,

                               text_res_start=text_res_start,
                               temp_start=temp_start,
                               wind_speed_start=wind_speed_start,
                               rain_prob_start=rain_prob_start,
                               adr_start=adr_start,

                               text_res_end=text_res_end,
                               temp_end=temp_end,
                               wind_speed_end=wind_speed_end,
                               rain_prob_end=rain_prob_end,
                               adr_end=adr_end,)
    else:
        return "<h1>Ошибка: Не все поля заполнены!</h1>"


if __name__ == '__main__':
    app.run(debug=True)
