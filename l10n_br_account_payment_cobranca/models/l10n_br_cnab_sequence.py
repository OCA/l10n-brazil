# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class L10nBrCnabSequence(models.Model):
    _name = 'l10n_br_cnab.sequence'

    code = fields.Char(u'Código')
    name = fields.Char(u'Nome')
    internal_sequence_id = fields.Many2one(
        'ir.sequence', u'Sequência Interna')
    parent_payment_mode = fields.Many2one(
        'payment.mode', "Conta de exportação", select=True)

    # 'parent_id': fields.many2one('res.partner.category',
    # 'Parent Category', select=True, ondelete='cascade')
    # 400: um modo de cobrança = 1 conta bancária = 1 sequencia de arquivo
    # 500: n modos de pagamento (ted, doc) = 1 conta bancária = 1 sequencia de
    # arquivo
