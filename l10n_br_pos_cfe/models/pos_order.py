# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from base64 import b64decode

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    MODELO_FISCAL_CFE,
)

_logger = logging.getLogger(__name__)

try:
    from satcomum.ersat import ChaveCFeSAT
except ImportError:
    _logger.error("Biblioteca satcomum não instalada")


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)

        document_key = ui_order.get("document_key")
        document_type = ui_order.get("document_type")

        if document_key and document_type == MODELO_FISCAL_CFE:
            key = ChaveCFeSAT(document_key)
            order_fields.update(
                {
                    "document_number": key.numero_cupom_fiscal,
                    "document_serie": key.numero_serie,
                }
            )

        return order_fields

    def _prepare_invoice_vals(self):
        invoice_values = super()._prepare_invoice_vals()

        pos_config = self.env["pos.config"].browse(self.config_id.id)

        if pos_config.simplified_document_type == MODELO_FISCAL_CFE:
            document_type_id = pos_config.simplified_document_type_id
            fiscal_operation_id = pos_config.out_pos_fiscal_operation_id
            document_serie_id = pos_config.document_serie_id

            invoice_values.update(
                {
                    "document_type_id": document_type_id.id,
                    "fiscal_operation_id": fiscal_operation_id.id,
                    "document_key": self.document_key.replace("CFe", ""),
                    "document_number": self.document_number,
                    "state_edoc": self.state_edoc,
                    "status_code": self.status_code,
                    "status_name": self.status_name,
                    "operation_name": fiscal_operation_id.name,
                    "document_serie_id": document_serie_id.id,
                }
            )

        return invoice_values

    @api.model
    def _process_order(self, order_values, is_draft, existing_order):
        order_id = super()._process_order(order_values, is_draft, existing_order)
        order = self.env["pos.order"].browse(order_id)

        if order.document_type == MODELO_FISCAL_CFE:
            event_id = self._create_save_xml_event(order)
            self._save_event_file(event_id, order)
            self._update_event_vals(event_id)
            self._update_document_authorization_event(order, event_id)

        return order_id

    def _create_save_xml_event(self, order):
        authorization_file = b64decode(order.authorization_file.decode("utf-8")).decode(
            "utf-8"
        )
        fiscal_document = order.account_move.fiscal_document_id
        company = order.session_id.config_id.company_id

        return fiscal_document.event_ids.create_event_save_xml(
            company_id=company,
            environment=(
                EVENT_ENV_PROD
                if self.company_id.nfe_environment == "1"
                else EVENT_ENV_HML
            ),
            event_type="0",
            xml_file=authorization_file,
            document_id=fiscal_document,
        )

    def _save_event_file(self, event_id, order):
        authorization_file = b64decode(order.authorization_file.decode("utf-8")).decode(
            "utf-8"
        )

        event_id._save_event_file(
            file=authorization_file,
            file_extension="xml",
            authorization=True,
        )

    def _update_event_vals(self, event_id):
        event_id.write({"state": "done"})

    def _update_document_authorization_event(self, order, event_id):
        fiscal_document = order.account_move.fiscal_document_id
        fiscal_document.authorization_event_id = event_id
        fiscal_document.date_in_out = fields.Datetime.now()
