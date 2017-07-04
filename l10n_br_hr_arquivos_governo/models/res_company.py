# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import logging

from openerp import api, exceptions, fields, models, _
from ..constantes_rh import CENTRALIZADORA

_logger = logging.getLogger(__name__)

try:
    from pybrasil import telefone
except ImportError:
    _logger.info('Cannot import pybrasil')


OUTRAS_ENTIDADES = [
    ('0000', "Em branco"),
    ('0001', u"Salário educação"),
    ('0002', u"INCRA"),
    ('0003', u"Salário educação + INCRA"),
    ('4096', u"SESCOOP"),
    ('4097', u"SESCOOP + Salário educação"),
    ('4098', u"SESCOOP + INCRA"),
    ('4099', u"SESCOOP + INCRA + Salário educação"),
]


class ResCompany(models.Model):
    """Override company to activate validate phones"""

    _inherit = "res.company"

    @api.constrains('phone')
    def _check_phone_br(self):
        if self.phone:
            if not telefone.valida_fone(self.phone):
                raise exceptions.Warning(
                    _('Número do Telefone Inválido'))

    supplier_partner_id = fields.Many2one(
        string='Fornecedor do sistema', comodel_name='res.partner'
    )

    codigo_outras_entidades = fields.Selection(
        string="Código de Outras Entidades",
        selection=OUTRAS_ENTIDADES,
        default='0000'
    )

    codigo_recolhimento_GPS = fields.Integer(
        string=u"Código de recolhimento do GPS",
    )

    porcentagem_filantropia = fields.Float(
        string=u"Porcentagem de Isenção de Filantropia",
        default=000.00,
    )

    centralizadora = fields.Selection(
        selection=CENTRALIZADORA, strin=u'Centralizadora do FGTS'
    )
