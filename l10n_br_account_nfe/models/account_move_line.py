# Copyright (C) 2022-Today - Akretion (<https://akretion.com/pt-BR>).
# @author Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_A_ENVIAR,
)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def write(self, values):

        result = super().write(values)
        MOVE_LINE_FIELDS = ["date_maturity", "name", "amount_currency"]
        if any(field in values.keys() for field in MOVE_LINE_FIELDS):
            invoices = self.mapped("invoice_id")
            for invoice in invoices.filtered(
                lambda i: i.fiscal_document_id.id != i.company_id.fiscal_dummy_id.id
                and i.processador_edoc == PROCESSADOR_OCA
                and i.document_type_id.code in [MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE]
                and i.issuer == DOCUMENT_ISSUER_COMPANY
                and i.state_edoc == SITUACAO_EDOC_A_ENVIAR
            ):
                invoice.fiscal_document_id.action_document_confirm()
                invoice.fiscal_document_id._document_export()
        return result
