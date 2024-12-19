import requests

weather_key = ''  #вставьте свой код от accuweather

maps_key = '' #вставьте свой код от геокодера яндекса


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
        return 'not a valid address'

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
        forecast_url = f'http://dataservice.accuweather.com/forecasts/v1/daily/1day/{lockey}'
        params = {
            'apikey': weather_key,
            'details': True,
            'metric': True,
        }
        try:
            response = requests.get(forecast_url, params=params)
        except:
            return 'cant get forecast data'
    else:
        return 'cant access geodata'

    temp_min = response.json()['DailyForecasts'][0]['Temperature']['Minimum']['Value']
    temp_max = response.json()['DailyForecasts'][0]['Temperature']['Maximum']['Value']

    humidity_procent_max = response.json()['DailyForecasts'][0]['Day']['RelativeHumidity']['Maximum']
    humidity_procent_avg = response.json()['DailyForecasts'][0]['Day']['RelativeHumidity']['Average']
    humidity_procent_min = response.json()['DailyForecasts'][0]['Day']['RelativeHumidity']['Minimum']

    wind_speed = response.json()['DailyForecasts'][0]['Day']['Wind']['Speed']['Value']

    rain_prob = response.json()['DailyForecasts'][0]['Day']['RainProbability']
    return {
        'temp': {'min': temp_min, 'max': temp_max},
        'humidity_procent': {'min': humidity_procent_min, 'max': humidity_procent_max, 'avg': humidity_procent_avg},
        'wind_speed': wind_speed,
        'rain_prob': rain_prob,
    }

def define_if_weather_is_bad(temp, wind_speed, rain_prob):
  if 0 < temp < 35:
    if wind_speed < 11:
      if rain_prob < 70:
        return 'weather is good'
  return 'weather is bad'