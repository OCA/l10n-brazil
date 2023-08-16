# Copyright (C) 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    FISCAL_PAYMENT_MODE,
    MODELO_FISCAL_NFCE,
)


class AccountMove(models.Model):

    _inherit = "account.move"

    def view_pdf(self):
        self.ensure_one()
        if self.document_type != MODELO_FISCAL_NFCE:
            return super(AccountMove, self).view_pdf()

        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", "l10n_br_pos_nfce.report_danfe_nfce")],
                limit=1,
            )
            .report_action(self, data=self._prepare_nfce_danfe_values())
        )

    def _prepare_nfce_danfe_values(self):
        return {
            "company_ie": self.company_inscr_est,
            "company_cnpj": self.company_cnpj_cpf,
            "company_legal_name": self.company_legal_name,
            "company_street": self.company_street,
            "company_number": self.company_number,
            "company_district": self.company_district,
            "company_city": self.company_city_id.display_name,
            "company_state": self.company_state_id.name,
            "lines": self._prepare_nfce_danfe_line_values(),
            "total_product_quantity": len(
                self.line_ids.filtered(lambda line: line.product_id)
            ),
            "amount_total": self.amount_total,
            "amount_discount_value": self.amount_discount_value,
            "amount_freight_value": self.amount_freight_value,
            "payments": self._prepare_nfce_danfe_payment_values(),
            "amount_change": self.nfe40_vTroco,
            "nfce_url": self.fiscal_document_id.get_nfce_qrcode_url(),
            "document_key": self.document_key,
            "document_number": self.document_number,
            "document_serie": self.document_serie,
            "document_date": self.document_date.astimezone().strftime(
                "%d/%m/%y %H:%M:%S"
            ),
            "authorization_protocol": self.authorization_protocol,
            "document_qrcode": self.fiscal_document_id.get_nfce_qrcode(),
            "system_env": self.nfe40_tpAmb,
            "unformatted_amount_freight_value": self.amount_freight_value,
            "unformatted_amount_discount_value": self.amount_discount_value,
            "contingency": self.nfe_transmission != "1",
            "homologation_environment": self.nfe_environment == "2",
        }

    def _prepare_nfce_danfe_line_values(self):
        lines_list = []
        lines = self.line_ids.filtered(lambda line: line.product_id)
        for index, line in enumerate(lines):
            product_id = line.product_id
            lines_list.append(
                {
                    "product_index": index + 1,
                    "product_default_code": product_id.default_code,
                    "product_name": product_id.name,
                    "product_quantity": line.quantity,
                    "product_uom": product_id.uom_name,
                    "product_unit_value": product_id.lst_price,
                    "product_unit_total": line.quantity * product_id.lst_price,
                }
            )
        return lines_list

    def _prepare_nfce_danfe_payment_values(self):
        payments_list = []
        for payment in self.nfe40_detPag:
            payments_list.append(
                {
                    "method": dict(FISCAL_PAYMENT_MODE)[payment.nfe40_tPag],
                    "value": payment.nfe40_vPag,
                }
            )
        return payments_list
