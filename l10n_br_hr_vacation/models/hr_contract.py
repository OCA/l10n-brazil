# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from dateutil.relativedelta import relativedelta
from lxml import etree
from openerp.exceptions import Warning as UserError


class HrContract(models.Model):
    _inherit = 'hr.contract'

    vacation_control_ids = fields.One2many(
        comodel_name='hr.vacation.control',
        inverse_name='contract_id',
        string=u'Periodos Aquisitivos Alocados',
        ondelete="cascade",
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
        if vals.get('date_start') and \
                (vals.get('date_start') != self.date_start):
            self.verificar_controle_ferias()
            self.atualizar_linhas_controle_ferias(vals.get('date_start'))
        return super(HrContract, self).write(vals)

    @api.model
    def create(self, vals):
        hr_contract_id = super(HrContract, self).create(vals)
        if vals.get('date_start'):
            hr_contract_id.atualizar_linhas_controle_ferias(
                vals.get('date_start'))
        return hr_contract_id

    def verificar_controle_ferias(self):
        """
        Função que verifica se em algum controle de férias ja tem um pedido de
        Férias ja aprovado. Se nao existir nenhum, exclui todas as linhas de
        controle de férias e chama a função para criar novas
        :return:
        """
        vacation_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_vacation').id

        holidays_ferias_do_contrato = self.env['hr.holidays'].search([
            ('type', '=', 'remove'),
            ('contrato_id', '=', self.id),
            ('holiday_status_id', '=', vacation_id),
        ])
        if holidays_ferias_do_contrato:
            raise UserError(
                "Não é possível alterar a data de início de contratos "
                "que possuem ocorrências ou férias confirmadas.")

        for holiday in holidays_ferias_do_contrato:
            holiday.unlink()

        for linha in self.vacation_control_ids:
            linha.unlink()

    @api.multi
    def action_button_update_controle_ferias(self):
        """
        Ação disparada pelo botão na view, que atualiza as linhas de controle
        de férias desde que nao contenham férias atreladas a elas
        """
        self.verificar_controle_ferias()
        self.atualizar_linhas_controle_ferias(self.date_start)

    @api.multi
    def atualizar_linhas_controle_ferias(self, date_start):
        """
        Dada um data inicial, gerar as linhas de controle de férias
        :param date_start: string - 2017-05-01 Data de admissao do funcionario
        :return:
        """
        for linha in self.vacation_control_ids:
                linha.unlink()
        if not date_start:
            date_start = self.date_start
        inicio = fields.Date.from_string(date_start)
        hoje = fields.Date.from_string(fields.Date.today())
        lista_controle_ferias = []
        controle_ferias_obj = self.env['hr.vacation.control']

        while(inicio <= hoje):
            vals = controle_ferias_obj.calcular_datas_aquisitivo_concessivo(
                str(inicio)
            )
            controle_ferias = controle_ferias_obj.create(vals)
            inicio = inicio + relativedelta(years=1)
            lista_controle_ferias.append(controle_ferias.id)
        self.vacation_control_ids = lista_controle_ferias

        # gerar automaticamente as ferias (holidays) dos 2 ultimos controles
        ultimos_controles = self.vacation_control_ids[-2:]
        for controle_ferias in ultimos_controles:
            controle_ferias.gerar_holidays_ferias()
        return self

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
        """
        Função disparada  pelo cron que dispara diarimente.
        Atualiza o controle de férias, verificando por periodos
        aquisitivos que se encerraram ontem, para criar novas linhas de
        controle de ferias.
        """
        domain = [
            '|',
            ('date_end', '>', fields.Date.today()),
            ('date_end', '=', False),
        ]
        contratos_ids = self.env['hr.contract'].search(domain)

        for contrato in contratos_ids:
            if contrato.vacation_control_ids:
                ultimo_controles = contrato.vacation_control_ids[0]
                for ultimo_controle in ultimo_controles:
                    if ultimo_controle.fim_aquisitivo < fields.Date.today():
                        controle_ferias_obj = self.env['hr.vacation.control']
                        hoje = fields.Date.today()
                        vals = controle_ferias_obj.\
                            calcular_datas_aquisitivo_concessivo(hoje)
                        novo_controle_ferias = controle_ferias_obj.create(vals)
                        novo_controle_ferias.gerar_holidays_ferias()
                        novo_controle_ferias.contract_id = contrato

                programacao_ferias = self.env['ir.config_parameter'].get_param(
                    'l10n_br_hr_vacation_programacao_ferias_futuras',
                    default=False
                )

                if programacao_ferias:
                    dias = ultimo_controle.dias
                else:
                    dias = ultimo_controle.saldo

                for periodo_aquisitivo in ultimo_controle.hr_holiday_ids:
                    if periodo_aquisitivo.type == 'add':
                        periodo_aquisitivo.number_of_days_temp = dias
