# -*- coding: utf-8 -*-
# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from ..febraban.boleto.document import Boleto


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    @api.multi
    def generate_boleto(self, validate=True):
        boleto_list = []

        for move_line in self:

            if validate and move_line.state_cnab not in \
                    ['accepted', 'accepted_hml']:
                if move_line.state_cnab == 'not_accepted':
                    raise UserError(_(
                        u'Essa fatura foi transmitida com erro ao banco, '
                        u'é necessário corrigí-la e reenviá-la.'
                    ))
                raise UserError(_(
                    u'Antes de imprimir o boleto é necessário transmitir a '
                    u'fatura para registro no banco.'
                ))

            boleto = Boleto.getBoleto(
                move_line, move_line.nosso_numero
            )

            # Se a cobrança tiver sido emitida em homologação
            if move_line.state_cnab == 'accepted_hml':
                boleto.boleto.instrucoes.append(_(
                    u'Boleto emitido em homologacao! Sem valor fiscal!'))

            boleto_list.append(boleto.boleto)

        if not boleto_list:
            raise UserError(
                'Error !', ('Não é possível gerar os boletos\n'
                            'Certifique-se que a fatura esteja confirmada e o '
                            'forma de pagamento seja duplicatas'))
        pdf_string = Boleto.get_pdfs(boleto_list)
        return pdf_string