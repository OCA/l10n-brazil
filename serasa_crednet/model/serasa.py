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

    _name = 'consulta.serasa'
    _order = "id desc"

    @api.multi
    @api.depends('cheque_ids', 'pefin_ids', 'cheque_ids')
    def _count_serasa(self):
        for rec in self:
            for pefin in rec.pefin_ids:
                rec.pefin_count += 1
                rec.pefin_sum += pefin.value
            for cheque in rec.cheque_ids:
                rec.cheque_count += 1
                rec.cheque_sum += cheque.value
            for protesto in rec.protesto_ids:
                rec.protesto_count += 1
                rec.protesto_sum += protesto.value

    data_consulta = fields.Date('Data Consulta', default=datetime.now())
    status = fields.Char('Estado')
    partner_id = fields.Many2one('res.partner', required=True)
    partner_fundation = fields.Date('Data de Fundação')
    partner_identification = fields.Char('Documento')
    string_retorno = fields.Text('StringRetorno')
    protesto_count = fields.Integer('Protestos', compute='_count_serasa')
    protesto_sum = fields.Float('Valor', compute='_count_serasa')
    protesto_ids = fields.One2many('serasa.protesto', 'serasa_id')
    pefin_count = fields.Integer('Pefin', compute='_count_serasa')
    pefin_sum = fields.Float('Valor', compute='_count_serasa')
    pefin_ids = fields.One2many('serasa.pefin', 'serasa_id')
    cheque_count = fields.Integer('Cheques', compute='_count_serasa')
    cheque_sum = fields.Float('Valor', compute='_count_serasa')
    cheque_ids = fields.One2many('serasa.cheque', 'serasa_id')

    def _check_partner(self):
        id_consulta_serasa = self.id
        company = self.env.user.company_id
        retorno_consulta = consulta.consulta_cnpj(self.partner_id, company)
        if len(retorno_consulta) == 1:
            from openerp.exceptions import Warning
            raise Warning(retorno_consulta)

        result = self.write({
                'status': retorno_consulta['status'],
                'string_retorno': retorno_consulta['texto'],
                'partner_fundation': retorno_consulta['fundacao'],
                'partner_identification': self.partner_id.cnpj_cpf,
            })

        pefin_obj = self.env['serasa.pefin']
        for pefin in retorno_consulta['pefin']:
            pefin_obj.create({
                'value': pefin['value'],
                'date': pefin['date'],
                'modalidade': pefin['modalidade'],
                'origem': pefin['origem'],
                'avalista': pefin['avalista'],
                'serasa_id': id_consulta_serasa,
            })

        protesto_obj = self.env['serasa.protesto']
        for protesto in retorno_consulta['protesto']:
            protesto_obj.create({
                'value': protesto['value'],
                'date': protesto['date'],
                'cartorio': protesto['cartorio'],
                'city': protesto['city'],
                'uf': protesto['uf'],
                'serasa_id': id_consulta_serasa,
            })

        cheque_obj = self.env['serasa.cheque']
        for cheque in retorno_consulta['cheque']:
            cheque_obj.create({
                'value': cheque['value'],
                'date': cheque['date'],
                'num_cheque': cheque['num_cheque'],
                'alinea': cheque['alinea'],
                'serasa_id': id_consulta_serasa,
                'name_bank': cheque['name_bank'],
                'city': cheque['city'],
                'uf': cheque['uf'],
            })

        return result

    @api.model
    def create(self, vals):
        rec = super(Serasa, self).create(vals)
        rec._check_partner()
        return rec


class SerasaProtesto(models.Model):

    _name = 'serasa.protesto'

    cartorio = fields.Char('Cartorio')
    city = fields.Char('Cidade')
    uf = fields.Char('UF')
    serasa_id = fields.Many2one('consulta.serasa', required=True)
    date = fields.Date('Data')
    value = fields.Float('Valor')


class SerasaPefin(models.Model):

    _name = 'serasa.pefin'

    modalidade = fields.Char('Modalidade')
    origem = fields.Char('Origem')
    avalista = fields.Char('Avalista')
    serasa_id = fields.Many2one('consulta.serasa', required=True)
    date = fields.Date('Data')
    value = fields.Float('Valor')


class SerasaCheque(models.Model):

    _name = 'serasa.cheque'

    num_cheque = fields.Integer(u'Número do Cheque')
    alinea = fields.Integer(u'Alínea')
    serasa_id = fields.Many2one('consulta.serasa', required=True)
    name_bank = fields.Char('Nome do Banco')
    city = fields.Char('Cidade')
    uf = fields.Char('UF')
    date = fields.Date('Data')
    value = fields.Float('Valor')
