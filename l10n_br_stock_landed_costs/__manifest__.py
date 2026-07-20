# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Custos Adicionais de Estoque (Landed Costs) - Localização Brasileira",
    "summary": "Gera landed costs a partir de documentos fiscais de frete"
    " (CT-e) e despesas, pelo custo líquido",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "version": "16.0.1.0.0",
    "depends": [
        "stock_landed_costs",
        "l10n_br_stock_account",
    ],
    "data": [
        "views/fiscal_document_view.xml",
    ],
    "installable": True,
}
