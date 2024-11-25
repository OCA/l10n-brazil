# Copyright 2023 KMEE INFORMATICA LTDA
# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models

from ..constants.cte import (
    CTE_ENVIRONMENT_DEFAULT,
    CTE_ENVIRONMENTS,
    CTE_TRANSMISSION_DEFAULT,
    CTE_TRANSMISSIONS,
    CTE_TYPE,
    CTE_TYPE_DEFAULT,
    CTE_VERSION_DEFAULT,
    CTE_VERSIONS,
)

PROCESSADOR_ERPBRASIL_EDOC = "oca"
PROCESSADOR = [(PROCESSADOR_ERPBRASIL_EDOC, "erpbrasil.edoc")]


class ResCompany(spec_models.SpecModel):
    _name = "res.company"
    _inherit = ["res.company", "cte.40.tcte_emit"]
    _cte_search_keys = ["cte40_CNPJ", "cte40_xNome", "cte40_xFant"]

    ##########################
    # CT-e models fields
    ##########################

    cte_default_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie",
        string="CT-e Default Serie",
    )

    cte_dacte_layout = fields.Selection(
        selection=[("1", "Paisagem"), ("2", "Retrato")],
        string="CT-e DACTE Layout",
        default="1",
    )

    cte_transmission = fields.Selection(
        selection=CTE_TRANSMISSIONS,
        string="CTe Transmission",
        copy=False,
        default=CTE_TRANSMISSION_DEFAULT,
    )

    cte_type = fields.Selection(
        selection=CTE_TYPE,
        string="CTe Type",
        default=CTE_TYPE_DEFAULT,
    )

    cte_environment = fields.Selection(
        selection=CTE_ENVIRONMENTS,
        string="CTe Environment",
        default=CTE_ENVIRONMENT_DEFAULT,
    )

    cte_version = fields.Selection(
        selection=CTE_VERSIONS,
        string="CTe Version",
        default=CTE_VERSION_DEFAULT,
    )

    processador_edoc = fields.Selection(
        selection_add=PROCESSADOR,
    )

    cte_authorize_accountant_download_xml = fields.Boolean(
        string="Include Accountant Partner data in persons authorized to "
        "download CTe XML",
        default=False,
    )

    cte40_enderEmit = fields.Many2one(
        comodel_name="res.partner",
        related="partner_id",
        readonly=False,
    )

    cte40_choice_emit = fields.Selection(
        [("cte40_CNPJ", "CNPJ"), ("cte40_CPF", "CPF")],
        string="CNPJ ou CPF?",
        compute="_compute_cte_data",
    )

    cte40_CNPJ = fields.Char(related="partner_id.cte40_CNPJ")

    cte40_CPF = fields.Char(related="partner_id.cte40_CPF")

    cte40_xNome = fields.Char(related="partner_id.legal_name")

    cte40_xFant = fields.Char(related="partner_id.name")

    cte40_IE = fields.Char(related="partner_id.cte40_IE")

    cte40_fone = fields.Char(related="partner_id.cte40_fone")

    cte40_CRT = fields.Selection(related="tax_framework")

    dacte_margin_top = fields.Integer(
        default=5, help="Top margin in mm for the DACTE layout."
    )

    dacte_margin_right = fields.Integer(
        default=5, help="Right margin in mm for the DACTE layout."
    )

    dacte_margin_bottom = fields.Integer(
        default=5, help="Bottom margin in mm for the DACTE layout."
    )

    dacte_margin_left = fields.Integer(
        default=5, help="Left margin in mm for the DACTE layout."
    )

    def _compute_cte_data(self):
        # compute because a simple related field makes the match_record fail
        for rec in self:
            if rec.partner_id.is_company:
                rec.cte40_choice_emit = "cte40_CNPJ"
            else:
                rec.cte40_choice_emit = "cte40_CPF"

    def _build_attr(self, node, fields, vals, path, attr):
        if attr[0] == "enderEmit" and self.env.context.get("edoc_type") == "in":
            # we don't want to try build a related partner_id for enderEmit
            # when importing an CTe
            # instead later the emit tag will be imported as the
            # document partner_id (dest) and the enderEmit data will be
            # injected in the same res.partner record.
            return
        return super()._build_attr(node, fields, vals, path, attr)

    @api.model
    def _prepare_import_dict(
        self, values, model=None, parent_dict=None, defaults_model=None
    ):
        # we disable enderEmit related creation with dry_run=True
        context = self._context.copy()
        context["dry_run"] = True
        values = super(ResCompany, self.with_context(**context))._prepare_import_dict(
            values, model, parent_dict, defaults_model
        )
        if not values.get("name"):
            values["name"] = values.get("cte40_xFant") or values.get("cte40_xNome")
        return values
