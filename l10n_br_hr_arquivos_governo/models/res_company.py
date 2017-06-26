# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import logging

from openerp import api, exceptions, fields, models, _

_logger = logging.getLogger(__name__)

try:
    from pybrasil import telefone
except ImportError:
    _logger.info('Cannot import pybrasil')


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
