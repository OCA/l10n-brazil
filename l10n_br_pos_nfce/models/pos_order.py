# Copyright (C) 2023  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import pytz
import re

from odoo import api, fields, models

CODIGO_BANDEIRA_CARTAO = {
    '01': 'Visa',
    '02': 'Mastercard',
    '03': 'American Express',
    '04': 'Sorocred',
    '05': 'Diners Club',
    '06': 'Elo',
    '07': 'Hipercard',
    '08': 'Aura',
    '09': 'Cabal',
    '99': 'Outros',
}


class PosOrder(models.Model):
    _inherit = "pos.order"

    is_contingency = fields.Boolean(
        string="Is Contingency?", default=False, readonly=True
    )

    def _prepare_invoice_vals(self):
        vals = super(PosOrder, self)._prepare_invoice_vals()

        pos_config_id = self.session_id.config_id
        payment_mode_id = self.payment_ids[0].payment_method_id.payment_mode_id

        if pos_config_id.simplified_document_type == "65":
            vals.update(
                {
                    "document_type_id": pos_config_id.simplified_document_type_id.id,
                    "fiscal_operation_id": pos_config_id.out_pos_fiscal_operation_id.id,
                    "ind_pres": "1",
                    "document_serie_id": pos_config_id.nfce_document_serie_id.id,
                    "partner_id": pos_config_id.partner_id.id,
                    "payment_mode_id": payment_mode_id.id,
                    "nfe40_vTroco": self.amount_return,
                }
            )
            if self.document_key and not self.authorization_protocol:
                self.is_contingency = True
                vals.update(
                    {
                        "document_key": self.document_key,
                        "document_number": self.document_number,
                    }
                )
                pos_config_id.nfce_document_serie_sequence_number_next = (
                    self.document_number
                )
            else:
                vals.update(
                    {
                        "document_number": pos_config_id.nfce_document_serie_sequence_number_next  # noqa
                    }
                )
                pos_config_id.nfce_document_serie_sequence_number_next += 1

        return vals

    @api.model
    def _process_order(self, pos_order_vals, draft, existing_order):
        res = super(PosOrder, self)._process_order(
            pos_order_vals, draft, existing_order
        )
        created_order = self.env["pos.order"].browse(res)
        pos_config_id = created_order.session_id.config_id

        if pos_config_id.simplified_document_type == "65":

            # It was necessary to insert the next line so that the flow of issuing
            #   the NFC-e by frontend becomes possible.
            # What error that has been happening is: during the validation process
            #   of the tax document, the required record that will become the tag of
            #   payment, and which is being created automatically, does not exist
            #   yet in the database and therefore account.move cannot link with it,
            #   which ends up generating an error when validating the XML. Forcing
            #   this record through the commit, the issue flow works through
            #   from a record created by a POS session works perfectly

            # TODO: Change the flow so that it is not necessary to commit to the db
            self.env.cr.commit()  # pylint: disable=E8102

            for temp in created_order.account_move.fiscal_document_id.nfe40_detPag:
                temp.unlink()

            for payment in created_order.payment_ids:
                if payment.payment_method_id[0].payment_mode_id.fiscal_payment_mode in ["03", "04"]:
                    card_vals = {
                        "nfe40_tpIntegra": "1",
                        "nfe40_CNPJ": re.sub(r'[^\w\s]', '', payment.terminal_transaction_network_cnpj),
                        "nfe40_tBand": CODIGO_BANDEIRA_CARTAO[payment.terminal_transaction_administrator],
                        "nfe40_cAut": payment.transaction_id,
                    }
                    vals = {
                        "nfe40_indPag": "0",
                        "nfe40_tPag": payment.payment_method_id.payment_mode_id.fiscal_payment_mode,
                        "nfe40_vPag": payment.amount,
                    }
                    created_order.account_move.fiscal_document_id.nfe40_detPag = [(0, 0, vals)]
                    result = self.env["nfe.40.card"].create(card_vals)
                    self.env.cr.commit()    # pylint: disable=E8102
                    created_order.account_move.fiscal_document_id.nfe40_detPag[-1].write({"nfe40_card": result.id})
                elif payment.payment_method_id[0].payment_mode_id.fiscal_payment_mode == "99":
                    vals = {
                        "nfe40_indPag": "0",
                        "nfe40_tPag": payment.payment_method_id.payment_mode_id.fiscal_payment_mode,
                        "nfe40_xPag": "Outros",
                        "nfe40_vPag": payment.amount,
                    }
                    created_order.account_move.fiscal_document_id.nfe40_detPag = [(0, 0, vals)]
                else:
                    vals = {
                        "nfe40_indPag": "0",
                        "nfe40_tPag": payment.payment_method_id.payment_mode_id.fiscal_payment_mode,
                        "nfe40_vPag": payment.amount,
                    }
                    created_order.account_move.fiscal_document_id.nfe40_detPag = [(0, 0, vals)]

            self.env.cr.commit()    # pylint: disable=E8102
            # FIXME: The next line is a workaround to fix the problem of the
            #  missing compute fields in the fiscal document line.
            for line in created_order.account_move.fiscal_document_id.fiscal_line_ids:
                line._compute_choice12()
                line._compute_choice15()
                line.tax_icms_or_issqn = "icms"
                line._compute_choice11()
            if created_order.is_contingency:
                created_order.account_move.fiscal_document_id.write(
                    {
                        "document_date": created_order.date_order,
                        "edoc_transmission": "9",
                        "nfe40_dhCont": created_order.date_order,
                        "nfe40_xJust": "Sem comunicação com a Internet.",
                    }
                )
            created_order.account_move.fiscal_document_id.action_document_confirm()
            created_order.account_move.fiscal_document_id.action_document_send()

        return res

    def _prepare_invoice_line(self, order_line):
        vals = super(PosOrder, self)._prepare_invoice_line(order_line)
        pos_config_id = self.session_id.config_id

        if pos_config_id.simplified_document_type == "65":
            pos_fiscal_map_id = order_line.product_id.pos_fiscal_map_ids.filtered(
                lambda o: self.config_id.id == o.pos_config_id.id
            )[0]
            fiscal_tax_ids = [
                (
                    6,
                    0,
                    [
                        pos_fiscal_map_id.icms_tax_id.id,
                        pos_fiscal_map_id.ipi_tax_id.id,
                        pos_fiscal_map_id.cofins_tax_id.id,
                        pos_fiscal_map_id.pis_tax_id.id,
                    ],
                )
            ]
            vals.update(
                {
                    "product_uom_id": order_line.product_uom_id.id,
                    "fiscal_operation_id": pos_fiscal_map_id.fiscal_operation_id.id,
                    "tax_icms_or_issqn": "icms",
                    "uom_id": order_line.product_id.uom_id.id,
                    "ncm_id": order_line.product_id.ncm_id.id,
                    "fiscal_operation_line_id": pos_fiscal_map_id.fiscal_operation_line_id.id,
                    "cfop_id": pos_fiscal_map_id.cfop_id.id,
                    "uot_id": pos_fiscal_map_id.uot_id.id,
                    "fiscal_genre_id": order_line.product_id.fiscal_genre_id.id,
                    "icms_tax_id": pos_fiscal_map_id.icms_tax_id.id,
                    "icms_cst_id": pos_fiscal_map_id.icms_cst_id.id,
                    "icms_base": pos_fiscal_map_id.icms_base,
                    "icms_percent": pos_fiscal_map_id.icms_percent,
                    "icms_value": pos_fiscal_map_id.icms_value,
                    "ipi_tax_id": pos_fiscal_map_id.ipi_tax_id.id,
                    "ipi_cst_id": pos_fiscal_map_id.ipi_cst_id.id,
                    "ipi_base": pos_fiscal_map_id.ipi_base,
                    "ipi_percent": pos_fiscal_map_id.ipi_percent,
                    "ipi_value": pos_fiscal_map_id.ipi_value,
                    "cofins_tax_id": pos_fiscal_map_id.cofins_tax_id.id,
                    "cofins_cst_id": pos_fiscal_map_id.cofins_cst_id.id,
                    "cofins_base": pos_fiscal_map_id.cofins_base,
                    "cofins_percent": pos_fiscal_map_id.cofins_percent,
                    "cofins_value": pos_fiscal_map_id.cofins_value,
                    "pis_tax_id": pos_fiscal_map_id.pis_tax_id.id,
                    "pis_cst_id": pos_fiscal_map_id.pis_cst_id.id,
                    "pis_base": pos_fiscal_map_id.pis_base,
                    "pis_percent": pos_fiscal_map_id.pis_percent,
                    "pis_value": pos_fiscal_map_id.pis_value,
                    "fiscal_tax_ids": fiscal_tax_ids,
                }
            )
        return vals

    @api.model
    def create_from_ui(self, orders, draft=False):
        local_timezone = pytz.timezone("America/Sao_Paulo")
        response = super(PosOrder, self).create_from_ui(orders, draft)
        for option in response:
            order = self.env["pos.order"].search([("id", "=", option["id"])])
            if order.document_type == "65":
                fiscal_document_id = order.account_move.fiscal_document_id
                authorization_date = False
                if fiscal_document_id.authorization_date:
                    authorization_date = fiscal_document_id.authorization_date.strftime(
                        "%m/%d/%Y %H:%M:%S"
                    )
                order.write({"state_edoc": fiscal_document_id.state_edoc})
                option.update(
                    {
                        "status_description": order.account_move.status_description,
                        "status_code": order.account_move.status_code,
                        "authorization_protocol": fiscal_document_id.authorization_protocol,
                        "document_key": fiscal_document_id.document_key,
                        "document_number": fiscal_document_id.document_number,
                        "document_serie": fiscal_document_id.document_serie,
                        "url_consulta": order.account_move.estado_de_consulta_da_nfce(),
                        "qr_code": order.account_move._monta_qrcode(),
                        "authorization_date": authorization_date,
                        "document_date": fiscal_document_id.document_date.astimezone(
                            local_timezone
                        ).strftime("%m/%d/%Y %H:%M:%S"),
                    }
                )
        return response

    def cancel_nfce_from_ui(self, order_id, cancel_reason):
        order = self.env["pos.order"].search([("pos_reference", "=", order_id)])
        order.account_move.fiscal_document_id._document_cancel(cancel_reason)
        vals = {
            "state_edoc": order.account_move.fiscal_document_id.state_edoc,
            "state": "cancel",
        }
        order.write(vals)
        order.account_move.write({"state": "cancel"})
        order.with_context(
            mail_create_nolog=True,
            tracking_disable=True,
            mail_create_nosubscribe=True,
            mail_notrack=True,
        ).refund()
        refund_order = self.search(
            [("pos_reference", "=", order.pos_reference), ("amount_total", ">", 0)]
        )
        refund_order.pos_reference = f"{order.pos_reference}-cancelled"
        return order.account_move.fiscal_document_id.state_edoc
