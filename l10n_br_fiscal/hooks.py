# Copyright 2025-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import logging

_logger = logging.getLogger(__name__)


def fill_missing_xml_ids(env):
    """
    Backfill missing ir.model.data (XML IDs) for manually created records
    in every model that inherits l10n_br_fiscal.data.editable.mixin and
    implements _get_xml_id_name(). This ensures that manual records are
    tracked and can be properly updated or preserved during future module
    updates.

    This helper can also be called from a migration script when deploying
    the mixin on an existing database (post_init_hook only runs at install).
    """
    mixin = env["l10n_br_fiscal.data.editable.mixin"]
    for model_name in env.registry:
        model = env[model_name]
        if (
            model._auto
            and not model._abstract
            and isinstance(model, type(mixin))
            # skip models that don't implement their own naming convention:
            and type(model)._get_xml_id_name is not type(mixin)._get_xml_id_name
        ):
            model.fill_missing_xml_ids()


def post_init_hook(env):
    """Set company-dependent fiscal values on demo products and backfill the
    xml_ids of the fiscal data records created before the editable data mixin."""

    fill_missing_xml_ids(env)

    # Check if demo data is being installed
    if not env.ref("base.module_l10n_br_fiscal").demo:
        _logger.info(
            "Skipping fiscal demo post_init_hook: demo data not being installed."
        )
        return

    try:
        company_sn = env.ref("l10n_br_base.empresa_simples_nacional")
        company_lp = env.ref("l10n_br_base.empresa_lucro_presumido")
    except ValueError:
        _logger.warning("Brazilian demo companies not found, skipping hook.")
        return

    _logger.info(
        "Applying company-specific fiscal data for l10n_br_fiscal demo products."
    )

    # Map product XML IDs to the values that need to be set
    product_fiscal_data = {
        "product.product_product_1": {"fiscal_type": "09"},
        "product.product_product_2": {"fiscal_type": "09"},
        "product.expense_hotel": {"fiscal_type": "09"},
        "product.product_delivery_01": {"fiscal_type": "00", "icms_origin": "5"},
        "product.product_delivery_02": {"fiscal_type": "00", "icms_origin": "5"},
        "product.product_order_01": {"fiscal_type": "00", "icms_origin": "5"},
        "product.product_product_3": {"fiscal_type": "04", "icms_origin": "0"},
        "product.product_product_4": {"fiscal_type": "04", "icms_origin": "5"},
        "product.product_product_5": {"fiscal_type": "00", "icms_origin": "0"},
        "product.product_product_6": {"fiscal_type": "00", "icms_origin": "5"},
        "product.product_product_7": {"fiscal_type": "00", "icms_origin": "5"},
        "product.product_product_8": {"fiscal_type": "00", "icms_origin": "5"},
        "product.product_product_9": {"fiscal_type": "00", "icms_origin": "2"},
        "product.product_product_10": {"fiscal_type": "00", "icms_origin": "0"},
        "product.product_product_11": {"fiscal_type": "00", "icms_origin": "0"},
        "product.product_product_12": {"fiscal_type": "00", "icms_origin": "0"},
        "product.product_product_13": {"fiscal_type": "00", "icms_origin": "0"},
        "product.product_product_16": {"fiscal_type": "00", "icms_origin": "5"},
        "product.product_product_20": {"fiscal_type": "00", "icms_origin": "0"},
        "product.product_product_22": {"fiscal_type": "00", "icms_origin": "0"},
        "product.product_product_24": {"fiscal_type": "00", "icms_origin": "0"},
        "product.product_product_25": {"fiscal_type": "00", "icms_origin": "3"},
        "product.product_product_27": {"fiscal_type": "04", "icms_origin": "5"},
        "product.consu_delivery_03": {"fiscal_type": "00", "icms_origin": "0"},
        "product.consu_delivery_02": {"fiscal_type": "00", "icms_origin": "0"},
        "product.consu_delivery_01": {"fiscal_type": "04", "icms_origin": "0"},
        "product.expense_product": {"fiscal_type": "99"},
        "l10n_br_fiscal.customized_development_sale": {"fiscal_type": "09"},
    }

    for xml_id, values in product_fiscal_data.items():
        try:
            product_tmpl = env.ref(xml_id).product_tmpl_id
            product_tmpl.with_company(company_sn).write(values)
            product_tmpl.with_company(company_lp).write(values)
        except ValueError:
            _logger.warning(f"Could not find record for XML ID {xml_id}, skipping.")
        except Exception as e:
            _logger.error(f"Error setting fiscal data for {xml_id}: {e}")
