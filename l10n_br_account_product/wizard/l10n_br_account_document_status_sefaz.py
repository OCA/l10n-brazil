# -*- coding: utf-8 -*-
# Copyright (C) 2013 Luis Felipe Miléo - KMEE
# Copyright (C) 2014 Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class L10nBrAccountDocumentStatusSefaz(models.TransientModel):
    """ Check fiscal document key"""
    _name = 'l10n_br_account_product.document_status_sefaz'
    _description = 'Check fiscal document key on sefaz'

    state = fields.Selection(
        selection=[('init', 'Init'),
                   ('error', 'Error'),
                   ('done', 'Done')],
        string='State',
        index=True,
        readonly=True,
        default='init')

    version = fields.Text(
        string=u'Versão',
        readonly=True)

    nfe_environment = fields.Selection(
        selection=[('1', u'Produção'),
                   ('2', u'Homologação')],
        string='Ambiente')

    xMotivo = fields.Text(
        string='Motivo',
        readonly=True)

    # FIXME
    cUF = fields.Integer(
        string='Codigo Estado',
        readonly=True)

    chNFe = fields.Char(
        string='Chave de Acesso NFE',
        size=44)

    protNFe = fields.Text(
        string='Protocolo NFE',
        readonly=True)

    retCancNFe = fields.Text(
        string='Cancelamento NFE',
        readonly=True)

    procEventoNFe = fields.Text(
        sting='Processamento Evento NFE',
        readonly=True)

    @api.multi
    def get_document_status(self):
        for data in self:
            # Call some method from l10n_br_account to check chNFE
            call_result = {
                'version': '2.01',
                'nfe_environment': '2',
                'xMotivo': '101',
                'cUF': 27,
                'chNFe': data.chNFe,
                'protNFe': '123',
                'retCancNFe': '',
                'procEventoNFe': '',
                'state': 'done',
                }
            data.write(call_result)

            view_rec = self.env['ir.model.data'].get_object_reference(
                'l10n_br_account_product',
                'l10n_br_account_product_document_status_sefaz_form')
            view_id = view_rec and view_rec[1] or False

            return {
                'view_type': 'form',
                'view_id': [view_id],
                'view_mode': 'form',
                'res_model': 'l10n_br_account_product.document_status_sefaz',
                'res_id': data.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': data.env.context,
            }
