# (c) 2014 Kmee - Rafael da Silva Lima <rafael.lima@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    cnpj_cei = fields.Char(string="CNPJ/CEI Tomadora/Obra")
