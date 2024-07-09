# Copyright 2024 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nBrTradeImportDeclarationWizard(models.TransientModel):

    _name = "l10n_br_trade_import.declaration.wizard"

    declaration_file = fields.Binary()

    def doit(self):
        result_ids = []

        for wizard in self:
            declaration = self.env[
                "l10n_br_trade_import.declaration"
            ].import_declaration(wizard.declaration_file)
            result_ids.append(declaration.id)
        action = self.env.ref("l10n_br_trade_import.action_import_declaration").read(
            []
        )[0]
        action["domain"] = [("id", "in", result_ids)]
        return action
