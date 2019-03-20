# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime
from dateutil.relativedelta import relativedelta
from pybrasil.data import ultimo_dia_mes
from pybrasil.data import formata_data
import logging

_logger = logging.getLogger(__name__)

MES_DO_ANO = [
    (1, u'Janeiro'),
    (2, u'Fevereiro'),
    (3, u'Março'),
    (4, u'Abril'),
    (5, u'Maio'),
    (6, u'Junho'),
    (7, u'Julho'),
    (8, u'Agosto'),
    (9, u'Setembro'),
    (10, u'Outubro'),
    (11, u'Novembro'),
    (12, u'Dezembro'),
    (13, u'13º Salário')
]

TIPO_DE_FOLHA = [
    ('normal', u'Folha normal'),
    ('adiantamento_13', u'13º Salário - Adiantamento'),
    ('decimo_terceiro', u'13º Salário'),
    ('provisao_ferias', u'Provisão de Férias'),
    ('provisao_decimo_terceiro', u'Provisão de Décimo Terceiro (13º)'),
]


class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"
    _order = "ano desc,mes_do_ano desc,tipo_de_folha asc, company_id asc"
    _sql_constraints = [
        ('lote_unico',
         'unique(ano, mes_do_ano, tipo_de_folha, company_id)',
         'Este Lote de Holerite já existe!'),
        ('nome',
         'unique(display_name)',
         'Este nome de Lote já existe ! ' 
         'Por favor digite outro que não se repita')
    ]

    name = fields.Char(
        string='Name',
        compute='get_compute_name',
        inverse='inverse_name',
        store=True,
    )

    mes_do_ano = fields.Selection(
        selection=MES_DO_ANO,
        string=u'Mês',
        required=True,
        default=datetime.now().month,
    )
    ano = fields.Integer(
        string=u'Ano',
        default=datetime.now().year,
    )
    tipo_de_folha = fields.Selection(
        selection=TIPO_DE_FOLHA,
        string=u'Tipo de folha',
        default='normal',
    )
    contract_id = fields.Many2many(
        comodel_name='hr.contract',
        string='Contratos',
    )
    departamento_id = fields.Many2one(
        comodel_name='hr.department',
        string='Departamento',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Empresa',
        default=lambda self: self.env.user.company_id or '',
    )
    eh_mes_comercial = fields.Boolean(
        string=u"Mês Comercial?",
    )

    payslip_rescisao_ids = fields.Many2many(
        string="Rescisões",
        comodel_name="hr.payslip",
        rel="rel_hr_payslip_run_hr_paysip_rescisao",
        column1="slip_id",
        column2="hr_payslip_run_id",
    )

    data_de_pagamento = fields.Date(
        string=u'Data de Pagamento',
    )

    @api.onchange('tipo_de_folha')
    def fixa_decimo_terceiro(self):
        if self.tipo_de_folha == 'adiantamento_13' and self.mes_do_ano == 12:
            self.tipo_de_folha = 'decimo_terceiro'
            self.mes_do_ano = 13
        else:
            if self.tipo_de_folha == 'decimo_terceiro':
                self.mes_do_ano = 13
            elif self.mes_do_ano == 13:
                self.mes_do_ano = datetime.now().month

    @api.onchange('mes_do_ano', 'ano')
    def buscar_datas_periodo(self):
        if not self.mes_do_ano:
            self.mes_do_ano = datetime.now().month

        if self.tipo_de_folha == 'adiantamento_13' and self.mes_do_ano == 12:
            self.tipo_de_folha = 'decimo_terceiro'
            self.mes_do_ano = 13

        mes = self.mes_do_ano
        if mes > 12:
            mes = 12
            self.tipo_de_folha = 'decimo_terceiro'
        elif self.tipo_de_folha == 'decimo_terceiro':
            self.tipo_de_folha = 'normal'

        ultimo_dia_do_mes = str(
            self.env['resource.calendar'].get_ultimo_dia_mes(
                mes, self.ano))

        primeiro_dia_do_mes = str(
            datetime.strptime(str(mes) + '-' +
                              str(self.ano), '%m-%Y'))

        self.date_start = primeiro_dia_do_mes
        self.date_end = ultimo_dia_do_mes


    @api.multi
    def verificar_holerites_gerados(self):

        # remover holerites que foram gerados pelo lote mas nao foram
        # confirmados
        # not_done = self.slip_ids.filtered(lambda s: not s.state == 'done')
        # not_done.unlink()

        # holerites que ja foram confirmados
        # done = self.slip_ids.filtered(lambda s: s.state == 'done')

        for lote in self:
            # pegar todos contratos da empresa que são válidos,
            dominio_contratos = [
                ('date_start', '<=', lote.date_end),
                ('tipo', '!=', 'autonomo'),
                ('compor_lote', '=', True),
                ('company_id', '=', lote.company_id.id),
            ]

            # Se existir  holerites ja concluidos nao buscar os contratos
            # destes holerites
            # if done:
            #     dominio_contratos += [
            #         ('id', 'not in', done.mapped('contract_id').ids),
            #     ]

            # Se for lote de folha normal nao pegar as categorias inválidas
            if lote.tipo_de_folha != 'normal':
                dominio_contratos += [
                    ('categoria', 'not in', ['721', '722']),
                ]
            # else:
            #     dominio_contratos += [
            #         ('date_end', '>', lote.date_start),
            #     ]

            # Buscar contratos validos
            contracts_id = self.env['hr.contract'].search(dominio_contratos)

            # Caso o tipo de lote for "Adiantamento de 13º", deverá ser trocado
            # por "decimo_terceiro", já que os holerites são criados com esse
            # tipo
            if self.tipo_de_folha == 'adiantamento_13':
                tipo_de_folha = 'decimo_terceiro'
            else:
                tipo_de_folha = self.tipo_de_folha

            # buscar payslip ja processadas dos contratos validos
            dominio_payslips = [
                ('tipo_de_folha', '=', tipo_de_folha),
                ('contract_id', 'in', contracts_id.ids)
            ]

            # se o lote for de provisao de ferias, buscar entre o periodo todo
            if lote.tipo_de_folha != 'provisao_ferias':
                dominio_payslips += [
                    ('date_from', '>=', self.date_start),
                    ('date_to', '<=', self.date_end),
                ]

            # Se o lote for de qualquer utro tipo, buscar apenas paylisps
            # do mes setado no lote.
            else:
                dominio_payslips += [
                    ('mes_do_ano', '=', self.mes_do_ano),
                    ('ano', '=', self.ano),
                ]

            # Buscar payslips dos contratos validos que ja foram processadas
            payslips = self.env['hr.payslip'].search(dominio_payslips)

            # grupo contendo os contratos que ja foram processados naquele período
            contratos_com_holerites = []
            for payslip in payslips:
                if payslip.contract_id.id not in contratos_com_holerites:
                    contratos_com_holerites.append(payslip.contract_id.id)

            contratos_sem_holerite = []
            for contrato in contracts_id:
                 # se o contrato valido nao esta nos contratos que ja possuem
                 # payslip naquele periodo
                 if contrato.id not in contratos_com_holerites:
                     # remover contratos finalizados
                     if not contrato.date_end:
                         contratos_sem_holerite.append(contrato.id)
                     else:
                         if contrato.date_end > lote.date_end:
                             contratos_sem_holerite.append(contrato.id)

            # Adiantamento eh uma rubrica
            # no processamento do lote de adiantamento de 13,
            # filtrar os contratos que ja foram processados naquele intervalo
            # com aquela rubrica
            if lote.tipo_de_folha == 'adiantamento_13':
                # buscar as rubricas que foram processadas de adiantamento 13
                rubricas_ids = self.env['hr.payslip.line'].search([
                    ('contract_id', 'in', contratos_sem_holerite),
                    ('code', '=', 'ADIANTAMENTO_13'),
                    ('slip_id.ano', '=', self.ano),
                    ('slip_id.mes_do_ano', '<=', self.mes_do_ano),
                    ('slip_id.state', '=', 'done'),
                    ('total', '>', 0),
                ])

                # filtrar os contratos dessas rubricas
                contratos_ids = rubricas_ids.mapped('contract_id')

                # remover esses contratos dos contratos validos
                contratos_sem_holerite = \
                    list(set(contratos_sem_holerite) - set(contratos_ids.ids))

            # Buscar rescisoes da competencia
            domain = [
                ('tipo_de_folha', '=', 'rescisao'),
                ('is_simulacao', '!=', True),
                ('mes_do_ano', '=', self.mes_do_ano),
                ('ano', '=', self.ano),
                ('company_id', '=', lote.company_id.id),
            ]
            self.payslip_rescisao_ids = self.env['hr.payslip'].search(domain)

            lote.write({
                'contract_id': [(6, 0, contratos_sem_holerite)],
            })

    @api.multi
    def gerar_holerites(self):
        for contrato in self.contract_id:
            # Provisionamento de ferias
            if self.tipo_de_folha == 'provisao_ferias':

                # recuperar primeiro dia do mes
                inicio_mes = str(self.ano).zfill(4) + '-' + \
                              str(self.mes_do_ano).zfill(2) + '-01'

                # se o contrato iniciou na metade do mes corrente
                # ex.: provisionando mes marco e contrato iniciou 15/03
                if contrato.date_start > inicio_mes:
                    inicio_mes = contrato.date_start

                data_inicio = fields.Date.to_string(ultimo_dia_mes(inicio_mes))

                contrato.action_button_update_controle_ferias(
                    data_referencia=data_inicio)

                for periodo in contrato.vacation_control_ids:
                    if periodo.saldo > 0 and not periodo.inicio_gozo:
                        try:
                            data_fim = fields.Date.from_string(inicio_mes) + \
                                  relativedelta(days=periodo.saldo)
                            payslip_obj = self.env['hr.payslip']

                            periodo_aquisitivo_provisao = \
                                str(int(periodo.saldo)) + \
                                ' dias referente a ' + \
                                formata_data(periodo.inicio_aquisitivo) + \
                                ' - ' + \
                                formata_data(periodo.fim_aquisitivo)

                            payslip = payslip_obj.create({
                                'contract_id': contrato.id,
                                'periodo_aquisitivo': periodo.id,
                                'mes_do_ano': self.mes_do_ano,
                                'mes_do_ano2': self.mes_do_ano,
                                'date_from': inicio_mes,
                                'date_to': data_fim,
                                'ano': self.ano,
                                'employee_id': contrato.employee_id.id,
                                'tipo_de_folha': self.tipo_de_folha,
                                'payslip_run_id': self.id,
                                'periodo_aquisitivo_provisao':
                                    periodo_aquisitivo_provisao,
                                'eh_mes_comercial': self.eh_mes_comercial,
                            })
                            # payslip._compute_set_dates()
                            payslip.compute_sheet()
                            self.env.cr.commit()
                            _logger.info(u"Holerite " + contrato.name +
                                         u" processado com sucesso!")
                        except:
                            _logger.warning(u"Holerite " + contrato.name +
                                            u" falhou durante o cálculo!")
                            payslip.unlink()
                            continue
                contrato.action_button_update_controle_ferias()
            else:
                try:
                    tipo_de_folha = self.tipo_de_folha
                    if tipo_de_folha == 'adiantamento_13':
                        tipo_de_folha = 'decimo_terceiro'
                    payslip_obj = self.env['hr.payslip']

                    mes_do_ano = self.mes_do_ano
                    if mes_do_ano == 13:
                        mes_do_ano = 12

                    ultimo_dia_do_mes = str(
                        self.env['resource.calendar'].get_ultimo_dia_mes(
                            self.mes_do_ano, self.ano))

                    primeiro_dia_do_mes = str(
                        datetime.strptime(str(self.mes_do_ano) + '-' +
                                          str(self.ano), '%m-%Y'))

                    payslip = payslip_obj.create({
                        'contract_id': contrato.id,
                        'mes_do_ano': self.mes_do_ano,
                        'mes_do_ano2': mes_do_ano,
                        'ano': self.ano,
                        'date_from': primeiro_dia_do_mes,
                        'date_to': ultimo_dia_do_mes,
                        'employee_id': contrato.employee_id.id,
                        'tipo_de_folha': tipo_de_folha,
                        'payslip_run_id': self.id,
                        'eh_mes_comercial': self.eh_mes_comercial,
                    })
                    payslip._compute_set_dates()
                    payslip._compute_set_employee_id()
                    payslip.compute_sheet()
                    _logger.info(
                        u"Holerite " + contrato.display_name +
                        u" processado com sucesso!")
                    self.env.cr.commit()
                except:
                    _logger.warning(
                        u"Holerite " + contrato.display_name +
                        u" falhou durante o cálculo!")
                    payslip.unlink()
                    continue
        self.verificar_holerites_gerados()

    @api.multi
    def close_payslip_run(self):
        """
        Só fechar lotes, se não tiver nenhum em rascunho
        """
        for lote in self:
            if any(l == 'draft' for l in lote.slip_ids.mapped('state')):
                raise UserError(
                    _('Erro no fechamento deste Lote !\n'
                      'Há holerite(s) não confirmados!')
                )
            return super(HrPayslipRun, self).close_payslip_run()

    @api.depends('mes_do_ano', 'ano', 'company_id', 'tipo_de_folha')
    def get_compute_name(self):
        """
        """
        for record in self:
            name = ''

            if record.tipo_de_folha:
                name += dict(TIPO_DE_FOLHA).get(record.tipo_de_folha)
                name += ' '

            if record.mes_do_ano:
                name += dict(MES_DO_ANO).get(record.mes_do_ano)
                name += '/'

            if record.ano:
                name += str(record.ano)
                name += ' - '

            if record.company_id:
                name += str(record.company_id.name)

            record.name = name

    def inverse_name(self):
        """
        """
        pass

    @api.multi
    def unlink(self):
        """
        Validacao para exclusao de lote de holerites
        Nao permitir excluir o lote se ao menos um holerite nao estiver no
        state draft.vali
        """
        for lote in self:
            if any(l != 'draft' for l in lote.slip_ids.mapped('state')):
                raise UserError(
                    _('Erro na exclusão deste Lote !\n'
                      'Há holerite(s) já confirmados!')
                )
        return super(HrPayslipRun, self).unlink()
