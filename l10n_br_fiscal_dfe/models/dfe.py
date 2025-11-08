# Copyright (C) 2025-Today - Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from lxml import etree

from odoo import _, api, fields, models

from ..constants.dfe import (
    OPERATION_TYPE,
    SITUACAO_NFE,
)

DFE_DESCRIPTION_MAP = {
    "procNFe": "XML NF-e completo (procNFe) via distribuição DF-e",
    "resNFe": "Resumo de NF-e (resNFe) via distribuição DF-e",
    "procEventoNFe": "XML de evento de NF-e (procEventoNFe) via distribuição DF-e",
    "resEvento": "Resumo de evento de NF-e (resEvento) via distribuição DF-e",
}


class DFe(models.Model):
    _name = "l10n_br_fiscal.dfe"
    _description = "DF-e"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _rec_name = "display_name"

    nfe_dfe_bundle_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.nfe_dfe_bundle", string="Chave de Acesso"
    )

    key = fields.Char(string="Access Key", size=44, related="nfe_dfe_bundle_id.key")

    serie = fields.Char(size=3, index=True)

    document_number = fields.Float(index=True, digits=(18, 0))

    emitter = fields.Char(size=60)

    vat = fields.Char(string="CNPJ/CPF", size=18)

    nsu = fields.Char(string="NSU", size=25, index=True)

    schema_type = fields.Char(
        help="Type of the DF-e document according to the XML schema.",
    )

    # Saida ou Entrada
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
        string="DF-e Type (NF-e)",
    )

    dfe_monitor_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.dfe_monitor",
        string="DFe Monitor",
    )

    attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        help="XML Attachment stored in Odoo.",
    )

    xml_pretty = fields.Text(string="XML Pretty", compute="_compute_xml_pretty")

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
        self.attachment_id = self.env["ir.attachment"].create(
            {
                "name": f"{self.schema_type}{self.key}.xml",
                "datas": base64.b64encode(xml),
                "description": DFE_DESCRIPTION_MAP.get(self.schema_type),
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

    def import_document(self):
        self.ensure_one()
        try:
            document = self.dfe_monitor_id._download_document(self.key)
            document_id = self.dfe_monitor_id._parse_xml_document(document)
        except Exception as e:
            self.message_post(
                body=_("Error importing document: \n\n %(error)s", error=e)
            )
            return
        if document_id:
            self.document_id = document_id

    def import_document_multi(self):
        for rec in self:
            rec.import_document()

    @api.depends("attachment_id")
    def _compute_xml_pretty(self):
        for rec in self:
            rec.xml_pretty = False
            data = rec.attachment_id.with_context(bin_size=False).datas
            if not data:
                continue
            xml_file = base64.b64decode(data)
            root = etree.fromstring(xml_file)
            rec.xml_pretty = etree.tostring(
                root,
                pretty_print=True,
                encoding="unicode",
            )
