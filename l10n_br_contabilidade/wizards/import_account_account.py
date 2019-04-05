# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)

from openerp import api, fields, models


class WizardImportAccountAccount(models.TransientModel):
    _name = 'wizard.import.account.account'

    referencia_plano_id = fields.Many2one(
        string='Nome do Plano de Contas Externo',
        comodel_name='account.mapeamento.referencia',
        required=True,
    )

    plano_de_contas_file = fields.Binary(
        string='Arquivo Telefonia (PABX)',
        filters='*.csv',
        require=True,
        copy=False,
    )


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
                parent_ids = {}

                arq = base64.b64decode(record.plano_de_contas_file)
                linhas = arq.splitlines(True)

                for linha in linhas:

                    l = linha.split(',')

                    # HEADER da planilha
                    if l[0] == 'id':
                        qtd_max_colunas = len(l)
                        continue

                    if qtd_max_colunas and len(l) != qtd_max_colunas:
                        continue

                    try:
                        xml_id = l[0]
                        name = l[1]
                        code = l[2]
                    except IndexError:  # empty node
                        pass

                    code = code.replace('.', '')

                    if not xml_id:
                        xml_id = 'account_account_{}_{}'.format(
                            record.referencia_plano_id.name.upper(), code)

                    parent_ids[code] = xml_id

                    parent_id = parent_ids.get(code[:-1], False)
                    if parent_id:
                        parent_id = self.env.ref('account.{}'.format(parent_id)).id

                    vals = {
                        'code': code,
                        'name': name,
                        'parent_id': parent_id,
                        'user_type': self.env.ref(l[32]).id,
                        # 'referencia_plano_id': record.referencia_plano_id.id,
                    }

                    account_account_id = self.env['account.account'].create(vals)

                    self.env['ir.model.data'].create({
                        'module': 'account',
                        'name': xml_id,
                        'model': 'account.account',
                        'res_id': account_account_id.id,
                    })