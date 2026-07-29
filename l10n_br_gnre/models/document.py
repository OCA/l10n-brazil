# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

GNRE_DOCUMENT_TYPE = "23"

# Códigos de valor do layout 2.00, elemento itensGNRE/item/valor.
VALUE_TYPE_ICMS = "11"
VALUE_TYPE_FCP = "12"

# Modalidades do elemento tipoGnre.
GNRE_TYPE_SIMPLE = "0"
GNRE_TYPE_MULTI_DOCUMENT = "1"
GNRE_TYPE_MULTI_REVENUE = "2"


class Document(models.Model):
    """A guia GNRE, materializada como documento fiscal do tipo 23.

    A guia não tem linhas de produto: o que ela tem são itens, e cada item vem
    de uma obrigação de recolhimento. As notas que originaram os itens ficam em
    `document_related_ids`, que é o mecanismo que a localização já usa para
    documentos referenciados.
    """

    _inherit = "l10n_br_fiscal.document"

    gnre_obligation_ids = fields.One2many(
        comodel_name="l10n_br_gnre.obligation",
        inverse_name="guide_id",
        string="Obrigações",
        readonly=True,
    )

    gnre_obligation_count = fields.Integer(
        compute="_compute_gnre_obligation_count",
    )

    gnre_fiscal_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="UF Favorecida",
        readonly=True,
        help="Uma guia atende uma única UF favorecida.",
    )

    gnre_type = fields.Selection(
        selection=[
            (GNRE_TYPE_SIMPLE, "GNRE Simples"),
            (GNRE_TYPE_MULTI_DOCUMENT, "GNRE Múltiplos Documentos de Origem"),
            (GNRE_TYPE_MULTI_REVENUE, "GNRE Múltiplas Receitas"),
        ],
        string="Tipo da GNRE",
        readonly=True,
    )

    @api.depends("gnre_obligation_ids")
    def _compute_gnre_obligation_count(self):
        for record in self:
            record.gnre_obligation_count = len(record.gnre_obligation_ids)

    @api.model
    def _gnre_document_type(self):
        document_type = self.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", GNRE_DOCUMENT_TYPE)], limit=1
        )
        if not document_type:
            raise UserError(_("Tipo de documento fiscal 23 (GNRE) não encontrado."))
        return document_type

    @api.model
    def _gnre_type_for(self, obligations):
        """Pick the tipoGnre that matches what is actually in the guide."""
        documents = obligations.mapped("document_id")
        revenues = set(obligations.mapped("revenue_code"))
        if len(revenues) > 1:
            return GNRE_TYPE_MULTI_REVENUE
        if len(documents) > 1:
            return GNRE_TYPE_MULTI_DOCUMENT
        return GNRE_TYPE_SIMPLE

    @api.model
    def _prepare_gnre_guide(self, obligations):
        first = obligations[0]
        return {
            "company_id": first.company_id.id,
            "document_type_id": self._gnre_document_type().id,
            "document_date": fields.Datetime.now(),
            "partner_id": first.authority_partner_id.id,
            "gnre_fiscal_state_id": first.fiscal_state_id.id,
            "gnre_type": self._gnre_type_for(obligations),
        }

    @api.model
    def _create_gnre_guide(self, obligations):
        """Turn a batch of obligations into one guide.

        The batch is expected to come from `group_for_guides`, which already
        guarantees a single favoured state, a coherent due date and at most
        100 items.
        """
        if not obligations:
            raise UserError(_("Nenhuma obrigação para gerar a guia."))

        states = obligations.mapped("fiscal_state_id")
        if len(states) > 1:
            raise UserError(_("Uma guia não pode misturar mais de uma UF favorecida."))

        guide = self.create(self._prepare_gnre_guide(obligations))
        guide._gnre_reference_origin(obligations)
        obligations.write({"guide_id": guide.id, "state": "grouped"})
        return guide

    def _gnre_reference_origin(self, obligations):
        """Link the notes that originated the items to this guide."""
        self.ensure_one()
        related = self.env["l10n_br_fiscal.document.related"]
        for document in obligations.mapped("document_id"):
            related.create(
                {
                    "document_id": self.id,
                    "document_related_id": document.id,
                    "document_type_id": document.document_type_id.id,
                    "document_serie": document.document_serie,
                    "document_number": document.document_number,
                    "document_date": document.document_date,
                    "document_key": document.document_key,
                }
            )

    def action_view_gnre_obligations(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Obrigações"),
            "res_model": "l10n_br_gnre.obligation",
            "view_mode": "tree,form",
            "domain": [("guide_id", "=", self.id)],
        }

    def action_gnre_render_xml(self):
        """Return the lote XML for the selected guides."""
        return self.env["l10n_br_gnre.xml"].render_lote(self)
