# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _
from odoo.exceptions import Warning as UserError

from odoo.addons.l10n_br_base.tools import fiscal


class L10nbrAccountDocumentRelated(models.Model):
    _name = 'l10n_br_account_product.document.related'

    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string=u'Documento Fiscal',
        ondelete='cascade',
        index=True)

    invoice_related_id = fields.Many2one(
        comodel_name='account.invoice',
        string=u'Documento Fiscal',
        ondelete='cascade',
        index=True)

    document_type = fields.Selection(
        selection=[('nf', 'NF'),
                   ('nfe', 'NF-e'),
                   ('cte', 'CT-e'),
                   ('nfrural', 'NF Produtor'),
                   ('cf', 'Cupom Fiscal')],
        string=u'Tipo Documento',
        required=True)

    access_key = fields.Char(
        string=u'Chave de Acesso',
        size=44)

    serie = fields.Char(
        string=u'Série',
        size=12)

    number = fields.Char(
        string=u'Número',
        size=32)

    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string=u'Estado',
        domain="[('country_id.code', '=', 'BR')]")

    cnpj_cpf = fields.Char(
        string=u'CNPJ/CPF',
        size=18)

    cpfcnpj_type = fields.Selection(
        selection=[('cpf', 'CPF'),
                   ('cnpj', 'CNPJ')],
        string=u'Tipo Doc.',
        default='cnpj')

    inscr_est = fields.Char(
        string='Inscr. Estadual/RG',
        size=16)

    date = fields.Date(
        string='Data')

    fiscal_document_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.document',
        string='Documento')

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

    @api.onchange('invoice_related_id')
    def _onchange_invoice_related_id(self):
        related = self.invoice_related_id
        if not related and not related.fiscal_document_id:
            return False

        if related.fiscal_document_id.code == '01':
            self.document_type = 'nf'
        elif related.fiscal_document_id.code == '04':
            self.document_type = 'nfrural'
        elif related.fiscal_document_id.code == '55':
            self.document_type = 'nfe'
        elif related.fiscal_document_id.code == '57':
            self.document_type = 'cte'
        elif related.fiscal_document_id.code in ('2B', '2C', '2D'):
            self.document_type = 'cf'
        else:
            self.document_type = False

        if related.fiscal_document_id.code in ('55', '57'):
            self.access_key = related.nfe_access_key
            self.serie = False
            self.number = False
            self.state_id = False
            self.cnpj_cpf = False
            self.cpfcnpj_type = False
            self.date = False
            self.fiscal_document_id = False
            self.inscr_est = False

        if related.fiscal_document_id.code in ('01', '04'):
            self.access_key = False
            if related.issuer == '0':
                self.serie = related.document_serie_id and \
                    related.document_serie_id.code or False
            else:
                self.serie = related.vendor_serie

            self.number = related.fiscal_number
            self.state_id = related.partner_id and \
                related.partner_id.state_id and \
                related.partner_id.state_id.id or False
            self.cnpj_cpf = related.partner_id and \
                related.partner_id.cnpj_cpf or False

            if related.partner_id.is_company:
                self.cpfcnpj_type = 'cnpj'
            else:
                self.cpfcnpj_type = 'cpf'

            self.date = related.date_invoice
            self.fiscal_document_id = \
                related.fiscal_document_id and \
                related.fiscal_document_id.id or False

        if related.fiscal_document_id.code == '04':
            self.inscr_est = related.partner_id and \
                related.partner_id.inscr_est or False

    @api.onchange('cnpj_cpf', 'cpfcnpj_type')
    def _onchange_mask_cnpj_cpf(self):
        country = 'BR'
        is_company = True

        if self.cpfcnpj_type == 'cpf':
            is_company = False

        cpf_cnpj = fiscal.format_cpf_cnpj(self.cnpj_cpf, country, is_company)

        self.cnpj_cpf = cpf_cnpj
