# Copyright (C) 2019-2020 - Raphael Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import logging

import nfelib
import pkg_resources
from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc

from odoo import SUPERUSER_ID, Command, api, fields
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # The companies created before the install don't get the field default,
    # as the profile record didn't exist yet when the column was created.
    env["res.company"].with_context(active_test=False).search(
        [("danfe_profile_id", "=", False)]
    ).danfe_profile_id = env.ref("l10n_br_nfe.danfe_profile_default")
    if env.ref("base.module_l10n_br_nfe").demo:
        res_items = (
            "nfe",
            "samples",
            "v4_0",
            "leiauteNFe",
            "35180834128745000152550010000474491454651420-nfe.xml",
        )
        resource_path = "/".join(res_items)
        nfe_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        binding = TnfeProc.from_xml(nfe_stream.read().decode())
        document_number = binding.NFe.infNFe.ide.nNF
        existing_nfes = env["l10n_br_fiscal.document"].search(
            [("document_number", "=", document_number)]
        )
        try:
            existing_nfes.unlink()
            env["l10n_br_fiscal.document"].import_binding_nfe(
                binding, edoc_type="in", dry_run=False
            )
        except ValidationError:
            _logger.info(f"NF-e already {document_number} imported by hooks")
        _create_import_match_demo(env)
    # NOTE: the candidate SQL view is rebuilt by the l10n_br_fiscal_edi
    # post_init_hook (which runs later in the graph) with the full registry.


def _create_import_match_demo(env):
    """Demo data for the NFe import "match source" feature.

    Created only on demo databases and only for the modules actually
    installed (soft dependencies): a confirmed purchase order when
    ``purchase`` is installed (its receipts come for free with
    ``purchase_stock``), or a standalone incoming picking when only
    ``stock`` is installed.

    The supplier is the issuer of the sample NFe imported just above and the
    product codes match its XML cProd values, so re-importing that same XML
    through the import wizard immediately shows the match source candidates:
    PO1 has the same product (1094) on two lines and 1095 is on both POs,
    demonstrating the multi-line / multi-order disambiguation.
    """
    supplier = env["res.partner"].search(
        [("cnpj_cpf_stripped", "=", "34128745000152")], limit=1
    )
    if not supplier:
        supplier = env["res.partner"].create(
            {
                "name": "NFe Match Demo Supplier",
                "cnpj_cpf": "34.128.745/0001-52",
            }
        )
    company = env.company
    products = {}
    for code, name in [
        ("1094", "GRANOLA TRADICIONAL 800G"),
        ("1095", "GRANOLA BANANA & MEL 800G"),
        ("1097", "GRANOLA ZERO 800G"),
    ]:
        product = env["product.product"].search([("default_code", "=", code)], limit=1)
        if not product:
            product = env["product.product"].create(
                {
                    "name": name,
                    "default_code": code,
                    "purchase_ok": True,
                    "type": "product" if env.get("stock.move") else "consu",
                }
            )
        products[code] = product

    if env.get("purchase.order") is not None:
        _create_import_match_demo_pos(env, supplier, company, products)
    elif env.get("stock.picking") is not None:
        _create_import_match_demo_picking(env, supplier, company, products)


def _create_import_match_demo_pos(env, supplier, company, products):
    PurchaseOrder = env["purchase.order"]
    if PurchaseOrder.search([("partner_id", "=", supplier.id)], limit=1):
        return  # idempotent
    has_fiscal = "fiscal_operation_id" in PurchaseOrder._fields
    for lines in [
        [(products["1094"], 2.0), (products["1095"], 5.0), (products["1094"], 1.0)],
        [(products["1095"], 3.0)],
    ]:
        vals = {
            "partner_id": supplier.id,
            "company_id": company.id,
            "order_line": [
                Command.create(
                    {
                        "product_id": product.id,
                        "name": product.name,
                        "product_qty": qty,
                        "price_unit": 10.0,
                        "date_planned": fields.Datetime.now(),
                    }
                )
                for product, qty in lines
            ],
        }
        if has_fiscal and company.purchase_fiscal_operation_id:
            vals["fiscal_operation_id"] = company.purchase_fiscal_operation_id.id
        order = PurchaseOrder.create(vals)
        try:
            order.with_context(tracking_disable=True).button_confirm()
        except ValidationError as err:
            _logger.warning("NFe match demo PO %s left draft: %s", order.name, err)


def _create_import_match_demo_picking(env, supplier, company, products):
    """Stock-but-no-purchase scenario: a standalone incoming picking."""
    StockPicking = env["stock.picking"]
    if StockPicking.search(
        [("partner_id", "=", supplier.id), ("state", "not in", ("done", "cancel"))],
        limit=1,
    ):
        return  # idempotent
    picking_type = env["stock.picking.type"].search(
        [("code", "=", "incoming"), ("company_id", "=", company.id)], limit=1
    )
    if not picking_type:
        return
    location_src = env.ref("stock.stock_location_suppliers", raise_if_not_found=False)
    if not location_src or not picking_type.default_location_dest_id:
        return
    picking = StockPicking.create(
        {
            "partner_id": supplier.id,
            "picking_type_id": picking_type.id,
            "location_id": location_src.id,
            "location_dest_id": picking_type.default_location_dest_id.id,
            "move_ids": [
                Command.create(
                    {
                        "name": products["1094"].name,
                        "product_id": products["1094"].id,
                        "product_uom_qty": 4.0,
                        "product_uom": products["1094"].uom_id.id,
                        "location_id": location_src.id,
                        "location_dest_id": picking_type.default_location_dest_id.id,
                    }
                )
            ],
        }
    )
    picking.action_confirm()
