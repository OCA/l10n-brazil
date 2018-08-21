# -*- coding: utf-8 -*-
# Copyright 2018 ABGF - Hendrix Costa <hendrix.costa@abgf.giv.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from openerp import api
from openerp.addons.report_py3o.py3o_parser import py3o_report_extender


class Ligacao(object):
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
    'l10n_br_hr_payroll_report.report_telefonia_py3o_report')
def payslip_rescisao(pool, cr, uid, localcontext, context):
    self = localcontext['objects']
    company_logo = self.env.user.company_id.logo

    # Variaveis de Informações
    data_atual = datetime.now()
    dia_atual = \
        str(data_atual.day) + "/" + str(data_atual.month) + "/" + \
        str(data_atual.year)

    # Buscar ligacoes dentro do lote
    domain = [
        ('id', 'in', self.slip_ids._ids),
        ('ligacoes_ids', '!=', False),
    ]

    holerites_ids = self.slip_ids.search(domain)

    totalizador_ligacoes = []

    for holerite_id in holerites_ids:
        ligacao = Ligacao()
        ligacao.nome = holerite_id.contract_id.employee_id.name
        ligacao.valor = format_money_mask(
            sum(holerite_id.ligacoes_ids.mapped('valor')))
        totalizador_ligacoes.append(ligacao)

    data = {
        'cnpj_cpf': self.company_id.cnpj_cpf,
        'name': self.company_id.name,
        'legal_name': self.company_id.legal_name,
        'company_logo': company_logo,
        'mes_do_ano':
            dict(self._fields['mes_do_ano'].selection).get(self.mes_do_ano),
        'ano': self.ano,
        'data_atual': dia_atual,
        'ligacoes': totalizador_ligacoes,
    }
    localcontext.update(data)
