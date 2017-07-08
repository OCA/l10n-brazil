# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountResConfig(models.Model):
    _inherit = "account.config.settings"

    automated_payslip_payment_order = fields.Boolean(
        string="Gerar Ordem de Pagamento dos Holerites Automaticamente",
    )
