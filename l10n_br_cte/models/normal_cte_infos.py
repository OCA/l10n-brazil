# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class CTeNormalInfos(spec_models.StackedModel):
    _name = "l10n_br_cte.normal.infos"
    _inherit = ["cte.40.tcte_infctenorm"]
    _stacked = "cte.40.tcte_infctenorm"
    _field_prefix = "cte40_"
    _schema_name = "cte"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_cte"
    _spec_module = "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    _binding_module = "nfelib.cte.bindings.v4_0.cte_tipos_basico_v4_00"
    _spec_tab_name = "CTe"
    _description = "Grupo de informações do CTe Normal e Substituto"
    _force_stack_paths = "infctenorm.infdoc"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="document_id.company_id.currency_id",
    )

    cte40_vCarga = fields.Monetary(
        related="document_id.cte40_vCarga",
        currency_field="currency_id",
    )

    cte40_proPred = fields.Char(
        related="document_id.cte40_proPred",
    )

    cte40_xOutCat = fields.Char(
        related="document_id.cte40_xOutCat",
    )

    cte40_infQ = fields.One2many(
        comodel_name="l10n_br_cte.cargo.quantity.infos",
        related="document_id.cte40_infQ",
    )

    cte40_vCargaAverb = fields.Monetary(
        related="document_id.cte40_vCargaAverb",
    )

    cte40_veicNovos = fields.One2many(
        comodel_name="l10n_br_cte.transported.vehicles",
        related="document_id.cte40_veicNovos",
    )

    cte40_infNFe = fields.One2many(
        comodel_name="l10n_br_fiscal.document.related",
        related="document_id.document_related_ids",
    )
