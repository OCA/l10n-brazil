# -*- encoding: utf-8 -*-
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


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    file_number = fields.Integer(u'Número sequencial do arquivo')
    # TODO adicionar domain para permitir o modo de pagamento correspondente
    # ao mode
    serie_id = fields.Many2one(
        'l10n_br_cnab_sequence', u'Sequencia interna')

    def get_next_number(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for ord in self.browse(cr, uid, ids):
            sequence = self.pool.get('ir.sequence')
            # sequence_read = sequence.read(
            #     cr, uid, ord.serie_id.internal_sequence_id.id,
            #     ['number_next'])
            seq_no = sequence.get_id(cr, uid,
                                     ord.serie_id.internal_sequence_id.id,
                                     context=context)
            self.write(cr, uid, ord.id, {'file_number': seq_no})
        return seq_no
