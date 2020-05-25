# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from openerp import api, models, fields
from pybrasil.data import parse_datetime, idade_meses, ultimo_dia_mes, \
    primeiro_dia_mes


class HrVacationControl(models.Model):
    _name = 'hr.vacation.control'
    _order = 'inicio_aquisitivo desc, inicio_gozo desc'
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
        compute='_compute_calcular_faltas',
    )

    afastamentos = fields.Integer(
        string=u'Afastamentos',
        default=0,
    )

    dias = fields.Integer(
        string=u'Dias de Direito',
        help=u'Dias que o funcionario tera direito a tirar ferias. '
             u'De acordo com a quantidade de faltas em seu perido aquisitivo',
        compute='_compute_calcular_dias',
    )

    saldo = fields.Float(
        string=u'Saldo de dias',
        help=u'Saldo dos dias de direitos proporcionalmente aos avos ja '
             u'trabalhados no periodo aquisitivo',
        compute='_compute_calcular_saldo_dias',
    )

    dias_gozados = fields.Float(
        string=u'Dias Gozados',
        help=u'Quantidade de dias de ferias do periodo aquisitivo que ja foram'
             u'gozados pelo funcionario em outro periodo de ferias',
        default=0,
    )

    dias_gozados_anteriormente = fields.Float(
        string=u'Dias Gozados Anteriormente',
        default=0,
    )

    avos = fields.Integer(
        string=u'Avos de direito',
        compute='_compute_calcular_avos',
    )

    avo_manual = fields.Integer(
        string=u'Forçar quantidade de avos',
    )

    avos_pendentes = fields.Float(
        string=u'Avos Pendentes',
        compute='_compute_calcular_avos_pendentes',
    )

    proporcional = fields.Boolean(
        string=u'Proporcional?',
    )

    vencida = fields.Boolean(
        string=u'Vencida?',
    )

    pagamento_dobro = fields.Boolean(
        string=u'Pagamento em Dobro?',
        compute='_compute_calcular_pagamento_dobro',
    )

    dias_pagamento_dobro = fields.Integer(
        string=u'Dias Pagamento em Dobro',
        compute='_compute_calcular_dias_pagamento_dobro',
    )

    perdido_afastamento = fields.Boolean(
        string=u'Perdido por Afastamento?',
    )

    contract_id = fields.Many2one(
        comodel_name='hr.contract',
        string=u'Contrato Vigente',
    )

    # hr_holiday_ids = fields.Many2many(
    #     comodel_name='hr.holidays',
    #     relation='vacation_control_holidays_rel',
    #     column1='hr_vacation_control_id',
    #     column2='holiday_id',
    #     string=u'Período Aquisitivo',
    #     ondelete='set null',
    # )

    hr_holiday_add_id = fields.Many2one(
        comodel_name='hr.holidays',
        string=u'Férias (ADD)',
    )

    hr_holiday_remove_id = fields.Many2one(
        comodel_name='hr.holidays',
        string=u'Pedido de férias',
    )

    display_name = fields.Char(
        string=u'Display name',
        compute='_compute_display_name',
        store=True,
    )

    # @api.depends('hr_holiday_ids')
    # @api.multi
    # def _compute_have_holidays(self):
    #     for controle in self:
    #         if controle.hr_holiday_ids:
    #             for holiday in controle.hr_holiday_ids:
    #                 if holiday.type == 'add':
    #                     controle.have_holidays = True

    # have_holidays = fields.Boolean(
    #     string=u'Have Holidays?',
    #     compute='_compute_have_holidays',
    #     default=False,
    # )

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
                fim_aquisitivo.strftime('%d/%m/%y'),
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

    def _compute_calcular_faltas(self):
        """
        Calcular a quantidade de faltas que irao pro cálculo de dias de
        direito em férias
        :return:
        """
        for record in self:

            qtd_desconto_ferias = 0

            domain = [
                ('state', '=', 'validate'),
                ('employee_id', '=', record.contract_id.employee_id.id),
                ('type', '=', 'remove'),
            ]

            clause_1 = [
                ('data_inicio', '>=', record.inicio_aquisitivo),
                ('data_inicio', '<=', record.fim_aquisitivo)]
            holidays_1_ids = self.env['hr.holidays'].search(domain + clause_1)

            clause_2 = [('data_fim', '>=', record.inicio_aquisitivo),
                        ('data_fim', '<=', record.fim_aquisitivo)]
            holidays_2_ids = self.env['hr.holidays'].search(domain + clause_2)

            for leave in holidays_1_ids | holidays_2_ids:

                data_referencia = fields.Datetime.from_string(leave.data_inicio)
                data_fim_holidays = fields.Datetime.from_string(leave.data_fim)

                while data_referencia <= data_fim_holidays:

                    inicio = \
                        fields.Datetime.from_string(record.inicio_aquisitivo)
                    fim = fields.Datetime.from_string(record.fim_aquisitivo)

                    if data_referencia >= inicio and data_referencia <= fim :
                        if leave.holiday_status_id.descontar_ferias:
                            # Levar em consideração o tipo de dias
                            if leave.holiday_status_id.type_day == 'uteis':
                                rc = self.env['resource.calendar']
                                if rc.data_eh_dia_util(data_referencia):
                                    qtd_desconto_ferias += 1
                            else:
                                qtd_desconto_ferias += 1
                    data_referencia += timedelta(days=1)

            record.faltas = qtd_desconto_ferias

    def dias_de_direito(self):
        dias_de_direito = 30
        if self.faltas > 23:
            dias_de_direito = 12
        elif self.faltas > 14:
            dias_de_direito = 18
        elif self.faltas > 5:
            dias_de_direito = 24
        dias_de_direito -= self.dias_gozados_anteriormente
        return dias_de_direito

    def _compute_calcular_avos_pendentes(self):
        for record in self:
            record.avos_pendentes = record.saldo / 2.5

    def _compute_calcular_avos(self):
        for record in self:
            date_begin = record.inicio_aquisitivo

            # Pega data_fim do contexto se existir, para cálculo de simulações
            if "data_fim" in self.env.context:
                hoje = self.env.context['data_fim']
            else:
                hoje = fields.Date.today()

            if hoje < record.fim_aquisitivo:
                date_end = hoje
            else:
                date_end = record.fim_aquisitivo

            if record.contract_id.date_end and record.contract_id.date_end <= record.fim_aquisitivo:
                date_end = record.contract_id.date_end

            date_end = fields.Date.from_string(date_end) + \
                       relativedelta(days=1)
            date_end = fields.Date.to_string(date_end)

            #
            # Calcula os avos
            #
            ultimo_dia_primeiro_mes = ultimo_dia_mes(date_begin)

            # Se rescisao menor que o ultimo dia do mês
            if fields.Date.from_string(date_end) < ultimo_dia_mes(date_begin):
                ultimo_dia_primeiro_mes = ultimo_dia_mes(date_begin)

            # Se no primeiro mes trabalhou mais do que 14 dias contabilizar avo
            dias_trabalhados_primeiro_mes = \
                ultimo_dia_primeiro_mes - parse_datetime(date_begin).date()

            if dias_trabalhados_primeiro_mes >= timedelta(days=14):
                avos_primeiro_mes = 1
            else:
                avos_primeiro_mes = 0

            #
            # Se for para cálculo de rescisão, calcule o avo do fim do
            # período aquisitivo de acordo com instruções abaixo.
            #
            """
            
O cálculo de férias usa a regra dos 15 dias trabalhados no mês, mas leva em 
consideração a data de "aniversário" do período aquisitivo, ou seja, dia 06 de 
cada mês no caso do Antônio, assim teremos; Mar (trabalhou mais de 15 dias), 
Abr, Mai, Jun, Jul, Ago, Set, Out, Nov e Dez/2016 totalizando 10 avos, 
para jan/2017, levando em consideração o dia 06 e a data da rescisão (16/01), 
dá menos que 15 dias trabalhados, não considera o avo.

Transcrevo abaixo o Art. 130 da CLT:

Art. 130 - Após cada período de 12 (doze) meses de vigência do contrato de 
trabalho, o empregado terá direito a férias, na seguinte proporção: (Redação 
dada pelo Decreto-lei nº 1.535, de 13.4.1977)

I - 30 (trinta) dias corridos, quando não houver faltado ao serviço mais de 5 
(cinco) vezes;  (Incluído pelo Decreto-lei nº 1.535, de 13.4.1977)

II - 24 (vinte e quatro) dias corridos, quando houver tido de 6 (seis) a 14 
(quatorze) faltas; (Incluído pelo Decreto-lei nº 1.535, de 13.4.1977)

III - 18 (dezoito) dias corridos, quando houver tido de 15 (quinze) a 23 
(vinte e três) faltas; (Incluído pelo Decreto-lei nº 1.535, de 13.4.1977)

IV - 12 (doze) dias corridos, quando houver tido de 24 (vinte e quatro) a 32 
(trinta e duas) faltas. (Incluído pelo Decreto-lei nº 1.535, de 13.4.1977)

§ 1º - É vedado descontar, do período de férias, as faltas do empregado ao 
serviço. (Incluído pelo Decreto-lei nº 1.535, de 13.4.1977)

§ 2º - O período das férias será computado, para todos os efeitos, como tempo 
de serviço.(Incluído pelo Decreto-lei nº 1.535, de 13.4.1977)

Como podemos observar, o artigo leva em consideração a vigência do contrato, 
isto é, a data de admissão do funcionário, e combinado com o Art. 146 da CLT, 
fica interpretado que os avos são considerados a partir da data de admissão e 
não do mês civil.

 Observação: Além das informações acima, consultamos o nosso apoio jurídico 
 trabalhista IOB.
 Carlos Eduardo Silva
            """
            avos_ultimo_mes = 0

            # Para contabilizar os avos das férias, levar em consideraçõ o
            # "aniversario" do  periodo aquisitivo
            dia_aniversario_periodo_aquisitivo = \
                fields.Date.from_string(record.inicio_aquisitivo).day

            # Resolver casos que o aniversario do periodo aquisitivo for no dia
            # 31 e alguns meses nao tem 31 dias.
            primeiro_dia_ultimo_mes = False
            while not primeiro_dia_ultimo_mes:
                try:
                    primeiro_dia_ultimo_mes = primeiro_dia_mes(date_end)
                except ValueError:
                    dia_aniversario_periodo_aquisitivo += -1

            ultimo_dia_ultimo_mes = ultimo_dia_mes(date_end)

            # calcular dias trabalhados no ultimo mes a partir do aniversario
            # do periodo aquisitivo
            dias = parse_datetime(date_end).date() - primeiro_dia_ultimo_mes

            dias_mes = ultimo_dia_ultimo_mes - primeiro_dia_ultimo_mes

            if dias > timedelta(days=15):
                # Se trabalhou mais do que 15 dias no ultimo mes do
                # periodo aquisitvo, pagar avos na rescisao
                avos_ultimo_mes = 1
            elif dias == timedelta(days=15):
                if dias_mes != timedelta(days=30):
                    avos_ultimo_mes = 1

            primeiro_dia_mes_cheio = \
                ultimo_dia_mes(date_begin) + timedelta(days=1)

            ultimo_dia_mes_cheio = primeiro_dia_mes(date_end)

            avos_meio = idade_meses(parse_datetime(primeiro_dia_mes_cheio),
                                    parse_datetime(ultimo_dia_mes_cheio))

            avos = avos_primeiro_mes + avos_meio + avos_ultimo_mes

            # TODO: Essa correção foi criada para que o sistema não aceite
            # mais que 12 avos em um só período, mas deverá ser corrigido
            # por uma correção definitiva.
            if avos > 12:
                avos = 12

            record.avos = avos

            if record.avo_manual:
                record.avos = record.avo_manual

            # avos_decimal = (date_end - date_begin).days / 30.0
            # decimal = avos_decimal - int(avos_decimal)
            #
            # if decimal > 0.5:
            #     record.avos = int(avos_decimal) + 1
            # else:
            #     record.avos = int(avos_decimal)

    @api.depends('dias_gozados')
    def _compute_calcular_saldo_dias(self):
        for record in self:
            saldo = record.dias_de_direito() * record.avos / 12.0
            record.saldo = saldo - record.dias_gozados

    def _compute_calcular_dias(self):
        for record in self:
            record.dias = record.dias_de_direito()

    def _compute_calcular_dias_pagamento_dobro(self):
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

    def _compute_calcular_pagamento_dobro(self):
        for record in self:
            pagamento_dobro = (record.dias_pagamento_dobro > 0)
            record.pagamento_dobro = pagamento_dobro

    def gerar_holidays_ferias(self):
        """
        Gera novos pedidos de férias (holidays do tipo 'add') de acordo com as
        informaçoes do controle de férias em questão.
        """
        vacation_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_vacation').id

        vals = {
            'name': 'Periodo Aquisitivo: %s ate %s'
                    % (self.inicio_aquisitivo,
                       self.fim_aquisitivo),
            'employee_id': self.contract_id.employee_id.id,
            'contrato_id': self.contract_id.id,
            'holiday_status_id': vacation_id,
            'type': 'add',
            'tipo': 'ferias',
            'holiday_type': 'employee',
            'vacations_days': 30,
            'sold_vacations_days': 0,
            'number_of_days_temp': 30,
            'controle_ferias': [(6, 0, [self.id])],
            'controle_ferias_ids': [(6, 0, [self.id])],
        }

        holiday_id = self.env['hr.holidays'].\
            with_context(mail_notrack=True).create(vals)

        holiday_id.state = 'validate'

        return holiday_id

    @api.multi
    def action_create_periodo_aquisitivo(self):
        """
        Acção disparada na linha da visão tree do controle de férias
        :return:
        """
        for controle in self:
            controle.gerar_holidays_ferias()

    # @api.multi
    # def unlink(self):
    #     """
    #    Se excluir o controle de ferias, excluir todos os holidays atrelados
    #     FIXTO: utilizar o ondelete=cascade na definição do campo
    #    """
    #     for holidays in self.hr_holiday_ids:
    #        holidays.unlink()
    #     return super(HrVacationControl, self).unlink()
