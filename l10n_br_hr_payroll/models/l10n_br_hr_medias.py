# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models, exceptions, _
from datetime import datetime

MES_DO_ANO = [
    (1, u'Jan'),
    (2, u'Fev'),
    (3, u'Mar'),
    (4, u'Abr'),
    (5, u'Mai'),
    (6, u'Jun'),
    (7, u'Jul'),
    (8, u'Ago'),
    (9, u'Set'),
    (10, u'Out'),
    (11, u'Nov'),
    (12, u'Dez'),
]


class L10nBrHrMedias(models.Model):
    _name = 'l10n_br.hr.medias'
    _description = 'Brazilian HR - Medias dos Proventos'
    # _order = 'year desc'

    contrato_id = fields.Many2one(
        string=u'Contrato',
        comodel_name='hr.contract',
    )

    data_inicio = fields.Date(
        string="Data Inicio",
    )

    data_fim = fields.Date(
        string="Data Fim",
    )

    lines_id = fields.One2many(
        comodel_name='l10n_br.hr.medias.lines',
        inverse_name='parent_id',
        string='Linhas de médias',
    )

    @api.multi
    def gerar_media_dos_proventos(self):
        """
        Recuperar os proventos do periodo e retornar média
        :param date_from:
        :param date_to:
        :param contract_id:
        :return:
        """
        for linha in self.lines_id:
            linha.unlink()

        folha_obj = self.env['hr.payslip']
        domain = [
            ('date_from', '>=', self.data_inicio),
            ('date_to', '<=', self.data_fim),
            ('contract_id', '=', self.contrato_id.id),
        ]
        folhas_periodo = folha_obj.search(domain)
        medias = {}
        for folha in folhas_periodo:
            for linha in folha.line_ids:
                if linha.salary_rule_id.category_id.code == "PROVENTO":
                    if not medias.get(linha.salary_rule_id.id):
                        medias.update({linha.salary_rule_id.id:
                            [{
                                'mes': MES_DO_ANO[folha.mes_do_ano],
                                'valor': linha.total,
                            }]
                        })
                    else:
                        medias[linha.salary_rule_id.id].append({
                            'mes': MES_DO_ANO[folha.mes_do_ano],
                            'valor': linha.total,
                        })

        linha_obj = self.env['l10n_br.hr.medias.lines']
        for rubrica in medias:
            mes_cont = 1
            vals = {}

            nome_rubrica = self.env['hr.salary.rule'].\
                browse(rubrica).display_name

            vals.update({'nome_rubrica' : nome_rubrica})
            vals.update({'parent_id' : self.id})
            vals.update({'meses' : len(medias[rubrica])})

            for mes in medias[rubrica]:
                vals.update({
                    'mes_' + str(mes_cont) : str(mes['valor']),
                })
                mes_cont += 1
            linha_obj.create(vals)
