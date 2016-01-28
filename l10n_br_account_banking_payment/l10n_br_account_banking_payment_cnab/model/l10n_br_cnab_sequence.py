# -*- coding: utf-8 -*-
# #############################################################################
#
#
#    Copyright (C) 2012 KMEE (http://www.kmee.com.br)
#    @author Fernando Marcato Rodrigues
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields


class L10nBrCnabSequence(models.Model):
    _name = 'l10n_br_cnab.sequence'

    code = fields.Char(u'Código')
    name = fields.Char(u'Nome')
    internal_sequence_id = fields.Many2one(
        'ir.sequence', u'Sequência Interna')
    parent_payment_mode = fields.Many2one(
        'payment.mode', "Conta de exportação", select=True)

    # 'parent_id': fields.many2one('res.partner.category', 'Parent Category', select=True, ondelete='cascade')
    # 400: um modo de cobrança = 1 conta bancária = 1 sequencia de arquivo
    # 500: n modos de pagamento (ted, doc) = 1 conta bancária = 1 sequencia de arquivo
