# Copyright (C) 2022  Renan Hiroki Bastos - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models

# from datetime import datetime


class NfeImport(models.TransientModel):
    """Importar XML Nota Fiscal Eletrônica"""

    _inherit = "l10n_br_nfe.import_xml"

    # TODO: Mover isso pro módulo l10n_br_nfe
    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Fiscal Operation",
    )

    def _create_edoc_from_xml(self):
        edoc = super()._create_edoc_from_xml()

        edoc.fiscal_operation_id = self.fiscal_operation_id

        invoice_values = {
            "partner_id": edoc.partner_id.id,
            "invoice_date": edoc.document_date,  # TODO: Arrumar datedue
            "move_type": "in_invoice",
        }
        invoice = self.env["account.move"].create(invoice_values)
        invoice.fiscal_document_id = edoc
        # TODO: Colocar operação e linhas de operação

        invoice_lines = self.env["account.move.line"]
        fiscal_position = self.env["account.fiscal.position"].browse(
            invoice.partner_id.property_account_position_id.id
        )
        for line in edoc.fiscal_line_ids:
            values = line._convert_to_write(line.read()[0])
            values.update(
                {
                    "move_id": invoice.id,
                    "exclude_from_invoice_tab": True,
                    # TODO: Adicionar lógica igual do stock_invoice_on_shipping para a conta
                    "account_id": fiscal_position.map_account(
                        line.product_id.categ_id.property_account_expense_categ_id
                    ).id,
                }
            )
            invoice_line = self.env["account.move.line"].create(values)
            invoice_line.fiscal_document_line_id = line
            invoice_line.exclude_from_invoice_tab = (
                False  # TODO: Criar novo campo para essa checagem
            )
            invoice_line.fiscal_operation_id = self.fiscal_operation_id
            invoice_line._onchange_fiscal_operation_id()
            invoice_lines += invoice_line
        # for dup in edoc.nfe40_dup:
        #     invoice_line = self.env['account.move.line'].new({
        #     'name': invoice.payment_reference or '',
        #     'debit': 0.0,
        #     'credit': dup.nfe40_vDup,
        #     'quantity': 1.0,
        #     'date_maturity': dup.nfe40_dVenc,
        #     'move_id': invoice.id,
        #     'currency_id': invoice.currency_id.id,
        #     'account_id': invoice.partner_id.property_account_payable_id.id,
        #     'partner_id': invoice.partner_id.id,
        #     'exclude_from_invoice_tab': True,
        # })
        # invoice_lines += invoice_line
        invoice.write({"line_ids": [(6, 0, invoice_lines.ids)]})

        if not self.partner_id:
            self.partner_id = edoc.partner_id

        self._attach_original_nfe_xml_to_document(edoc)
        self.imported_products_ids._find_or_create_product_supplierinfo()

        return edoc
