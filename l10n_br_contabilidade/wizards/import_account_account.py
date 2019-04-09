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

                # Definir a conta 0 - PAi de todas
                vals = {
                    'code': '0',
                    'name': record.account_depara_plano_id.name.upper(),
                    'parent_id': False,
                    'account_depara_plano_id': record.account_depara_plano_id.id,
                    'user_type':
                        self.env.ref('account.data_account_type_asset').id,
                }

                account_account_id = self.env['account.account'].create(vals)

                xml_id_root = 'account_account_{}_{}'.format(
                    record.account_depara_plano_id.name.upper(), '0')

                self.env['ir.model.data'].create({
                    'module': 'account',
                    'name': xml_id_root,
                    'model': 'account.account',
                    'res_id': account_account_id.id,
                })

                parent_ids = {0: xml_id_root}

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

                # Pular primeira por ser cabeçalho
                for linha in linhas[1:]:

                    l = linha.split(',')

                    # As linnhas só serão processadas
                    if qtd_max_colunas and len(l) != qtd_max_colunas:
                        erro += ' Erro linha: {} \n'.format(l)
                        continue

                    name = l[1]
                    code = l[0]

                    if not name or not code:
                        erro += ' Erro linha: {} \n'.format(l)
                        continue

                    code = code.replace('.', '')

                    xml_id = 'account_account_{}_{}'.format(
                        record.account_depara_plano_id.name.upper(), code)

                    parent_ids[code] = xml_id
                    parent_id = parent_ids.get(code[:-1], xml_id_root)

                    try:
                        if parent_id:
                            parent_id = self.env.ref(
                                'account.{}'.format(parent_id)).id
                    except ValueError:
                        pass

                    vals = {
                        'code': code,
                        'name': name,
                        'parent_id': parent_id,
                        'user_type':
                            self.env.ref('account.data_account_type_asset').id,
                        'account_depara_plano_id': record.account_depara_plano_id.id,
                    }

                    account_account_id = \
                        self.env['account.account'].create(vals)

                    self.env['ir.model.data'].create({
                        'module': 'account',
                        'name': xml_id,
                        'model': 'account.account',
                        'res_id': account_account_id.id,
                    })
                    _logger.info('ZCOnta Criada: {} '.format(name))

            _logger.info(erro)
