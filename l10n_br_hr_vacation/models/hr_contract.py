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
        inicio = fields.Date.from_string(vals['date_start'])
        hoje = fields.Date.from_string(fields.Date.today())
        hr_contract_id = super(HrContract, self).create(vals)
        lista_controle_ferias = []
        controle_ferias_obj = self.env['hr.vacation.control']

        while(inicio < hoje):
            vals = controle_ferias_obj.calcular_datas_aquisitivo_concessivo(
                str(inicio)
            )
            controle_ferias = controle_ferias_obj.create(vals)
            inicio = inicio + relativedelta(years=1)
            lista_controle_ferias.append(controle_ferias.id)

        hr_contract_id.vacation_control_ids = lista_controle_ferias
        return hr_contract_id

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(HrContract, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu
        )
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

    @api.multi
    def atualizar_controle_ferias(self):
        domain = [
            '|',
            ('date_end', '>', fields.Date.today()),
            ('date_end', '=', False),
        ]
        contratos_ids = self.env['hr.contract'].search(domain)

        for contrato in contratos_ids:
            if contrato.vacation_control_ids:
                ultimo_controle = contrato.vacation_control_ids[0]
                if not ultimo_controle.hr_holiday_ids:
                    controle_ferias = ultimo_controle
                elif ultimo_controle.fim_aquisitivo < fields.Date.today():
                    controle_ferias_obj = self.env['hr.vacation.control']

                    vals = controle_ferias_obj.\
                        calcular_datas_aquisitivo_concessivo(
                            fields.Date.today()
                        )
                    controle_ferias = controle_ferias_obj.create(vals)
                    contrato.vacation_control_ids.append(controle_ferias)
                else:
                    continue

                vacation_id = self.env.ref(
                    'l10n_br_hr_vacation.holiday_status_vacation').id
                holiday_id = self.env['hr.holidays'].create({
                    'name': 'Periodo Aquisitivo: %s ate %s'
                            % (controle_ferias.inicio_aquisitivo,
                               controle_ferias.fim_aquisitivo),
                    'employee_id': contrato.employee_id.id,
                    'holiday_status_id': vacation_id,
                    'type': 'add',
                    'holiday_type': 'employee',
                    'vacations_days': 30,
                    'sold_vacations_days': 0,
                    'number_of_days_temp': 30,
                    'contract_id': controle_ferias.contract_id.id,
                })
                controle_ferias.hr_holiday_ids = holiday_id
