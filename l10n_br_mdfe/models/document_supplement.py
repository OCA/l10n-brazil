# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo.addons.spec_driven_model.models import spec_models


class MDFeSupplement(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.supplement"
    _inherit = "mdfe.30.infmdfesupl"
    _stacked = "mdfe.30.infmdfesupl"
    _field_prefix = "mdfe30_"
    _schema_name = "mdfe"
    _schema_version = "3.0.0"
    _odoo_module = "l10n_br_mdfe"
    _spec_module = "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_tipos_basico_v3_00"
    _spec_tab_name = "MDFe"
