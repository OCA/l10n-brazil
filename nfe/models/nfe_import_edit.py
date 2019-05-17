# -*- coding: utf-8 -*-
# Copyright (C) 2015 Trustcode - www.trustcode.com.br
#              Danimar Ribeiro <danimaribeiro@gmail.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import cPickle

from odoo import api, fields, models
from odoo.exceptions import Warning as UserError
from odoo.tools.translate import _


class NfeImportEdit(models.TransientModel):
    _name = 'nfe.import.edit'

    @api.multi
    def name_get(self):
        return [(rec.id,
                 u"Editando NF-e ({0})".format(
                     rec.number)) for rec in self]

    @api.multi
    def _default_category(self):
        return self.env['ir.model.data'].get_object_reference(
            'product', 'product_category_all')[1]

    def _default_company(self):
        return self.env.user.company_id

    company_id = fields.Many2one('res.company', string="Empresa",
                                 default=_default_company)
    currency_id = fields.Many2one(related='company_id.currency_id',
                                  string='Moeda', readonly=True)
    xml_data = fields.Binary(string="Xml Data", readonly=True)
    edoc_input = fields.Binary(u'Arquivo do documento eletrônico',
                               help=u'Somente arquivos no formato TXT e XML')
    file_name = fields.Char('File Name', size=128)

    number = fields.Char(string="Número", size=20, readonly=True)
    supplier_id = fields.Many2one('res.partner', string="Fornecedor",
                                  readonly=True)

    natureza_operacao = fields.Char(string="Natureza da operação", size=200,
                                    readonly=True)
    amount_total = fields.Float(string="Valor Total", digits=(18, 2),
                                readonly=True)

    import_from_invoice = fields.Boolean(u'Importar da fatura')
    account_invoice_id = fields.Many2one('account.invoice',
                                         u'Fatura de compra',
                                         readonly=True)
    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal')
    fiscal_position = fields.Many2one(
        'account.fiscal.position', 'Posição Fiscal',
        domain="[('fiscal_category_id','=',fiscal_category_id)]")

    product_import_ids = fields.One2many('nfe.import.products',
                                         'nfe_import_id', string="Produtos")
    create_product = fields.Boolean(
        u'Criar produtos automaticamente?', default=True,
        help=u'Cria o produto automaticamente caso não seja informado um')

    create_suplierinfo = fields.Boolean(
        u'Criar informações de fornecedor automaticamente?', default=False,
        help=u'Cria informações do fornecedor '
             u'automaticamente caso não seja informado um'
    )

    product_category_id = fields.Many2one('product.category',
                                          u'Categoria Produto',
                                          default=_default_category)

    @api.model
    def create(self, values):
        return super(NfeImportEdit, self).create(values)

    def _validate(self):
        indice = 0
        for item in self.product_import_ids:
            if self.import_from_invoice and not item.invoice_line_id:
                raise UserError(
                    u'Escolha a linha da fatura correspondente: {0} - {1}'
                    .format(str(indice), item.product_xml))
            if self.import_from_invoice and \
                    item.invoice_line_id.product_id.id != item.product_id.id:
                raise UserError(
                    u'Produto incompatível com a linha da fatura: {0} - {1}'
                    .format(str(indice), item.product_xml))
            if self.import_from_invoice and \
                    item.quantity_xml != item.invoice_line_id.quantity:
                raise UserError(
                    u'Quantidades do produto incompatíveis:\n\
                    Quantidade xml: {0} - Quantidade Fatura: {1}'
                    .format(str(indice), item.product_xml))
            if not item.product_id:
                raise UserError(u'Escolha o produto do item {0} - {1}'.format(
                    str(indice), item.product_xml))
            if not item.cfop_id:
                raise UserError(u'Escolha a CFOP do item {0} - {1}'.format(
                    str(indice), item.product_xml))

            if not item.uom_id:
                raise UserError(u'Escolha a Unidade do item {0} - {1}'.format(
                    str(indice), item.product_xml))

            if item.product_id.uom_po_id.category_id.id != \
                    item.uom_id.category_id.id:
                raise UserError(u'Unidades de medida incompatíveis no item \
                            {0} - {1}'.format(str(indice), item.product_xml))
            indice += 1

    @api.multi
    def confirm_values(self):
        self.ensure_one()
        inv_values = cPickle.loads(self.xml_data)
        inv_values['journal_id'] = self.env['account.journal'].search(
            [], limit=1).id

        for index, item in enumerate(self.product_import_ids):
            line = inv_values['invoice_line'][index][2]

            if not item.product_id:
                if self.create_product:
                    product_created = self.product_create(
                        inv_values, line, item, self.product_category_id)
                    item.product_id = product_created
                    item.uom_id = product_created.uom_id

                    line['product_id'] = product_created.id
                    line['uos_id'] = product_created.uom_id.id
                    line['account_id'] = (
                        product_created.property_account_income_id.id or
                        product_created.product_tmpl_id.categ_id.
                        property_account_income_categ_id.id)

                    if self.create_suplierinfo:
                        self.env['product.supplierinfo'].create({
                            'name': self.supplier_id.id,
                            'product_name': item.product_xml,
                            'product_code': item.code_product_xml,
                            'product_tmpl_id':
                                item.product_id.product_tmpl_id.id
                        })

            else:
                line['product_id'] = item.product_id.id
                line['account_id'] = (
                    item.product_id.property_account_income_id or
                    item.product_id.categ_id.property_account_income_categ_id
                ).id
                line['uos_id'] = item.uom_id.id
                line['cfop_id'] = item.cfop_id.id

                if self.create_suplierinfo:
                    total_recs = self.env['product.supplierinfo'].search_count(
                        [('name', '=', self.supplier_id.id),
                         ('product_code', '=', item.code_product_xml)]
                    )
                    if total_recs == 0:
                        self.env['product.supplierinfo'].create({
                            'name': self.supplier_id.id,
                            'product_name': item.product_xml,
                            'product_code': item.code_product_xml,
                            'product_tmpl_id':
                                item.product_id.product_tmpl_id.id
                        })

            inv_values['invoice_line'][index][2].update(
                self.fiscal_position.fiscal_position_map(line)
            )

        self._validate()

        invoice = self.save_invoice_values(inv_values)
        if not self.account_invoice_id:
            self.create_stock_picking(invoice)
        self.attach_doc_to_invoice(invoice.id, self.edoc_input,
                                   self.file_name)

        res = self.env.ref('account.action_invoice_tree2').read()[0]
        res['domain'] = res['domain'][:-1] + \
            ",('id', 'in', %s)]" % [invoice.id]
        return res

    @api.multi
    def save_invoice_values(self, inv_values):
        self.ensure_one()

        existing_invoice = self.env['account.invoice'].search([
            ('company_id', '=', inv_values['company_id']),
            ('nfe_access_key', '=', inv_values['nfe_access_key']),
        ])

        if existing_invoice and not self.account_invoice_id:
            self.account_invoice_id = existing_invoice.ensure_one()

        if self.account_invoice_id:
            selected_nfe_key = self.account_invoice_id.nfe_access_key
            if existing_invoice:
                existing_key = existing_invoice.nfe_access_key
                if selected_nfe_key and selected_nfe_key != existing_key:
                    raise UserError(
                        'Existe NFe cadastrada na empresa com a chave de ' +
                        'acesso que consta no XML fornecedido. Esta chave ' +
                        'difere da chave de acesso da NFe a ser vinculada.')
            else:
                if (selected_nfe_key and
                        selected_nfe_key != inv_values['nfe_access_key']):
                    raise UserError(_(
                        'A NFe a ser vinculada possui chave de acesso ' +
                        'diferente da que consta no XML fornecido.'))

            vals = {
                'serie_nfe': inv_values['serie_nfe'],
                'fiscal_document_id': inv_values['fiscal_document_id'],
                'date_hour_invoice': inv_values['date_hour_invoice'],
                'date_in_out': inv_values['date_in_out'],
                'supplier_invoice_number': inv_values[
                    'supplier_invoice_number'],
                'comment': inv_values['comment'],
                'fiscal_comment': inv_values['fiscal_comment'],
                'nfe_access_key': inv_values['nfe_access_key'],
                'nfe_version': inv_values['nfe_version'],
                'nfe_purpose': inv_values['nfe_purpose'],
                'freight_responsibility': inv_values['freight_responsibility'],
                'carrier_name': inv_values['carrier_name'],
                'vehicle_plate': inv_values['vehicle_plate'],
                'amount_freight': inv_values['amount_freight'],
                'amount_insurance': inv_values['amount_insurance'],
                'amount_costs': inv_values['amount_costs'],
                'fiscal_document_related_ids': inv_values[
                    'fiscal_document_related_ids']
            }
            self.account_invoice_id.write(vals)

            index = 0
            for item in self.product_import_ids:
                line_xml = inv_values['invoice_line'][index][2]
                vals = {
                    'cfop_id': (item.invoice_line_id.cfop_id.id or
                                item.cfop_id.id),
                    'invoice_id': self.account_invoice_id.id,
                }
                line_xml.update(vals)
                if item.invoice_line_id:
                    item.invoice_line_id.write(line_xml)
                else:
                    item.invoice_line_id = \
                        self.env['account.invoice.line'].create(line_xml)
                index += 1

            self.account_invoice_id._compute_amount()

            return self.account_invoice_id
        else:
            invoice = self.env['account.invoice'].create(inv_values)
            invoice._compute_amount()

            return invoice

    @api.multi
    def product_create(
            self, inv_values, line, item_grid, default_category=None):
        if not line['fiscal_classification_id']:
            fc_env = self.env['account.product.fiscal.classification']
            ncm = fc_env.search([('name', '=', line['ncm_xml'])], limit=1)
            if not ncm:
                ncm = fc_env.create({
                    'name': line['ncm_xml'],
                    'company_id': inv_values['company_id'],
                    'type': 'normal'
                })
            line['fiscal_classification_id'] = ncm.id

        vals = {
            'name': line['product_name_xml'],
            'type': 'product',
            'fiscal_type': 'product',
            'fiscal_classification_id': line['fiscal_classification_id'],
            'default_code': line['product_code_xml'],
        }

        if default_category:
            vals['categ_id'] = default_category.id

        if self.env['barcode.nomenclature'].check_ean(line['ean_xml']):
            vals['barcode'] = line['ean_xml']

        if item_grid.uom_id:
            vals['uom_id'] = item_grid.uom_id.id
            vals['uom_po_id'] = item_grid.uom_id.id

        product_tmpl = self.env['product.template'].create(vals)
        return product_tmpl.product_variant_ids[0]

    def create_stock_picking(self, invoice):
        warehouse = self.env['stock.warehouse'].search([
            ('partner_id', '=', self.env.user.company_id.partner_id.id)
        ])
        picking_type_id = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', warehouse.id), ('code', '=', 'incoming')
        ])

        picking_vals = {
            'name': '/',
            'origin': 'Fatura: %s-%s' % (invoice.fiscal_number,
                                         invoice.document_serie_id.code),
            'partner_id': invoice.partner_id.id,
            'invoice_state': 'invoiced',
            'fiscal_category_id': invoice.fiscal_category_id.id,
            'fiscal_position': invoice.fiscal_position_id.id,
            'picking_type_id': picking_type_id.id,
            'move_lines': [],
            'invoice_ids': [(4, invoice.id)],
            'location_id': picking_type_id.default_location_src_id.id,
            'location_dest_id':
                picking_type_id.default_location_dest_id.id,
        }
        for line in invoice.invoice_line_ids:
            move_vals = {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_id.uom_po_id.id,
                'invoice_state': 'none',
                'fiscal_category_id': line.fiscal_category_id.id,
                'fiscal_position': line.fiscal_position.id,
                'location_id': picking_type_id.default_location_src_id.id,
                'location_dest_id':
                    picking_type_id.default_location_dest_id.id,
            }
            picking_vals['move_lines'].append((0, 0, move_vals))

        picking = self.env['stock.picking'].create(picking_vals)
        picking.action_confirm()

    @api.onchange('fiscal_position')
    def position_fiscal_onchange(self):
        for item in self.product_import_ids:
            item.cfop_id = self.fiscal_position.cfop_id.id

    def attach_doc_to_invoice(self, invoice_id, doc, file_name):
        obj_attachment = self.env['ir.attachment']

        attachment_id = obj_attachment.create({
            'name': file_name,
            'datas': doc,
            'description': _('Xml de entrada NF-e'),
            'res_model': 'account.invoice',
            'res_id': invoice_id
        })
        return attachment_id


class NfeImportProducts(models.TransientModel):
    _name = 'nfe.import.products'

    nfe_import_id = fields.Many2one('nfe.import.edit', string="Nfe Import")
    invoice_id = fields.Many2one(
        'account.invoice',
        related='nfe_import_id.account_invoice_id')

    invoice_line_id = fields.Many2one(
        'account.invoice.line', string='Linha da fatura',
        domain="[('invoice_id', '=', invoice_id)]")
    product_id = fields.Many2one('product.product', string="Produto")
    uom_id = fields.Many2one('product.uom', string="Unidade de Medida")
    cfop_id = fields.Many2one('l10n_br_account_product.cfop', string="CFOP")

    code_product_xml = fields.Char(
        string="Código Forn.", size=20, readonly=True)
    product_xml = fields.Char(string="Produto Forn.", size=120, readonly=True)
    uom_xml = fields.Char(string="Un. Medida Forn.", size=10, readonly=True)
    cfop_xml = fields.Char(string="CFOP Forn.", size=10, readonly=True)

    quantity_xml = fields.Float(
        string="Quantidade", digits=(18, 4), readonly=True)
    unit_amount_xml = fields.Float(
        string="Valor Unitário", digits=(18, 4), readonly=True)
    discount_total_xml = fields.Float(
        string="Desconto total", digits=(18, 2), readonly=True)
    total_amount_xml = fields.Float(
        string="Valor Total", digits=(18, 2), readonly=True)

    @api.onchange('invoice_line_id')
    def invoice_line_id_onchange(self):
        if self.invoice_line_id:
            if self.invoice_line_id.quantity != self.quantity_xml:
                return {'value': {'invoice_line_id': False, },
                        'warning': {
                            'title': u'Atenção',
                            'message': u'Quantidades incompatíveis'
                }}
            self.uom_id = self.invoice_line_id.product_id.uom_po_id
            self.product_id = self.invoice_line_id.product_id
            if self.invoice_line_id.cfop_id:
                self.cfop_id = self.invoice_line_id.cfop_id

    @api.onchange('product_id')
    def product_onchange(self):
        if self.product_id.uom_po_id and self.uom_id:
            if (self.product_id.uom_po_id.category_id.id !=
                    self.uom_id.category_id.id):
                return {'value': {},
                        'warning': {
                            'title': 'Atenção',
                            'message': u'Unidades de medida incompatíveis'}}
        self.uom_id = self.product_id.uom_po_id.id

    @api.onchange('uom_id')
    def uom_onchange(self):
        if self.product_id.uom_po_id and self.uom_id:
            if (self.product_id.uom_po_id.category_id.id !=
                    self.uom_id.category_id.id):
                return {'value': {},
                        'warning': {
                            'title': 'Atenção',
                            'message': u'Unidades de medida incompatíveis'}}
