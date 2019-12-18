# Copyright (C) 2016  Hendrix Costa - KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    cnpj_cpf = fields.Char(string="CNPJ/CPF", related="partner_id.cnpj_cpf")
    legal_name = fields.Char(string="Razão Social", related="partner_id.legal_name")
    ie = fields.Char(string="Inscrição Estadual", related="partner_id.inscr_est")
