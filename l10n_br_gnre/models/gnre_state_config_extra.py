# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

EXTRA_FIELD_TYPE = [
    ("T", "Texto"),
    ("N", "Número"),
    ("D", "Data"),
]

EXTRA_SOURCE = [
    ("document_date", "Data de emissão do documento de origem"),
    ("document_key", "Chave de acesso do documento de origem"),
    ("document_number", "Número do documento de origem"),
    ("fixed", "Valor fixo"),
]


class GnreStateConfigExtra(models.Model):
    """Campo extra que a UF exige no item da guia (camposExtras/campoExtra).

    O código e o tipo vêm da consulta de configurações da UF; o valor sai do
    documento de origem ou de um texto fixo.
    """

    _name = "l10n_br_gnre.state.config.extra"
    _description = "GNRE State Configuration Extra Field"
    _order = "config_id, code"

    config_id = fields.Many2one(
        comodel_name="l10n_br_gnre.state.config",
        required=True,
        ondelete="cascade",
    )

    code = fields.Integer(string="Código", required=True)

    name = fields.Char(string="Título")

    field_type = fields.Selection(
        selection=EXTRA_FIELD_TYPE,
        string="Tipo",
        default="T",
        required=True,
    )

    source = fields.Selection(
        selection=EXTRA_SOURCE,
        string="Origem do Valor",
        default="fixed",
        required=True,
    )

    fixed_value = fields.Char(string="Valor Fixo", size=100)

    def _value_for(self, obligation):
        """Text of the campoExtra for one obligation of the guide."""
        self.ensure_one()
        document = obligation.document_id
        if self.source == "document_date":
            date = fields.Date.to_date(document.document_date)
            return date.strftime("%Y-%m-%d") if date else False
        if self.source == "document_key":
            return document.document_key or False
        if self.source == "document_number":
            return document.document_number or False
        return self.fixed_value or False
