# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, _

from ..febraban.boleto.document import Boleto
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
        self.write({'state_cnab': 'added'})
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
            boleto = Boleto.getBoleto(
                move_line, move_line.nosso_numero
            )
            boleto_list.append(boleto.boleto)
        return boleto_list
