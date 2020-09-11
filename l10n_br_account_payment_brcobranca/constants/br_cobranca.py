# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# Copyright 2020 KMEE
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import namedtuple

DICT_BRCOBRANCA_CNAB_TYPE = {
    '240': 'cnab240',
    '400': 'cnab400',
}

BankRecord = namedtuple('Bank', 'name, retorno, remessa')

DICT_BRCOBRANCA_BANK = {
    '001': BankRecord('banco_brasil', retorno=['400'], remessa=['240', '400']),
    '004': BankRecord('banco_nordeste', retorno=['400'], remessa=['400']),
    '021': BankRecord('banestes', retorno=[], remessa=[]),
    '033': BankRecord('santander', retorno=['240'], remessa=['400']),
    '041': BankRecord('banrisul', retorno=['400'], remessa=['400']),
    '070': BankRecord('banco_brasilia', retorno=[], remessa=['400']),
    '097': BankRecord('credisis', retorno=['400'], remessa=['400']),
    '104': BankRecord('caixa', retorno=['240'], remessa=['240']),
    '136': BankRecord('unicred', retorno=['400'], remessa=['240', '400']),
    '237': BankRecord('bradesco', retorno=['400'], remessa=['400']),
    '341': BankRecord('itau', retorno=['400'], remessa=['400']),
    '399': BankRecord('hsbc', retorno=[], remessa=[]),
    '745': BankRecord('citibank', retorno=[], remessa=['400']),
    '748': BankRecord('sicred', retorno=['240'], remessa=['240']),
    '756': BankRecord('sicoob', retorno=['240'], remessa=['240', '400']),
}
