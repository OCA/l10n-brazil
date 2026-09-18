# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from io import BytesIO

from brazilfiscalreport.danfe import (
    DanfeConfig,
    DecimalConfig,
    FontSize,
    FontType,
    FooterStamp,
    InvoiceDisplay,
    Margins,
    ProductDescriptionConfig,
    ReceiptPosition,
)

from odoo import fields, models

from ..constants.nfe import (
    DANFE_FONT_SIZE_DEFAULT,
    DANFE_FONT_SIZES,
    DANFE_FONT_TYPE_DEFAULT,
    DANFE_FONT_TYPES,
    DANFE_INVOICE_DISPLAY,
    DANFE_INVOICE_DISPLAY_DEFAULT,
    DANFE_RECEIPT_POSITION_DEFAULT,
    DANFE_RECEIPT_POSITIONS,
)

INVOICE_DISPLAYS = {
    "full_details": InvoiceDisplay.FULL_DETAILS,
    "duplicates_only": InvoiceDisplay.DUPLICATES_ONLY,
}

RECEIPT_POSITIONS = {
    "top": ReceiptPosition.TOP,
    "bottom": ReceiptPosition.BOTTOM,
}

FONT_TYPES = {
    "times": FontType.TIMES,
    "courier": FontType.COURIER,
}

FONT_SIZES = {
    "small": FontSize.SMALL,
    "big": FontSize.BIG,
}


class DanfeProfile(models.Model):
    """Printing options of the DANFE.

    Each company points to a profile, the same way it points to a
    report.paperformat, instead of stacking the brazilfiscalreport options
    into res.company.
    """

    _name = "l10n_br_nfe.danfe.profile"
    _description = "DANFE Profile"
    _order = "name"

    name = fields.Char(required=True, translate=True)

    active = fields.Boolean(default=True)

    company_ids = fields.Many2many(
        comodel_name="res.company",
        string="Companies",
        compute="_compute_company_ids",
        inverse="_inverse_company_ids",
        help="Companies printing their DANFEs with this profile. Adding a company "
        "here replaces its current profile.",
    )

    invoice_display = fields.Selection(
        selection=DANFE_INVOICE_DISPLAY,
        required=True,
        default=DANFE_INVOICE_DISPLAY_DEFAULT,
        help="Choose to generate a full or incomplete invoice frame in the DANFE.",
    )

    display_pis_cofins = fields.Boolean(
        string="Display PIS/COFINS",
        help="Select whether PIS and COFINS should be displayed in DANFE.",
    )

    margin_top = fields.Integer(default=5, help="Top margin in mm.")

    margin_right = fields.Integer(default=5, help="Right margin in mm.")

    margin_bottom = fields.Integer(default=5, help="Bottom margin in mm.")

    margin_left = fields.Integer(default=5, help="Left margin in mm.")

    receipt_position = fields.Selection(
        selection=DANFE_RECEIPT_POSITIONS,
        required=True,
        default=DANFE_RECEIPT_POSITION_DEFAULT,
        help="Position of the receipt (canhoto) in portrait DANFEs. "
        "Landscape DANFEs always print it on the left side.",
    )

    carrier_receipt = fields.Boolean(
        help="Print an extra receipt for the carrier to sign when collecting "
        "the goods, besides the delivery receipt. It is only printed when the "
        "NF-e has a carrier.",
    )

    font_type = fields.Selection(
        selection=DANFE_FONT_TYPES,
        required=True,
        default=DANFE_FONT_TYPE_DEFAULT,
    )

    font_size = fields.Selection(
        selection=DANFE_FONT_SIZES,
        required=True,
        default=DANFE_FONT_SIZE_DEFAULT,
    )

    price_precision = fields.Integer(
        string="Unit Price Precision",
        default=4,
        help="Number of decimal places used to print the unit prices.",
    )

    quantity_precision = fields.Integer(
        default=4,
        help="Number of decimal places used to print the quantities.",
    )

    infcpl_semicolon_newline = fields.Boolean(
        string="Break Additional Info on Semicolons",
        help="Start a new line at each semicolon (;) of the additional "
        "information (infCpl).",
    )

    display_product_additional_info = fields.Boolean(
        default=True,
        help="Print the product additional information (infAdProd) in the "
        "product description.",
    )

    display_lot = fields.Boolean(
        string="Display Lot Data",
        help="Print the traceability data (lot number, quantity, manufacturing "
        "and expiration dates) in the product description.",
    )

    lot_prefix = fields.Char(
        string="Lot Data Prefix",
        help="Text printed before the lot data of each product.",
    )

    display_anp = fields.Boolean(
        string="Display ANP Data",
        help="Print the ANP fuel data (product code, description and state of "
        "consumption) in the product description.",
    )

    display_anvisa = fields.Boolean(
        string="Display ANVISA Data",
        help="Print the ANVISA medicine data (product code and maximum consumer "
        "price) in the product description.",
    )

    footer_stamp_logo = fields.Binary(
        help="Logo printed at the bottom right corner of each DANFE page.",
    )

    footer_stamp_text = fields.Char(
        help="Text printed at the bottom of each DANFE page, to the left of the "
        "footer stamp logo.",
    )

    def _compute_company_ids(self):
        companies = self.env["res.company"].search(
            [("danfe_profile_id", "in", self._origin.ids)]
        )
        for profile in self:
            profile.company_ids = companies.filtered(
                lambda company, profile=profile: company.danfe_profile_id
                == profile._origin
            )

    def _inverse_company_ids(self):
        default_profile = self.env.ref(
            "l10n_br_nfe.danfe_profile_default", raise_if_not_found=False
        )
        for profile in self:
            current_companies = self.env["res.company"].search(
                [("danfe_profile_id", "=", profile.id)]
            )
            # The removed companies fall back to the default profile
            (current_companies - profile.company_ids).danfe_profile_id = (
                default_profile if default_profile != profile else False
            )
            (profile.company_ids - current_companies).danfe_profile_id = profile

    def _get_danfe_config(self, logo=None):
        """Translate the profile into the brazilfiscalreport DanfeConfig.

        Works on an empty recordset too, returning the default options.
        """
        profile = self or self.new({})
        profile.ensure_one()
        footer_stamp_logo = None
        if profile.footer_stamp_logo:
            footer_stamp_logo = BytesIO(base64.b64decode(profile.footer_stamp_logo))
        return DanfeConfig(
            logo=logo,
            margins=Margins(
                top=profile.margin_top,
                right=profile.margin_right,
                bottom=profile.margin_bottom,
                left=profile.margin_left,
            ),
            receipt_pos=RECEIPT_POSITIONS[profile.receipt_position],
            carrier_receipt=profile.carrier_receipt,
            decimal_config=DecimalConfig(
                price_precision=profile.price_precision,
                quantity_precision=profile.quantity_precision,
            ),
            invoice_display=INVOICE_DISPLAYS[profile.invoice_display],
            font_type=FONT_TYPES[profile.font_type],
            font_size=FONT_SIZES[profile.font_size],
            display_pis_cofins=profile.display_pis_cofins,
            infcpl_semicolon_newline=profile.infcpl_semicolon_newline,
            product_description_config=ProductDescriptionConfig(
                display_branch=profile.display_lot,
                display_anp=profile.display_anp,
                display_anvisa=profile.display_anvisa,
                branch_info_prefix=profile.lot_prefix or "",
                display_additional_info=profile.display_product_additional_info,
            ),
            footer_stamp=FooterStamp(
                logo=footer_stamp_logo,
                text=profile.footer_stamp_text or "",
            ),
        )
