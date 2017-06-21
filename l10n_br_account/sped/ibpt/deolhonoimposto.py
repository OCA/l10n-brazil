# -*- coding: utf-8 -*-
# Copyright (C) 2015  Luis Felipe Miléo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import urllib
import urllib2
import json
from collections import namedtuple


WS_SERVICOS = 0
WS_PRODUTOS = 1

WS_IBPT = {
    WS_SERVICOS: 'http://iws.ibpt.org.br/api/deolhonoimposto/Servicos/?',
    WS_PRODUTOS: 'http://iws.ibpt.org.br/api/deolhonoimposto/Produtos/?',
}


DeOlhoNoImposto = namedtuple('Config', 'token cnpj uf')


def _convert(dictionary):
    return namedtuple('Result', dictionary.keys())(**dictionary)


def _response_to_dict(response):
    json_acceptable_string = response.replace("'", "\"").lower()
    return json.loads(json_acceptable_string)


def _request(req):
    try:
        response = urllib2.urlopen(req)
        data = _response_to_dict(response.read())
        return _convert(data)

    except urllib2.HTTPError, e:
        from odoo import _
        from odoo.exceptions import Warning as UserError
        raise UserError(_('Error in the request: {0}'.format(e)))


def get_ibpt_product(config, ncm, ex='0', reference=None, description=None,
                     uom=None, amount=None, gtin=None):

    data = urllib.urlencode({
        'token': config.token,
        'cnpj': config.cnpj,
        'uf': config.uf,
        'codigo': ncm,
        'ex': ex,
        'codigoInterno': reference,
        'descricao': description,
        'unidadeMedida': uom,
        'valor': amount,
        'gtin': gtin,
    })

    req = urllib2.Request(WS_IBPT[WS_PRODUTOS] + data)
    return _request(req)


def get_ibpt_service(config, nbs, description=None, uom=None, amount=None):

    data = urllib.urlencode({
        'token': config.token,
        'cnpj': config.cnpj,
        'uf': config.uf,
        'codigo': nbs,
        'descricao': description,
        'unidadeMedida': uom,
        'valor': amount,
    })

    req = urllib2.Request(WS_IBPT[WS_SERVICOS] + data)
    return _request(req)
