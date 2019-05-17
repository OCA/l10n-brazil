# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

import pandas as pd

_logger = logging.getLogger(__name__)

from openerp import api, fields, models
from openerp.exceptions import Warning
from tempfile import TemporaryFile


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
        string='Instrução para Importação',
        default=lambda self: self._get_default_instrucao(),
        readonly=True,
    )

    def _get_default_instrucao(self):
        return """
        
        <h3>Para importação analisar o plano de contas (CSV) e preencher a configuração de níveis conforme exemplo:</h3> 
        <br />
        
        <style type="text/css">
.tg  {border-collapse:collapse;border-spacing:0;border-color:#aabcfe;}
.tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:#aabcfe;color:#669;background-color:#e8edff;}
.tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:#aabcfe;color:#039;background-color:#b9c9fe;}
.tg .tg-phtq{background-color:#D2E4FC;border-color:inherit;text-align:left;vertical-align:top}
.tg .tg-baqh{text-align:center;vertical-align:top}
.tg .tg-c3ow{border-color:inherit;text-align:center;vertical-align:top}
.tg .tg-0pky{border-color:inherit;text-align:left;vertical-align:top}
.tg .tg-svo0{background-color:#D2E4FC;border-color:inherit;text-align:center;vertical-align:top}
.tg .tg-0lax{text-align:left;vertical-align:top}
</style>
<table class="tg" class="oe_center">
  <tr>
    <th class="tg-0pky">Código</th>
    <th class="tg-0pky">Nome</th>
    <th class="tg-0pky">Código do Conta Pai</th>
  </tr>
  <tr>
    <td class="tg-phtq">1</td>
    <td class="tg-phtq">Ativo</td>
    <td class="tg-svo0">0</td>
  </tr>
  <tr>
    <td class="tg-0pky">1.1</td>
    <td class="tg-0pky">Ativo Circulante</td>
    <td class="tg-c3ow">1</td>
  </tr>
  <tr>
    <td class="tg-phtq">1.1.01</td>
    <td class="tg-phtq">Disponibilidades</td>
    <td class="tg-svo0">1.1</td>
  </tr>
  <tr>
    <td class="tg-0lax">1.1.01.0001</td>
    <td class="tg-0lax">Caixa</td>
    <td class="tg-baqh">1.1.01</td>
  </tr>
</table>
<br />
PS.: A planilha não pode conter quebras manuais (\\n) e nem aspas (")
 nas células pois a estrutura do CSV entenderá como uma coluna a mais.
        
        """

    @api.multi
    def import_account_account(self):
        """
        Rotina para importação de um plano de contas externa
        """
        for record in self:
            if record.plano_de_contas_file:

                qtd_max_colunas = 0
                erro = ''

                conta_raiz_id = \
                    record.account_depara_plano_id.account_account_id.id

                xml_id_root = record.env['ir.model.data'].search([
                    ('model', '=', 'account.account'),
                    ('res_id', '=', conta_raiz_id),
                ])

                parent_ids = {
                    '0': {'xml_id': xml_id_root, 'id': conta_raiz_id}
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

                # Pular primeira por ser cabeçalho
                for linha in linhas[1:]:

                    l = linha.split(',')

                    # As linhas só serão processadas
                    if qtd_max_colunas and len(l) != qtd_max_colunas:
                        for linha_texto in l[2:]:
                            l[1] += ' ' + linha_texto.replace('"', '')

                    code = l[0]
                    name = l[1]

                    try:
                        parent_code = l[2]
                    except IndexError:
                        raise ValueError(
                            'PAI inexistente ou nao preenchido. '
                            'Conta: {} - {} '.format(code, name)
                        )

                    code = \
                        code.replace('#', '').replace('@', '').replace('!', '')

                    if not name or not code:
                        erro += ' Erro linha: {} \n'.format(l)
                        continue

                    # code = code.replace('.', '')

                    xml_id = 'account_account_{}_{}'.format(
                        record.account_depara_plano_id.name.upper(),
                        code.replace('.', ''))

                    parent_ids[code] = {'xml_id': xml_id, 'id': False}
                    parent_code = l[2]

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
                        'type': 'view',
                    }

                    account_account_id = \
                        self.env['account.account'].create(vals)

                    parent_ids[code]['id'] = account_account_id.id

                    _logger.info('COnta Criada: {} - {}'.format(code, name))

            _logger.info(erro)

    @api.multi
    def analise_account_account(self):
        """
        Validação de um plano de contas externo
        """
        for record in self:
            if record.plano_de_contas_file:
                file = record.plano_de_contas_file.decode('base64')
                fileobj = TemporaryFile('wb+')
                fileobj.write(file)
                fileobj.seek(0)
                df = pd.read_csv(fileobj)

                df['result'] = df['Conta Superior'].apply(
                    lambda x: x in df['code'].values)

                df_erro = df[(df.result != True)]
                if not df_erro.empty:
                    df_erro['erro'] = \
                        df_erro['code'].apply(str) + ' - ' + df_erro['name']

                    erro = '\n'.join(map(
                        lambda x:
                        'Conta sem pai: {}'.format(x), df_erro['erro'].values))

                    raise Warning(erro)
