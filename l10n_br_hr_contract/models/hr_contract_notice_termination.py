# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# Copyright 2025 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class HrContractNoticeTermination(models.Model):
    _name = "hr.contract.notice.termination"
    _description = "Type of notice period"

    name = fields.Char(string="Notice of termination type", required=True)
