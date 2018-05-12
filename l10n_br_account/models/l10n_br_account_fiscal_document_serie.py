# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

from .l10n_br_account import (PRODUCT_FISCAL_TYPE,
                              PRODUCT_FISCAL_TYPE_DEFAULT)


class L10nBrAccountDocumentSerie(models.Model):
    _name = 'l10n_br_account.document.serie'
    _description = 'Serie de documentos fiscais'

    code = fields.Char(
        string=u'Código',
        size=3,
        required=True)

    name = fields.Char(
        string=u'Descrição',
        required=True)

    active = fields.Boolean(string='Ativo')

    fiscal_type = fields.Selection(
        selection=PRODUCT_FISCAL_TYPE,
        string=u'Tipo Fiscal',
        default=PRODUCT_FISCAL_TYPE_DEFAULT)

    fiscal_document_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.document',
        string='Documento Fiscal',
        required=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Empresa',
        required=True)

    internal_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string=u'Sequência Interna')

    @api.model
    def _create_sequence(self, vals):
        """ Create new no_gap entry sequence for every
         new document serie """
        seq = {
            'name': vals['name'],
            'implementation': 'no_gap',
            'padding': 1,
            'number_increment': 1}
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        return self.env['ir.sequence'].create(seq).id

    @api.model
    def create(self, vals):
        """ Overwrite method to create a new ir.sequence if
         this field is null """
        if not vals.get('internal_sequence_id'):
            vals.update({'internal_sequence_id': self._create_sequence(vals)})
        return super(L10nBrAccountDocumentSerie, self).create(vals)
