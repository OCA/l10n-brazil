# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class Aereo(spec_models.StackedModel):
    _name = "l10n_br_cte.modal.aereo"
    _inherit = "cte.40.aereo"
    _stacked = "cte.40.aereo"
    _binding_module = "nfelib.cte.bindings.v4_0.cte_modal_aereo_v4_00"
    _field_prefix = "cte40_"
    _schema_name = "cte"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_cte"
    _spec_module = "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_modal_aereo_v4_00"
    _spec_tab_name = "CTe"
    _description = "Modal Aereo CTe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_dPrevAereo = fields.Date(related="document_id.flight_delivery_forecast")

    def _prepare_dacte_values(self):
        if not self:
            return {}


class Tarifa(spec_models.SpecModel):
    _name = "l10n_br_cte.modal.aereo.tarifa"
    _inherit = "cte.40.tarifa"
    _binding_module = "nfelib.cte.bindings.v4_0.cte_modal_aereo_v4_00"
    _description = "Informações de tarifa"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_CL = fields.Selection(
        string="Classe",
        selection=[
            ("M", "Tarifa Mínima"),
            ("G", "Tarifa Geral"),
            ("E", "Tarifa Específica"),
        ],
        store=True,
        default="G",
    )

    cte40_vTar = fields.Monetary(currency_field="brl_currency_id")


class NatCarga(spec_models.SpecModel):
    _name = "l10n_br_cte.modal.aereo.natcarga"
    _inherit = "cte.40.natcarga"
    _binding_module = "nfelib.cte.bindings.v4_0.cte_modal_aereo_v4_00"
    _description = "Natureza da carga"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_xDime = fields.Char(
        string="Dimensão",
        help=(
            "Dimensão\nFormato:1234X1234X1234 (cm). Esse campo deve sempre que"
            " possível ser preenchido. Entretanto, quando for impossível o "
            "preenchimento das dimensões, fica obrigatório o preenchimento da "
            "cubagem em metro cúbico do leiaute do CT-e da estrutura genérica "
            "(infQ)."
        ),
    )
