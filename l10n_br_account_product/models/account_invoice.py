# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import datetime

from odoo import models, fields, api, _, tools
from odoo.addons import decimal_precision as dp
from odoo.exceptions import (RedirectWarning,
                             Warning as UserError)

from .l10n_br_account_product import (
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_DEFAULT)

from ..sped.nfe.validator import txt


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    _order = 'date_hour_invoice DESC, fiscal_number DESC'

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount',
                 'currency_id', 'company_id', 'date_invoice', 'type')
    def _compute_amount(self):
        self.icms_base = 0.0
        self.icms_base_other = 0.0
        self.icms_value = 0.0
        self.icms_st_base = 0.0
        self.icms_st_value = 0.0
        self.ipi_base = sum(line.ipi_base for line in self.invoice_line_ids)
        self.ipi_base_other = sum(
            line.ipi_base_other for line in self.invoice_line_ids)
        self.ipi_value = sum(line.ipi_value for line in self.invoice_line_ids)
        self.pis_base = sum(line.pis_base for line in self.invoice_line_ids)
        self.pis_value = sum(line.pis_value for line in self.invoice_line_ids)
        self.cofins_base = sum(
            line.cofins_base for line in self.invoice_line_ids)
        self.cofins_value = sum(
            line.cofins_value for line in self.invoice_line_ids)
        self.ii_value = sum(line.ii_value for line in self.invoice_line_ids)
        self.icms_fcp_value = sum(
            line.icms_fcp_value for line in self.invoice_line_ids)
        self.icms_dest_value = sum(
            line.icms_dest_value for line in self.invoice_line_ids)
        self.icms_origin_value = sum(
            line.icms_origin_value for line in self.invoice_line_ids)
        self.amount_discount = sum(
            line.discount_value for line in self.invoice_line_ids)
        self.amount_insurance = sum(
            line.insurance_value for line in self.invoice_line_ids)
        self.amount_costs = sum(
            line.other_costs_value for line in self.invoice_line_ids)
        self.amount_freight = sum(
            line.freight_value for line in self.invoice_line_ids)
        self.amount_total_taxes = sum(
            line.total_taxes for line in self.invoice_line_ids)
        self.amount_gross = sum(
            line.price_gross for line in self.invoice_line_ids)
        self.amount_tax_discount = 0.0
        self.amount_untaxed = sum(
            line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(tax.amount
                              for tax in self.tax_line_ids
                              if not tax.tax_id.tax_group_id.tax_discount)
        self.amount_total = self.amount_tax + self.amount_untaxed

        for line in self.invoice_line_ids:
            if line.icms_cst_id.code not in (
                    '101', '102', '201', '202', '300', '500'):
                self.icms_base += line.icms_base
                self.icms_base_other += line.icms_base_other
                self.icms_value += line.icms_value
            else:
                self.icms_base += 0.00
                self.icms_base_other += 0.00
                self.icms_value += 0.00
            self.icms_st_base += line.icms_st_base
            self.icms_st_value += line.icms_st_value

    @api.model
    @api.returns('l10n_br_account.fiscal_category')
    def _default_fiscal_category(self):
        DEFAULT_FCATEGORY_PRODUCT = {
            'in_invoice': 'in_invoice_fiscal_category_id',
            'out_invoice': 'out_invoice_fiscal_category_id',
            'in_refund': 'in_refund_fiscal_category_id',
            'out_refund': 'out_refund_fiscal_category_id'
        }
        default_fo_category = {'product': DEFAULT_FCATEGORY_PRODUCT}
        invoice_type = self._context.get('type', 'out_invoice')
        invoice_fiscal_type = self._context.get('fiscal_type', 'product')
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company[default_fo_category[invoice_fiscal_type][invoice_type]]

    @api.model
    def _default_fiscal_document(self):
        if self.env.context.get('fiscal_document_code'):
            company = self.env['res.company'].browse(
                self.env.user.company_id.id)
            return company.product_invoice_id

    @api.model
    def _default_nfe_version(self):
        if self.env.context.get('fiscal_document_code'):
            company = self.env['res.company'].browse(
                self.env.user.company_id.id)
            return company.nfe_version

    @api.model
    def _default_fiscal_document_serie(self):
        result = self.env['l10n_br_account.document.serie']
        if self.env.context.get('fiscal_document_code'):
            company = self.env['res.company'].browse(
                self.env.user.company_id.id)
            fiscal_document_series = [doc_serie for doc_serie in
                                      company.document_serie_product_ids if
                                      doc_serie.fiscal_document_id.id ==
                                      company.product_invoice_id.id and
                                      doc_serie.active]
            if fiscal_document_series:
                result = fiscal_document_series[0]
        return result

    @api.model
    def _default_nfe_purpose(self):
        nfe_purpose_default = {
            'in_invoice': '1',
            'out_invoice': '1',
            'in_refund': '4',
            'out_refund': '4'
        }
        invoice_type = self.env.context.get('type', 'out_invoice')
        return nfe_purpose_default.get(invoice_type)

    @api.one
    @api.depends('invoice_line_ids.cfop_id')
    def _compute_cfops(self):
        lines = self.env['l10n_br_account_product.cfop']
        for line in self.invoice_line_ids:
            if line.cfop_id:
                lines |= line.cfop_id
        self.cfop_ids = (lines).sorted()

    issuer = fields.Selection(
        [('0', u'Emissão própria'), ('1', 'Terceiros')],
        'Emitente',
        default='0',
        readonly=True,
        states={'draft': [('readonly', False)]})

    fiscal_number = fields.Char(
        string='Fiscal Number',
        size=32,
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]},
        help="""Unique number of the invoice, computed
            automatically when the invoice is created.""")

    type = fields.Selection(
        states={'draft': [('readonly', False)]})

    vendor_serie = fields.Char(
        string=u'Série NF Entrada',
        size=12,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help=u"Série do número da Nota Fiscal do Fornecedor")

    nfe_version = fields.Selection(
        selection=[('1.10', '1.10'),
                   ('2.00', '2.00'),
                   ('3.10', '3.10'),
                   ('4.00', '4.00')],
        string=u'Versão NFe',
        readonly=True,
        default=_default_nfe_version,
        states={'draft': [('readonly', False)]})

    date_hour_invoice = fields.Datetime(
        string=u'Data e hora de emissão',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
        index=True,
        help="Deixe em branco para usar a data atual")

    ind_final = fields.Selection(
        selection=[('0', u'Não'),
                   ('1', u'Sim')],
        string=u'Consumidor final',
        readonly=True,
        related='fiscal_position_id.ind_final',
        states={'draft': [('readonly', False)]},
        required=False,
        help=u'Indica operação com Consumidor final.')

    ind_pres = fields.Selection(
        selection=[('0', u'Não se aplica (por exemplo,'
                         u' Nota Fiscal complementar ou de ajuste)'),
                   ('1', u'Operação presencial'),
                   ('2', u'Operação não presencial, pela Internet'),
                   ('3', u'Operação não presencial, Teleatendimento'),
                   ('4', u'NFC-e em operação com entrega em domicílio'),
                   ('5', u'Operação presencial, fora do estabelecimento'),
                   ('9', u'Operação não presencial, outros')],
        string=u'Tipo de operação',
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=False,
        default='0',
        help=u'Indicador de presença do comprador no\n'
             u'estabelecimento comercial no momento\n'
             u'da operação.',)

    fiscal_document_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.document',
        string=u'Documento',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_document)

    fiscal_document_electronic = fields.Boolean(
        related='fiscal_document_id.electronic')

    document_serie_id = fields.Many2one(
        comodel_name='l10n_br_account.document.serie',
        string=u'Série',
        domain="[('fiscal_document_id', '=', fiscal_document_id),\
            ('company_id','=',company_id)]",
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_document_serie)

    fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Categoria Fiscal',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_category)

    date_in_out = fields.Datetime(
        string=u'Data de Entrada/Saida',
        readonly=True,
        states={'draft': [('readonly', False)]},
        index=True,
        copy=False,
        help="Deixe em branco para usar a data atual")

    fiscal_type = fields.Selection(
        selection=PRODUCT_FISCAL_TYPE,
        string=u'Tipo Fiscal',
        default=PRODUCT_FISCAL_TYPE_DEFAULT)

    partner_shipping_id = fields.Many2one(
        comodel_name='res.partner',
        string=u'Endereço de Entrega',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Shipping address for current sales order.")

    shipping_state_id = fields.Many2one(
        comodel_name='res.country.state',
        string=u'Estado de Embarque')

    shipping_location = fields.Char(
        string=u'Local de Embarque',
        size=32)

    expedition_location = fields.Char(
        string='Local de Despacho',
        size=32)

    nfe_purpose = fields.Selection(
        selection=[('1', 'Normal'),
                   ('2', 'Complementar'),
                   ('3', 'Ajuste'),
                   ('4', u'Devolução de Mercadoria')],
        string=u'Finalidade da Emissão',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_nfe_purpose)

    nfe_access_key = fields.Char(
        string=u'Chave de Acesso NFE',
        size=44,
        readonly=True, states={'draft': [('readonly', False)]},
        copy=False)

    nfe_protocol_number = fields.Char(
        string=u'Protocolo',
        size=15,
        readonly=True,
        copy=False, states={'draft': [('readonly', False)]})

    nfe_status = fields.Char(
        string=u'Status na Sefaz',
        size=44,
        readonly=True,
        copy=False)

    nfe_date = fields.Datetime(
        string=u'Data do Status NFE',
        readonly=True,
        copy=False)

    nfe_export_date = fields.Datetime(
        string=u'Exportação NFE',
        readonly=True)

    cfop_ids = fields.Many2many(
        comodel_name='l10n_br_account_product.cfop',
        string=u'CFOP',
        copy=False,
        compute='_compute_cfops')

    fiscal_document_related_ids = fields.One2many(
        comodel_name='l10n_br_account_product.document.related',
        inverse_name='invoice_id',
        string=u'Fiscal Document Related',
        readonly=True,
        states={'draft': [('readonly', False)]})

    carrier_name = fields.Char(
        string=u'Nome Transportadora',
        size=32)

    vehicle_plate = fields.Char(
        string=u'Placa do Veículo',
        size=7)

    vehicle_state_id = fields.Many2one(
        comodel_name='res.country.state',
        string=u'UF da Placa')

    vehicle_l10n_br_city_id = fields.Many2one(
        comodel_name='l10n_br_base.city',
        string=u'Município',
        domain="[('state_id', '=', vehicle_state_id)]")

    amount_untaxed = fields.Float(
        string=u'Untaxed',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    amount_tax = fields.Float(
        string=u'Tax',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    amount_total = fields.Float(
        string=u'Total',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    amount_gross = fields.Float(
        string=u'Vlr. Bruto',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount',
        readonly=True)

    amount_discount = fields.Float(
        string=u'Desconto',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    icms_base = fields.Float(
        string=u'Base ICMS',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    icms_base_other = fields.Float(
        string=u'Base ICMS Outras',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount',
        readonly=True)

    icms_value = fields.Float(
        string=u'Valor ICMS',
        digits=dp.get_precision('Account'),
        compute='_compute_amount',
        store=True)

    icms_st_base = fields.Float(
        string=u'Base ICMS ST',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    icms_st_value = fields.Float(
        string=u'Valor ICMS ST',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    ipi_base = fields.Float(
        string=u'Base IPI',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    ipi_base_other = fields.Float(
        string=u'Base IPI Outras',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    ipi_value = fields.Float(
        string=u'Valor IPI',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    pis_base = fields.Float(
        string=u'Base PIS',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    pis_value = fields.Float(
        string=u'Valor PIS',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    cofins_base = fields.Float(
        string=u'Base COFINS',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    cofins_value = fields.Float(
        string=u'Valor COFINS',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount',
        readonly=True)

    ii_value = fields.Float(
        string=u'Valor II',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount',
        readonly=True)

    icms_fcp_value = fields.Float(
        string=u'Valor total do Fundo de Combate à Pobreza (FCP)',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount',
        readonly=True)

    icms_dest_value = fields.Float(
        string=u'Valor total do ICMS Interestadual para a UF de destino',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount',
        readonly=True)

    icms_origin_value = fields.Float(
        string=u'Valor total do ICMS Interestadual para a UF do remetente',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount',
        readonly=True)

    weight = fields.Float(
        string=u'Gross weight',
        states={'draft': [('readonly', False)]},
        help="The gross weight in Kg.",
        readonly=True)

    weight_net = fields.Float(
        string=u'Net weight',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="The net weight in Kg.")

    number_of_packages = fields.Integer(
        string=u'Volume',
        readonly=True,
        states={'draft': [('readonly', False)]})

    kind_of_packages = fields.Char(
        string=u'Espécie',
        size=60,
        readonly=True,
        states={'draft': [('readonly', False)]})

    brand_of_packages = fields.Char(
        string=u'Brand',
        size=60,
        readonly=True,
        states={'draft': [('readonly', False)]})

    notation_of_packages = fields.Char(
        string=u'Numeração',
        size=60,
        readonly=True,
        states={'draft': [('readonly', False)]})

    amount_insurance = fields.Float(
        string=u'Valor do Seguro',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    amount_freight = fields.Float(
        string=u'Valor do Frete',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    amount_costs = fields.Float(
        string=u'Outros Custos',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    amount_total_taxes = fields.Float(
        string=u'Total de Tributos',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    type_nf_payment = fields.Selection(
        selection=[('01', u'01 - Dinheiro'),
                   ('02', u'02 - Cheque'),
                   ('03', u'03 - Cartão de Crédito'),
                   ('04', u'04 - Cartão de Débito'),
                   ('06', u'05 - Crédito Loja'),
                   ('10', u'10 - Vale Alimentação'),
                   ('11', u'11 - Vale Refeição'),
                   ('12', u'12 - Vale Presente'),
                   ('13', u'13 - Vale Combustível'),
                   ('14', u'14 - Duplicata Mercantil'),
                   ('15', u'15 - Boleto Bancário'),
                   ('90', u'90 - Sem pagamento'),
                   ('99', u'99 - Outros')],
        string='Tipo de Pagamento da NF',
        default='99',
        help=u'Obrigatório o preenchimento do Grupo Informações de Pagamento'
             u' para NF-e e NFC-e. Para as notas com finalidade de Ajuste'
             u' ou Devolução o campo Forma de Pagamento deve ser preenchido'
             u' com 90 - Sem Pagamento.')

    @api.one
    @api.constrains('number')
    def _check_invoice_number(self):
        domain = []
        if self.number:
            fiscal_document = self.fiscal_document_id and\
                self.fiscal_document_id.id or False
            domain.extend([('fiscal_number', '=', self.number),
                           ('fiscal_type', '=', self.fiscal_type),
                           ('fiscal_document_id', '=', fiscal_document)
                           ])
            if self.issuer == '0':
                domain.extend([
                    ('company_id', '=', self.company_id.id),
                    ('fiscal_number', '=', self.number),
                    ('fiscal_document_id', '=', self.fiscal_document_id.id),
                    ('issuer', '=', '0')])
            else:
                domain.extend([
                    ('partner_id', '=', self.partner_id.id),
                    ('vendor_serie', '=', self.vendor_serie),
                    ('issuer', '=', '1')])

            invoices = self.env['account.invoice'].search(domain)
            if len(invoices) > 1:
                raise UserError(u'Não é possível registrar documentos\
                              fiscais com números repetidos.')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        context = self.env.context
        fiscal_document_code = context.get('fiscal_document_code')
        active_id = context.get('active_id')
        nfe_form = 'l10n_br_account_product.l10n_br_account_product_nfe_form'
        nfe_tree = 'l10n_br_account_product.l10n_br_account_product_nfe_tree'
        nfe_views = {'form': nfe_form, 'tree': nfe_tree}

        if active_id and not fiscal_document_code:
            invoice = self.browse(active_id)
            fiscal_document_code = invoice.fiscal_document_id.code

        if nfe_views.get(view_type) and fiscal_document_code == u'55':
            view_id = self.env.ref(nfe_views.get(view_type)).id

        return super(AccountInvoice, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        round_curr = self.currency_id.round
        for line in self.invoice_line_ids:
            price = (line.price_unit * (1 - (line.discount or 0.0) / 100.0))

            taxes = line.invoice_line_tax_ids.compute_all(
                price, self.currency_id, line.quantity,
                partner=self.partner_id,
                fiscal_position=line.fiscal_position_id,
                insurance_value=line.insurance_value,
                freight_value=line.freight_value,
                other_costs_value=line.other_costs_value)['taxes']

            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(
                    tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                    tax_grouped[key]['base'] = round_curr(val['base'])
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += round_curr(val['base'])
        return tax_grouped

    # TODO Imaginar em não apagar o internal number para nao ter a necessidade
    # de voltar a numeracão
    @api.multi
    def action_invoice_draft(self):
        result = super(AccountInvoice, self).action_invoice_draft()
        self.write({
            'fiscal_number': False,
            'nfe_access_key': False,
            'nfe_status': False,
            'nfe_date': False,
            'nfe_export_date': False})
        return result

    @api.multi
    def action_invoice_open(self):
        self.action_number()
        self.nfe_check()
        result = super(AccountInvoice, self).action_invoice_open()
        self.invoice_sefaz_export()
        return result

    @api.multi
    def invoice_sefaz_export(self):
        to_sefaz_export = self.filtered(
            lambda inv: inv.state in ('draft', 'open')
            and inv.fiscal_document_electronic
            and inv.issuer == '0')
        return to_sefaz_export.write({'state': 'sefaz_export'})

    @api.multi
    def action_sefaz_open(self):
        if self.filtered(
                lambda inv: inv.state == 'sefaz_export'
                and not inv.nfe_export_date):
            raise UserError(_(
                "A NF-e deve ser exportada antes de validada."))
        to_open_invoices = self.filtered(
            lambda inv: inv.state == 'sefaz_export'
            and inv.nfe_export_date)
        return to_open_invoices.write({'state': 'open'})

    @api.multi
    def nfe_check(self):
        if self.env.context.get('fiscal_document_code', '') == '55':
            result = txt.validate(self)
            return result

    @api.multi
    def action_number(self):
        # TODO: not correct fix but required a fresh values before reading it.
        self.write({})

        for invoice in self:
            if invoice.issuer == '0' and invoice.fiscal_document_id:
                sequence_obj = self.env['ir.sequence']
                sequence = sequence_obj.browse(
                    invoice.document_serie_id.internal_sequence_id.id)
                invalid_number = self.env[
                    'l10n_br_account.invoice.invalid.number'].search(
                    [('number_start', '<=', sequence.number_next),
                     ('number_end', '>=', sequence.number_next),
                     ('document_serie_id', '=', invoice.document_serie_id.id),
                     ('state', '=', 'done')])

                if invalid_number:
                    raise UserError(
                        _("O número: %s da série: %s, esta inutilizado") % (
                            sequence.number_next,
                            invoice.document_serie_id.name))

                seq_number = sequence_obj.get_id(
                    invoice.document_serie_id.internal_sequence_id.id)
                date_time_invoice = (invoice.date_hour_invoice or
                                     fields.datetime.now())
                date_in_out = invoice.date_in_out or fields.datetime.now()
                self.write(
                    {'fiscal_number': seq_number,
                     'number': seq_number,
                     'date_hour_invoice': date_time_invoice,
                     'date_in_out': date_in_out})

        return True

    @api.onchange('type')
    def _onchange_type(self):
        ctx = dict(self.env.context)
        ctx.update({'type': self.type})
        self.fiscal_category_id = (self.with_context(ctx).
                                   _default_fiscal_category())

    @api.onchange('fiscal_document_id')
    def _onchange_fiscal_document_id(self):
        if self.fiscal_type == 'product':
            if self.issuer == '0':
                series = [doc_serie for doc_serie in
                          self.company_id.document_serie_product_ids if
                          doc_serie.fiscal_document_id.id ==
                          self.fiscal_document_id.id and doc_serie.active]

                if not series:
                    action = self.env.ref(
                        'l10n_br_account.'
                        'action_l10n_br_account_document_serie_form')
                    msg = _(u'Você deve ser uma série de documento fiscal'
                            u'para este documento fiscal.')
                    raise RedirectWarning(
                        msg, action.id, _(u'Criar uma nova série'))
                self.document_serie_id = series[0]

    @api.onchange('partner_id',
                  'company_id',
                  'fiscal_category_id')
    def _onchange_fiscal(self):
        if (self.company_id and self.partner_id
                and self.fiscal_category_id):
            if self.fiscal_category_id.property_journal:
                self.journal_id = self.fiscal_category_id.property_journal
            else:
                raise UserError(
                    _("Nenhum Diário !\n"
                      "Categoria fiscal: '%s', não tem um diário contábil "
                      "para a empresa %s") % (self.fiscal_category_id.name,
                                              self.company_id.name))

            kwargs = {
                'company_id': self.company_id,
                'partner_id': self.partner_id,
                'partner_invoice_id': self.partner_id,
                'fiscal_category_id': self.fiscal_category_id}

            if self.partner_id.property_payment_term_id:
                payment_term = self.partner_id.property_payment_term_id
                self.payment_term_id = payment_term

            if self.type in ('out_invoice', 'out_refund'):
                use_domain = ('use_sale', '=', True)
            else:
                use_domain = ('use_purchase', '=', True)

            fiscal_rule = self.env['account.fiscal.position.rule']
            fp = fiscal_rule.with_context(
                {'use_domain': use_domain}).apply_fiscal_mapping(**kwargs)
            if fp:
                self.fiscal_position_id = fp.id
            else:
                self.fiscal_position_id = False

    @api.multi
    def action_date_assign(self):
        for inv in self:
            if not inv.date_hour_invoice:
                date_hour_invoice = fields.Datetime.context_timestamp(
                    self, datetime.datetime.now())
            else:
                if inv.issuer == '1':
                    date_move = inv.date_in_out
                else:
                    date_move = inv.date_hour_invoice

                date_hour_invoice = fields.Datetime.context_timestamp(
                    self, datetime.datetime.strptime(
                        date_move, tools.DEFAULT_SERVER_DATETIME_FORMAT))

            date_invoice = date_hour_invoice.strftime(
                tools.DEFAULT_SERVER_DATE_FORMAT)
            inv.date_invoice = date_invoice
            date_time_now = fields.datetime.now()
            if not inv.date_hour_invoice:
                inv.date_hour_invoice = date_time_now
            if not inv.date_in_out:
                inv.date_in_out = date_time_now

        super(AccountInvoice, self).action_date_assign()

    @api.multi
    def open_fiscal_document(self):
        """return action to open NFe form"""
        result = super(AccountInvoice, self).open_fiscal_document()
        result['name'] = _('NF-e')
        return result

    @api.onchange('payment_mode_id')
    def onchange_payment_mode(self):
        for record in self:
            if record.payment_mode_id:
                record.type_nf_payment = \
                    record.payment_mode_id.type_nf_payment
