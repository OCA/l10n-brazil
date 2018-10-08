# -*- coding: utf-8 -*-
# Copyright 2018 ABGF - Hendrix Costa <hendrix.costa@abgf.giv.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from openerp import api
from openerp.addons.report_py3o.py3o_parser import py3o_report_extender


class LinhaDarf(object):
    def __init__(self):
        self.nome = ''
        self.valor = ''


def format_money_mask(value):
    """
    Function to transform float values to pt_BR currency mask
    :param value: float value
    :return: value with brazilian money format
    """
    import locale
    locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
    value_formated = locale.currency(value, grouping=True)

    return value_formated[3:]

@api.model
@py3o_report_extender(
    'l10n_br_hr_arquivos_governo.report_py3o_darf_analitico')
def darf_analitico(pool, cr, uid, localcontext, context):

    self = localcontext['objects']

    empresas, darfs, contribuicao_sindical, pss, darf_analitico = \
        self.gerar_guias_pagamento()

    company_logo = self.env.user.company_id.logo
    company_nfe_logo = self.env.user.company_id.nfe_logo

    localcontext['company_logo'] = \
        company_nfe_logo if company_nfe_logo else company_logo
    localcontext['company_logo2'] = \
        company_nfe_logo if company_nfe_logo else company_logo

    #
    # # Variaveis de Informações
    # data_atual = datetime.now()
    # dia_atual = \
    #     str(data_atual.day) + "/" + str(data_atual.month) + "/" + \
    #     str(data_atual.year)
    #
    # # Buscar ligacoes dentro do lote
    # domain = [
    #     ('id', 'in', self.slip_ids._ids),
    #     ('ligacoes_ids', '!=', False),
    # ]
    #
    # holerites_ids = self.slip_ids.search(domain)

    totalizador_darf_funcionarios = []
    totalizador_darf_dirigentes = []
    total_darf_funcionarios = 0
    total_darf_dirigentes = 0

    for linha in darf_analitico:
        darf_line = LinhaDarf()
        darf_line.nome = linha.get('nome')
        darf_line.valor = format_money_mask(linha.get('valor'))

        if linha.get('codigo_darf') == '0588':
            totalizador_darf_dirigentes.append(darf_line)
            total_darf_dirigentes += linha.get('valor')
        else:
            totalizador_darf_funcionarios.append(darf_line)
            total_darf_funcionarios += linha.get('valor')

    data = {
        'totalizador_darf_dirigentes': totalizador_darf_dirigentes,
        'totalizador_darf_funcionarios': totalizador_darf_funcionarios,
        'total_darf_dirigentes': format_money_mask(total_darf_dirigentes),
        'total_darf_funcionarios': format_money_mask(total_darf_funcionarios),
        # 'name': self.company_id.name,
        # 'legal_name': self.company_id.legal_name,
        # 'company_logo': company_logo,
        # 'mes_do_ano':
        #     dict(self._fields['mes_do_ano'].selection).get(self.mes_do_ano),
        # 'ano': self.ano,
        # 'data_atual': dia_atual,
        # 'ligacoes': totalizador_ligacoes,
    }
    localcontext.update(data)



