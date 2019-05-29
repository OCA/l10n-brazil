# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    own_number_type = fields.Selection(
        selection=[
            ('0', u'Sequêncial único por empresa'),
            ('1', u'Numero sequêncial da Fatura'),
            ('2', u'Sequêncial único por modo de pagamento'), ],
        string=u'Tipo de nosso número',
        default='2'
    )

    own_number_sequence = fields.Many2one(
        comodel_name='ir.sequence',
        string=u'Sequência do Nosso Número'
    )

    transaction_id_sequence = fields.Many2one('ir.sequence',
                                              string=u'Sequência da fatura')
