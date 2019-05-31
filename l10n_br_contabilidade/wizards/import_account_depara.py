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
        """

        if not self.depara_file:
            raise Warning("Inserir arquivo para importação")

        # import csv
        import base64
        erro_csv = ''
        erro_conta_oficial = ''
        erro_conta_externa = ''

        arq = base64.b64decode(self.depara_file)
        linhas = arq.splitlines(True)

        # Pular primeira por ser cabeçalho
        for linha in linhas[1:]:

            l = linha.split(',')

            code_oficial = l[0]
            name = l[1]
            code_externo = l[2].replace('\n', '')

            if not code_oficial  or (not code_externo or code_externo == '\n'):
                erro_csv += ' Erro importação linha: {} \n'.format(l)
                continue

            # code_oficial = code_oficial.replace('.', '_')
            # xmlid_conta_oficial = \
            #     'account.account_account_id_{}'.format(code_oficial)

            conta_oficial_id = self.env['account.account'].search([
                ('custom_code', '=', code_oficial),
            ], limit=1)

            if not conta_oficial_id:
                erro_conta_oficial += ("Conta: {} {}\n ".
                                       format(code_oficial, name))
                continue

            code_externo = code_externo.replace('.', '')
            xmlid_conta_externa = \
                'account.account_account_{}_{}'.format(
                    self.account_depara_plano_id.name.upper(),
                    code_externo
                )

            try:
                conta_externa_id = self.env.ref(xmlid_conta_externa)

            except ValueError as e:
                erro_conta_externa += ("Conta: {}\n ".format(e.message))
                continue

            # Se ja existir o mapemaneto, incrementar com conta oficial
            account_depara_id = self.env['account.depara'].search([
                ('conta_referencia_id', '=', conta_externa_id.id),
            ])
            if account_depara_id:
                account_depara_id.conta_sistema_id = [(4, conta_oficial_id.id)]

            # Se ainda nao existir, criar o mapeamento
            else:
                try:
                    vals = {
                        'conta_referencia_id': conta_externa_id.id,
                        'conta_sistema_id': [(4, conta_oficial_id.id)],
                        'account_depara_plano_id':
                            self.account_depara_plano_id.id,
                    }

                    self.env['account.depara'].create(vals)
                    _logger.info('Mapeamento Criado: {} '.format(name))

                except ValueError as e:
                    pass

        if erro_conta_externa or erro_conta_oficial or erro_csv:

            mensagem = 'Identificado inconsistências.\nPor favor efetue as ' \
                       'correções e tente novamente a importação.'

            if erro_conta_oficial:
                mensagem += '\n\n Contas Oficiais inválidas:\n {}'.\
                    format(erro_conta_oficial)

            if erro_conta_externa:
                mensagem += '\n\n Contas Externas inválidas:\n {}'.\
                    format(erro_conta_externa)

            if erro_csv:
                mensagem += '\n\n Erro de importação:\n {}'.\
                    format(erro_csv)

            raise Warning(mensagem)
