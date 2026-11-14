# Copyright (C) 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants.duimp import DUIMP_DOCUMENT_TYPE_CODE

_logger = logging.getLogger(__name__)


class DocumentImportWizard(models.TransientModel):
    _inherit = "l10n_br_fiscal.document.import.wizard"

    duimp_number = fields.Char(string="DUIMP Number")

    duimp_version = fields.Integer(string="DUIMP Version")

    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
    )

    duimp_afrmm_value = fields.Monetary(
        string="AFRMM Total",
        currency_field="company_currency_id",
        help="Total AFRMM (Additional Freight for Renewal of the Merchant "
        "Marine) amount. This value is not returned by the DUIMP query "
        "API (it is handled by Siscomex Carga/Mercante) and must be "
        "entered manually from the DUIMP extract. It is allocated to "
        "each item proportionally to its customs value.",
    )

    duimp_siscomex_value = fields.Monetary(
        string="Siscomex Fee Total",
        currency_field="company_currency_id",
    )

    duimp_capatazia_value = fields.Monetary(
        string="Capatazia Total",
        currency_field="company_currency_id",
    )

    @api.onchange("duimp_number")
    def _onchange_duimp_number(self):
        self.duimp_version = 0

    def action_consult_duimp(self):
        """Query the Portal Único Siscomex, create/refresh the persistent
        DUIMP declaration and open it for reconciliation."""
        self.ensure_one()
        if not self.duimp_number:
            raise UserError(_("Please enter the DUIMP number!"))

        self._detect_document_type(DUIMP_DOCUMENT_TYPE_CODE)

        webservice = self.company_id._get_duimp_webservice()
        general_data = webservice.get_general_data(
            self.duimp_number, self.duimp_version or None
        )
        items = webservice.get_items(self.duimp_number, self.duimp_version or None)

        declaracao = self._get_or_create_declaracao()
        declaracao._import_from_payload(general_data, items)
        # Only the costs actually typed in the wizard are written back:
        # AFRMM and the Siscomex fee are read from the payload by
        # _prepare_header_totals_from_items, so writing the (empty) wizard
        # fields unconditionally would zero what was just imported.
        vals = {"state": "open"}
        for wizard_field, declaracao_field in (
            ("duimp_afrmm_value", "afrmm_amount"),
            ("duimp_siscomex_value", "siscomex_fee_amount"),
            ("duimp_capatazia_value", "handling_fee_amount"),
        ):
            value = self[wizard_field]
            if value:
                vals[declaracao_field] = value
        if self.fiscal_operation_id:
            vals["fiscal_operation_id"] = self.fiscal_operation_id.id
        declaracao.write(vals)
        if self.issuer_partner_id:
            declaracao.partner_id = self.issuer_partner_id
        return declaracao.get_formview_action()

    def _get_or_create_declaracao(self):
        declaracao_model = self.env["l10n_br_duimp.declaration"]
        # When no version is given, reuse the latest non-invoiced
        # declaration of this number: the payload bumps "versao" on
        # import, so filtering on versao == 0 here would create a
        # duplicate on the next query.
        domain = [
            ("number", "=", self.duimp_number),
            ("company_id", "=", self.company_id.id),
            ("state", "!=", "locked"),
        ]
        if self.duimp_version:
            domain.append(("version", "=", self.duimp_version))
        declaracao = declaracao_model.search(domain, order="version desc", limit=1)
        if not declaracao:
            create_vals = {
                "number": self.duimp_number,
                "version": self.duimp_version or 0,
                "company_id": self.company_id.id,
            }
            # Only pass the fiscal operation when the wizard has one, so
            # the model default (company import fiscal operation) is not
            # silently overridden with an empty value.
            if self.fiscal_operation_id:
                create_vals["fiscal_operation_id"] = self.fiscal_operation_id.id
            declaracao = declaracao_model.create(create_vals)
        return declaracao
