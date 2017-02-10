# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields
from dateutil.relativedelta import relativedelta


class HrVacationControl(models.Model):
    _name = 'hr.vacation.control'
    _order = 'inicio_aquisitivo desc'

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
        string=u'Dias',
        compute='calcular_dias',
    )

    saldo = fields.Float(
        string=u'Saldo',
        compute='calcular_saldo_dias',
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

    hr_holiday_ids = fields.One2many(
        comodel_name='hr.holidays',
        inverse_name='controle_ferias',
        string='Período Aquisitivo'
    )

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

    def calcular_saldo_dias(self):
        for record in self:
            record.saldo = record.avos * record.dias_de_direito() / 12.0

    def calcular_dias(self):
        for record in self:
            record.dias = record.dias_de_direito()

    def calcular_dias_pagamento_dobro(self):
        for record in self:
            dias_pagamento_dobro = 0
            if record.fim_gozo > record.fim_concessivo:
                dias_pagamento_dobro = (
                    fields.Date.from_string(record.fim_gozo) -
                    fields.Date.from_string(record.fim_concessivo)
                ).days
            if dias_pagamento_dobro > 30:
                dias_pagamento_dobro = 30
            record.dias_pagamento_dobro = dias_pagamento_dobro

    def calcular_pagamento_dobro(self):
        for record in self:
            pagamento_dobro = (record.dias_pagamento_dobro > 0)
            record.pagamento_dobro = pagamento_dobro
