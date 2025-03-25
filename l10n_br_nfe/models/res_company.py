# Copyright 2019 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models

from ..constants.nfe import (
    DANFE_INVOICE_DISPLAY,
    DANFE_INVOICE_DISPLAY_DEFAULT,
    NFCE_DANFE_LAYOUT_DEFAULT,
    NFCE_DANFE_LAYOUTS,
    NFE_DANFE_LAYOUT_DEFAULT,
    NFE_DANFE_LAYOUTS,
    NFE_ENVIRONMENT_DEFAULT,
    NFE_ENVIRONMENTS,
    NFE_TRANSMISSION_DEFAULT,
    NFE_TRANSMISSIONS,
    NFE_VERSION_DEFAULT,
    NFE_VERSIONS,
)

PROCESSADOR_ERPBRASIL_EDOC = "oca"
PROCESSADOR = [(PROCESSADOR_ERPBRASIL_EDOC, "erpbrasil.edoc")]


class ResCompany(spec_models.SpecModel):
    _name = "res.company"
    _inherit = ["res.company", "nfe.40.emit"]
    _nfe_search_keys = ["nfe40_CNPJ", "nfe40_xNome", "nfe40_xFant"]

    nfe40_CNPJ = fields.Char(related="partner_id.nfe40_CNPJ")
    nfe40_CPF = fields.Char(related="partner_id.nfe40_CPF")
    nfe40_xNome = fields.Char(related="partner_id.legal_name")
    nfe40_xFant = fields.Char(related="partner_id.name")
    nfe40_IE = fields.Char(related="partner_id.nfe40_IE")
    nfe40_fone = fields.Char(related="partner_id.nfe40_fone")
    nfe40_CRT = fields.Selection(related="tax_framework")

    nfe40_enderEmit = fields.Many2one(
        comodel_name="res.partner",
        related="partner_id",
        readonly=False,
    )

    nfe40_choice_emit = fields.Selection(
        [("nfe40_CNPJ", "CNPJ"), ("nfe40_CPF", "CPF")],
        string="CNPJ ou CPF?",
        compute="_compute_nfe_data",
    )

    processador_edoc = fields.Selection(
        selection_add=PROCESSADOR,
    )

    nfe_version = fields.Selection(
        selection=NFE_VERSIONS,
        string="NFe Version",
        default=NFE_VERSION_DEFAULT,
    )

    nfe_environment = fields.Selection(
        selection=NFE_ENVIRONMENTS,
        string="NFe Environment",
        default=NFE_ENVIRONMENT_DEFAULT,
    )

    nfe_enable_sync_transmission = fields.Boolean(
        help=(
            "When enabled, this option configures the system to transmit the "
            "NFe (Electronic Invoice) using a synchronous method instead of an "
            "asynchronous one. This means that the system will wait for an immediate "
            "response from the tax authority's system (SEFAZ) upon submission of the "
            "NFe, providing quicker feedback on the submission status. Before "
            "activating this option, please ensure that the SEFAZ in your state "
            "supports synchronous processing for NFe submissions. Failure to verify "
            "compatibility may result in transmission errors or rejections."
        ),
    )

    nfe_separate_async_process = fields.Boolean(
        string="Separate NF-e Send and Consult",
        help=(
            "If enabled, the system will send the NF-e and store the receipt without "
            "immediately consulting it. The user must manually consult the receipt "
            "later. This option is valid only in asynchronous mode."
        ),
    )

    nfe_enable_contingency_ws = fields.Boolean(
        help=(
            "When enabled, all NFe-related services will be accessed using the "
            "contingencyweb services. This ensures that operations such as issuing, "
            "canceling, and consulting NFe will use the contingency web services "
            "instead of the primary web services."
        ),
    )

    nfe_transmission = fields.Selection(
        selection=NFE_TRANSMISSIONS,
        string="Transmission Type",
        default=NFE_TRANSMISSION_DEFAULT,
        help="1=Emissão normal (não em contingência);"
        "\n2=Contingência FS-IA, com impressão do DANFE em Formulário"
        " de Segurança - Impressor Autônomo;"
        "\n3=Contingência SCAN (Sistema de Contingência do Ambiente Nacional);"
        " *Desativado * NT 2015/002"
        "\n4=Contingência EPEC (Evento Prévio da Emissão em Contingência);"
        "\n5=Contingência FS-DA, com impressão do DANFE em Formulário "
        "de Segurança - Documento Auxiliar;"
        "\n6=Contingência SVC-AN (SEFAZ Virtual de Contingência do AN);"
        "\n7=Contingência SVC-RS (SEFAZ Virtual de Contingência do RS);"
        "\n9=Contingência off-line da NFC-e;"
        "\nObservação: Para a NFC-e somente é válida a opção de contingência:"
        "\n9-Contingência Off-Line e, a critério da UF, opção "
        "4-Contingência EPEC. (NT 2015/002)",
    )

    nfe_danfe_layout = fields.Selection(
        selection=NFE_DANFE_LAYOUTS,
        string="NFe Layout",
        default=NFE_DANFE_LAYOUT_DEFAULT,
    )

    nfce_danfe_layout = fields.Selection(
        selection=NFCE_DANFE_LAYOUTS,
        string="NFCe Layout",
        default=NFCE_DANFE_LAYOUT_DEFAULT,
    )

    nfe_default_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie",
        string="NF-e Default Serie",
    )

    nfe_authorize_accountant_download_xml = fields.Boolean(
        string="Include Accountant Partner data in persons authorized to "
        "download NFe XML",
        default=False,
    )

    nfe_authorize_technical_download_xml = fields.Boolean(
        string="Include Technical Support Partner data in persons authorized to "
        "download NFe XML",
        default=False,
    )

    nfce_qrcode_version = fields.Selection(
        selection=[("1", "1.00"), ("2", "2.00")],
        string="QRCode Version",
        default="2",
    )

    nfce_csc_token = fields.Char(
        string="CSC Token",
        help="Token CSC (Código de Segurança do Contribuinte) "
        "fornecido pela SEFAZ para a NFC-e",
    )

    nfce_csc_code = fields.Char(
        string="CSC Code",
        help="Código CSC (Código de Segurança do Contribuinte) "
        "fornecido pela SEFAZ para a NFC-e",
    )

    danfe_invoice_display = fields.Selection(
        selection=DANFE_INVOICE_DISPLAY,
        default=DANFE_INVOICE_DISPLAY_DEFAULT,
        help="Choose to generate a full or incomplete invoice frame in the DANFE.",
    )

    danfe_display_pis_cofins = fields.Boolean(
        default=False,
        help="Select whether PIS and COFINS should be displayed in DANFE.",
    )

    danfe_margin_top = fields.Integer(
        default=5, help="Top margin in mm for the DANFE layout."
    )

    danfe_margin_right = fields.Integer(
        default=5, help="Right margin in mm for the DANFE layout."
    )

    danfe_margin_bottom = fields.Integer(
        default=5, help="Bottom margin in mm for the DANFE layout."
    )

    danfe_margin_left = fields.Integer(
        default=5, help="Left margin in mm for the DANFE layout."
    )

    def _compute_nfe_data(self):
        # compute because a simple related field makes the match_record fail
        for rec in self:
            if rec.partner_id.is_company:
                rec.nfe40_choice_emit = "nfe40_CNPJ"
            else:
                rec.nfe40_choice_emit = "nfe40_CPF"

    def _build_attr(self, node, fields, vals, path, attr):
        if attr[0] == "enderEmit" and self.env.context.get("edoc_type") == "in":
            # we don't want to try build a related partner_id for enderEmit
            # when importing an NFe
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
            values["name"] = values.get("nfe40_xFant") or values.get("nfe40_xNome")
        return values
