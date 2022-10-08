# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e",
    "summary": """
        NFS-e""",
    "version": "14.0.1.9.2",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["gabrielcardoso21", "mileo", "luismalta", "marcelsavegnago"],
    "website": "https://github.com/OCA/l10n-brazil",
    "external_dependencies": {
        "python": [
            "erpbrasil.edoc",
            "erpbrasil.assinatura",
            "erpbrasil.transmissao",
            "erpbrasil.base",
        ],
    },
    "depends": [
        "l10n_br_fiscal",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/document_view.xml",
        "views/product_template_view.xml",
        "views/product_product_view.xml",
        "views/document_line_view.xml",
        "views/res_company_view.xml",
        "report/danfse.xml",
    ],
    "demo": [
        "demo/product_demo.xml",
        "demo/fiscal_document_demo.xml",
    ],
}
