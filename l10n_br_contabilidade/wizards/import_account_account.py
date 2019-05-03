# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)

from openerp import api, fields, models
from openerp.exceptions import Warning


class WizardImportAccountAccount(models.TransientModel):
    _name = 'wizard.import.account.account'

    account_depara_plano_id = fields.Many2one(
        string='Nome do Plano de Contas Externo',
        comodel_name='account.depara.plano',
        required=True,
    )

    plano_de_contas_file = fields.Binary(
        string='Plano de Contas Externo (.CSV)',
        filters='*.csv',
        require=True,
        copy=False,
    )

    instrucao = fields.Html(
        string='Instrução de Importação',
        compute='compute_instrucao',
    )

    config_nivel_ids = fields.One2many(
        string='Configuração dos níveis',
        comodel_name='wizard.import.account.nivel',
        inverse_name='wizard_import_account_account_id',
    )

    @api.multi
    def compute_instrucao(self):
        for record in self:
            record.instrucao = \
                "<h2>A primeira Linha do CSV deverá ser a header indicando " \
                "os campos: code,name </h2>"

    @api.multi
    def import_account_account(self):
        """

        :param data:
        :return:
        """

        for record in self:
            if record.plano_de_contas_file:

                # import csv
                import base64
                qtd_max_colunas = 0
                erro = ''

                conta_raiz_id = \
                    record.account_depara_plano_id.account_account_id.id

                xml_id_root = record.env['ir.model.data'].search(
                    [
                        ('model', '=', 'account.account'),
                        ('res_id', '=', conta_raiz_id)
                    ]
                )

                if not xml_id_root:
                    xml_id_root = 'account_account_{}_{}'.format(
                        record.account_depara_plano_id.name.upper(), '0')

                    self.env['ir.model.data'].create({
                        'module': 'account',
                        'name': xml_id_root,
                        'model': 'account.account',
                        'res_id': conta_raiz_id,
                    })

                parent_ids = {
                    0: {
                        'xml_id': xml_id_root,
                        'id': conta_raiz_id
                    }
                }

                arq = base64.b64decode(record.plano_de_contas_file)
                linhas = arq.splitlines(True)

                # HEADER da planilha
                cabecalho = linhas[0]
                if cabecalho.split(',')[0] in ['id', 'code', 'name']:
                    qtd_max_colunas = len(cabecalho.split(','))

                else:
                    raise Warning(
                        'Primeira linha deverá ser header com id,nome ou'
                        ' code e em seguida informar as colunas')

                dicionario_niveis = record._get_dicionario_niveis_conta_pai()

                # Pular primeira por ser cabeçalho
                for linha in linhas[1:]:

                    l = linha.split(',')

                    # As linnhas só serão processadas
                    if qtd_max_colunas and len(l) != qtd_max_colunas:
                        for linha_texto in l[2:]:
                            l[1] += ' ' + linha_texto.replace('"', '')

                    name = l[1]
                    code = l[0]

                    code = code.replace('#', '').replace('@', '').replace('!', '')

                    if not name or not code:
                        erro += ' Erro linha: {} \n'.format(l)
                        continue

                    code = code.replace('.', '')

                    xml_id = 'account_account_{}_{}'.format(
                        record.account_depara_plano_id.name.upper(), code)

                    parent_ids[code] = {'xml_id': xml_id, 'id': False}
                    parent_code = self._get_parent_code(code, dicionario_niveis)

                    if not parent_ids.get(parent_code):
                        raise Warning(
                            'Conta pai não localizada '
                            'para a conta {} - {}'.format(code, name)
                        )

                    vals = {
                        'code': code,
                        'name': name,
                        'parent_id': parent_ids[parent_code]['id'],
                        'user_type':
                            self.env.ref('account.data_account_type_view').id,
                        'account_depara_plano_id':
                            record.account_depara_plano_id.id,
                    }

                    account_account_id = \
                        self.env['account.account'].create(vals)

                    parent_ids[code]['id'] = account_account_id.id

                    self.env['ir.model.data'].create({
                        'module': 'account',
                        'name': xml_id,
                        'model': 'account.account',
                        'res_id': account_account_id.id,
                    })
                    _logger.info('COnta Criada: {} - {}'.format(code, name))

            _logger.info(erro)

    def _get_dicionario_niveis_conta_pai(self):
        niveis = {}
        valor_inicial = 0
        somatorio_niveis = 1
        for line in self.config_nivel_ids:
            if line.nivel == 1:
                niveis[somatorio_niveis] = 0
            else:
                niveis[somatorio_niveis] = somatorio_niveis - valor_inicial
            valor_inicial = line.algarismos
            somatorio_niveis += line.algarismos

        return niveis

    def _get_parent_code(self, code, dicionario_niveis):
        code_result = False
        if code in ['1', '2', '3', '4', '5']:
            code_result = 0
            return code_result

        code_result = code[:dicionario_niveis[len(code)]]

        return code_result


class WizardImportAccountNivel(models.TransientModel):
    _name = 'wizard.import.account.nivel'

    nivel = fields.Selection(
        string=u'Nível',
        selection=[
            (1, '1'),
            (2, '2'),
            (3, '3'),
            (4, '4'),
            (5, '5'),
            (6, '6'),
            (7, '7'),
            (8, '8'),
            (9, '9'),
            (10, '10'),
            (11, '11'),
            (12, '12'),
        ],
    )

    algarismos = fields.Integer(
        string=u'Quantidade de Algarismos',
    )

    wizard_import_account_account_id = fields.Many2one(
        comodel_name='wizard.import.account.account',
    )
