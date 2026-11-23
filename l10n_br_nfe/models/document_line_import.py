# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=consider-merging-classes-inherited

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal_edi.tools import EDI_IMPORT_NO_CREATE

# Char fields that mirror a registry record (NCM, CEST...): writing them when the
# record does not exist makes the ORM create an empty one.
REGISTRY_MIRROR_KEYS = (
    "nfe40_NCM",
    "nfe40_CEST",
    "nfe40_EXTIPI",
    "nfe40_CFOP",
    "nfe40_uCom",
    "nfe40_uTrib",
)


def _valid_gtin(code):
    """A GTIN-8, 12, 13 or 14 whose check digit is right ("SEM GTIN" is not)."""
    if not code or not code.isdigit() or len(code) not in (8, 12, 13, 14):
        return False
    digits = [int(digit) for digit in reversed(code[:-1])]
    total = sum(
        digit * (3 if index % 2 == 0 else 1) for index, digit in enumerate(digits)
    )
    return (10 - total % 10) % 10 == int(code[-1])


class DocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    partner_barcode = fields.Char(
        string="Barcode Declared by Partner",
        copy=False,
        readonly=True,
        help="Barcode (GTIN) as declared by the counterparty in the imported NF-e, "
        "when it is a valid one.",
    )

    @api.model
    def _build_attr(self, node, fields, vals, path, attr):
        result = super()._build_attr(node, fields, vals, path, attr)
        if not self.env.context.get(EDI_IMPORT_NO_CREATE):
            return result
        key = f"nfe40_{attr[0]}"
        declared = getattr(node, attr[0], None)
        if key in REGISTRY_MIRROR_KEYS:
            vals.pop(key, None)
        if key == "nfe40_vProd" and declared is not None:
            vals["partner_price_gross"] = float(declared)
        elif key in ("nfe40_cEAN", "nfe40_cEANTrib") and _valid_gtin(declared):
            vals["partner_barcode"] = declared
        elif key == "nfe40_NCM" and declared:
            vals["partner_ncm_code"] = str(declared)
        elif key in ("nfe40_uCom", "nfe40_uTrib") and declared:
            uom = self.env["uom.uom"]._match_by_fiscal_code(str(declared))
            if key == "nfe40_uCom":
                vals["partner_uom_code"] = str(declared)
                vals["uom_id"] = uom.id
            else:
                vals["uot_id"] = uom.id
        return result

    @api.model
    def _prepare_import_dict(
        self, values, model=None, parent_dict=None, defaults_model=None
    ):
        values = super()._prepare_import_dict(
            values, model, parent_dict, defaults_model
        )
        if self.env.context.get(EDI_IMPORT_NO_CREATE) and values.get(
            "partner_ncm_code"
        ):
            # the NCM of the file, not the one of the product that was matched
            values["ncm_id"] = (
                self.env["l10n_br_fiscal.ncm"]
                .search([("code_unmasked", "=", values["partner_ncm_code"])], limit=1)
                .id
            )
        return values

    def _get_partner_product_code(self):
        return self.nfe40_cProd or super()._get_partner_product_code()

    def _get_partner_product_name(self):
        return self.nfe40_xProd or super()._get_partner_product_name()

    def _edi_import_product_vals(self):
        vals = super()._edi_import_product_vals()
        if self.partner_barcode:
            vals["barcode"] = self.partner_barcode
        return vals

    def _get_supplierinfo_unit(self, supplierinfo):
        return supplierinfo.partner_uom_id, supplierinfo.partner_uom_factor

    def _prepare_supplierinfo_vals(self):
        vals = super()._prepare_supplierinfo_vals()
        declared = self.env["uom.uom"]._match_by_fiscal_code(self.partner_uom_code)
        if declared:
            # the factor only holds for the unit it was learned with
            vals.update(
                {
                    "partner_uom_id": declared.id,
                    "partner_uom_factor": self.import_uom_factor or 1.0,
                }
            )
        return vals
