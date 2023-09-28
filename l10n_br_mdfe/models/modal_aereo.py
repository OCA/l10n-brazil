# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class MDFeModalAereo(spec_models.StackedModel):
    _name = "l10n_br_mdfe.modal.aereo"
    _inherit = "mdfe.30.aereo"
    _stacked = "mdfe.30.aereo"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_aereo_v3_00"
    _field_prefix = "mdfe30_"
    _schema_name = "mdfe"
    _schema_version = "3.0.0"
    _odoo_module = "l10n_br_mdfe"
    _spec_module = "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_modal_aereo_v3_00"
    _spec_tab_name = "MDFe"
    _description = "Modal Aereo MDFe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_nac = fields.Char(related="document_id.airplane_nationality")

    mdfe30_matr = fields.Char(related="document_id.airplane_registration")

    mdfe30_nVoo = fields.Char(related="document_id.flight_number")

    mdfe30_dVoo = fields.Date(related="document_id.flight_date")

    mdfe30_cAerEmb = fields.Char(related="document_id.boarding_airfield")

    mdfe30_cAerDes = fields.Char(related="document_id.landing_airfield")

    def _prepare_damdfe_values(self):
        if not self:
            return {}

        return {
            "airplane_nationality": self.mdfe30_nac,
            "airplane_registration": self.mdfe30_matr,
            "flight_number": self.mdfe30_nVoo,
            "flight_date": self.mdfe30_dVoo.strftime("%d/%m/%y"),
            "boarding_airfield": self.mdfe30_cAerEmb,
            "landing_airfield": self.mdfe30_cAerDes,
        }
