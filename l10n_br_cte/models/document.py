# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class CTe(spec_models.StackedModel):

    _name = "l10n_br_fiscal.document"
    _inherit = ["l10n_br_fiscal.document", "cte.40.tcte_infcte", "cte.40.tcte_fat"]
    _stacked = "cte.40.tcte_infcte"
    _field_prefix = "cte40_"
    _schema_name = "cte"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_cte"
    _spec_module = "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    _binding_module = "nfelib.cte.bindings.v4_0.cte_v4_00"
    _cte_search_keys = ["cte40_Id"]

    INFCTE_TREE = """
    > infCte
        > <ide>
        - <toma> res.partner
        > <emit> res.company
        > <dest> res.partner
        > <vPrest>
        > <imp>
        - <ICMS>
        - <ICMSUFFim>
        > <infCTeNorm>
        - <infCarga>
        - <infModal>"""

    ##########################
    # CT-e spec related fields
    ##########################

    ##########################
    # CT-e tag: infCte
    ##########################

    cte40_versao = fields.Char(related="document_version")

    cte40_Id = fields.Char(
        compute="_compute_cte40_Id",
        inverse="_inverse_cte40_Id",
    )

    ##########################
    # CT-e tag: Id
    # Methods
    ##########################

    @api.depends("document_type_id", "document_key")
    def _compute_cte40_Id(self):
        for record in self.filtered():
            if (
                record.document_type_id
                and record.document_type.prefix
                and record.document_key
            ):
                record.cte40_Id = "{}{}".format(
                    record.document_type.prefix, record.document_key
                )
            else:
                record.cte40_Id = False

    def _inverse_cte40_Id(self):
        for record in self:
            if record.cte40_Id:
                record.document_key = re.findall(r"\d+", str(record.cte40_Id))[0]
