# -*- coding: utf-8 -*-
# Copyright 2012 KMEE - Fernando Marcato Rodrigues
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, models, fields

import logging
_logger = logging.getLogger(__name__)
try:
    from cnab240.constantes import FORMA_LANCAMENTO
except ImportError as err:
    _logger.debug = (err)


class PaymentOrder(models.Model):
    _inherit = b'payment.order'

    file_number = fields.Integer(u'Número sequencial do arquivo')
    # TODO adicionar domain para permitir o modo de pagamento correspondente
    # ao mode

    serie_id = fields.Many2one(
        'l10n_br_cnab.sequence',
        u'Sequencia interna'
    )

    sufixo_arquivo = fields.Integer(u'Sufixo do arquivo')

    serie_sufixo_arquivo = fields.Many2one(
        u'Série do Sufixo do arquivo',
        'l10n_br_cnab_file_sufix.sequence',
    )

    forma_lancamento = fields.Selection(
        string='Forma de Lançamento do CNAB',
        selection=FORMA_LANCAMENTO,
    )

    @api.multi
    def get_next_number(self):
        for ord in self:
            sequence = self.env['ir.sequence']
            # sequence_read = sequence.read(
            #     cr, uid, ord.serie_id.internal_sequence_id.id,
            #     ['number_next'])
            seq_no = sequence.get_id(ord.serie_id.internal_sequence_id.id)
            ord.write({'file_number': seq_no})
        return seq_no

    # TODO: funcao a ser chamada por ação automatizada para resetar o sufixo
    #     diariamente

    @api.multi
    def get_next_sufixo(self):
        for ord in self:
            sequence = self.env['ir.sequence']
            # sequence_read = sequence.read(
            #     cr, uid, ord.serie_id.internal_sequence_id.id,
            #     ['number_next'])
            seq_no = sequence.get_id(
                ord.serie_sufixo_arquivo.internal_sequence_id.id)
            ord.write({'sufixo_arquivo': seq_no})
        return seq_no

    # @api.multi
    # def set_to_draft(self, *args):
    #     super(PaymentOrder, self).set_to_draft(*args)
    #
    #     for order in self:
    #         for line in order.line_ids:
    #             self.write_added_state_to_move_line(line.move_line_id)
    #     return True

    # @api.multi
    # def write_added_state_to_move_line(self, mov_line):
    #     mov_line.state_cnab = 'added'
