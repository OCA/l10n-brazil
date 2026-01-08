# Copyright (C) 2023 Antônio S. P. Neto <neto@engene.one> -
# Engenere LTDA (https://engenere.one).
# Copyright (C) 2023 Marcel Savegnago <marcel.savegnago@escodoo.com.br> -
# Escodoo (https://www.escodoo.com.br).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_open_nfse_paulistana(self):
        self.ensure_one()
        return self.fiscal_document_id.action_open_nfse_paulistana()
