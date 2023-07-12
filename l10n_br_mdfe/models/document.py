# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


def filtered_processador_edoc_mdfe(record):
    if record.processador_edoc == "oca" and record.document_type_id.code in ["57"]:
        return True
    return False


class MDFe(spec_models.StackedModel):

    _name = "l10n_br_fiscal.document"
    _inherit = ["l10n_br_fiscal.document", "mdfe.30.tmdfe_infmdfe"]
    _stacked = "mdfe.30.tmdfe_infmdfe"
    _field_prefix = "mdfe30_"
    _schame_name = "mdfe"
    _schema_version = "3.0.0"
    _odoo_module = "l10n_br_mdfe"
    _spec_module = "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_tipos_basico_v3_00"
    _spec_tab_name = "MDFe"
    _mdfe_search_keys = ["mdfe30_Id"]

    INFMDFE_TREE = """
    > <infMDFe>
        > <ide>
        - <emit> res.company
        - <infModal>
        - <infDoc> l10n_br_fiscal.document.related
        > <tot>
    """

    ##########################
    # MDF-e spec related fields
    ##########################

    ##########################
    # MDF-e tag: infMDFe
    ##########################

    mdfe30_versao = fields.Char(related="document_version")

    mdfe30_Id = fields.Char(
        compute="_compute_mdfe40_id_tag",
        inverse="_inverse_mdfe40_id_tag",
    )

    ##########################
    # MDF-e tag: id
    # Methods
    ##########################

    @api.depends("document_type_id", "document_key")
    def _compute_mdfe40_id_tag(self):
        """Set schema data which are not just related fields"""

        for record in self.filtered(filtered_processador_edoc_mdfe):
            if (
                record.document_type_id
                and record.document_type.prefix
                and record.document_key
            ):
                record.mdfe30_Id = "{}{}".format(
                    record.document_type.prefix, record.document_key
                )
            else:
                record.mdfe30_Id = False

    def _inverse_mdfe40_id_tag(self):
        for record in self:
            if record.cte40_Id:
                record.document_key = re.findall(r"\d+", str(record.mdfe30_Id))[0]
