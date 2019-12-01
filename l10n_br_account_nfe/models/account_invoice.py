from odoo import api, fields
from odoo.addons.spec_driven_model.models import spec_models


class AccountInvoice(spec_models.SpecModel):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'spec.mixin']
    _concrete_skip = ('nfe.40.det',)  # will be mixed in later

#    nfe40_dest = fields.Many2one(related='partner_id')
    # TODO map nfe40_enderDest

    # TODO: with the fiscal doc inheritage and mapping
    # this should not be needed. However import fails without it...
    nfe40_dest = fields.Many2one(related='partner_id',
                                 comodel_name='res.partner')

    # TODO should be automatic?
    nfe40_det = fields.One2many(related='invoice_line_ids',
                                comodel_name='account.invoice.line',
                                inverse_name='invoice_id')
    nfe40_dhEmi = fields.Datetime(inverse='_inverse_dhEmi')

    fiscal_document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document',
        string='Fiscal Document',
        required=True,
        default=False)

    def _inverse_dhEmi(self):
        for inv in self:
            if inv.nfe40_dhEmi:
                inv.date_invoice = inv.nfe40_dhEmi.date()

    @api.model
    def _prepare_import_dict(self, vals, defaults={}):
        """As the invoice and the fiscal document can exist independently,
        inevitably they have some common fields. However to be able to
        write the fiscal document fields through the invoice, these fields
        have a special prefix. We keep them in sync here. It doesn't hurt
        so much as the vast majority of the fiscal fields are carried
        only by the fiscal document."""
        vals = super(AccountInvoice, self)._prepare_import_dict(vals,
                                                                defaults)
        sub_keys = [k for k in self.fields_get().keys()
            if k.startswith('fiscal_doc_') and k != 'fiscal_doc_state']
        sub_vals = {k: vals.get(k.replace('fiscal_doc_', '')) for k in\
                    sub_keys if vals.get(k.replace('fiscal_doc_', ''))}
        vals.update(sub_vals)
        return vals

    @api.model
    def create(self, vals):
        vals = self._prepare_import_dict(vals)
        res = super(AccountInvoice, self).create(vals)
        for line in res.invoice_line_ids:
            line.fiscal_document_line_id.document_id = res.fiscal_document_id.id
        return res

    @api.multi
    def write(self, vals):
        vals = self._prepare_import_dict(vals)
        return super(AccountInvoice, self).write(vals)


class AccountInvoiceLine(spec_models.SpecModel):
    _name = 'account.invoice.line'
    _inherit = ['account.invoice.line', 'spec.mixin']

    nfe40_qTrib = fields.Float(related='quantity')
    nfe40_cProd = fields.Char(related='product_id.code')
    nfe40_cEAN = fields.Char(related='product_id.barcode')
    nfe40_cEANTrib = fields.Char(related='product_id.barcode')
    nfe40_xProd = fields.Char(related='product_id.name')
    nfe40_vUnCom = fields.Float(related='price_unit')
    nfe40_vUnTrib = fields.Float(related='price_unit')
    nfe40_uCom = fields.Char(related='uom_id.name')
#    nfe40_vProd = fields.Char(related='price_gross')
#    nfe40_vFrete = fields.Char(related='') # freight
#    nfe40_vDesc = fields.Char(related='discount_value')
# TODO finish mapping
# see prototype here:
# https://github.com/akretion/l10n-brazil/blob/10.0-replace_pysped_for_nfelib/l10n_br_account_product/sped/nfe/document.py#L466
# TODO onchanges/warning and formatting

    fiscal_document_line_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.line',
        string='Fiscal Document Line',
        required=True,
        default=False)

    @api.model
    def _prepare_import_dict(self, vals, defaults={}):
        "see comments on the invoice _prepare_import_dict"
        vals = super(AccountInvoiceLine, self)._prepare_import_dict(vals,
                                                                    defaults)
        if not vals.get('name'):
            import_name = vals.get('nfe40_xProd') or vals.get('nfe40_cProd')
            if import_name is not None:
                vals['name'] = import_name

        if not vals.get('account_id'):
            if vals.get('product_id'):
                product = self.env['product.product'].browse(vals['product_id'])
                company_id = vals.get('company_id', defaults.get('company_id'))
                comp = self.env['res.company'].browse(company_id)
                inv_type = vals.get('type', defaults.get('type'))
                fpos = False  # TODO
                account = self.get_invoice_line_account(
                    inv_type, product, fpos, comp)
                vals['account_id'] = account.id

        # TODO use the same field names in fiscal doc line here?
        if vals.get('price_unit'):
            vals['fiscal_doc_line_price'] = vals.get('price_unit')
        if vals.get('amount_total'):
            vals['amount_total'] = vals.get('price_subtotal')

        # see AccountInvoice _prepare_import_dict
        sub_keys = [k for k in self.fields_get().keys()
            if k.startswith('fiscal_doc_line_')]
        sub_vals = {k: vals.get(k.replace('fiscal_doc_line_', '')) for k in\
                    sub_keys if vals.get(k.replace('fiscal_doc_line_', ''))}
        vals.update(sub_vals)
        return vals

    @api.model  #TODO create multi
    def create(self, vals):
        vals = self._prepare_import_dict(vals)
        line = super(AccountInvoiceLine, self).create(vals)
        line.fiscal_document_line_id.document_id =\
            line.invoice_id.fiscal_document_id.id
        return line

    @api.model
    def write(self, vals):
        vals = self._prepare_import_dict(vals)
        return super(AccountInvoiceLine, self).write(vals)
