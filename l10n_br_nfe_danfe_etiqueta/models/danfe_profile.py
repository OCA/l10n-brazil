# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from brazilfiscalreport.danfe import DanfeEtiquetaConfig, Margins

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.l10n_br_nfe.models.danfe_profile import FONT_TYPES

# NT 2020.004: the label paper must be at least 55 mm wide.
ETIQUETA_MIN_PAPER_WIDTH = 55


class DanfeProfile(models.Model):
    _inherit = "l10n_br_nfe.danfe.profile"

    etiqueta_paper_width = fields.Integer(
        string="Label Paper Width",
        default=100,
        help="Width of the label paper in mm. The NT 2020.004 requires at "
        "least 55 mm; 100 x 150 mm is the usual shipping label format.",
    )

    etiqueta_paper_height = fields.Integer(
        string="Label Paper Height",
        default=150,
        help="Height of the label paper in mm.",
    )

    etiqueta_margin_top = fields.Integer(
        string="Label Top Margin", default=3, help="Top margin of the label in mm."
    )

    etiqueta_margin_right = fields.Integer(
        string="Label Right Margin",
        default=3,
        help="Right margin of the label in mm.",
    )

    etiqueta_margin_bottom = fields.Integer(
        string="Label Bottom Margin",
        default=3,
        help="Bottom margin of the label in mm.",
    )

    etiqueta_margin_left = fields.Integer(
        string="Label Left Margin", default=3, help="Left margin of the label in mm."
    )

    etiqueta_display_total = fields.Boolean(
        string="Label Displays the Total",
        default=True,
        help="Print the total amount of the NF-e in the label. Optional "
        "since the NT 2020.004 v1.10.",
    )

    etiqueta_display_delivery_address = fields.Boolean(
        string="Label Displays the Delivery Address",
        default=True,
        help="Print the delivery address in the label: the address of the "
        "recipient, or the one of the delivery group (entrega) when the NF-e "
        "has one.",
    )

    etiqueta_display_items = fields.Boolean(
        string="Label Displays the Items",
        help="Print the list of products in the label, as far as they fit "
        "in the page.",
    )

    @api.constrains("etiqueta_paper_width")
    def _check_etiqueta_paper_width(self):
        for profile in self:
            if profile.etiqueta_paper_width < ETIQUETA_MIN_PAPER_WIDTH:
                raise ValidationError(
                    _(
                        "The DANFE Simplificado - Etiqueta requires paper at "
                        "least %(width)s mm wide (NT 2020.004).",
                        width=ETIQUETA_MIN_PAPER_WIDTH,
                    )
                )

    def _get_danfe_etiqueta_config(self):
        """Translate the profile into the brazilfiscalreport
        DanfeEtiquetaConfig.

        Works on an empty recordset too, returning the default options.
        """
        profile = self or self.new({})
        profile.ensure_one()
        return DanfeEtiquetaConfig(
            paper_width=profile.etiqueta_paper_width,
            paper_height=profile.etiqueta_paper_height,
            margins=Margins(
                top=profile.etiqueta_margin_top,
                right=profile.etiqueta_margin_right,
                bottom=profile.etiqueta_margin_bottom,
                left=profile.etiqueta_margin_left,
            ),
            font_type=FONT_TYPES[profile.font_type],
            display_total=profile.etiqueta_display_total,
            display_delivery_address=profile.etiqueta_display_delivery_address,
            display_items=profile.etiqueta_display_items,
        )
