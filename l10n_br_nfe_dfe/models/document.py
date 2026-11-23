# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import _, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_PARTNER,
    FISCAL_IN,
    MODELO_FISCAL_NFE,
)

from ..constants.nfe_dfe import ACKNOWLEDGEMENT_DAYS, MANIFESTATION_GROUP

EVENT_TYPE_BY_OPTION = {"ciencia": "ciente", "confirmacao": "confirmado"}


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _after_document_authorize(self):
        result = super()._after_document_authorize()
        self._nfe_dfe_manifest_on_confirm()
        return result

    def _nfe_dfe_manifest_on_confirm(self):
        """Register the manifestation the company chose when an NF-e received
        from a supplier is confirmed. The event goes by a job, so a failure of
        the tax authority never undoes the confirmation."""
        self.ensure_one()
        event_type = EVENT_TYPE_BY_OPTION.get(
            self.company_id.nfe_manifest_on_document_confirm
        )
        if (
            not event_type
            or not self.imported_document
            or self.issuer != DOCUMENT_ISSUER_PARTNER
            or self.fiscal_operation_type != FISCAL_IN
            or self.document_type_id.code != MODELO_FISCAL_NFE
        ):
            return
        if not (self.env.su or self.env.user.has_group(MANIFESTATION_GROUP)):
            self.message_post(
                body=_(
                    "The manifestation of the recipient was not registered: it is "
                    "sent to the tax authority with the certificate of the company "
                    "and %s has no permission of NF-e user. Ask who has it to "
                    "register it."
                )
                % self.env.user.name
            )
            return
        if event_type == "ciente" and self._nfe_dfe_acknowledgement_expired():
            self.message_post(
                body=_(
                    "The acknowledgement of the operation was not registered: it "
                    "is only accepted until %s days after the authorization."
                )
                % ACKNOWLEDGEMENT_DAYS
            )
            return
        events = self.env["l10n_br_nfe.md_event"].sudo()
        if events.search_count(
            [
                ("access_key", "=", self.document_key),
                ("company_id", "=", self.company_id.id),
                ("event_type", "=", event_type),
            ]
        ):
            return
        self.with_delay(
            channel="root.dfe",
            description=_("Manifestation of %s on confirmation") % self.document_key,
        )._nfe_dfe_register_manifestation(event_type)

    def _nfe_dfe_acknowledgement_expired(self):
        self.ensure_one()
        authorized = self.authorization_date or self.document_date
        return bool(
            authorized
            and fields.Datetime.now() - authorized
            > timedelta(days=ACKNOWLEDGEMENT_DAYS)
        )

    def _nfe_dfe_register_manifestation(self, event_type):
        """Job: the event is sent with the certificate of the company, by who
        confirmed and has the permission of NF-e user (checked on confirm)."""
        self.ensure_one()
        dfe_document = (
            self.env["l10n_br_fiscal_dfe.document"]
            .sudo()
            .search(
                [
                    ("access_key", "=", self.document_key),
                    ("company_id", "=", self.company_id.id),
                ],
                limit=1,
            )
        )
        event = self.env["l10n_br_nfe.md_event"].create(
            {
                "access_key": self.document_key,
                "event_type": event_type,
                "company_id": self.company_id.id,
                "document_type": "nfe",
                "dfe_document_id": dfe_document.id,
            }
        )
        event.with_company(self.company_id).action_confirm()
