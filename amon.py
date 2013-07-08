#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import os
import sys
import urllib
import uuid

import times
from ooop import OOOP

CUPS_CACHE = {}
DEVICE_MP_REL = {}
CUPS_UUIDS = {}
PARTNERS = []
UNITS = {'1': '', '1000': 'k'}

REST_SERVER = 'http://localhost:5000'


def make_uuid(model, model_id):
    token = '%s,%s' % (model, model_id)
    return str(uuid.uuid5(uuid.NAMESPACE_OID, token))


def make_post_data(json_list):
    post_data = {}
    for idx, item in enumerate(json_list):
        post_data['item%s' % idx] = item
    return urllib.urlencode(post_data)

def get_device_serial(device_id):
    return device_id[3:].lstrip('0')

def get_cups_from_device(device_id):
    # Remove brand prefix and right zeros
    serial = get_device_serial(device_id)
    if serial in CUPS_CACHE:
        return CUPS_CACHE[serial]
    else:
        # Search de meter
        cid = O.GiscedataLecturesComptador.search([('name', '=', serial)])
        if not cid:
            res = False
        else:
            cid = O.GiscedataLecturesComptador.get(cid[0])
            res = make_uuid('giscedata.cups.ps', cid.polissa.cups.name)
            CUPS_UUIDS[res] = cid.polissa.cups.id
        CUPS_CACHE[serial] = res
        return res
        

def make_utc_timestamp(timestamp):
    return times.to_universal(timestamp, 'Europe/Madrid').isoformat('T') + 'Z'

def get_street_name(cups):
    street = []
    street_name = u''
    if cups.cpo or cups.cpa:
        street = u'CPO %s CPA %s' % (cups.cpo, cups.cpa)
    else:
        if cups.tv:
            street.append(cups.tv.name)
        if cups.nv:
            street.append(cups.nv)
        street_name += u' '.join(street)
        street = [street_name]
        for f_name, f in [(u'número', 'pnp'), (u'escalera', 'es'),
                          (u'planta', 'pt'), (u'puerta', 'pu')]:
            val = getattr(cups, f)
            if val:
                street.append(u'%s %s' % (f_name, val))
    street_name = ', '.join(street)
    return street_name

def datestring_to_epoch(date_string):
    if not date_string:
        return None
    if not isinstance(date_string, datetime):
        dt = datetime.strptime(date_string, '%Y-%m-%d')
    else:
        dt = date_string
    return dt.strftime('%s')

def remove_none(struct, context=None):
    if not context:
        context = {}
    if 'xmlrpc' in context:
        return struct
    converted = struct.copy()
    for key, value in struct.items():
        if isinstance(value, dict):
            converted[key] = remove_none(value)
        else:
            if value is None or (isinstance(value, bool) and not value):
                del converted[key]
    return converted

def profile_to_amon(profiles):
    """Return a list of AMON readinds.

    {
        "deviceId": "c1810810-0381-012d-25a8-0017f2cd3574",
        "meteringPointId": "c1759810-90f3-012e-0404-34159e211070",
        "readings": [
            {
                "type": "electricityConsumption",
                "unit": "kWh",
                "period": "INSTANT",
            },
            {
                "type": "electricityKiloVoltAmpHours",
                "unit": "kVArh",
                "period": "INSTANT",
            }
        ],
        "measurements": [
            {
                "type": "electricityConsumption",
                "timestamp": "2010-07-02T11:39:09Z", # UTC
                "value": 7
            },
            {
                "type": "electricityKiloVoltAmpHours",
                "timestamp": "2010-07-02T11:44:09Z", # UTC
                "value": 6
            }
        ]
    }
    """
    res = []
    if not hasattr(profiles, '__iter__'):
        profiles = [profiles]
    for profile in profiles:
        mp_uuid = get_cups_from_device(profile['name'])
        if not mp_uuid:
            continue
        device_uuid = make_uuid('giscedata.lectures.comptador', profile['name'])
        DEVICE_MP_REL[device_uuid] = mp_uuid
        res.append({
            "deviceId": device_uuid,
            "meteringPointId": mp_uuid,
            "readings": [
                {
                    "type":  "electricityConsumption",
                    "unit": "%sWh" % UNITS[profile['magn']],
                    "period": "INSTANT",
                },
                {
                    "type": "electricityKiloVoltAmpHours",
                    "unit": "%sVArh" % UNITS[profile['magn']],
                    "period": "INSTANT",
                }
            ],
            "measurements": [
                {
                    "type": "electricityConsumption",
                    "timestamp": make_utc_timestamp(profile['timestamp']),
                    "value": profile['ai']
                },
                {
                    "type": "electricityKiloVoltAmpHours",
                    "timestamp": make_utc_timestamp(profile['timestamp']),
                    "value": profile['r1']
                }
        ]
        })
    return res

def cups_to_amon(mp_uuids, context=None):
    """Convert CUPS to Amon.

    {
        "meteringPointId": uuid,
        "metadata": {
            "cupsnumber": "ES0987543210987654ZF",
            "address": {
                "street": "Calle y número",
                "postalCode": "CodigoPostal",
                "city": "Nombre ciudad",
                "cityCode": "Código INE ciudad",
                "province": "Nombre provincia",
                "provinceCode": "Código INE provincia",
                "country": "España",
                "countryCode": "ES. Codigo según ISO 3166",
                "parcelNumber": "Referencia catastral"
            }
        }
    }
    """
    res = []
    cups_obj = O.GiscedataCupsPs
    if not hasattr(mp_uuids, '__iter__'):
        mp_uuids = [mp_uuids]
    for mp_uuid in mp_uuids:
        cups = cups_obj.get(CUPS_UUIDS[mp_uuid])
        res.append(remove_none({
            "meteringPointId": mp_uuid,
            "metadata": {
                'cupsnumber': cups.name,
                'address': {
                    'street': get_street_name(cups),
                    'postalCode': cups.dp,
                    'city': cups.id_municipi.name,
                    'cityCode': cups.id_municipi.ine,
                    'province': cups.id_municipi.state.name,
                    'provinceCode': cups.id_municipi.state.code,
                    'country': cups.id_municipi.state.country_id.name,
                    'countryCode': cups.id_municipi.state.country_id.code,
                    'parcelNumber': cups.ref_catastral
                }
            },
        }, context))
    return res

def device_to_amon(device_uuids):
    """Convert a device to AMON.

    {
        "deviceId": required string UUID,
        "meteringPointId": required string UUID,
        "metadata": {
            # Think what we could put inside this
        }, 
    }
    """
    res = []
    if not hasattr(device_uuids, '__iter__'):
        device_uuids = [device_uuids]
    for dev_uuid in device_uuids:
        res.append(remove_none({
            "deviceId": dev_uuid,
            "meteringPointId": DEVICE_MP_REL[dev_uuid],
            "metadata": {
            }
        }))
    return res

def contract_to_amon(contract_ids, context=None):
    """Converts contracts to AMON.

    {
        "id": "uuid",
        "owenerId": "uuid",
        "payerId": "uuid",
        "version": "2",
        "start": 1332806400,
        "end": 1362009600,
        "tariffId": "2.0A",
        "power": 3300,
        "activityCode": "CNAE",
        "meteringPointId": "c1759810-90f3-012e-0404-34159e211070",
    }
    """
    if not context:
        context = {}
    res = []
    pol = O.GiscedataPolissa
    modcon_obj = O.GiscedataPolissaModcontractual
    if not hasattr(contract_ids, '__iter__'):
        contract_ids = [contract_ids]
    for contract_id in contract_ids:
        polissa = pol.get(contract_id)
        if 'modcon_id' in context:
            modcon = modcon_obj.get(context['modcon_id'])
        else:
            modcon = polissa.modcontractual_activa
        PARTNERS.append(modcon.titular.id)
        res.append(remove_none({
            'id': make_uuid('giscedata.polissa', polissa.name),
            'ownerId': make_uuid('res.partner', modcon.titular.id),
            'payerId': make_uuid('res.partner', modcon.pagador.id),
            'start': datestring_to_epoch(times.to_universal(modcon.data_inici, 'Europe/Madrid')),
            'end': datestring_to_epoch(times.to_universal(modcon.data_final, 'Europe/Madrid')),
            'tariffId': modcon.tarifa.name,
            'power': int(modcon.potencia * 1000),
            'version': modcon.name,
            'activityCode': modcon.cnae and modcon.cnae.name or None,
            'meteringPointId': make_uuid('giscedata.cups.ps', modcon.cups.name),
        }, context))
    return res

def partners_to_amon(partner_ids, context=None):
    """Convert a partner to JSON Format.

    {
      "id": "sample string 1",
      "firstName": "sample string 3",
      "firstSurname": "sample string 4",
      "secondSurname": "sample string 5",
      "address": {
        "street": "sample string 1",
        "postalCode": "sample string 2",
        "city": "sample string 3",
        "cityCode": "sample string 4",
        "province": "sample string 5",
        "provinceCode": "sample string 6",
        "country": "sample string 7",
        "countryCode": "sample string 8",
        "parcelNumber": "sample string 9"
      }
    }
    """
    if not hasattr(partner_ids, '__iter__'):
        partner_ids = [partner_ids]
    addr_obj = O.ResPartnerAddress
    if not context:
        context = {}
    res = []
    for partner_id in partner_ids:
        partner = O.ResPartner.get(partner_id)
        vat = len(partner.vat) == 9 and partner.vat or partner.vat[2:]
        if (vat[0] not in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
                           'J', 'U', 'V', 'N', 'P', 'Q', 'R', 'S', 'W')
                and ',' in partner.name):
            first_name = partner.name.split(',')[-1].strip()
            first_surname = ' '.join([
                x.strip() for x in partner.name.split(',')[:-1]
            ])
        else:
            first_name = partner.name
            first_surname = ''
        if 'address_id' in context:
            addr = addr_obj.get(context['address_id'])
        else:
            if not partner.address:
                continue
            addr = partner.address[0]
        res.append(remove_none({
            'id': make_uuid('res.partner', partner.id),
            'firstName': first_name,
            'firstSurname': first_surname,
            'address': {
                'street': addr.street,
                'postalCode': addr.zip,
                'city': addr.municipi and addr.municipi.name or None,
                'cityCode': addr.municipi and addr.municipi.ine or None,
                'province': addr.state_id.name,
                'provinceCode': addr.state_id.code,
                'country': addr.country_id.name,
                'countryCode': addr.country_id.code,
                'parcelNumber': None
            }
        }, context))
    return res

if __name__ == '__main__':
    ooop_config = {}
    for key, value in os.environ.items():
        if key.startswith('OOOP_'):
            key = key.split('_')[1].lower()
            if key == 'port':
                value = int(value)
            ooop_config[key] = value
    print "Using OOOP CONFIG: %s" % ooop_config

    O = OOOP(**ooop_config)
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
    else:
        limit = 80
    profiles = O.TgProfile.search([], 0, limit)
    profiles = O.TgProfile.read(profiles,)
    profiles_json = profile_to_amon(profiles)
    profiles_post = make_post_data(profiles_json)
    res = urllib.urlopen(REST_SERVER, profiles_post)
    print res.read()
    cups_json = cups_to_amon(CUPS_UUIDS.keys())
    cups_post = make_post_data(cups_json)
    res = urllib.urlopen(REST_SERVER, cups_post)
    print res.read()
    device_json = device_to_amon(DEVICE_MP_REL.keys())
    device_post = make_post_data(device_json)
    res = urllib.urlopen(REST_SERVER, device_post)
    print res.read()
    pids = O.GiscedataPolissa.search([('cups.id', 'in', CUPS_UUIDS.values())])
    contracts_json = contract_to_amon(pids)
    contracts_post = make_post_data(contracts_json)
    res = urllib.urlopen(REST_SERVER, contracts_post)
    print res.read()
    partners_json = partners_to_amon(PARTNERS)
    partners_post = make_post_data(partners_json)
    res = urllib.urlopen(REST_SERVER, partners_post)
    print "Total generated:"
    print "  Profiles: %s" % len(profiles_json)
    print "  CUPS: %s" % len(cups_json)
    print "  Devices: %s" % len(device_json)
    print "  Contracts: %s" % len(contracts_json)
    print "  Partners: %s" % len(partners_json)
    
