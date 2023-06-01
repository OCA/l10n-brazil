# Copyright (C) 2023  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re

import pytz

from odoo import api, fields, models

CODIGO_BANDEIRA_CARTAO = {
    "01": "Visa",
    "02": "Mastercard",
    "03": "American Express",
    "04": "Sorocred",
    "05": "Diners Club",
    "06": "Elo",
    "07": "Hipercard",
    "08": "Aura",
    "09": "Cabal",
    "99": "Outros",
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
                    "partner_id": self.partner_id.id,
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
        fiscal_document_id = created_order.account_move.fiscal_document_id
        pos_config_id = created_order.session_id.config_id

        if pos_config_id.simplified_document_type == "65":
            if created_order.is_contingency:
                fiscal_document_id.write(
                    {
                        "document_date": created_order.date_order,
                        "nfe_transmission": "9",
                        "nfe40_dhCont": created_order.date_order,
                        "nfe40_xJust": "Sem comunicação com a Internet.",
                    }
                )

            # FIXME: Workaround to fix the problem of missing compute fields in
            #   fiscal document lines
            for line in fiscal_document_id.fiscal_line_ids:
                line._compute_choice12()
                line._compute_choice15()
                line.tax_icms_or_issqn = "icms"
                line._compute_choice11()

            # The line below was added to enable frontend issuance of NFC-e. A
            #   necessary record for payment tag creation does not exist in the
            #   database during tax document validation, which causes an XML
            #   validation error. The record is added through commit to resolve
            #   this issue and ensure successfull record creation.
            # TODO: Change the flow so that it is not necessary to commit to the db
            self.env.cr.commit()  # pylint: disable=E8102

            # Remove the onChange-generated payment tag to create a new one
            if fiscal_document_id.nfe40_detPag:
                fiscal_document_id.nfe40_detPag.unlink()

            for payment in created_order.payment_ids:
                if payment.amount > 0:
                    payment_mode_id = payment.payment_method_id.payment_mode_id
                    vals = {
                        "nfe40_indPag": "0",
                        "nfe40_tPag": payment_mode_id.fiscal_payment_mode,
                        "nfe40_vPag": payment.amount,
                    }
                    if payment_mode_id.fiscal_payment_mode in ["03", "04"]:
                        terminal_transaction_network_cnpj = (
                            payment.terminal_transaction_network_cnpj
                            if hasattr(payment, "terminal_transaction_network_cnpj")
                            else ""
                        )
                        cnpj = re.sub(r"[^\w\s]", "", terminal_transaction_network_cnpj)
                        card_accq = (
                            payment.terminal_transaction_administrator
                            if hasattr(payment, "terminal_transaction_administrator")
                            else ""
                        )
                        card_vals = {
                            "nfe40_tpIntegra": "1",
                            "nfe40_CNPJ": cnpj or "",
                            "nfe40_tBand": CODIGO_BANDEIRA_CARTAO[card_accq]
                            if card_accq in CODIGO_BANDEIRA_CARTAO
                            else "",
                            "nfe40_cAut": payment.transaction_id
                            if hasattr(payment, "transaction_id")
                            else "",
                        }
                        fiscal_document_id.nfe40_detPag = [(0, 0, vals)]
                        result = self.env["nfe.40.card"].create(card_vals)
                        fiscal_document_id.nfe40_detPag[-1].write(
                            {"nfe40_card": result.id}
                        )
                    elif payment_mode_id.fiscal_payment_mode == "99":
                        vals.update({"nfe40_xPag": "Outros"})
                        fiscal_document_id.nfe40_detPag = [(0, 0, vals)]
                    else:
                        fiscal_document_id.nfe40_detPag = [(0, 0, vals)]

            # Fill the CPF/CNPJ in anonymous consumer before sending the document
            #   so that the minimum information is included in the XML
            if self._check_the_anonymous_consumer(created_order):
                if len(created_order.cnpj_cpf) == 14:
                    created_order.partner_id.write(
                        {
                            "company_type": "company",
                            "ind_ie_dest": "9",
                        }
                    )
                    created_order.partner_id.nfe40_CPF = ""
                else:
                    created_order.partner_id.nfe40_CNPJ = ""
                created_order.partner_id.write({"cnpj_cpf": created_order.cnpj_cpf})
                fiscal_document_id.nfe40_dest.nfe40_xNome = ""

            # Same use case as the one above
            self.env.cr.commit()  # pylint: disable=E8102

            try:
                fiscal_document_id.action_document_confirm()
                fiscal_document_id.action_document_send()
            except Exception:
                pass

            # Clean the CPF/CNPJ in anonymous consumer after sending the document
            if self._check_the_anonymous_consumer(created_order):
                created_order.partner_id.write(
                    {"company_type": "person", "cnpj_cpf": False}
                )

        return res

    def _check_the_anonymous_consumer(self, created_order):
        return created_order.cnpj_cpf and created_order.partner_id.is_anonymous_consumer

    def _prepare_invoice_line(self, order_line):
        vals = super(PosOrder, self)._prepare_invoice_line(order_line)
        pos_config_id = self.session_id.config_id

        if pos_config_id.simplified_document_type == "65":
            fiscal_map_id = order_line.product_id.pos_fiscal_map_ids.search(
                [("pos_config_id", "=", self.config_id.id)], limit=1
            )
            pos_fiscal_map_id = self.env["l10n_br_pos.product_fiscal_map"].browse(
                fiscal_map_id.id
            )
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
                    "discount_value": (order_line.discount * order_line.amount_total)
                    / 100,
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
        try:
            order.account_move.fiscal_document_id._document_cancel(cancel_reason)
        except Exception as e:
            error_message = f"Failed to cancel fiscal document: {str(e)}"
            error_response = {
                "status_code": 400,
                "message": error_message,
            }
            return error_response
        finally:
            if order.account_move.fiscal_document_id.state_edoc == "cancelada":
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
                    [
                        ("pos_reference", "=", order.pos_reference),
                        ("amount_total", ">", 0),
                    ]
                )
                refund_order.pos_reference = f"{order.pos_reference}-cancelled"
            else:
                raise Exception("Não foi possível cancelar a NFC-e.")
        return order.account_move.fiscal_document_id.state_edoc
