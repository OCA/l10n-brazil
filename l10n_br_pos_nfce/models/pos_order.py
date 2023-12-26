# Copyright (C) KMEE 2023
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_NFCE

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    is_contingency = fields.Boolean(
        string="Is Contingency?", default=False, readonly=True
    )

    def _prepare_invoice_vals(self):
        vals = super()._prepare_invoice_vals()

        pos_config_id = self.session_id.config_id
        if pos_config_id.simplified_document_type == MODELO_FISCAL_NFCE:
            nfce_vals = self._prepare_nfce_vals(pos_config_id)

            if self.document_key and not self.authorization_protocol:
                self.is_contingency = True
                nfce_vals.update(
                    {
                        "document_key": self.document_key,
                        "document_number": self.document_number,
                    }
                )
                pos_config_id.nfce_document_serie_sequence_number_next = (
                    self.document_number
                )
            else:
                next_number = pos_config_id.nfce_document_serie_sequence_number_next
                nfce_vals.update({"document_number": next_number})
                pos_config_id.nfce_document_serie_sequence_number_next += 1

            vals.update(nfce_vals)

        return vals

    def _prepare_nfce_vals(self, pos_config_id):
        if not self.payment_ids:
            return dict()

        payment_mode_id = self.payment_ids[0].payment_method_id.payment_mode_id
        return {
            "document_type_id": pos_config_id.simplified_document_type_id.id,
            "fiscal_operation_id": pos_config_id.out_pos_fiscal_operation_id.id,
            "ind_pres": "1",
            "document_serie_id": pos_config_id.nfce_document_serie_id.id,
            "partner_id": self.partner_id.id,
            "payment_mode_id": payment_mode_id.id,
            "nfe40_vTroco": self.amount_return,
        }

    @api.model
    def _process_order(self, pos_order_vals, draft, existing_order):
        res = super()._process_order(pos_order_vals, draft, existing_order)

        created_order = self.browse(res)
        pos_config_id = created_order.session_id.config_id
        if pos_config_id.simplified_document_type == MODELO_FISCAL_NFCE:
            fiscal_document_id = created_order.account_move.fiscal_document_id
            if created_order.is_contingency:
                fiscal_document_id.write(
                    {
                        "document_date": created_order.date_order,
                        "nfe_transmission": "9",
                        "nfe40_dhCont": created_order.date_order,
                        "nfe40_xJust": "Sem comunicação com a Internet.",
                    }
                )

            created_order._setup_anonymous_consumer()

            try:
                fiscal_document_id.action_document_confirm()
                fiscal_document_id.action_document_send()
            except Exception as e:
                _logger.error("Error sending NFCe document: %s" % e)
            finally:
                created_order._clear_anonymous_consumer()

        return res

    def _setup_anonymous_consumer(self):
        if self._has_anonymous_consumer():
            if len(self.cnpj_cpf) == 14:
                self.partner_id.write(
                    {
                        "company_type": "company",
                        "ind_ie_dest": "9",
                    }
                )
                self.partner_id.nfe40_CPF = ""
            else:
                self.partner_id.nfe40_CNPJ = ""
            self.partner_id.write({"cnpj_cpf": self.cnpj_cpf})
            self.account_move.fiscal_document_id.nfe40_dest.nfe40_xNome = ""

    def _clear_anonymous_consumer(self):
        if self._has_anonymous_consumer():
            self.partner_id.write({"company_type": "person", "cnpj_cpf": False})

    def _has_anonymous_consumer(self):
        return self.cnpj_cpf and self.partner_id.is_anonymous_consumer

    def _prepare_invoice_line(self, order_line):
        vals = super()._prepare_invoice_line(order_line)

        if self.config_id.simplified_document_type == MODELO_FISCAL_NFCE:
            vals.update(order_line._prepare_nfce_tax_dict())

        return vals

    @api.model
    def create_from_ui(self, orders, draft=False):
        response = super().create_from_ui(orders, draft)
        for option in response:
            order = self.env["pos.order"].search([("id", "=", option["id"])])
            if order.document_type == MODELO_FISCAL_NFCE:
                fiscal_document_id = order.account_move.fiscal_document_id
                order.write({"state_edoc": fiscal_document_id.state_edoc})
                option.update(order._prepare_fiscal_document_dict())
        return response

    def _prepare_fiscal_document_dict(self):
        fiscal_document_id = self.account_move.fiscal_document_id

        authorization_date = False
        if fiscal_document_id.authorization_date:
            authorization_date = fiscal_document_id.authorization_date.strftime(
                "%m/%d/%Y %H:%M:%S"
            )

        return {
            "status_description": self.account_move.status_description,
            "status_code": self.account_move.status_code,
            "authorization_protocol": fiscal_document_id.authorization_protocol,
            "document_key": fiscal_document_id.document_key,
            "document_number": fiscal_document_id.document_number,
            "document_serie": fiscal_document_id.document_serie,
            "url_consulta": fiscal_document_id.get_nfce_qrcode_url(),
            "qr_code": fiscal_document_id.get_nfce_qrcode(),
            "authorization_date": authorization_date,
        }

    def cancel_nfce_from_ui(self, order_id, cancel_reason):
        order = self.env["pos.order"].search([("pos_reference", "=", order_id)])

        try:
            order.account_move.fiscal_document_id._document_cancel(cancel_reason)
        except Exception as e:
            _logger.error("Error cancelling NFCe document: %s" % e)
        finally:
            order.write(
                {
                    "state_edoc": order.account_move.fiscal_document_id.state_edoc,
                }
            )
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
        return order.account_move.fiscal_document_id.state_edoc


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    def _prepare_nfce_tax_dict(self):
        # Get fiscal map for this product
        fiscal_map_id = self.product_id.pos_fiscal_map_ids.search(
            [("pos_config_id", "=", self.order_id.config_id.id)], limit=1
        )

        # Create base tax_dict
        tax_dict = {
            "fiscal_operation_id": fiscal_map_id.fiscal_operation_id.id,
            "fiscal_operation_line_id": fiscal_map_id.fiscal_operation_line_id.id,
            "cfop_id": fiscal_map_id.cfop_id.id,
            "uot_id": fiscal_map_id.uot_id.id,
            "fiscal_genre_id": self.product_id.fiscal_genre_id.id,
            "discount_value": (self.discount * self.amount_total) / 100,
            "uom_id": self.product_id.uom_id.id,
            "ncm_id": self.product_id.ncm_id.id,
        }

        # Update tax dict for each tax domain
        tax_dict.update(self._prepare_nfce_icms_dict(fiscal_map_id))
        tax_dict.update(self._prepare_nfce_ipi_dict(fiscal_map_id))
        tax_dict.update(self._prepare_nfce_cofins_dict(fiscal_map_id))
        tax_dict.update(self._prepare_pis_icms_dict(fiscal_map_id))
        tax_dict.update(self._prepare_pis_icms_dict(fiscal_map_id))
        # Update tax dict with fiscal_tax_ids data
        tax_dict.update(self._prepare_nfce_fiscal_tax_ids(fiscal_map_id))

        return tax_dict

    def _prepare_nfce_icms_dict(self, fiscal_map_id):
        return {
            "icms_tax_id": fiscal_map_id.icms_tax_id.id,
            "icms_cst_id": fiscal_map_id.icms_cst_id.id,
            "icms_base": fiscal_map_id.icms_base,
            "icms_percent": fiscal_map_id.icms_percent,
            "icms_value": fiscal_map_id.icms_value,
            "icmssn_tax_id": fiscal_map_id.icmssn_tax_id.id,
            "icmssn_range_id": fiscal_map_id.icmssn_range_id.id,
            "icmssn_base": fiscal_map_id.icmssn_base,
            "icmssn_percent": fiscal_map_id.icmssn_percent,
        }

    def _prepare_nfce_ipi_dict(self, fiscal_map_id):
        return {
            "ipi_tax_id": fiscal_map_id.ipi_tax_id.id,
            "ipi_cst_id": fiscal_map_id.ipi_cst_id.id,
            "ipi_base": fiscal_map_id.ipi_base,
            "ipi_percent": fiscal_map_id.ipi_percent,
            "ipi_value": fiscal_map_id.ipi_value,
        }

    def _prepare_nfce_cofins_dict(self, fiscal_map_id):
        return {
            "cofins_tax_id": fiscal_map_id.cofins_tax_id.id,
            "cofins_cst_id": fiscal_map_id.cofins_cst_id.id,
            "cofins_base": fiscal_map_id.cofins_base,
            "cofins_percent": fiscal_map_id.cofins_percent,
            "cofins_value": fiscal_map_id.cofins_value,
        }

    def _prepare_pis_icms_dict(self, fiscal_map_id):
        return {
            "pis_tax_id": fiscal_map_id.pis_tax_id.id,
            "pis_cst_id": fiscal_map_id.pis_cst_id.id,
            "pis_base": fiscal_map_id.pis_base,
            "pis_percent": fiscal_map_id.pis_percent,
            "pis_value": fiscal_map_id.pis_value,
        }

    def _prepare_nfce_fiscal_tax_ids(self, fiscal_map_id):
        fiscal_taxes_list = list()
        if fiscal_map_id.icms_tax_id:
            fiscal_taxes_list.append(fiscal_map_id.icms_tax_id.id)
        if fiscal_map_id.icmssn_tax_id:
            fiscal_taxes_list.append(fiscal_map_id.icmssn_tax_id.id)
        if fiscal_map_id.ipi_tax_id:
            fiscal_taxes_list.append(fiscal_map_id.ipi_tax_id.id)
        if fiscal_map_id.cofins_tax_id:
            fiscal_taxes_list.append(fiscal_map_id.cofins_tax_id.id)
        if fiscal_map_id.pis_tax_id:
            fiscal_taxes_list.append(fiscal_map_id.pis_tax_id.id)

        if fiscal_taxes_list:
            return {
                "fiscal_tax_ids": [
                    (
                        6,
                        0,
                        fiscal_taxes_list,
                    )
                ],
            }
        return dict()
