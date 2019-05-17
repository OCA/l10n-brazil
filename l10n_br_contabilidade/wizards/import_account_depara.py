# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)

from openerp import api, fields, models
from openerp.exceptions import Warning


class WizardImportAccountDepara(models.TransientModel):
    _name = 'wizard.import.account.depara'

    account_depara_plano_id = fields.Many2one(
        string='Plano de Contas do Mapeamento (Externo)',
        comodel_name='account.depara.plano',
        required=True,
    )

    depara_file = fields.Binary(
        string='Mapeamento DEPARA(.CSV)',
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
                "<h2>Primeira linha deverá ser cabeçalho código, " \
                "nome da conta, código conta externa\n" \
                "Primeira Coluna: Código Conta Oficial\n" \
                "Segunda Coluna: Nome da Conta Oficial\n" \
                "Terceira Coluna: Código Conta Externa\n </h2>"

    @api.multi
    def import_account_depara(self):
        """

        :param data:
        :return:
        """

        for record in self:
            if record.depara_file:

                # import csv
                import base64
                qtd_max_colunas = 0
                erro_csv = ''
                erro_conta = ''

                arq = base64.b64decode(record.depara_file)
                linhas = arq.splitlines(True)

                # Pular primeira por ser cabeçalho
                for linha in linhas[1:]:

                    l = linha.split(',')

                    # As linnhas só serão processadas
                    code_oficial = l[0]
                    name = l[1]
                    code_externo = l[2].replace('\n', '')

                    if (not code_oficial or not name) or \
                            (not code_externo or code_externo == '\n'):
                        erro_csv += ' Erro importação linha: {} \n'.format(l)
                        continue

                    code_oficial = code_oficial.replace('.', '')
                    xmlid_conta_oficial = \
                        'account.account_account_{}_{}'.format(
                            record.account_depara_plano_id.name.upper(),
                            code_oficial
                        )

                    code_externo = code_externo.replace('.', '')
                    xmlid_conta_externa = \
                        'account.account_account_{}_{}'.format(
                            record.account_depara_plano_id.name.upper(),
                            code_externo
                        )

                    try:
                        vals = {
                            'account_depara_plano_id':
                                record.account_depara_plano_id.id,
                            'conta_referencia_id':
                                self.env.ref(xmlid_conta_externa).id,
                            'conta_sistema_id':
                                [(4, self.env.ref(xmlid_conta_oficial).id)],
                        }

                        account_depara_id = \
                            self.env['account.depara'].create(vals)
                        _logger.info('Mapeamento Criado: {} '.format(name))

                    except ValueError as e:
                        erro_conta += \
                            ("Conta nao encontrada: {}\n ".format(e.message))

            _logger.info(erro_csv)
            _logger.info(erro_conta)

            if erro_conta or erro_csv:
                raise Warning("Identificado inconsistências. Por favor efetue "
                              "as correções e tente novamente a importação.\n"
                              "\n\n Erros de Importações:\n {} \n "
                              "\n\n Erros de Contas: \n {} \n".format(
                    erro_csv, erro_conta))
