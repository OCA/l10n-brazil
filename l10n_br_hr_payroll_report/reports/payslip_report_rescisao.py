# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.report_py3o.py3o_parser import py3o_report_extender

from openerp import api, _, exceptions
import logging

_logger = logging.getLogger(__name__)
try:
    from pybrasil import valor, data

except ImportError:
    _logger.info('Cannot import pybrasil')


class linha(object):
    def __init__(self, one, two, three):
        self.one = one
        self.two = two
        self.three = three


class item_obj(object):
    def __init__(self, line_ids):
        self.display_name = line_ids['display_name']
        self.valor_fmt = line_ids['valor_fmt']


def buscar_ultimo_salario(self):
    mes = self.mes_do_ano - 1
    ano = self.ano
    if mes == 0:
        mes = 12
        ano -= 1

    ultimo_holerite_id = self.env['hr.payslip'].search(
        [
            ('contract_id', '=', self.contract_id.id),
            ('mes_do_ano', '=', mes),
            ('ano', '=', ano),
            ('tipo_de_folha', '=', 'normal'),
        ]
    )
    for line in ultimo_holerite_id.line_ids:
        if line.code == "SALARIO":
            return line.total


@api.model
@py3o_report_extender(
    'l10n_br_hr_payroll_report.report_payslip_py3o_rescisao')
def payslip_rescisao(pool, cr, uid, localcontext, context):
    self = localcontext['objects']
    companylogo = self.env.user.company_id.logo
    data = {
        'companylogo': companylogo,
        'ultimo_salario':buscar_ultimo_salario(self),
        'provento_line': popula_valor(self, 'PROVENTO'),
        'deducao_line': popula_valor(self, ['DEDUCAO', 'INSS', 'IRPF']),
        'categoria_contrato': self[0].contract_id.category_id.name,
    }
    localcontext.update(data)


def popula_valor(self, tipo):

    # Popula as linhas para impressão
    coluna = 1
    linhas = []
    for registro in self.rescisao_ids:
        if registro.tipo in tipo:
            line = {}
            line['display_name'] = str(registro.codigo_fmt) + ' ' + registro.name
            line['valor_fmt'] = valor.formata_valor(registro.valor)
            if coluna == 1:
                objeto1 = item_obj(line)
                coluna = 2
            elif coluna == 2:
                objeto2 = item_obj(line)
                coluna = 3
            elif coluna == 3:
                objeto3 = item_obj(line)
                linha_obj = linha(objeto1, objeto2, objeto3)
                linhas.append(linha_obj)
                coluna = 1
    objeto_branco = item_obj({'display_name': '', 'valor_fmt': ''})
    if coluna == 3:
        linhas.append(linha(objeto1, objeto2, objeto_branco))
    elif coluna == 2:
        linhas.append(linha(objeto1, objeto_branco, objeto_branco))

    return linhas
