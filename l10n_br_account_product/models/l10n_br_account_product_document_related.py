# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api, _

from openerp.addons.l10n_br_base.tools import fiscal


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
