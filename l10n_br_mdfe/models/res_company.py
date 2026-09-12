# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models

from ..constants.mdfe import (
    MDFE_EMIT_TYPE_DEFAULT,
    MDFE_EMIT_TYPES,
    MDFE_ENVIRONMENT_DEFAULT,
    MDFE_ENVIRONMENTS,
    MDFE_TRANSMISSION_DEFAULT,
    MDFE_TRANSMISSIONS,
    MDFE_TRANSP_TYPE,
    MDFE_TRANSP_TYPE_DEFAULT,
    MDFE_VERSION_DEFAULT,
    MDFE_VERSIONS,
)


class ResCompany(spec_models.SpecModel):
    _name = "res.company"
    _inherit = [
        "res.company",
        "mdfe.30.emit",
    ]
    _mdfe_search_keys = ["mdfe30_CNPJ", "mdfe30_xNome", "mdfe_xFant"]

    mdfe_version = fields.Selection(
        selection=MDFE_VERSIONS,
        string="MDFe Version",
        default=MDFE_VERSION_DEFAULT,
    )

    mdfe_environment = fields.Selection(
        selection=MDFE_ENVIRONMENTS,
        string="MDFe Environment",
        default=MDFE_ENVIRONMENT_DEFAULT,
    )

    mdfe_emit_type = fields.Selection(
        selection=MDFE_EMIT_TYPES,
        string="MDFe Emit Type",
        default=MDFE_EMIT_TYPE_DEFAULT,
    )

    mdfe_transp_type = fields.Selection(
        selection=MDFE_TRANSP_TYPE,
        string="MDFe Transp Type",
        default=MDFE_TRANSP_TYPE_DEFAULT,
    )

    mdfe_transmission = fields.Selection(
        selection=MDFE_TRANSMISSIONS,
        string="MDFe Transmission",
        copy=False,
        default=MDFE_TRANSMISSION_DEFAULT,
    )

    mdfe30_enderEmit = fields.Many2one(
        comodel_name="res.partner",
        related="partner_id",
        string="Endereço Emitente - MDFe",
    )

    mdfe30_CNPJ = fields.Char(related="partner_id.mdfe30_CNPJ")

    mdfe30_CPF = fields.Char(related="partner_id.mdfe30_CPF")

    mdfe30_xNome = fields.Char(related="partner_id.legal_name")

    mdfe30_xFant = fields.Char(related="partner_id.name")

    mdfe30_IE = fields.Char(related="partner_id.mdfe30_IE")

    mdfe30_fone = fields.Char(related="partner_id.mdfe30_fone")

    mdfe30_choice_emit = fields.Selection(
        [("mdfe30_CNPJ", "CNPJ"), ("mdfe30_CPF", "CPF")],
        string="MDFe emit CNPJ/CPF",
        compute="_compute_mdfe_data",
    )

    mdfe_authorize_accountant_download_xml = fields.Boolean(
        string="Include Accountant Partner data in persons authorized to "
        "download MDFe XML",
        default=False,
    )

    damdfe_margin_top = fields.Integer(
        default=5, help="Top margin in mm for the DAMDFE layout."
    )

    damdfe_margin_right = fields.Integer(
        default=5, help="Right margin in mm for the DAMDFE layout."
    )

    damdfe_margin_bottom = fields.Integer(
        default=5, help="Bottom margin in mm for the DAMDFE layout."
    )

    damdfe_margin_left = fields.Integer(
        default=5, help="Left margin in mm for the DAMDFE layout."
    )

    def _compute_mdfe_data(self):
        for rec in self:
            if rec.partner_id.is_company:
                rec.mdfe30_choice_emit = "mdfe30_CNPJ"
            else:
                rec.mdfe30_choice_emit = "mdfe30_CPF"

    def _build_attr(self, node, fields, vals, path, attr):
        if attr[0] == "enderEmit" and self.env.context.get("edoc_type") == "in":
            # we don't want to try build a related partner_id for enderEmit
            # when importing an MDFe
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
            values["name"] = values.get("mdfe30_xFant") or values.get("mdfe30_xNome")
        return values
