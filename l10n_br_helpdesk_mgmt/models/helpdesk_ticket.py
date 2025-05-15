# Copyright (C) 2025-Today - KMEE (<http://www.kmee.com.br>).
# @author Diego Paradeda <diego.paradeda@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    cnpj_cpf = fields.Char(string="CNPJ/CPF", related="partner_id.cnpj_cpf")
    legal_name = fields.Char(string="Legal Name", related="partner_id.legal_name")
    inscr_est = fields.Char(string="State Tax Number", related="partner_id.inscr_est")
