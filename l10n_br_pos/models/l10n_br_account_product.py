# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models

DOCUMENT_TYPE = [
    ('nf', 'NF'),
    ('nfe', 'NF-e'),
    ('cte', 'CT-e'),
    ('nfrural', 'NF Produtor'),
    ('cf', 'Cupom Fiscal'),
    ('sat', 'CF-e/SAT')
]


class L10nbrAccountCFOP(models.Model):
    """CFOP - Código Fiscal de Operações e Prestações"""
    _inherit = 'l10n_br_account_product.cfop'

    is_pos = fields.Boolean(
        string=u"Permitida no POS",
        help=u"Marque esta seleção para que a CFOP possa ser utililizada no "
             u"NFC-E/SAT")


class L10nbrAccountDocumentRelated(models.Model):
    _inherit = 'l10n_br_account_product.document.related'

    pos_order_related_id = fields.Many2one('pos.order',
                                           string=u'Documento Fiscal SAT',
                                           ondelete='cascade', select=True)

    document_type = fields.Selection(
        [('nf', 'NF'), ('nfe', 'NF-e'), ('cte', 'CT-e'),
         ('nfrural', 'NF Produtor'), ('cf', 'Cupom Fiscal'),
         ('sat', 'CF-e/SAT')],
        'Tipo Documento', required=True)

    @api.onchange('document_type')
    def onchange_document_type(self):
        if self.document_type:
            if self.document_type != 'sat':
                self.pos_order_related_id = False
            if self.document_type != 'nfe':
                self.invoice_related_id = False
            if self.document_type not in ('nfe', 'sat', 'cte'):
                self.access_key = False

    @api.onchange('pos_order_related_id')
    def onchange_pos_order_related_id(self):
        if self.pos_order_related_id:
            self.document_type = 'sat'
            self.access_key = self.pos_order_related_id.chave_cfe[3:]
            self.date = self.pos_order_related_id.date_order[:10]
