# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Luiz Felipe do Divino (luiz.divino@kmee.com.br)
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

from openerp import models, fields, api
from ..serasa import consulta
from datetime import datetime


class Serasa(models.Model):
    _name = 'consulta_serasa'
    _order = "id desc"


    data_consulta = fields.Date('Data Consulta', default=datetime.now())
    status = fields.Char('Estado')
    partner_id = fields.Many2one('res.partner', required=True)
    stringRetorno = fields.Text('StringRetorno')

    def _check_partner(self):
        company = self.env.user.company_id
        status, texto = consulta.consulta_cnpj(self.partner_id, company)
        result = self.write({
            'status': status,
            'stringRetorno': texto,
            })
        return result

    @api.model
    def create(self, vals):
        rec = super(Serasa, self).create(vals)
        rec._check_partner()
        return rec
