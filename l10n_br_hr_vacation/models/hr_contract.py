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

    @api.model
    def create(self, vals):
        inicio_aquisitivo = vals['date_start']
        fim_aquisitivo = fields.Date.from_string(inicio_aquisitivo) + \
                         relativedelta(years=1, days=-1)

        inicio_concessivo =  fim_aquisitivo + relativedelta(days=1)
        fim_concessivo = inicio_concessivo + \
                         relativedelta(years=1, days=-1)

        limite_gozo = fim_concessivo + relativedelta(months=-1)
        limite_aviso = limite_gozo + relativedelta(months=-1)

        controle_ferias = self.env['hr.vacation.control'].create({
            'inicio_aquisitivo' : inicio_aquisitivo,
            'fim_aquisitivo' : fim_aquisitivo,
            'inicio_concessivo': inicio_concessivo,
            'fim_concessivo': fim_concessivo,
            'limite_gozo': limite_gozo,
            'limite_aviso': limite_aviso,
        })
        hr_contract_id = super(HrContract, self).create(vals)
        hr_contract_id.vacation_control_ids = controle_ferias
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
