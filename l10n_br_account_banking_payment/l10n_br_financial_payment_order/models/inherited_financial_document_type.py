# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models, _


from ..constantes import TIPO_SERVICO, TIPO_SERVICO_COMPLEMENTO, \
    FORMA_LANCAMENTO, BOLETO_ESPECIE


class FinancialDocumentType(models.Model):
    _inherit = b'financial.document.type'

    #
    # Integração bancária via CNAB
    #
    tipo_servico = fields.Selection(
        selection=TIPO_SERVICO,
        string='Tipo de serviço',
        help='Campo G025 do CNAB'
    )
    tipo_servico_complemento = fields.Selection(
        selection=TIPO_SERVICO_COMPLEMENTO,
        string='Complemento do tipo de serviço',
        help='Campo P005 do CNAB'
    )
    forma_lancamento = fields.Selection(
        selection=FORMA_LANCAMENTO,
        string='Forma de lançamento',
        help='Campo G029 do CNAB'
    )
    boleto_especie = fields.Selection(
        string='Espécie do Título',
        selection=BOLETO_ESPECIE,
    )