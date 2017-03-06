# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from dateutil.relativedelta import relativedelta
from datetime import datetime


class HrVacationControl(models.Model):
    _name = 'hr.vacation.control'
    _order = 'inicio_aquisitivo desc'
    _rec_name = 'display_name'

    inicio_aquisitivo = fields.Date(
        string=u'Início Período Aquisitivo',
    )

    fim_aquisitivo = fields.Date(
        string=u'Fim Período Aquisitivo',
    )

    inicio_concessivo = fields.Date(
        string=u'Início Período Concessivo',
    )

    fim_concessivo = fields.Date(
        string=u'Fim Período Concessivo',
    )

    inicio_gozo = fields.Date(
        string=u'Início Período Gozo',
    )

    fim_gozo = fields.Date(
        string=u'Fim Período Gozo',
    )

    data_aviso = fields.Date(
        string=u'Data do Aviso',
    )

    limite_gozo = fields.Date(
        string=u'Limite para Gozo',
    )

    limite_aviso = fields.Date(
        string=u'Limite para Aviso',
    )

    faltas = fields.Integer(
        string=u'Faltas',
        compute='calcular_faltas',
    )

    afastamentos = fields.Integer(
        string=u'Afastamentos',
        default=0,
    )

    dias = fields.Integer(
        string=u'Dias de Direito',
        help=u'Dias que o funcionario tera direito a tirar ferias. '
             u'De acordo com a quantidade de faltas em seu perido aquisitivo',
        compute='calcular_dias',
    )

    saldo = fields.Float(
        string=u'Saldo',
        help=u'Saldo dos dias de direitos proporcionalmente aos avos ja '
             u'trabalhados no periodo aquisitivo',
        compute='calcular_saldo_dias',
    )

    dias_gozados = fields.Float(
        string=u'Dias Gozados',
        help=u'Quantidade de dias de ferias do periodo aquisitivo que ja foram'
             u'gozados pelo funcionario em outro periodo de ferias',
        default=0,
    )

    avos = fields.Integer(
        string=u'Avos',
        compute='calcular_avos',
    )

    proporcional = fields.Boolean(
        string=u'Proporcional?',
    )

    vencida = fields.Boolean(
        string=u'Vencida?',
    )

    pagamento_dobro = fields.Boolean(
        string=u'Pagamento em Dobro?',
        compute='calcular_pagamento_dobro',
    )

    dias_pagamento_dobro = fields.Integer(
        string=u'Dias Pagamento em Dobro',
        compute='calcular_dias_pagamento_dobro',
    )

    perdido_afastamento = fields.Boolean(
        string=u'Perdido por Afastamento?',
    )

    contract_id = fields.Many2one(
        comodel_name='hr.contract',
        string=u'Contrato Vigente',
    )

    hr_holiday_ids = fields.Many2many(
        comodel_name='hr.holidays',
        relation='vacation_control_holidays_rel',
        column1='hr_vacation_control_id',
        column2='holiday_id',
        string='Período Aquisitivo'
    )

    display_name = fields.Char(
        string=u'Display name',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('hr_holiday_ids')
    @api.multi
    def _compute_have_holidays(self):
        for controle in self:
            if controle.hr_holiday_ids:
                for holiday in controle.hr_holiday_ids:
                    if holiday.type == 'add':
                        controle.have_holidays = True

    have_holidays = fields.Boolean(
        string=u'Have Holidays?',
        compute='_compute_have_holidays',
        default=False,
    )

    @api.depends('inicio_aquisitivo', 'fim_aquisitivo')
    def _compute_display_name(self):
        for controle_ferias in self:
            inicio_aquisitivo = datetime.strptime(
                controle_ferias.inicio_aquisitivo, '%Y-%m-%d'
            )
            fim_aquisitivo = datetime.strptime(
                controle_ferias.fim_aquisitivo, '%Y-%m-%d'
            )
            nome = '%s - %s' % (
                inicio_aquisitivo.strftime('%d/%m/%y'),
                fim_aquisitivo.strftime('%d/%m/%y')
            )
            controle_ferias.display_name = nome

    def calcular_datas_aquisitivo_concessivo(self, inicio_periodo_aquisitivo):
        fim_aquisitivo = fields.Date.from_string(inicio_periodo_aquisitivo) + \
            relativedelta(years=1, days=-1)
        inicio_concessivo = fim_aquisitivo + relativedelta(days=1)
        fim_concessivo = inicio_concessivo + relativedelta(years=1, days=-1)
        limite_gozo = fim_concessivo + relativedelta(months=-1)
        limite_aviso = limite_gozo + relativedelta(months=-1)

        return {
            'inicio_aquisitivo': inicio_periodo_aquisitivo,
            'fim_aquisitivo': fim_aquisitivo,
            'inicio_concessivo': inicio_concessivo,
            'fim_concessivo': fim_concessivo,
            'limite_gozo': limite_gozo,
            'limite_aviso': limite_aviso,
        }

    def calcular_faltas(self):
        for record in self:
            employee_id = record.contract_id.employee_id.id
            leaves = record.env['resource.calendar'].get_ocurrences(
                employee_id,
                record.inicio_aquisitivo,
                record.fim_aquisitivo
            )
            record.faltas = leaves['quantidade_dias_faltas_nao_remuneradas']

    def dias_de_direito(self):
        dias_de_direito = 30
        if self.faltas > 23:
            dias_de_direito = 12
        elif self.faltas > 14:
            dias_de_direito = 18
        elif self.faltas > 5:
            dias_de_direito = 24
        return dias_de_direito

    def calcular_avos(self):
        for record in self:
            date_begin = fields.Datetime.from_string(record.inicio_aquisitivo)
            if fields.Date.today() < record.fim_aquisitivo:
                date_end = fields.Datetime.from_string(fields.Date.today())
            else:
                date_end = fields.Datetime.from_string(record.fim_aquisitivo)
            avos_decimal = (date_end - date_begin).days / 30.0
            decimal = avos_decimal - int(avos_decimal)

            if decimal > 0.5:
                record.avos = int(avos_decimal) + 1
            else:
                record.avos = int(avos_decimal)

    @api.depends('dias_gozados')
    def calcular_saldo_dias(self):
        for record in self:
            saldo = record.dias_de_direito() * record.avos / 12.0
            record.saldo = saldo - record.dias_gozados

    def calcular_dias(self):
        for record in self:
            record.dias = record.dias_de_direito()

    def calcular_dias_pagamento_dobro(self):
        for record in self:
            pass
            # dias_pagamento_dobro = 0
            # if record.fim_gozo > record.fim_concessivo:
            #     dias_pagamento_dobro = (
            #         fields.Date.from_string(record.fim_gozo) -
            #         fields.Date.from_string(record.fim_concessivo)
            #     ).days
            # if dias_pagamento_dobro > 30:
            #     dias_pagamento_dobro = 30
            # record.dias_pagamento_dobro = dias_pagamento_dobro

    def calcular_pagamento_dobro(self):
        for record in self:
            pagamento_dobro = (record.dias_pagamento_dobro > 0)
            record.pagamento_dobro = pagamento_dobro

    def gerar_holidays_ferias(self):
        """
        Gera novos pedidos de férias (holidays do tipo 'add') de acordo com as
        informaçoes do controle de férias em questão.
        """
        vacation_id = self.env.ref(
            'l10n_br_hr_vacation.holiday_status_vacation').id
        holiday_id = self.env['hr.holidays'].create({
            'name': 'Periodo Aquisitivo: %s ate %s'
                    % (self.inicio_aquisitivo,
                       self.fim_aquisitivo),
            'employee_id': self.contract_id.employee_id.id,
            'holiday_status_id': vacation_id,
            'type': 'add',
            'holiday_type': 'employee',
            'vacations_days': 30,
            'sold_vacations_days': 0,
            'number_of_days_temp': 30,
            'controle_ferias': [(6, 0, [self.id])],
            'contrato_id': self.contract_id.id,
        })
        return holiday_id

    @api.multi
    def action_create_periodo_aquisitivo(self):
        """
        Acção disparada na linha da visão tree do controle de férias
        :return:
        """
        for controle in self:
            controle.gerar_holidays_ferias()
