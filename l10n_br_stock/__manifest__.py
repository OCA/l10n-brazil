{
    "name": "Brazilian Localization Warehouse",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "http://odoo-brasil.org",
    "version": "12.0.1.0.0",
    "depends": ["stock", "l10n_br_base"],
    "data": ["views/stock_view.xml"],
    "demo": ["demo/res_users_demo.xml"],
    "installable": True,
    "auto_install": False,
    "post_init_hook": "post_init_hook",
}
