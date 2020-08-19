# Copyright 2012 KMEE - Fernando Marcato Rodrigues
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# @ 2018 Akretion - www.akretion.com.br
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _, api, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    codigo_da_empresa = fields.Integer(
        string='Código da empresa',
        size=20,
        help="Será informado pelo banco depois do cadastro do beneficiário "
             "na agência",
    )
