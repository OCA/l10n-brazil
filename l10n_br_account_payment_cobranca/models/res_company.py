# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, fields

from ..constantes import (
    SEQUENCIAL_EMPRESA, SEQUENCIAL_FATURA, SEQUENCIAL_CARTEIRA
)


class ResCompany(models.Model):
    _inherit = 'res.company'

    own_number_type = fields.Selection(
        selection=[
            (SEQUENCIAL_EMPRESA, u'Sequêncial único por empresa'),
            (SEQUENCIAL_FATURA, u'Numero sequêncial da Fatura'),
            (SEQUENCIAL_CARTEIRA, u'Sequêncial único por carteira'), ],
        string=u'Tipo de nosso número',
        default='2'
    )

    own_number_sequence = fields.Many2one(
        comodel_name='ir.sequence',
        string=u'Sequência do Nosso Número'
    )

    @api.multi
    def get_own_number_sequence(self):
        self.ensure_one()
        return self.own_number_sequence.next_by_id()
