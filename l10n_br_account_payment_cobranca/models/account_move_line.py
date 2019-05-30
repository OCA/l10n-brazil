# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from datetime import date

from odoo import models, fields, api, _

from ..boleto.document import Boleto
from ..boleto.document import BoletoException
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


ESTADOS_CNAB = [
    ('draft', u'Inicial'),                           # ok
    ('added', u'Adicionada à ordem de pagamento'),   # ok
    ('exported', u'Exportada'),                      # ok
    ('accepted', u'Aceita'),
    ('not_accepted', u'Não aceita pelo banco'), # importar novamente
]


class AccounMoveLine(models.Model):
    _inherit = "account.move.line"

    state_cnab = fields.Selection(
        ESTADOS_CNAB, u'Estados CNAB', default='draft')

    # is_cnab_rejected = fields.Boolean(
    #     u'Pode ser exportada novamente', default=False,
    #     help='Marque esse campo para indicar um título que pode ser '
    #          'exportado novamente pelo CNAB')
    # cnab_rejected_code = fields.Char(u'Rejeição')
    # transaction_ref = fields.char('Transaction Ref.',
    #                               select=True,
    #                               store=True,
    #                               related='name')
    date_payment_created = fields.Date(
        u'Data da criação do pagamento', readonly=True)
    nosso_numero = fields.Char(
        string=u'Nosso Numero',
    )
    numero_documento = fields.Char(
        string=u'Número documento'
    )
    identificacao_titulo_empresa = fields.Char(
        string=u'Identificação Titulo Empresa',
    )

    @api.multi
    def _prepare_payment_line_vals(self, payment_order):
        vals = super(AccounMoveLine, self)._prepare_payment_line_vals(
            payment_order
        )
        vals['nosso_numero'] = self.nosso_numero
        vals['numero_documento'] = self.numero_documento
        vals['identificacao_titulo_empresa'] = \
            self.identificacao_titulo_empresa
        return vals

    @api.multi
    def create_payment_line_from_move_line(self, payment_order):
        """
        Altera estado do cnab para adicionado a ordem
        :param payment_order:
        :return:
        """
        self.state_cnab = 'added'
        return super(AccounMoveLine, self).create_payment_line_from_move_line(
            payment_order
        )


    @api.multi
    def generate_boleto(self):
        boleto_list = []

        for move_line in self:

            if move_line.state_cnab != 'accepted':
                if move_line.state_cnab == 'not_accepted':
                    raise UserError(_(
                        u'O arquivo CNAB relacionado a essa nota foi '
                        u'transmitido com erro, é necessário corrigi-lo '
                        u'e reenviá-lo'
                    ))
                raise UserError(_(
                    u'É necessário transmitir e processar o retorno do CNAB'
                    u' referente a essa nota para garantir que o '
                    u'boleto está registrado no banco'
                ))
            # try:

                # if move_line.payment_mode_id.type_payment == '00':
                #     number_type = move_line.company_id.own_number_type
                #     if not move_line.boleto_own_number:
                #         if number_type == '0':
                #             nosso_numero = self.env['ir.sequence'].next_by_id(
                #                 move_line.company_id.own_number_sequence.id)
                #         elif number_type == '1':
                #             nosso_numero = \
                #                 move_line.transaction_ref.replace('/', '')
                #         else:
                #             nosso_numero = self.env['ir.sequence'].next_by_id(
                #                 move_line.payment_mode_id.
                #                 internal_sequence_id.id
                #             )
                #     else:
                #         nosso_numero = move_line.boleto_own_number

            boleto = Boleto.getBoleto(
                move_line, move_line.transaction_ref.replace('/','')
            )
                # if boleto:
                    # move_line.date_payment_created = date.today()
                    # move_line.transaction_ref = \
                    #     boleto.boleto.format_nosso_numero()
                    # move_line.boleto_own_number = nosso_numero

            boleto_list.append(boleto.boleto)
            # except BoletoException as be:
            #     _logger.error(be.message or be.value, exc_info=True)
            #     continue
            # except Exception as e:
            #     _logger.error(e.message or e.value, exc_info=True)
            #     continue
        return boleto_list
