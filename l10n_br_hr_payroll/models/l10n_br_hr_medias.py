# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models

MES_DO_ANO = [
    (1, u'Janeiro'),
    (2, u'Fevereiro'),
    (3, u'Marco'),
    (4, u'Abril'),
    (5, u'Maio'),
    (6, u'Junho'),
    (7, u'Julho'),
    (8, u'Agosto'),
    (9, u'Setembro'),
    (10, u'Outubro'),
    (11, u'Novembro'),
    (12, u'Dezembro'),
]


class L10nBrHrMedias(models.Model):
    _name = 'l10n_br.hr.medias'
    _description = 'Brazilian HR - Medias dos Proventos'
    # _order = 'year desc'

    holerite_id = fields.Many2one(
        string=u'Holerite',
        comodel_name='hr.payslip',
    )
    rubrica_id = fields.Many2one(
        comodel_name="hr.salary.rule",
        string="Id da rubrica"
    )
    nome_rubrica = fields.Char(
        string=u'Nome da Rubrica',
    )
    mes_1 = fields.Char(
        string=u'1º Mes',
    )
    mes_2 = fields.Char(
        string=u'2º Mes',
    )
    mes_3 = fields.Char(
        string=u'3º Mes',
    )
    mes_4 = fields.Char(
        string=u'4º Mes',
    )
    mes_5 = fields.Char(
        string=u'5º Mes',
    )
    mes_6 = fields.Char(
        string=u'6º Mes',
    )
    mes_7 = fields.Char(
        string=u'7º Mes',
    )
    mes_8 = fields.Char(
        string=u'8º Mes',
    )
    mes_9 = fields.Char(
        string=u'9º Mes',
    )
    mes_10 = fields.Char(
        string=u'10º Mes',
    )
    mes_11 = fields.Char(
        string=u'11º Mes',
    )
    mes_12 = fields.Char(
        string=u'12º Mes',
    )
    soma = fields.Float(
        string=u'Total dos Meses',
        compute='calcular_soma'
    )
    meses = fields.Float(
        string=u'Meses do periodo',
    )
    media = fields.Float(
        string=u'Média',
        compute='calcular_media',
    )
    media_texto = fields.Char(
        string=u'Média'
    )
    linha_de_titulo = fields.Boolean(
        string=u'Linha do Titulo',
        help='Indica se é a linha construida para compor o título',
        default=False,
    )

    def calcular_soma(self):
        for linha in self:
            if not linha.linha_de_titulo:
                linha.soma = \
                    float(linha.mes_1) + float(linha.mes_2) + \
                    float(linha.mes_3) + float(linha.mes_4) + \
                    float(linha.mes_5) + float(linha.mes_6) + \
                    float(linha.mes_7) + float(linha.mes_8) + \
                    float(linha.mes_9) + float(linha.mes_10) + \
                    float(linha.mes_11) + float(linha.mes_12)

    def calcular_media(self):
        for linha in self:
            if not linha.linha_de_titulo:
                if linha.meses == 0:
                    linha.media = 123
                else:
                    linha.media = linha.soma/linha.meses

    @api.multi
    def gerar_media_dos_proventos(self, data_inicio, data_fim, holerite_id):
        """
        Recuperar os proventos do periodo e retornar média
        :param data_inicio:
        :param data_fim:
        :param holerite_id:
        :return:
        """
        for linha in holerite_id.medias_proventos:
            linha.unlink()

        folha_obj = self.env['hr.payslip']
        domain = [
            ('date_from', '>=', data_inicio),
            ('date_to', '<=', data_fim),
            ('contract_id', '=', holerite_id.contract_id.id),
            ('state', '=', 'done'),
        ]
        folhas_periodo = folha_obj.search(domain)
        folhas_periodo = folhas_periodo.sorted(key=lambda r: r.date_from)
        medias = {}
        for folha in folhas_periodo:
            for linha in folha.line_ids:
                if linha.salary_rule_id.category_id.code == "PROVENTO":
                    if not medias.get(linha.salary_rule_id.id):
                        medias.update({
                            linha.salary_rule_id.id:
                                [{
                                    'mes': MES_DO_ANO[folha.mes_do_ano-1][1],
                                    'valor': linha.total,
                                }]
                        })
                    else:
                        medias[linha.salary_rule_id.id].append({
                            'mes': MES_DO_ANO[folha.mes_do_ano-1][1],
                            'valor': linha.total,
                            'rubrica_id': linha.salary_rule_id.id,
                        })

        linha_obj = self.env['l10n_br.hr.medias']
        hr_medias_ids = []
        titulo = {}
        titulo_feito = False
        for rubrica in medias:
            mes_cont = 1
            vals = {}
            nome_rubrica = self.env['hr.salary.rule'].\
                browse(rubrica).display_name
            # definindo titulo da visao tree
            titulo.update({'meses': len(medias[rubrica])})
            titulo.update({'holerite_id': holerite_id.id})
            titulo.update({'linha_de_titulo': True})
            # definindo a linha
            vals.update({'nome_rubrica': nome_rubrica})
            vals.update({'meses': len(medias[rubrica])})
            vals.update({'holerite_id': holerite_id.id})
            vals.update({'rubrica_id': rubrica})

            for mes in medias[rubrica]:
                vals.update({
                    'mes_' + str(mes_cont): str(mes['valor']),
                })
                titulo.update({
                    'mes_' + str(mes_cont): str(mes['mes']),
                })
                mes_cont += 1

            if not titulo_feito:
                linha_obj.create(titulo)
                titulo_feito = True
            hr_medias_ids.append(linha_obj.create(vals))

        return hr_medias_ids
