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
from openerp.addons import decimal_precision as dp

class PaymentMode(models.Model):
    _inherit = "payment.mode"

    condicao_emissao_papeleta = fields.Selection(
        [('1', 'Banco emite e Processa'),
         ('2', 'Cliente emite e banco processa'),],
            u'Condição Emissão de Papeleta', default='1')
    cnab_percent_interest = fields.Float(string=u"Percentual de Juros",
                                         digits=dp.get_precision('Account'))
    # A exportação CNAB não se encaixa somente nos parâmetros de
    # débito e crédito.

