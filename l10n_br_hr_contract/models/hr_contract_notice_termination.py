# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class HrContractNoticeTermination(models.Model):
    _name = 'hr.contract.notice.termination'
    _description = 'Tipo de aviso prévio'

    name = fields.Char(
        string='Notice of termination type',
        required=True,
    )
