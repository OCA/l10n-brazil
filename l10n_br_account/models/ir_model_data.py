# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class IrModelData(models.Model):
    _inherit = "ir.model.data"

    @api.model
    def _update_xmlids(self, data_list, update=False):
        """
        Because of the _inherits, Odoo naturally expects XML records
        for account.move and account.move.line to have respectively a fiscal_document_id
        and a fiscal_document_line_id. But in l10n_br_account we allow account moves
        without fiscal documents. This override avoids crashing Odoo here.
        """
        to_remove = []
        for index, data in enumerate(data_list or []):
            if (
                data["record"]._name == "l10n_br_fiscal.document"
                and not data["record"].id
            ):
                to_remove.append(index)
            elif (
                data["record"]._name == "l10n_br_fiscal.document.line"
                and not data["record"].id
            ):
                to_remove.append(index)
        for i in to_remove:
            data_list.pop(i)
        return super()._update_xmlids(data_list, update)
