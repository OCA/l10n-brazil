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
        <th class="tg-0pky">code</th>
        <th class="tg-0pky">name</th>
        <th class="tg-0pky">parent</th>
        <th class="tg-0pky">type (visão/comum)</th>
        <th class="tg-0pky">natureza (devedora/credora)</th>
        <th class="tg-0pky">user_type (ativo/passivo/receita/despesa)</th>
    </tr>
    <tr>
        <td class="tg-phtq">1</td>
        <td class="tg-phtq">Ativo</td>
        <td class="tg-phtq">0</td>
        <td class="tg-phtq">visão</td>
        <td class="tg-phtq">devedora</th>
        <td class="tg-phtq">ativo</th>
    </tr>
    <tr>
        <td class="tg-0pky">1.1</td>
        <td class="tg-0pky">Ativo Circulante</td>
        <td class="tg-0pky">1</td>
        <td class="tg-0pky">visão</td>
        <td class="tg-0pky">devedora</th>
        <td class="tg-0pky">ativo</th>
    </tr>
    <tr>
        <td class="tg-phtq">1.1.01</td>
        <td class="tg-phtq">Disponibilidades</td>
        <td class="tg-phtq">1.1</td>
        <td class="tg-phtq">visão</td>
        <td class="tg-phtq">devedora</th>
        <td class="tg-phtq">ativo</th>
    </tr>
    <tr>
        <td class="tg-0pky">1.1.01.0001</td>
        <td class="tg-0pky">Caixa</td>
        <td class="tg-0pky">1.1.01</td>
        <td class="tg-0pky">comum</td>
        <td class="tg-0pky">devedora</th>
        <td class="tg-0pky">ativo</th>
    </tr>
</table>
<br />
<br />PS1.: Tipo de Conta pode ser Ativo/Passivo/Patrimônio Líquido/Receita/Despesa/Apuração do Resultado
<br />PS2.: A planilha não pode conter quebras manuais (\\n) e nem aspas (")
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

                # HEADER da planilha Validar HEADER
                cabecalho = linhas[0]
                # if cabecalho.split(',')[0] in ['code', 'name']:
                #     qtd_max_colunas = len(cabecalho.split(','))
                # else:
                #     raise Warning(
                #         'Primeira linha deverá ser header com code, name, parent')

                # Pular primeira por ser cabeçalho
                for linha in linhas[1:]:

                    l = linha.replace('\n', '').split(',')

                    # As linhas só serão processadas
                    if qtd_max_colunas and len(l) != qtd_max_colunas:
                        for linha_texto in l[2:]:
                            l[1] += ' ' + linha_texto.replace('"', '')

                    # Validar Coluna 0 - code
                    #
                    code = l[0]
                    code = \
                        code.replace('#', '').replace('@', '').replace('!', '')
                    if not code:
                        raise Warning(
                            'ERRO Linha deverá conter code {}'.format(l))

                    # Validar Coluna 1 - name
                    #
                    name = l[1]
                    if not name:
                        erro += ' Erro linha: {} \n'.format(l)
                        continue

                    # Validar Coluna 2 - parent
                    #
                    try:
                        parent_code = l[2]
                    except IndexError:
                        raise ValueError(
                            'PAI inexistente ou nao preenchido. '
                            'Conta: {} - {} '.format(code, name))

                    # Validar Coluna 3 - tipo_interno - type
                    #
                    tipo_interno = l[3].lower()

                    if tipo_interno in ['visão', 'visao', 'view']:
                        tipo_interno = 'view'

                    elif tipo_interno in ['other', 'comum']:
                        tipo_interno = 'other'

                    else:
                        raise Warning('Tipo Interno não localizado: {} \n'
                                      'Linha: {} '
                                      .format(tipo_interno, linha))

                    # Validar Coluna 4 - natureza
                    natureza = l[4].lower().strip()
                    if natureza not in ['credora', 'devedora', 'd/c']:
                        raise Warning(
                            'Natureza da Conta deverá ser credora ou devedora')
                    if natureza == 'devedora':
                        natureza_id = self.env.ref(
                            'l10n_br_contabilidade.'
                            'l10n_br_account_natureza_devedora')
                    elif natureza == 'credora':
                        natureza_id = \
                            self.env.ref('l10n_br_contabilidade.'
                                         'l10n_br_account_natureza_credora')
                    elif natureza == 'd/c':
                        natureza_id = \
                            self.env.ref('l10n_br_contabilidade.'
                                         'l10n_br_account_natureza_credora')
                    else:
                        raise Warning('Natureza de Conta não localizada: {} \n'
                                      'Linha: {} '
                                      .format(tipo_conta, linha))

                    # Validar Coluna 5 - tipo_conta - user_type
                    tipo_conta = l[5].lower()
                    if tipo_conta in ['ativo', 'passivo', 'despesa', 'receita', 'resultado']:
                        if tipo_conta == 'ativo':
                            tipo_conta = \
                                self.env.ref('account.data_account_type_asset')
                        elif tipo_conta == 'passivo':
                            tipo_conta = \
                                self.env.ref('l10n_br.passivo')
                        elif tipo_conta == 'receita':
                            tipo_conta = \
                                self.env.ref('account.data_account_type_income')
                        elif tipo_conta == 'despesa':
                            tipo_conta = \
                                self.env.ref('account.data_account_type_expense')
                        elif natureza == 'resultado':
                            pass
                        else:
                            raise Warning('Tipo de COnta não localizado: {} \n'
                                          'Linha: {} '
                                          .format(tipo_conta, linha))

                    xml_id = 'account_account_{}_{}'.format(
                        record.account_depara_plano_id.name.upper(),
                        code.replace('.', ''))

                    parent_ids[code] = {'xml_id': xml_id, 'id': False}

                    if not parent_ids.get(parent_code):
                        raise Warning(
                            'Conta pai não localizada '
                            'para a conta {} - {}'.format(code, name))

                    vals = {
                        'code': code,
                        'name': name,
                        'parent_id': parent_ids[parent_code]['id'],
                        'user_type': tipo_conta.id,
                        'account_depara_plano_id':
                            record.account_depara_plano_id.id,
                        'type': tipo_interno,
                        'natureza_conta_id':
                            natureza_id.id if natureza_id else False,
                    }

                    account_account_id = \
                        self.env['account.account'].create(vals)

                    parent_ids[code]['id'] = account_account_id.id

                    _logger.info('Conta Criada: {} - {}'.format(code, name))

            _logger.info(erro)

    @api.multi
    def analise_account_account(self):
        """
        Validação de um plano de contas externo
        """
        for record in self:
            if record.plano_de_contas_file:
                plano_de_contas_decoded = \
                    record.plano_de_contas_file.decode('base64')
                fileobj = TemporaryFile('wb+')
                fileobj.write(plano_de_contas_decoded)
                fileobj.seek(0)
                df = pd.read_csv(fileobj)
                erro = ''

                # Validar
                # l[2] - parent
                df['result_parent'] = df['parent'].apply(
                    lambda x: x in df['code'].values)

                df_erro_parent = df[(df.result_parent != True)]
                if not df_erro_parent.empty:
                    df_erro_parent['erro'] = \
                        df_erro_parent['code'].apply(str) + ' - ' + df_erro_parent['name']

                    erro += '\n'.join(map(
                        lambda x:
                        'Conta sem pai: {}'.format(x), df_erro_parent['erro'].values))

                # Validar
                # l[3] - type []
                valid_types = ['visão', 'visao', 'view', 'other', 'comum']
                df['result_type'] = df['type'].apply(
                    lambda x: x.lower() in valid_types)

                df_erro_type = df[(df.result_type != True)]
                if not df_erro_type.empty:
                    df_erro_type['erro'] = \
                        df_erro_type['type'].apply(str) + ' - ' + \
                        df_erro_type['code'].apply(str) + ' ' + df_erro_type['name']

                    erro += '\n'.join(map(
                        lambda x:
                        'Tipo inválido: {}'.format(x), df_erro_type['erro'].values))

                # Validar
                # l[4] - Natureza []
                valid_types = ['credora', 'devedora', 'd', 'c', 'd/c']
                df['result_natureza'] = df['natureza'].apply(
                    lambda x: x.lower().replace('\n', '').strip() in valid_types)

                df_erro_natureza = df[(df.result_natureza != True)]
                if not df_erro_natureza.empty:
                    df_erro_natureza['erro'] = \
                        df_erro_natureza['natureza'].apply(str) + ' - ' + \
                        df_erro_natureza['code'].apply(str) + ' ' + \
                        df_erro_natureza['name']

                    erro += '\n'.join(map(
                        lambda x:
                        'Natureza inválida: {} '.format(x), df_erro_natureza['erro'].values))


                # Validar
                # l[5] - User_type []
                valid_types = ['ativo', 'passivo', 'receita', 'depesa', 'resultado']
                df['result_default_type'] = df['user_type'].apply(
                    lambda x: x.lower().replace('\n', '').strip() in valid_types)

                df_erro_user_type = df[(df.result_natureza != True)]
                if not df_erro_user_type.empty:
                    df_erro_user_type['erro'] = \
                        df_erro_user_type['user_type'].apply(str) + ' - ' + \
                        df_erro_user_type['code'].apply(str) + ' ' + \
                        df_erro_user_type['name']

                    erro += '\n'.join(map(
                        lambda x:
                        'Tipo de Conta inválida: {} '.format(x), df_erro_user_type['erro'].values))


                if not erro:
                    'PARABENS! Tudo parece válido'
                raise Warning(erro)