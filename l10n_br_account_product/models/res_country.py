# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2015  Luis Felipe Miléo - KMEE                                #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp import models, fields


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    fcp_tax_id = fields.Many2one(
        'account.tax', string=u"% Fundo de Combate à Pobreza (FCP)",
        help=u"Percentual adicional inserido na alíquota interna"
        u" da UF de destino, relativo ao Fundo de Combate à"
        u" Pobreza (FCP) em operações interestaduais com o "
        u"consumidor com esta UF. "
        u"Nota: Percentual máximo de 2%,"
        u" conforme a legislação")
