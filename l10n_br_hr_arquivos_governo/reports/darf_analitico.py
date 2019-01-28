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
        self.base = ''
        self.company_id = ''
        self.codigo_darf = ''


class Darf(object):
    def __init__(self):
        self.codigo = ''
        self.base = 0
        self.valor = 0
        self.linhas = []


class Empresa(object):
    def __init__(self):
        self.guias = []
        self.total = ''
        self.titulo = ''



def format_money_mask(value):
    """
    Function to transform float values to pt_BR currency mask
    :param value: float value
    :return: value with brazilian money format
    """
    import locale
    locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
    value_formated = locale.currency(value, grouping=True)

    return value_formated.replace('R$', '')

@api.model
@py3o_report_extender(
    'l10n_br_hr_arquivos_governo.report_py3o_darf_analitico')
def darf_analitico(pool, cr, uid, localcontext, context):

    self = localcontext['objects']

    # LOGO
    company_logo = self.env.user.company_id.logo
    company_nfe_logo = self.env.user.company_id.nfe_logo

    localcontext['company_logo'] = \
        company_nfe_logo if company_nfe_logo else company_logo
    localcontext['company_logo2'] = \
        company_nfe_logo if company_nfe_logo else company_logo

    # footer
    localcontext['footer'] = self.company_id.rml_footer

    # Variaveis de Informações
    data_atual = datetime.now()
    dia_atual = \
        str(data_atual.day) + "/" + str(data_atual.month) + "/" + \
        str(data_atual.year)

    empresas, darfs, contribuicao_sindical, pss, darf_analitico = \
        self.gerar_guias_pagamento()

    # Empresas que tem guias DARF
    company_ids = set(map(lambda x: x.get('company_id'), darf_analitico))

    result = []

    for company_id in company_ids:

        empresa = Empresa()

        res_company = self.env['res.company'].browse(company_id)
        empresa.titulo = res_company.name

        codigos_darf = set(map(lambda x: x.get('codigo_darf'), darf_analitico))

        for codigo_darf in codigos_darf:

            darf = Darf()

            darf.codigo = codigo_darf

            for linha in filter(
                    lambda x: x.get('company_id') == company_id and
                              x.get('codigo_darf') == codigo_darf,
                    darf_analitico):

                darf_line = LinhaDarf()
                darf_line.nome = linha.get('nome')
                darf_line.valor = format_money_mask(linha.get('valor'))
                darf_line.base = format_money_mask(linha.get('base'))
                darf_line.company_id = linha.get('company_id')
                darf_line.codigo_darf = linha.get('codigo_darf')

                darf.linhas.append(darf_line)
                darf.base += linha.get('base')
                darf.valor += linha.get('valor')

            if darf.valor :
                darf.base = format_money_mask(darf.base)
                darf.valor = format_money_mask(darf.valor)
                empresa.guias.append(darf)

        result.append(empresa)

    data = {
        'object': self,
        'result': result,
        'data_atual': dia_atual,
    }
    localcontext.update(data)
