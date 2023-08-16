# Copyright (C) 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_NFCE


class NFCe(models.Model):
    _inherit = "l10n_br_fiscal.document"

    pos_order_id = fields.Many2one(comodel_name="pos.order")

    @api.depends("partner_shipping_id")
    def _compute_entrega_data(self):
        for doc in self:
            doc.nfe40_entrega = doc.partner_shipping_id

            if (
                doc.document_type == MODELO_FISCAL_NFCE
                and doc.partner_shipping_id.is_anonymous_consumer
            ):
                doc.nfe40_entrega = None

    @api.depends("partner_id")
    def _compute_dest_data(self):
        for doc in self:
            doc.nfe40_dest = doc.partner_id

            if (
                doc.partner_id.is_anonymous_consumer
                and not doc.partner_id.cnpj_cpf
                and doc.document_type != MODELO_FISCAL_NFCE
            ):
                doc.nfe40_dest = None

    def _eletronic_document_send(self):
        self._prepare_payments_for_nfce()

        super()._eletronic_document_send()

    def _prepare_payments_for_nfce(self):
        self.nfe40_detPag.filtered(lambda p: p.nfe40_tPag == "99").write(
            {"nfe40_xPag": "Outros"}
        )
