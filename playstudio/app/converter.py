import json
from dateutil import parser
from datetime import datetime

def event_converter(row, datafile_date):
    data = json.loads(row)
    ret = {}
    ret['datafile_date'] = datafile_date
    ret['id'] = data.get('id')
    ret['event_time'] = parser.parse(data.get('EvtDatetime')).strftime("%Y-%m-%d %H:%M:%S")
    ret['play_bet'] = data.get('play').get('bet')
    ret['play_win'] = data.get('play').get('win')
    ret['altid_supid'] = data.get('altId').get('supId')
    ret['altid_socid'] = data.get('altId').get('socId')
    ret['device_id'] = data.get('device').get('id')
    ret['device_id_type_os'] = data.get('device').get('type').get("OS")
    ret['device_id_type_model'] = data.get('device').get('type').get("Model", "")
    ret['device_platform'] = data.get('device').get('platform', "")

    return list(ret.values())

def player_converter(row, datafile_date):
    data = json.loads(row)
    ret = {}
    ret['datafile_date'] = datafile_date
    ret['id'] = data.get('id')
    ret['login_date'] = data.get('LoginDate')
    ret['install_date'] = data.get('InstallDate')
    ret['revenue'] = data.get('Revenue')

    return list(ret.values())
