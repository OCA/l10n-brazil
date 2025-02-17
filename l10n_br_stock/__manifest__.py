{
    "name": "Brazilian Localization Warehouse",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "16.0.1.0.4",
    "depends": ["stock", "l10n_br_base"],
    "data": ["views/stock_picking_view.xml"],
    "demo": [
        "demo/res_users_demo.xml",
        "demo/stock_location_demo.xml",
        "demo/res_company_demo.xml",
    ],
    "installable": True,
    "auto_install": False,
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
}
