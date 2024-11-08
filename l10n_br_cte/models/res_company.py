# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class ResCompany(spec_models.SpecModel):
    _name = "res.company"
    _inherit = ["res.company", "cte.40.emit"]
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
        selection=[
            ("1", "Normal"),
            ("2", "Regime Especial NFF"),
            ("4", "EPEC pela SVC"),
            ("5", "Contingência FSDA"),
            ("7", "Contingência SVC-RS"),
            ("8", "Contingência SVC-SP"),
        ],
        string="CT-e Transmission Type",
        default="1",
    )

    cte_type = fields.Selection(
        selection=[
            ("0", "CT-e Normal"),
            ("1", "CT-e de Complemento de Valores"),
            ("3", "CT-e de Substituição"),
        ],
        string="CT-e Type",
        default="0",
    )

    cte_environment = fields.Selection(
        selection=[("1", "Produção"), ("2", "Homologação")],
        string="CT-e Environment",
        default="2",
    )

    cte_version = fields.Selection(
        selection=[("3.00", "3.00"), ("4.00", "4.00")],
        string="CT-e Version",
        default="4.00",
    )

    # processador_edoc = fields.Selection(
    #     selection_add=[("erpbrasil.edoc", "erpbrasil.edoc")],
    # )

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

    cte40_CNPJ = fields.Char(related="partner_id.cte40_CNPJ")

    cte40_CPF = fields.Char(related="partner_id.cte40_CPF")

    cte40_xNome = fields.Char(related="partner_id.legal_name")

    cte40_xFant = fields.Char(related="partner_id.name")

    cte40_IE = fields.Char(related="partner_id.cte40_IE")

    cte40_fone = fields.Char(related="partner_id.cte40_fone")

    cte40_CRT = fields.Selection(related="tax_framework")

    cte40_choice_emit = fields.Selection(
        [("cte40_CNPJ", "CNPJ"), ("cte40_CPF", "CPF")],
        string="CNPJ ou CPF?",
        compute="_compute_cte_data",
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
