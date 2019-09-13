# Copyright (C) 2009  Renato Lima - Akretion
# Copyright (C) 2012  Raphaël Valyi - Akretion
# Copyright (C) 2014  Luis Felipe Miléo - KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        related='partner_id.cnpj_cpf',
    )
    legal_name = fields.Char(
        string='Razão Social',
        related='partner_id.legal_name',
    )
    ie = fields.Char(
        string='Inscrição Estadual',
        related='partner_id.inscr_est',
    )
