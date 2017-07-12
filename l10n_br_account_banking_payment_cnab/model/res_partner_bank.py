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


class ResPartnerBank(models.Model):
    """ Adiciona campos necessários para o cadastramentos de contas
    bancárias no Brasil."""
    _inherit = 'res.partner.bank'

    codigo_da_empresa = fields.Integer(
        u'Código da empresa', size=20,
        help=u"Será informado pelo banco depois do cadastro do beneficiário "
             u"na agência")
    tipo_de_conta = fields.Selection(
        [('01', u'Conta corrente individual'),
         ('02', u'Conta poupança individual'),
         ('03', u'Conta depósito judicial/Depósito em consignação individual'),
         ('11', u'Conta corrente conjunta'),
         ('12', u'Conta poupança conjunta'),
         ('13', u'Conta depósito judicial/Depósito em consignação conjunta')
         ],
        u'Tipo de Conta', default='01'
    )
