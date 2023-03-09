# Copyright (C) 2023  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import pytz

from odoo import api, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _prepare_invoice_vals(self):
        vals = super(PosOrder, self)._prepare_invoice_vals()

        pos_config_id = self.session_id.config_id
        payment_mode_id = self.payment_ids[0].payment_method_id.payment_mode_id

        vals.update(
            {
                "document_type_id": pos_config_id.simplified_document_type_id.id,
                "fiscal_operation_id": pos_config_id.out_pos_fiscal_operation_id.id,
                "ind_pres": "1",
                "document_serie_id": pos_config_id.nfce_document_serie_id.id,
                "partner_id": pos_config_id.partner_id.id,
                "payment_mode_id": payment_mode_id.id,
            }
        )

        return vals

    @api.model
    def _process_order(self, pos_order_vals, draft, existing_order):
        res = super(PosOrder, self)._process_order(
            pos_order_vals, draft, existing_order
        )
        created_order = self.env["pos.order"].browse(res)

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
        created_order.account_move.fiscal_document_id.action_document_confirm()
        created_order.account_move.fiscal_document_id.action_document_send()
        return res

    def _prepare_invoice_line(self, order_line):
        vals = super(PosOrder, self)._prepare_invoice_line(order_line)
        pos_fiscal_map_ids = order_line.product_id.pos_fiscal_map_ids
        fiscal_tax_ids = [
            (
                6,
                0,
                [
                    pos_fiscal_map_ids.icms_tax_id.id,
                    pos_fiscal_map_ids.ipi_tax_id.id,
                    pos_fiscal_map_ids.cofins_tax_id.id,
                    pos_fiscal_map_ids.pis_tax_id.id,
                ],
            )
        ]
        vals.update(
            {
                "product_uom_id": order_line.product_uom_id.id,
                "fiscal_operation_id": pos_fiscal_map_ids.fiscal_operation_id.id,
                "tax_icms_or_issqn": "icms",
                "uom_id": order_line.product_id.uom_id.id,
                "ncm_id": order_line.product_id.ncm_id.id,
                "fiscal_operation_line_id": pos_fiscal_map_ids.fiscal_operation_line_id.id,
                "cfop_id": pos_fiscal_map_ids.cfop_id.id,
                "uot_id": pos_fiscal_map_ids.uot_id.id,
                "fiscal_genre_id": order_line.product_id.fiscal_genre_id.id,
                "icms_tax_id": pos_fiscal_map_ids.icms_tax_id.id,
                "icms_cst_id": pos_fiscal_map_ids.icms_cst_id.id,
                "icms_base": pos_fiscal_map_ids.icms_base,
                "icms_percent": pos_fiscal_map_ids.icms_percent,
                "icms_value": pos_fiscal_map_ids.icms_value,
                "ipi_tax_id": pos_fiscal_map_ids.ipi_tax_id.id,
                "ipi_cst_id": pos_fiscal_map_ids.ipi_cst_id.id,
                "ipi_base": pos_fiscal_map_ids.ipi_base,
                "ipi_percent": pos_fiscal_map_ids.ipi_percent,
                "ipi_value": pos_fiscal_map_ids.ipi_value,
                "cofins_tax_id": pos_fiscal_map_ids.cofins_tax_id.id,
                "cofins_cst_id": pos_fiscal_map_ids.cofins_cst_id.id,
                "cofins_base": pos_fiscal_map_ids.cofins_base,
                "cofins_percent": pos_fiscal_map_ids.cofins_percent,
                "cofins_value": pos_fiscal_map_ids.cofins_value,
                "pis_tax_id": pos_fiscal_map_ids.pis_tax_id.id,
                "pis_cst_id": pos_fiscal_map_ids.pis_cst_id.id,
                "pis_base": pos_fiscal_map_ids.pis_base,
                "pis_percent": pos_fiscal_map_ids.pis_percent,
                "pis_value": pos_fiscal_map_ids.pis_value,
                "fiscal_tax_ids": fiscal_tax_ids,
            }
        )
        return vals

    @api.model
    def create_from_ui(self, orders, draft=False):
        local_timezone = pytz.timezone("America/Sao_Paulo")
        res = super(PosOrder, self).create_from_ui(orders, draft)
        for option in res:
            order = self.env["pos.order"].search([("id", "=", option["id"])])
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
        return res

    def cancel_nfce_from_ui(self, order_id, cancel_reason):
        order = self.env["pos.order"].search([("pos_reference", "=", order_id)])
        order.account_move.fiscal_document_id._document_cancel(cancel_reason)
        order.write({"state_edoc": order.account_move.fiscal_document_id.state_edoc})
        order.account_move.write({"state": "cancel"})
        return order.account_move.fiscal_document_id.state_edoc
