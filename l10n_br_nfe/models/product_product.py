# Copyright 2020 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.osv import expression


class ProductProduct(models.Model):
    _inherit = "product.product"
    _nfe40_odoo_module = "odoo.addons.l10n_br_nfe_spec.models.v4_0.leiaute_nfe_v4_00"
    _nfe_search_keys = ["default_code", "barcode"]

    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        domain_name, domain_barcode, domain_default_code = [], [], []

        if parent_dict.get("nfe40_xProd") and parent_dict.get("nfe40_cProd"):
            supplier_id = self.env["product.supplierinfo"].search(
                [
                    ("product_code", "=", parent_dict["nfe40_cProd"]),
                    ("product_name", "=", parent_dict["nfe40_xProd"]),
                ],
                limit=1,
            )
            if supplier_id and supplier_id.product_id:
                return supplier_id.product_id.id
        if parent_dict.get("nfe40_xProd"):
            rec_dict["name"] = parent_dict["nfe40_xProd"]
            domain_name = [("name", "=", rec_dict.get("name"))]

        if (
            parent_dict.get("nfe40_cEANTrib")
            and parent_dict["nfe40_cEANTrib"] != "SEM GTIN"
        ):
            rec_dict["barcode"] = parent_dict["nfe40_cEANTrib"]
            domain_barcode = [("barcode", "=", rec_dict.get("barcode"))]

        if parent_dict.get("nfe40_cProd"):
            rec_dict["default_code"] = parent_dict["nfe40_cProd"]
            domain_default_code = [("default_code", "=", rec_dict.get("default_code"))]

        domain = expression.OR([domain_name, domain_barcode, domain_default_code])
        match = self.search(domain, limit=1)
        if match:
            return match.id

        if self._context.get("dry_run"):
            rec_id = self.new(rec_dict).id
        else:
            rec_id = self.with_context(parent_dict=parent_dict).create(rec_dict).id
        return rec_id

    @api.model
    def _get_supplier_open_po_product_ids(self, supplier_id, company_id):
        """Ids of products with a not-fully-billed line on the supplier's
        confirmed/done purchase orders (soft dependency on ``purchase``)."""
        po_line_model = self.env.get("purchase.order.line")
        if po_line_model is None:
            return set()
        po_lines = po_line_model.sudo().search(
            [
                ("order_id.partner_id", "=", supplier_id),
                ("order_id.company_id", "=", company_id),
                ("order_id.state", "in", ("purchase", "done")),
            ]
        )
        return set(
            po_lines.filtered(
                lambda line: line.product_qty > line.qty_invoiced
            ).product_id.ids
        )

    @api.model
    def _name_search(
        self, name="", args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        """Propose the NFe supplier's open purchase-order products first.

        The fiscal document import wizard's product picker passes
        ``nfe_import_supplier_id`` and ``nfe_import_company_id`` in its
        context: the products on that supplier's confirmed purchase orders
        with quantity still to be billed are then proposed first in the
        many2one, while the search itself stays unrestricted so any other
        product remains selectable (typing filters the whole catalog).
        Without those context keys this is a plain ``super()`` pass-through.

        ``qty_to_invoice`` cannot be used as the "open" criterion: with the
        default ``purchase_method='receive'`` it is 0 until the goods are
        received, while the supplier NF-e typically arrives together with the
        truck. A search domain cannot compare two fields either, so the
        not-fully-billed check is done in Python over the confirmed/done
        order lines.
        """
        supplier_id = self.env.context.get("nfe_import_supplier_id")
        company_id = self.env.context.get("nfe_import_company_id")
        if not supplier_id or not company_id:
            return super()._name_search(
                name,
                args=args,
                operator=operator,
                limit=limit,
                name_get_uid=name_get_uid,
            )
        open_product_ids = self._get_supplier_open_po_product_ids(
            supplier_id, company_id
        )
        if not open_product_ids:
            return super()._name_search(
                name,
                args=args,
                operator=operator,
                limit=limit,
                name_get_uid=name_get_uid,
            )
        priority_args = expression.AND(
            [list(args or []), [("id", "in", list(open_product_ids))]]
        )
        priority_ids = super()._name_search(
            name,
            args=priority_args,
            operator=operator,
            limit=limit,
            name_get_uid=name_get_uid,
        )
        ids = super()._name_search(
            name,
            args=args,
            operator=operator,
            limit=limit,
            name_get_uid=name_get_uid,
        )
        merged = list(dict.fromkeys(list(priority_ids) + list(ids)))
        return merged[:limit] if limit else merged

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """Flag the supplier's open-PO products with a leading ``*``.

        ``name_search`` drives the many2one dropdown: prefixing a ``*`` marks
        the products still awaiting billing on the NFe supplier's confirmed
        purchase orders, so the operator can tell the proposed products apart
        from the rest of the (still fully searchable) catalog. The decoration
        only lives in the suggestion list — ``display_name``/``name_get`` are
        left untouched, so the selected value and every other view stay clean.
        """
        result = super().name_search(name, args=args, operator=operator, limit=limit)
        supplier_id = self.env.context.get("nfe_import_supplier_id")
        company_id = self.env.context.get("nfe_import_company_id")
        if not supplier_id or not company_id:
            return result
        open_product_ids = self._get_supplier_open_po_product_ids(
            supplier_id, company_id
        )
        if not open_product_ids:
            return result
        return [
            (pid, ("* " if pid in open_product_ids else "") + label)
            for pid, label in result
        ]

    @api.model
    def default_get(self, default_fields):
        """
        The nfe.40.prod mixin (prod XML tag) cannot be injected in
        the product.product object because the tag includes attributes from the
        Odoo fiscal document line and because we may have an Nfe with
        lines decsriptions instead of full blown products.
        So a part of the mapping is done
        in the fiscal document line:
        from Odoo -> XML by using related fields/_compute
        from XML -> Odoo by overriding the product default_get method
        """
        values = super().default_get(default_fields)
        parent_dict = self._context.get("parent_dict", {})
        if parent_dict.get("nfe40_xProd"):
            values["name"] = parent_dict["nfe40_xProd"]

        # Price Unit
        if parent_dict.get("nfe40_vUnCom"):
            values["standard_price"] = parent_dict.get("nfe40_vUnCom")
            values["list_price"] = parent_dict.get("nfe40_vUnCom")

        # Barcode
        if (
            parent_dict.get("nfe40_cEANTrib")
            and parent_dict["nfe40_cEANTrib"] != "SEM GTIN"
        ):
            values["barcode"] = parent_dict["nfe40_cEANTrib"]

        # NCM
        if parent_dict.get("nfe40_NCM"):
            ncm = self.env["l10n_br_fiscal.ncm"].search(
                [("code_unmasked", "=", parent_dict["nfe40_NCM"])], limit=1
            )

            values["ncm_id"] = ncm.id

            if not ncm:  # FIXME should not happen with prod data
                ncm = (
                    self.env["l10n_br_fiscal.ncm"]
                    .sudo()
                    .create(
                        {
                            "name": parent_dict["nfe40_NCM"],
                            "code": parent_dict["nfe40_NCM"],
                        }
                    )
                )
                values["ncm_id"] = ncm.id
        return values
