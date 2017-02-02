# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from dateutil.relativedelta import relativedelta


class HrVacationControl(models.Model):
    _name = 'hr.vacation.control'

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
        comodel_name ='hr.contract',
        string=u'Contrato Vigente',
    )

    def calcular_faltas(self):
        employee_id = self.contract_id.employee_id.id
        leaves  = self.env['resource.calendar'].get_ocurrences(
             employee_id, self.inicio_aquisitivo, self.fim_aquisitivo
        )
        self.faltas = leaves['quantidade_dias_faltas_nao_remuneradas']

    def dias_de_direito(self):
        dias_de_direito = 30
        if self.faltas > 23 : dias_de_direito = 12
        elif self.faltas > 14 : dias_de_direito = 18
        elif self.faltas > 5 : dias_de_direito = 24
        return dias_de_direito

    def calcular_avos(self):
        date_begin = fields.Datetime.from_string(self.inicio_aquisitivo)
        if fields.Date.today() < self.fim_aquisitivo:
            date_end = fields.Datetime.from_string(fields.Date.today())
        else:
            date_end = fields.Datetime.from_string(self.fim_aquisitivo)
        avos_decimal = (date_end - date_begin).days / 30.0
        decimal = avos_decimal - int(avos_decimal)

        if decimal > 0.5:
            self.avos = int(avos_decimal) + 1
        else:
            self.avos = int(avos_decimal)

    def calcular_saldo_dias(self):
        self.saldo = self.avos * self.dias_de_direito() / 12.0

    def calcular_dias(self):
        self.dias = self.dias_de_direito()

    def calcular_dias_pagamento_dobro(self):
        dias_pagamento_dobro = 0
        if self.fim_gozo > self.fim_concessivo:
            dias_pagamento_dobro = (fields.Date.from_string(self.fim_gozo) -
                                    fields.Date.from_string(
                                        self.fim_concessivo)).days
        if dias_pagamento_dobro > 30:
            dias_pagamento_dobro = 30
        self.dias_pagamento_dobro = dias_pagamento_dobro

    def calcular_pagamento_dobro(self):
        pagamento_dobro = self.dias_pagamento_dobro > 0
        self.pagamento_dobro = pagamento_dobro
