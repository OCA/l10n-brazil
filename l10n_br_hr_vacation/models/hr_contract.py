# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields, _
from dateutil.relativedelta import relativedelta
from lxml import etree
from openerp.exceptions import Warning as UserError

import logging

_logger = logging.getLogger(__name__)

try:
    from pybrasil import data

except ImportError:
    _logger.info('Cannot import pybrasil')

class HrContract(models.Model):
    _inherit = 'hr.contract'

    vacation_control_ids = fields.One2many(
        comodel_name='hr.vacation.control',
        inverse_name='contract_id',
        string=u'Periodos Aquisitivos Alocados',
        ondelete="cascade",
    )

    forca_inicio_periodo_aquisitivo = fields.Date(
        string=u'Data inicial Período Aquisitivo',
        help=u'Data Inicial para cálculo dos períodos aquisitivos.\n'
             u'Essa data substituirá a data de contratação e a regra do '
             u'funcionário cedido no cálculo dos períodos aquisitivos.'
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

    @api.multi
    def write(self, vals):
        """
        No HrContract, o método write é chamado tanto na api antiga quanto na
        api nova. No caso da alteração da data de início do contrato, a chamada
        é feita na api antiga, dessa forma, é passado uma lista com os ids a
        serem escritos e os valores a serem alterados num dicionário chamado
        context. A programação abaixo foi feita da seguinte forma: primeiro
        verifica-se se há holidays do tipo remove atrelados ao contrato, pois
        se existe, a data de início do contrato não pode ser alterado por
        motivos de integridade do sistema. Depois são deletados os holidays do
        tipo add e as linhas de controle de férias antigas. Por último, são
        criadas novas linhas de controle de férias e holidays do tipo add para
        a nova data de início do contrato.
        """
        # if vals.get('date_start') and \
        #         (vals.get('date_start') != self.date_start):
            # self.verificar_controle_ferias()
            # self.atualizar_linhas_controle_ferias(vals.get('date_start'))
        contract_id = super(HrContract, self).write(vals)
        # se o contrato ja se encerrou, replicar no controle de férias
        if 'date_end' in vals:
            self.atualizar_data_demissao()
        return contract_id

    @api.model
    def create(self, vals):
        hr_contract_id = super(HrContract, self).create(vals)
        if vals.get('tipo') == 'autonomo':
            return hr_contract_id
        if vals.get('date_start'):
            hr_contract_id.action_button_update_controle_ferias()
        # se o contrato ja se encerrou, replicar no controle de férias
        if vals.get('date_end'):
            hr_contract_id.atualizar_data_demissao()
        return hr_contract_id

    @api.multi
    def atualizar_data_demissao(self):
        """
        Se o contrato ja foi encerrado, replica a informação para o
        controle de ferias computar corretamente as ferias de direito
        :return:
        """
        for contrato in self:
            if contrato.date_end and \
                    contrato.vacation_control_ids and \
                    contrato.vacation_control_ids[0].fim_aquisitivo > \
                            contrato.date_end:
                contrato.vacation_control_ids[0].fim_aquisitivo = \
                    contrato.date_end
                contrato.vacation_control_ids[0].inicio_concessivo = ''
                contrato.vacation_control_ids[0].fim_concessivo = ''

            # Se estiver reativando o contrato, isto é, removendo a data de
            # demissão
            #
            if not contrato.date_end and contrato.vacation_control_ids:
                vc_obj = contrato.vacation_control_ids
                inicio_aquisit = \
                    contrato.vacation_control_ids[0].inicio_aquisitivo
                vals = \
                    vc_obj.calcular_datas_aquisitivo_concessivo(inicio_aquisit)
                # Atualizar datas do ultimo controle de ferias
                ultimo_controle = contrato.vacation_control_ids[0]
                ultimo_controle.fim_aquisitivo = \
                    vals.get('fim_aquisitivo')
                ultimo_controle.inicio_concessivo = \
                    vals.get('inicio_concessivo')
                ultimo_controle.fim_concessivo = \
                    vals.get('fim_concessivo')

    @api.multi
    def action_button_update_controle_ferias(
            self, context=False, data_referencia=False):
        """
        Ação disparada pelo botão na view, que atualiza as linhas de controle
        de férias
        """

        recalculo = True
        if not data_referencia:
            if self.date_end:
                data_referencia = self.date_end
            else:
                data_referencia = fields.Date.today()
            recalculo = False
        else:
            if self.date_end:
                if data_referencia > self.date_end:
                    data_referencia = self.date_end

        for contrato in self:

            controle_ferias_obj = self.env['hr.vacation.control']
            lista_controle_ferias = []

            # Apagar o controle de férias (períodos aquisitivos) do contrato
            #
            contrato.vacation_control_ids.unlink()

            # Criar os períodos aquisitivos
            #
            inicio = fields.Date.from_string(contrato.date_start)

            # para casos como funcionario cedente, utilizar a data de
            # admissao no orgao cedente
            if self.data_admissao_cedente:
                # Iniciar a contagem a partir do segundo dia  do ano
                # anterior a data de contratação do funcionario
                data_admissao = fields.Date.from_string(self.date_start)
                ano_admissao = data_admissao.year
                inicio = data_admissao.replace(
                    day=2, month=1, year=ano_admissao-1)

            if self.forca_inicio_periodo_aquisitivo:
                inicio = fields.Date.from_string(
                    self.forca_inicio_periodo_aquisitivo)

            hoje = fields.Date.from_string(data_referencia)

            while inicio <= hoje:
                vals = \
                    controle_ferias_obj.calcular_datas_aquisitivo_concessivo(
                        str(inicio)
                    )
                if inicio + relativedelta(years=1) > hoje and recalculo:
                    vals['fim_aquisitivo'] = hoje
                controle_ferias = controle_ferias_obj.create(vals)
                inicio = inicio + relativedelta(years=1)
                lista_controle_ferias.append(controle_ferias.id)

            # Ordena períodos aquisitivos recalculados
            #
            contrato.vacation_control_ids = \
                sorted(lista_controle_ferias, reverse=True)

            # Buscar holerites de Férias registradas
            #
            domain = [
                ('contract_id', '=', contrato.id),
                ('tipo_de_folha', '=', 'ferias'),
                ('is_simulacao', '=', False),
                ('state', '!=', 'cancel'),
            ]

            # Quando na execucao tiver uma data de referencia (provisoes de
            # férias) buscar as férias até a data de referencia somente
            if recalculo:
                domain.append(('date_from', '<=', hoje))

            holerites_ids = \
                self.env['hr.payslip'].search(domain, order='date_from')

            # Laço para percorrer todos os holerites de férias(aviso de férias)
            #
            for holerite in holerites_ids:

                # Buscar controle de férias referente ao aviso de férias que
                # esta sendo processado
                #
                controle_id = controle_ferias_obj.search([
                    ('inicio_aquisitivo', '=', holerite.inicio_aquisitivo),
                    ('fim_aquisitivo', '=', holerite.fim_aquisitivo),
                    ('inicio_gozo', '=', False),
                    ('fim_gozo', '=', False),
                    ('contract_id', '=', contrato.id)
                ])

                if controle_id:

                    # Recuperar datas do aviso de férias para construir
                    # controle de ferias
                    #
                    data_inicio = \
                        fields.Date.from_string(holerite.date_from)
                    data_fim = fields.Date.from_string(holerite.date_to)
                    abono_pecuniario = \
                        holerite.holidays_ferias.sold_vacations_days
                    dias_gozados = (data_fim - data_inicio).days + 1 + \
                                   abono_pecuniario

                    # se houver saldo de dias, isto é, se o funcinoario tirou
                    # apenas uma parte das férias, duplicar controle vazio
                    #
                    if (controle_id.saldo - dias_gozados) > 0:
                        novo_periodo = controle_id.copy()
                        novo_periodo.dias_gozados_anteriormente += dias_gozados

                    # Setar datas do novo controle de férias baseado no holerite
                    # de férias (aaviso de férias)
                    controle_id.inicio_gozo = holerite.date_from
                    controle_id.fim_gozo = holerite.date_to
                    controle_id.data_aviso = holerite.date_from
                    controle_id.dias_gozados = dias_gozados

                    # Linkar Holerite com o Período Aquisitivo
                    holerite.periodo_aquisitivo = controle_id

                    # Recuperar a solicitação de férias (holiday remove) holerite
                    #
                    controle_id.hr_holiday_remove_id = holerite.holidays_ferias

                    # Recuperar a alocação de férias (holiday add) da
                    # solicitação de férias
                    #
                    controle_id.hr_holiday_add_id = \
                        holerite.holidays_ferias.parent_id

            # Buscar os holiday do tipo ADD que perderam a relação com o
            # controle de férias
            #
            holidays_ids = self.env['hr.holidays'].search([
                ('controle_ferias', '=', False),
                ('contrato_id', '=', contrato.id),
                ('type', '=', 'add')
            ])

            # Se algum holiday coincidir data com o controle de ferias,
            # criar um relacionamento entre eles
            #
            for holiday_id in holidays_ids:
                for controle_id in contrato.vacation_control_ids:
                    if not controle_id.hr_holiday_add_id:
                        if controle_id.inicio_aquisitivo == holiday_id.inicio_aquisitivo and controle_id.fim_aquisitivo == holiday_id.fim_aquisitivo:
                            controle_id.hr_holiday_add_id = holiday_id

            # Para controle de férias que são novos, não ira encontrar nenhum
            # holiday do tipo ADD.
            # Entao se ficar vazio mesmo depois de toda a rotina, gerar holiday
            for controle_id in contrato.vacation_control_ids:
                if not controle_id.hr_holiday_add_id:
                    controle_id.hr_holiday_add_id = controle_id.gerar_holidays_ferias()

            #
            # Atualizar último periodo aquisitivo caso a data de demissão
            # esteja definida
            #
            if self.date_end:
                self.atualizar_data_demissao()

            # self.atualizar_linhas_controle_ferias(self.date_start)

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
    def cron_atualizar_controle_ferias(self):
        """
        Função disparada  pelo cron que dispara diarimente.
        Atualiza o controle de férias, verificando por periodos
        aquisitivos que se encerraram ontem, para criar novas linhas de
        controle de ferias.
        """

        # Dominio para selecionar apenas contratos ativos
        #
        domain = [
            '|',
            ('date_end', '>', fields.Date.today()),
            ('date_end', '=', False),
        ]

        # chamar a funcao passando a data corrente
        #
        contratos_ids = self.env['hr.contract'].search(domain)
        hoje = fields.Date.today()
        contratos_ids.action_button_update_controle_ferias(
            data_referencia=hoje)
