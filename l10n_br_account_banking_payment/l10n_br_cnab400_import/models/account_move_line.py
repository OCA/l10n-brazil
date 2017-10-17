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


class AccounMoveLine(models.Model):
    _inherit = "account.move.line"

    cnab_move_ids = fields.One2many(
        'l10n_br_cnab.move', 'move_line_id', u'Detalhes de retorno CNAB')
    ml_identificacao_titulo_no_banco = fields.Char(
        u'Identificação do título no banco')

    str_ocorrencia = fields.Char(u'Identificação de Ocorrência')
    str_motiv_a = fields.Char(u'Motivo da ocorrência 01')
    str_motiv_b = fields.Char(u'Motivo de ocorrência 02')
    str_motiv_c = fields.Char(u'Motivo de ocorrência 03')
    str_motiv_d = fields.Char(u'Motivo de ocorrência 04')
    str_motiv_e = fields.Char(u'Motivo de ocorrência 05')
