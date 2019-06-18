# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import pandas as pd

_logger = logging.getLogger(__name__)

from openerp import api, fields, models
from openerp.exceptions import Warning
from tempfile import TemporaryFile


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
        default=lambda self: self._get_default_instrucao(),
        readonly=True,
    )

    def _get_default_instrucao(self):
        return """
        
        <h3>Importação Do Depara</h3> 
        <br />
        
        <style type="text/css">
.tg  {border-collapse:collapse;border-spacing:0;border-color:#aabcfe;width: 50% !important;margin: auto;}
.tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:#aabcfe;color:#669;background-color:#e8edff;}
.tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:#aabcfe;color:#039;background-color:#b9c9fe;}
.tg .tg-phtq{background-color:#D2E4FC;border-color:inherit;text-align:left;vertical-align:top}
.tg .tg-baqh{text-align:center;vertical-align:top}
.tg .tg-c3ow{border-color:inherit;text-align:center;vertical-align:top}
.tg .tg-0pky{border-color:inherit;text-align:left;vertical-align:top}
.tg .tg-svo0{background-color:#D2E4FC;border-color:inherit;text-align:center;vertical-align:top}
.tg .tg-0lax{text-align:left;vertical-align:top}
</style>
<table class="tg" class="oe_center" >
    <tr>
        <th class="tg-0pky">code</th>
        <th class="tg-0pky">name</th>
        <th class="tg-0pky">code_externo</th>
    </tr>
    <tr>
        <td class="tg-phtq">1</td>
        <td class="tg-phtq">Ativo</td>
        <td class="tg-phtq">1</td>
    </tr>
    <tr>
        <td class="tg-0pky">1.1</td>
        <td class="tg-0pky">Ativo Circulante</td>
        <td class="tg-0pky">11</td>
    </tr>
    <tr>
        <td class="tg-phtq">1.1.1</td>
        <td class="tg-phtq">Disponibilidades</td>
        <td class="tg-phtq">111</td>
    </tr>
    <tr>
        <td class="tg-0pky">111101</td>
        <td class="tg-0pky">Caixa</td>
        <td class="tg-0pky">11111</td>
    </tr>
    <tr>
        <td class="tg-phtq">1111010002</td>
        <td class="tg-phtq">Caixa</td>
        <td class="tg-phtq">111110000001</td>
    </tr>
</table>
    <br />
    <br /><b>code:<b/> Código da conta Oficial 
    <br /><b>name:<b/> Nome da conta Oficial 
    <br /><b>code:<b/> Código da conta Externa 
"""

    def _get_all_account_ids(self, parent_id):
        if parent_id.mapped('child_parent_ids'):
            return \
                parent_id + \
                self._get_all_account_ids(parent_id.mapped('child_parent_ids'))
        else:
            return parent_id

    @api.multi
    def analisar_account_depara(self):
        """
        """
        contas = self._get_all_account_ids(
            self.account_depara_plano_id.account_account_id)

        # Pular primeira por ser cabeçalho
        if self.depara_file:

            # import csv
            import base64
            arq = base64.b64decode(self.depara_file)
            linhas = arq.splitlines(True)
            erro_csv = ''
            erro_conta_oficial = ''
            erro_conta_externa = ''

            for linha in linhas[1:]:

                l = linha.split(',')

                code_oficial = l[0]
                name = l[1]
                code_externo = l[2].replace('\n', '')

                if not code_oficial or (not code_externo or code_externo == '\n'):
                    erro_csv += ' Erro importação linha: {} \n'.format(l)

                conta_oficial_id = self.env['account.account'].search([
                    ('custom_code', '=', code_oficial),
                ], limit=1)
                if not conta_oficial_id:
                    erro_conta_oficial += code_oficial

                conta_externa = self.env['account.account'].search([
                    ('code', '=', code_externo),
                ], limit=1)
                if not conta_oficial_id:
                    erro_conta_externa += code_oficial

            contas_codigos = contas.mapped('code')

            plano_de_contas_decoded = self.depara_file.decode('base64')
            fileobj = TemporaryFile('wb+')
            fileobj.write(plano_de_contas_decoded)
            fileobj.seek(0)
            df = pd.read_csv(fileobj)

            # Validar se todas as contas estão no depara
            contas_externas = df['code_externo'].apply(lambda x: str(x)).values
            contas_fora_depara = \
                filter(lambda x: x not in contas_externas, contas_codigos)
            mensagem = map(lambda x: 'Conta sem registro no Depara:, {}'.
                           format(x), contas_fora_depara)
            erro_contas_sem_depara = '\n'.join(mensagem)

            erro = erro_csv + erro_conta_oficial + \
                   erro_conta_externa + erro_contas_sem_depara
            if not erro:
                erro += 'OK! Tudo parece válido'
            raise Warning(erro)

        else:

            erro_depara = ''
            contas = contas.filtered(lambda x: x.type=='other')
            for conta in contas:
                depara_id = self.env['account.depara'].search([
                    ('conta_referencia_id','=',conta.id),
                ])
                if not depara_id:
                    erro_depara += '\n {} - {}'.format(conta.code, conta.name)

            if not erro_depara:
                erro_depara += 'OK! Tudo parece válido'
            raise Warning(erro_depara)

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

            if not code_oficial or (not code_externo or code_externo == '\n'):
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
                mensagem += '\n\n Contas Oficiais inválidas:\n {}'. \
                    format(erro_conta_oficial)

            if erro_conta_externa:
                mensagem += '\n\n Contas Externas inválidas:\n {}'. \
                    format(erro_conta_externa)

            if erro_csv:
                mensagem += '\n\n Erro de importação:\n {}'. \
                    format(erro_csv)

            raise Warning(mensagem)
