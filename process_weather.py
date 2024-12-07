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

