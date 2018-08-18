# -*- coding: utf-8 -*-
#    Copyright (C) 2016 MultidadosTI (http://www.multidadosti.com.br)
#    @author Michell Stuttgart <michellstut@gmail.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re

from odoo import models, fields, api


class ResBank(models.Model):

    _inherit = 'res.bank'

    district = fields.Char(
        string=u'Bairro',
        size=32)

    number = fields.Char(
        string=u'Número',
        size=10)

    country_id = fields.Many2one(
        comodel_name='res.country',
        related='country',
        string=u'País')

    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string=u'Estado',
        related='state')

    l10n_br_city_id = fields.Many2one(
        comodel_name='l10n_br_base.city',
        string=u'Municipio',
        domain="[('state_id','=',state_id)]")

    @api.onchange('l10n_br_city_id')
    def _onchange_l10n_br_city_id(self):
        """ Ao alterar o campo l10n_br_city_id que é um campo relacional
        com o l10n_br_base.city que são os municípios do IBGE, copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.
        """
        if self.l10n_br_city_id:
            self.city = self.l10n_br_city_id.name

    @api.onchange('zip')
    def _onchange_zip(self):
        if self.zip:
            val = re.sub('[^0-9]', '', self.zip)
            if len(val) == 8:
                self.zip = "%s-%s" % (val[0:5], val[5:8])
