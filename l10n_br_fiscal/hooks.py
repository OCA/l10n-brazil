import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """This hook is used to set company-dependent fiscal values
    on demo products for the Brazilian localization."""

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
