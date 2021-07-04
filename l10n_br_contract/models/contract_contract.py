# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ContractContract(models.Model):
    _name = "contract.contract"
    _inherit = [_name, "l10n_br_fiscal.document.mixin"]

    currency_id = fields.Many2one(
        readonly=False,
    )

    @api.model
    def _fiscal_operation_domain(self):
        domain = [("state", "=", "approved")]
        return domain

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        contract_type = vals.get("contract_type")
        if contract_type:
            company_id = vals.get("company_id")
            if company_id:
                company_id = self.env["res.company"].browse(company_id)
            else:
                company_id = self.env.user.company_id
            if contract_type == "sale":
                fiscal_operation_id = company_id.contract_sale_fiscal_operation_id
            else:
                fiscal_operation_id = company_id.contract_purchase_fiscal_operation_id
            vals.update(
                {
                    "fiscal_operation_id": fiscal_operation_id.id,
                }
            )
        return vals

    cnpj_cpf = fields.Char(
        string="CNPJ/CPF",
        related="partner_id.cnpj_cpf",
    )

    legal_name = fields.Char(
        string="Legal Name",
        related="partner_id.legal_name",
    )

    ie = fields.Char(
        string="State Tax Number/RG",
        related="partner_id.inscr_est",
    )

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Fiscal Operation",
        domain=lambda self: self._fiscal_operation_domain(),
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="contract_comment_rel",
        column1="contract_id",
        column2="comment_id",
        string="Comments",
    )

    @api.multi
    def _get_amount_lines(self):
        """Get object lines instaces used to compute fields"""
        return self.mapped("contract_line_ids")

    @api.multi
    def _prepare_invoice(self, date_invoice, journal=None):
        self.ensure_one()
        invoice_vals = self._prepare_br_fiscal_dict()
        invoice_vals.update(super()._prepare_invoice(date_invoice, journal))
        return invoice_vals

    @api.model
    def _finalize_invoice_creation(self, invoices):
        super()._finalize_invoice_creation(invoices)

        for invoice in invoices:
            invoice.fiscal_document_id._onchange_document_serie_id()
            invoice.fiscal_document_id._onchange_company_id()

            for line in invoice.invoice_line_ids:
                line._onchange_product_id_fiscal()
                line.price_unit = line.contract_line_id.price_unit
                line._onchange_fiscal_operation_id()
                line._onchange_fiscal_tax_ids()

            invoice._onchange_invoice_line_ids()

    @api.multi
    def _prepare_recurring_invoices_values(self, date_ref=False):
        """
        Overwrite contract method to verify and create invoices according to
        the Fiscal Operation of each contract line
        :return: list of dictionaries (inv_ids)
        """
        super_inv_id = super()._prepare_recurring_invoices_values(date_ref=date_ref)

        if not self.fiscal_operation_id:
            for inv_id in super_inv_id:
                inv_id["document_type_id"] = False
            return super_inv_id

        if not isinstance(super_inv_id, list):
            super_inv_id = [super_inv_id]

        inv_ids = []
        document_type_list = []

        for invoice_id in super_inv_id:

            # Identify how many Document Types exist
            for inv_line in invoice_id.get("invoice_line_ids"):
                if type(inv_line[2]) == list:
                    continue
                operation_line_id = self.env["l10n_br_fiscal.operation.line"].browse(
                    inv_line[2].get("fiscal_operation_line_id")
                )

                fiscal_document_type = operation_line_id.get_document_type(
                    self.company_id
                )

                if fiscal_document_type.id not in document_type_list:
                    document_type_list.append(fiscal_document_type.id)
                    inv_to_append = invoice_id.copy()
                    inv_to_append["invoice_line_ids"] = [inv_line]
                    inv_to_append["document_type_id"] = fiscal_document_type.id
                    inv_to_append["document_serie_id"] = (
                        self.env["l10n_br_fiscal.document.serie"]
                        .search(
                            [
                                (
                                    "document_type_id",
                                    "=",
                                    inv_to_append["document_type_id"],
                                ),
                                ("company_id", "=", self.company_id.id),
                            ],
                            limit=1,
                        )
                        .id
                    )
                    inv_ids.append(inv_to_append)
                else:
                    index = document_type_list.index(fiscal_document_type.id)
                    inv_ids[index]["invoice_line_ids"].append(inv_line)

        return inv_ids

    @api.multi
    def recurring_create_invoice(self):
        """
        override the contract method to allow posting for more than one invoice
        """
        invoices = self._recurring_create_invoice()
        for invoice in invoices:
            self.message_post(
                body=_(
                    "Contract manually invoiced: "
                    '<a href="#" data-oe-model="%s" data-oe-id="%s">Invoice'
                    "</a>"
                )
                % (invoice._name, invoice.id)
            )
        return invoices
