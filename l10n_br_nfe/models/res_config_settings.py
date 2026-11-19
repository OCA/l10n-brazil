# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    nfe_version = fields.Selection(
        string="NF-e Version",
        related="company_id.nfe_version",
        readonly=False,
    )

    nfe_environment = fields.Selection(
        string="NFe Environment",
        related="company_id.nfe_environment",
        readonly=False,
    )

    nfe_transmission = fields.Selection(
        string="NFe Transmission",
        related="company_id.nfe_transmission",
        readonly=False,
    )

    nfe_enable_sync_transmission = fields.Boolean(
        related="company_id.nfe_enable_sync_transmission",
        readonly=False,
    )

    nfe_danfe_layout = fields.Selection(
        string="NFe Layout",
        related="company_id.nfe_danfe_layout",
        readonly=False,
    )

    nfce_danfe_layout = fields.Selection(
        string="NFCe Layout",
        related="company_id.nfce_danfe_layout",
        readonly=False,
    )

    nfe_version_name = fields.Char(
        string="NFe Proc Version",
        config_parameter="l10n_br_nfe.version.name",
    )

    nfe_authorize_accountant_download_xml = fields.Boolean(
        string="Include Accountant Partner data in persons authorized to "
        "download NFe XML",
        related="company_id.nfe_authorize_accountant_download_xml",
        readonly=False,
    )

    nfe_authorize_technical_download_xml = fields.Boolean(
        string="Include Technical Support Partner data in persons authorized to "
        "download NFe XML",
        related="company_id.nfe_authorize_technical_download_xml",
        readonly=False,
    )
