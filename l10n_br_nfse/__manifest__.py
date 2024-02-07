# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e",
    "summary": """
        NFS-e""",
    "version": "14.0.1.17.0",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["gabrielcardoso21", "mileo", "luismalta", "marcelsavegnago"],
    "website": "https://github.com/OCA/l10n-brazil",
    "external_dependencies": {
        "python": [
            "erpbrasil.edoc>=2.5.2",
            "erpbrasil.transmissao>=1.1.0",
            "erpbrasil.base>=2.3.0",
        ],
    },
    "depends": [
        "l10n_br_fiscal",
        "l10n_br_fiscal_certificate",
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
