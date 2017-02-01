# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class HrVacationControl(models.Model):
    _name = 'hr.vacation.control'

    inicio_aquisitivo = fields.Date(
        string=u'INÍCIO PERÍODO AQUISITIVO',
    )

    fim_aquisitivo = fields.Date(
        string=u'FIM PERÍODO AQUISITIVO',
    )

    inicio_concessivo = fields.Date(
        string=u'INÍCIO PERÍODO CONCESSIVO',
    )

    fim_concessivo = fields.Date(
        string=u'FIM PERÍODO CONCESSIVO',
    )

    inicio_gozo = fields.Date(
        string=u'INÍCIO PERÍODO GOZO',
    )

    fim_gozo = fields.Date(
        string=u'FIM PERÍODO GOZO',
    )

    data_aviso = fields.Date(
        string=u'DATA DO AVISO',
    )

    limite_gozo = fields.Date(
        string=u'LIMITE PARA GOZO',
    )

    limite_aviso = fields.Date(
        string=u'LIMITE PARA AVISO',
    )

    faltas = fields.Integer(
        string=u'FALTAS',
        default=0,
    )

    afastamentos = fields.Integer(
        string=u'AFASTAMENTOS',
        default=0,
    )

    dias = fields.Integer(
        string=u'DIAS',
        default=0,
    )

    saldo = fields.Float(
        string=u'SALDO',
    )

    avos = fields.Integer(
        string=u'AVOS',
        default=0,
    )

    proporcional = fields.Boolean(
        string=u'PROPORCIONAL?',
    )

    vencida = fields.Boolean(
        string=u'VENCIDA?',
    )

    pagamento_dobro = fields.Boolean(
        string=u'PAGAMENTO EM DOBRO?',
    )

    dias_pagamento_dobro = fields.Boolean(
        string=u'DIAS PAGAMENTO EM DOBRO',
        default=0,
    )

    perdido_afastamento = fields.Boolean(
        string=u'PERDIDO POR AFASTAMENTO?',
    )

    contract_id = fields.Many2one(
        comodel_name ='hr.contract',
        string=u'CONTRATO VIGENTE',
    )

    #
    # contract_id = fields.Many2one(
    #     comodel_name ='hr.contract',
    #     string=u'Contrato Vigente',
    # )
    # periodo_concessivo_inicio = fields.Date(
    #     string=u'Início Período Concessivo',
    # )
    # periodo_concessivo_fim = fields.Date(
    #     string=u'Fim Período Concessivo',
    # )
    # limite_gozo = fields.Date(
    #     string=u'Data limite para gozar férias',
    # )
    # limite_aviso = fields.Date(
    #     string=u'Data limite para aviso de férias',
    # )