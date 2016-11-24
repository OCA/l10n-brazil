# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError
from openerp.addons import decimal_precision as dp

from openerp.addons.l10n_br_base.tools import fiscal
from openerp.addons.l10n_br_account.models.l10n_br_account import TYPE

PRODUCT_FISCAL_TYPE = [
    ('product', 'Produto')
]

PRODUCT_FISCAL_TYPE_DEFAULT = PRODUCT_FISCAL_TYPE[0][0]

NFE_IND_IE_DEST = [
    ('1', '1 - Contribuinte do ICMS'),
    ('2', '2 - Contribuinte Isento do ICMS'),
    ('9', '9 - Não Contribuinte')
]

NFE_IND_IE_DEST_DEFAULT = NFE_IND_IE_DEST[0][0]


class L10nbrAccountCFOP(models.Model):
    """CFOP - Código Fiscal de Operações e Prestações"""
    _name = 'l10n_br_account_product.cfop'
    _description = 'CFOP'

    code = fields.Char(u'Código', size=4, required=True)
    name = fields.Char('Nome', size=256, required=True)
    small_name = fields.Char('Nome Reduzido', size=32, required=True)
    description = fields.Text(u'Descrição')
    type = fields.Selection(TYPE, 'Tipo', required=True)
    parent_id = fields.Many2one(
        'l10n_br_account_product.cfop', 'CFOP Pai')
    child_ids = fields.One2many(
        'l10n_br_account_product.cfop', 'parent_id', 'CFOP Filhos')
    internal_type = fields.Selection(
        [('view', u'Visualização'), ('normal', 'Normal')],
        'Tipo Interno', required=True, default='normal')
    id_dest = fields.Selection(
        [('1', u'Operação interna'),
         ('2', u'Operação interestadual'),
         ('3', u'Operação com exterior')],
        u'Local de destino da operação',
        help=u'Identificador de local de destino da operação.')

    _sql_constraints = [
        ('l10n_br_account_cfop_code_uniq', 'unique (code)',
            u'Já existe um CFOP com esse código !')
    ]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    # TODO migrate
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'code'], context,
                          load='_classic_write')
        return [(x['id'], (x['code'] and x['code'] or '') +
                 (x['name'] and ' - ' + x['name'] or '')) for x in reads]


class L10nBrAccountServiceType(models.Model):
    _name = 'l10n_br_account.service.type'
    _description = u'Cadastro de Operações Fiscais de Serviço'

    code = fields.Char(u'Código', size=16, required=True)
    name = fields.Char(u'Descrição', size=256, required=True)
    parent_id = fields.Many2one(
        'l10n_br_account.service.type', 'Tipo de Serviço Pai')
    child_ids = fields.One2many(
        'l10n_br_account.service.type', 'parent_id',
        u'Tipo de Serviço Filhos')
    internal_type = fields.Selection(
        [('view', u'Visualização'), ('normal', 'Normal')], 'Tipo Interno',
        required=True, default='normal')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            result.append((record['id'], name))
        return result


class L10nbrAccountDocumentRelated(models.Model):
    _name = 'l10n_br_account_product.document.related'

    invoice_id = fields.Many2one('account.invoice', 'Documento Fiscal',
                                 ondelete='cascade', select=True)
    invoice_related_id = fields.Many2one('account.invoice',
                                         'Documento Fiscal',
                                         ondelete='cascade',
                                         select=True)
    document_type = fields.Selection(
        [('nf', 'NF'), ('nfe', 'NF-e'), ('cte', 'CT-e'),
            ('nfrural', 'NF Produtor'), ('cf', 'Cupom Fiscal')],
        'Tipo Documento', required=True)
    access_key = fields.Char('Chave de Acesso', size=44)
    serie = fields.Char(u'Série', size=12)
    internal_number = fields.Char(u'Número', size=32)
    state_id = fields.Many2one('res.country.state', 'Estado',
                               domain="[('country_id.code', '=', 'BR')]")
    cnpj_cpf = fields.Char('CNPJ/CPF', size=18)
    cpfcnpj_type = fields.Selection(
        [('cpf', 'CPF'), ('cnpj', 'CNPJ')], 'Tipo Doc.',
        default='cnpj')
    inscr_est = fields.Char('Inscr. Estadual/RG', size=16)
    date = fields.Date('Data')
    fiscal_document_id = fields.Many2one(
        'l10n_br_account.fiscal.document', 'Documento')

    @api.one
    @api.constrains('cnpj_cpf')
    def _check_cnpj_cpf(self):

        check_cnpj_cpf = True

        if self.cnpj_cpf:
            if self.cpfcnpj_type == 'cnpj':
                if not fiscal.validate_cnpj(self.cnpj_cpf):
                    check_cnpj_cpf = False
            elif not fiscal.validate_cpf(self.cnpj_cpf):
                check_cnpj_cpf = False
        if not check_cnpj_cpf:
            raise UserError(
                _(u'CNPJ/CPF do documento relacionado é invalido!'))

    @api.one
    @api.constrains('inscr_est')
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False.

        :Parameters:
            - 'cr': Database cursor.
            - 'uid': Current user’s ID for security checks.
            - 'ids': List of partner objects IDs.
        """
        check_ie = True

        if self.inscr_est or self.inscr_est != 'ISENTO':
            uf = self.state_id and self.state_id.code.lower() or ''
            try:
                mod = __import__('openerp.addons.l10n_br_base.tools.fiscal',
                                 globals(), locals(), 'fiscal')

                validate = getattr(mod, 'validate_ie_%s' % uf)
                if not validate(self.inscr_est):
                    check_ie = False
            except AttributeError:
                if not fiscal.validate_ie_param(uf, self.inscr_est):
                    check_ie = False

        if not check_ie:
            raise UserError(
                _(u'Inscrição Estadual do documento fiscal inválida!'))

    @api.multi
    def onchange_invoice_related_id(self, invoice_related_id):
        result = {'value': {}}

        if not invoice_related_id:
            return result

        inv_related = self.env['account.invoice'].browse(invoice_related_id)

        if not inv_related.fiscal_document_id:
            return result

        if inv_related.fiscal_document_id.code == '01':
            result['value']['document_type'] = 'nf'
        elif inv_related.fiscal_document_id.code == '04':
            result['value']['document_type'] = 'nfrural'
        elif inv_related.fiscal_document_id.code == '55':
            result['value']['document_type'] = 'nfe'
        elif inv_related.fiscal_document_id.code == '57':
            result['value']['document_type'] = 'cte'
        elif inv_related.fiscal_document_id.code in ('2B', '2C', '2D'):
            result['value']['document_type'] = 'cf'
        else:
            result['value']['document_type'] = False

        if inv_related.fiscal_document_id.code in ('55', '57'):
            result['value']['access_key'] = inv_related.nfe_access_key
            result['value']['serie'] = False
            result['value']['serie'] = False
            result['value']['internal_number'] = False
            result['value']['state_id'] = False
            result['value']['cnpj_cpf'] = False
            result['value']['cpfcnpj_type'] = False
            result['value']['date'] = False
            result['value']['fiscal_document_id'] = False
            result['value']['inscr_est'] = False

        if inv_related.fiscal_document_id.code in ('01', '04'):
            result['value']['access_key'] = False
            if inv_related.issuer == '0':
                result['value']['serie'] = inv_related.document_serie_id and \
                    inv_related.document_serie_id.code or False
            else:
                result['value']['serie'] = inv_related.vendor_serie

            result['value']['internal_number'] = inv_related.internal_number
            result['value']['state_id'] = inv_related.partner_id and \
                inv_related.partner_id.state_id and \
                inv_related.partner_id.state_id.id or False
            result['value']['cnpj_cpf'] = inv_related.partner_id and \
                inv_related.partner_id.cnpj_cpf or False

            if inv_related.partner_id.is_company:
                result['value']['cpfcnpj_type'] = 'cnpj'
            else:
                result['value']['cpfcnpj_type'] = 'cpf'

            result['value']['date'] = inv_related.date_invoice
            result['value']['fiscal_document_id'] = \
                inv_related.fiscal_document_id and \
                inv_related.fiscal_document_id.id or False

        if inv_related.fiscal_document_id.code == '04':
            result['value']['inscr_est'] = inv_related.partner_id and \
                inv_related.partner_id.inscr_est or False

        return result

    @api.multi
    def onchange_mask_cnpj_cpf(self, cpfcnpj_type, cnpj_cpf):
        result = {'value': {}}
        if cnpj_cpf:
            val = re.sub('[^0-9]', '', cnpj_cpf)
            if cpfcnpj_type == 'cnpj' and len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s"\
                    % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
            elif cpfcnpj_type == 'cpf' and len(val) == 11:
                cnpj_cpf = "%s.%s.%s-%s"\
                    % (val[0:3], val[3:6], val[6:9], val[9:11])
            result['value'].update({'cnpj_cpf': cnpj_cpf})
        return result


class ImportDeclaration(models.Model):
    _name = 'l10n_br_account_product.import.declaration'

    invoice_line_id = fields.Many2one(
        'account.invoice.line', u'Linha de Documento Fiscal',
        ondelete='cascade', select=True)
    name = fields.Char(u'Número da DI', size=10, required=True)
    date_registration = fields.Date(u'Data de Registro', required=True)
    exporting_code = fields.Char(
        u'Código do Exportador', required=True, size=60)
    state_id = fields.Many2one(
        'res.country.state', u'Estado',
        domain="[('country_id.code', '=', 'BR')]")
    location = fields.Char(u'Local', required=True, size=60)
    date_release = fields.Date(u'Data de Liberação', required=True)
    type_transportation = fields.Selection([
        ('1', u'1 - Marítima'),
        ('2', u'2 - Fluvial'),
        ('3', u'3 - Lacustre'),
        ('4', u'4 - Aérea'),
        ('5', u'5 - Postal'),
        ('6', u'6 - Ferroviária'),
        ('7', u'7 - Rodoviária'),
        ('8', u'8 - Conduto / Rede Transmissão'),
        ('9', u'9 - Meios Próprios'),
        ('10', u'10 - Entrada / Saída ficta'),
    ], u'Transporte Internacional')
    afrmm_value = fields.Float(
        'Valor da AFRMM', digits=dp.get_precision('Account'), default=0.00)
    type_import = fields.Selection([
        ('1', u'1 - Importação por conta própria'),
        ('2', u'2 - Importação por conta e ordem'),
        ('3', u'3 - Importação por encomenda'),
    ], u'Tipo de Importação', default='1')
    thirdparty_cnpj = fields.Char('CNPJ', size=18)
    thirdparty_state_id = fields.Many2one(
        'res.country.state', u'Estado',
        domain="[('country_id.code', '=', 'BR')]")
    line_ids = fields.One2many(
        'l10n_br_account_product.import.declaration.line',
        'import_declaration_id', 'Linhas da DI')

    @api.multi
    def onchange_mask_cnpj_cpf(self, thirdparty_cnpj):
        result = {'value': {}}
        if thirdparty_cnpj:
            val = re.sub('[^0-9]', '', thirdparty_cnpj)
            if len(val) == 14:
                thirdparty_cnpj = "%s.%s.%s/%s-%s"\
                    % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
        result['value'].update({'thirdparty_cnpj': thirdparty_cnpj})
        return result


class ImportDeclarationLine(models.Model):
    _name = 'l10n_br_account_product.import.declaration.line'

    import_declaration_id = fields.Many2one(
        'l10n_br_account_product.import.declaration', u'DI',
        ondelete='cascade', select=True)
    sequence = fields.Integer(u'Sequência', default=1, required=True)
    name = fields.Char(u'Adição', size=3, required=True)
    manufacturer_code = fields.Char(
        u'Código do Fabricante', size=60, required=True)
    amount_discount = fields.Float(u'Valor',
                                   digits=dp.get_precision('Account'),
                                   default=0.00)


class L10nBrIcmsRelief(models.Model):

    _name = 'l10n_br_account_product.icms_relief'
    _description = 'Icms Relief'

    code = fields.Char(u'Código', size=2, required=True)
    name = fields.Char('Nome', size=256, required=True)
    active = fields.Boolean('Ativo', default=True)


class L10nBrIPIGuideline(models.Model):

    _name = 'l10n_br_account_product.ipi_guideline'
    _description = 'IPI Guidelines'

    code = fields.Char(u'Código', size=3, required=True)
    name = fields.Text(u'Descrição Enquadramento Legal do IPI', required=True)
    cst_group = fields.Selection([('imunidade', u'Imunidade'),
                                  ('suspensao', u'Suspensão'),
                                  ('isencao', u'Isenção'),
                                  ('reducao', u'Redução'),
                                  ('outros', u'Outros'),
                                  ], string='Grupo CST', required=True)
    tax_code_in_id = fields.Many2one(
        'account.tax.code.template', string=u'CST Entrada')
    tax_code_out_id = fields.Many2one(
        'account.tax.code.template', string=u'CST Saída')


class L10nBrTaxIcmsPartition(models.Model):

    _name = 'l10n_br_tax.icms_partition'
    _description = 'Icms Partition'

    date_start = fields.Date(
        u'Data Inicial',
        required=True
    )
    date_end = fields.Date(
        u'Data Final',
        required=True
    )
    rate = fields.Float(
        u'Percentual Interestadual de Rateio',
        required=True
    )


class L10nBrAccountProductCest(models.Model):

    _name = 'l10n_br_account_product.cest'

    code = fields.Char(
        u'Código',
        size=9
    )
    name = fields.Char(
        u'Nome'
    )
    segment = fields.Char(
        u'Segmento',
        size=32
    )
    item = fields.Char(
        u'Item',
        size=4
    )

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.multi
    def name_get(self):
        result = []
        for cest in self:
            name = cest.code + ' - ' + cest.name
            result.append((cest.id, name))
        return result
