import requests

weather_key = 'Hz0V96PzSdHT9Bbj1UpGKLcv1WQkGa4w'  #вставьте свой код от accuweather

maps_key = '182f8bbf-48db-450e-a902-b5134e510539' #вставьте свой код от геокодера яндекса


def get_coords_by_address(address: str):
    # находит ближайшее совпадение с введенным пользователем адресом, учитывая частые ошибки.
    # "При этом учитываются распространенные опечатки и предлагается несколько подходящих вариантов."
    # https://yandex.ru/dev/geocode/doc/ru/


    maps_url = 'https://geocode-maps.yandex.ru/1.x/'
    params = {
        'apikey': maps_key,
        'geocode': address,
        'format': 'json',
    }

    response = requests.get(maps_url, params=params)
    if response.status_code == 200:
        lon, lat = response.json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos'].split()
        res_adr = response.json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']
        return {'req_adr': address,
                'res_adr' : res_adr,
                'lon': lon,
                'lat': lat}
    else:
        return f'not a valid address code: {response.status_code}'

def get_geopos_by_lat_lon(lat, lon):
    geo_url = 'http://dataservice.accuweather.com/locations/v1/cities/geoposition/search'
    params = {
        'apikey': weather_key,
        'q': f'{lat},{lon}',
    }
    try:
        response = requests.get(geo_url, params=params)
    except:
        return 'cant access geodata'
    return response.json()['Key'] #str


def get_forecast_by_lat_lon(lat, lon):
    lockey = get_geopos_by_lat_lon(lat, lon)
    if lockey != 'cant access geodata':
        forecast_url = f'http://dataservice.accuweather.com/forecasts/v1/daily/5day/{lockey}'
        params = {
            'apikey': weather_key,
            'details': True,
            'metric': True,
        }
        try:
            response = requests.get(forecast_url, params=params)
        except:
            return 'cant get forecast data'

        data = []


        for day in response.json()['DailyForecasts']:
            temp_min = day['Temperature']['Minimum']['Value']
            temp_max = day['Temperature']['Maximum']['Value']

            humidity_procent_max = day['Day']['RelativeHumidity']['Maximum']
            humidity_procent_avg = day['Day']['RelativeHumidity']['Average']
            humidity_procent_min = day['Day']['RelativeHumidity']['Minimum']

            wind_speed = day['Day']['Wind']['Speed']['Value']

            rain_prob = day['Day']['RainProbability']

            data.append(
                {
                    'temp': {'min': temp_min, 'max': temp_max},
                    'humidity_procent': {'min': humidity_procent_min, 'max': humidity_procent_max,
                                         'avg': humidity_procent_avg},
                    'wind_speed': wind_speed,
                    'rain_prob': rain_prob,
                }
            )

        return data

    else:
        return 'cant access geodata'


def define_if_weather_is_bad(temp, wind_speed, rain_prob):
  if 0 < temp < 35:
    if wind_speed < 11:
      if rain_prob < 70:
        return 'weather is good'
  return 'weather is bad'