# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from dateutil.relativedelta import relativedelta
from lxml import etree


class HrContract(models.Model):
    _inherit = 'hr.contract'

    vacation_control_ids = fields.One2many(
        comodel_name='hr.vacation.control',
        inverse_name='contract_id',
        string='Periodos Aquisitivos Alocados'
    )

    def create_controle_ferias(self, inicio_periodo_aquisitivo):
        fim_aquisitivo = fields.Date.from_string(inicio_periodo_aquisitivo) + \
            relativedelta(years=1, days=-1)

        inicio_concessivo = fim_aquisitivo + relativedelta(days=1)
        fim_concessivo = inicio_concessivo + \
            relativedelta(years=1, days=-1)

        limite_gozo = fim_concessivo + relativedelta(months=-1)
        limite_aviso = limite_gozo + relativedelta(months=-1)

        controle_ferias = self.env['hr.vacation.control'].create({
            'inicio_aquisitivo': inicio_periodo_aquisitivo,
            'fim_aquisitivo': fim_aquisitivo,
            'inicio_concessivo': inicio_concessivo,
            'fim_concessivo': fim_concessivo,
            'limite_gozo': limite_gozo,
            'limite_aviso': limite_aviso,
        })
        return controle_ferias

    @api.model
    def create(self, vals):
        first = True
        inicio = fields.Date.from_string(vals['date_start'])
        hr_contract_id = super(HrContract, self).create(vals)
        lista_controle_ferias = []
        while(True):
            if(not first):
                inicio = inicio + relativedelta(years=1)
                today = fields.Date.from_string(fields.Date.today())
                if(inicio > today):
                    break
            controle_ferias = self.create_controle_ferias(str(inicio))
            lista_controle_ferias.append(controle_ferias.id)
            first = False
        hr_contract_id.vacation_control_ids = lista_controle_ferias
        return hr_contract_id

    def fields_view_get(self, cr, uid, view_id=None,
                        view_type='form', context=None,
                        toolbar=False, submenu=False):
        res = models.Model.fields_view_get(self, cr, uid,
                                           view_id=view_id,
                                           view_type=view_type,
                                           context=context,
                                           toolbar=toolbar,
                                           submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            for sheet in doc.xpath("//sheet"):
                parent = sheet.getparent()
                index = parent.index(sheet)
                for child in sheet:
                    parent.insert(index, child)
                    index += 1
                parent.remove(sheet)
            res['arch'] = etree.tostring(doc)
        return res
