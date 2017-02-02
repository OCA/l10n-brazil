# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


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
        default=30,
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
    )

    dias_pagamento_dobro = fields.Integer(
        string=u'Dias Pagamento em Dobro',
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

    def calcular_saldo_dias(self):
        employee_id = self.contract_id.employee_id.id
        quantidade_dias_ferias, quantidade_dias_abono = \
                self.env['resource.calendar'].get_quantidade_dias_ferias(
                    employee_id, self.inicio_concessivo, self.fim_concessivo)
        self.saldo = 30 - quantidade_dias_ferias - quantidade_dias_abono

    def calcular_avos(self):
        date_begin = fields.Datetime.from_string(self.inicio_aquisitivo)
        date_end = fields.Datetime.from_string(fields.Date.today())
        self.avos = (date_end - date_begin).days / 30
