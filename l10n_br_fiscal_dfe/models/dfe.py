# Copyright (C) 2025-Today - Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import fields, models

from ..constants.dfe import (
    OPERATION_TYPE,
    SITUACAO_NFE,
)


class DFe(models.Model):
    _name = "l10n_br_fiscal.dfe"
    _description = "DF-e"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _rec_name = "display_name"

    dfe_access_key_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.dfe_access_key", string="Chave de Acesso"
    )

    key = fields.Char(string="Access Key", size=44, related="dfe_access_key_id.key")

    serie = fields.Char(size=3, index=True)

    document_number = fields.Float(index=True, digits=(18, 0))

    emitter = fields.Char(size=60)

    vat = fields.Char(string="CNPJ/CPF", size=18)

    nsu = fields.Char(string="NSU", size=25, index=True)

    operation_type = fields.Selection(
        selection=OPERATION_TYPE,
    )

    document_amount = fields.Float(
        string="Document Total Value",
        readonly=True,
        digits=(18, 2),
    )

    ie = fields.Char(string="Inscrição estadual", size=18)

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier (partner)",
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        readonly=True,
    )

    emission_datetime = fields.Datetime(
        string="Emission Date",
        index=True,
        default=fields.Datetime.now,
    )

    inclusion_datetime = fields.Datetime(
        string="Inclusion Date",
        index=True,
        default=fields.Datetime.now,
    )

    inclusion_mode = fields.Char(size=255)

    document_state = fields.Selection(
        selection=SITUACAO_NFE,
        index=True,
    )

    cfop_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOPs",
    )

    dfe_nfe_document_type = fields.Selection(
        selection=[
            ("dfe_nfe_complete", "NF-e Completa"),
            ("dfe_nfe_summary", "Resumo da NF-e"),
            ("dfe_nfe_event", "Evento da NF-e"),
        ],
        string="DFe Document Type",
    )

    dfe_monitor_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.dfe_monitor",
        string="DFe Monitor",
    )

    attachment_id = fields.Many2one(comodel_name="ir.attachment")

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
    )

    event_type_dfe = fields.Char()

    def name_get(self):
        result = []
        for rec in self:
            document_type = dict(rec._fields["dfe_nfe_document_type"].selection).get(
                rec.dfe_nfe_document_type
            )
            result.append(
                (
                    rec.id,
                    f"{rec.key} - {document_type}",
                )
            )
        return result

    def create_xml_attachment(self, xml):
        file_name = "NFe%s.xml" % self.key
        self.attachment_id = self.env["ir.attachment"].create(
            {
                "name": file_name,
                "datas": base64.b64encode(xml),
                "store_fname": file_name,
                "description": "NFe via Manifesto",
                "res_model": self._name,
                "res_id": self.id,
            }
        )

    def action_download_xml(self):
        if len(self) == 1:
            return self.download_attachment(self.attachment_id)

        compressed_attachment_id = (
            self.env["l10n_br_fiscal.attachment"]
            .create([])
            .build_compressed_attachment(self.mapped("attachment_id"))
        )
        return self.download_attachment(compressed_attachment_id)

    def download_attachment(self, attachment_id):
        return {
            "type": "ir.actions.act_url",
            "url": (
                f"/web/content/{attachment_id.id}"
                f"/{attachment_id.name}?download=true"
            ),
            "target": "self",
        }
