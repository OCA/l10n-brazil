# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#   Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#
import logging

from odoo import api, models, fields, _
from odoo.exceptions import UserError, Warning

_logger = logging.getLogger(__name__)

try:
    from pysped.nfe import ProcessadorNFe
    from pysped.nfe.webservices_flags import *
    from pybrasil.inscricao import limpa_formatacao

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedInutilizacaoTipoDocumento(models.Model):
    _name = 'sped.inutilizacao.tipo.documento'
    _description = 'Tipo de Documento Fiscal'

    codigo = fields.Char(
        string=u'Codigo',
        size=8,
        required=True
    )

    name = fields.Char(
        string=u'Descrição',
        size=64
    )

    electronico = fields.Boolean(
        string=u'Eletrônico',
        default=False
    )


class SpedInutilizacaoDocumento(models.Model):
    _name = 'sped.inutilizacao.documento'
    _description = u'Inutilização de Faixa de Numeração'

    @api.multi
    def name_get(self):
        return [(rec.id,
                 u"{0} ({1}): {2} - {3}".format(
                     rec.tipo_documento_inutilizacao_id.name,
                     rec.serie_documento,
                     rec.inicio_numeracao, rec.fim_numeracao)
                 ) for rec in self]

    empresa_id = fields.Many2one(
        string=u'Empresa',
        comodel_name='sped.empresa',
        required=True,
        default=lambda self:
        self.env['sped.empresa']._empresa_ativa('sped.empresa')
    )

    state = fields.Selection(
        string=u'Estado Atual',
        selection=[
            ('digitacao', 'Em Digitação'),
            ('autorizado', 'Autorizado na Sefaz'),
            ('nao_autorizado', 'Não Autorizado na Sefaz')
        ],
        default='digitacao',
        readonly=True
    )

    status = fields.Char(
        string=u'Status',
        size=10,
        readonly=True
    )

    tipo_documento_inutilizacao_id = fields.Many2one(
        string=u'Tipo do Documento Fiscal',
        required=True,
        comodel_name='sped.inutilizacao.tipo.documento'
    )

    serie_documento = fields.Integer(
        string=u'Série do Documento',
        required=True
    )

    inicio_numeracao = fields.Integer(
        string=u'Número de início',
        required=True
    )

    fim_numeracao = fields.Integer(
        string=u'Número do fim',
        required=True
    )

    justificativa = fields.Char(
        string=u'Justificativa',
        required=True
    )

    menssagem = fields.Char(
        string=u'Mensagem',
        size=200,
        readonly=True
    )

    @api.one
    @api.constrains('justificativa')
    def _check_justificative(self):
        if len(self.justificativa) < 15:
            raise UserError(
                _('Justificativa deve ter tamanho minimo de 15 caracteres.'))
        return True

    @api.one
    @api.constrains('inicio_numeracao', 'fim_numeracao')
    def _check_range(self):
        if self.inicio_numeracao > self.fim_numeracao:
            raise UserError(_(u'Não é permitido faixas sobrepostas!'))
        return True

    _constraints = [
        (_check_range, u'Não é permitido faixas sobrepostas!',
         ['inicio_numeracao', 'fim_numeracao']),
        (_check_justificative,
         'Justificativa deve ter tamanho minimo de 15 caracteres.',
         ['justificativa'])
    ]

    @api.multi
    def enviar_inutilizacao(self):
        try:
            processo = self.send_request_to_sefaz()
            values = {
                'menssagem': processo[0]['message'],
            }

            if processo[0]['status'] == '102':
                values['state'] = 'autorizado'
                self.write(values)
                # self.attach_file_event(None, 'inu', 'xml')
            else:
                values['state'] = 'nao_autorizado'
                values['status'] = processo[0]['status']
                self.write(values)

        except Exception as e:
            raise Warning(_(e.message))
        return True

    @api.multi
    def send_request_to_sefaz(self):
        for item in self:

            self.validate_nfe_configuration(item.empresa_id)
            self.validate_nfe_invalidate_number(item.empresa_id, item)

            processador = self.empresa_id.processador_nfe()
            results = []
            try:
                parametros_inutilizacao = self.validar_parametros_inutilizacao_numeracao()
                processo = processador.inutilizar_nota(
                    ambiente=parametros_inutilizacao['ambiente'],
                    codigo_estado=parametros_inutilizacao['codigo_estado'],
                    ano=parametros_inutilizacao['ano'],
                    cnpj=parametros_inutilizacao['cnpj'],
                    serie=parametros_inutilizacao['serie'],
                    numero_inicial=parametros_inutilizacao['numero_inicial'],
                    numero_final=parametros_inutilizacao['numero_final'],
                    justificativa=parametros_inutilizacao['justificativa']
                )
                vals = {
                    'type': str(processo.webservice),
                    'status': processo.resposta.infInut.cStat.valor,
                    'response': '',
                    'empresa_id': item.empresa_id.id,
                    'origin': '[INU] {0} - {1}'.format(str(item.inicio_numeracao),
                                                       str(item.fim_numeracao)),
                    'message': processo.resposta.infInut.xMotivo.valor,
                    'state': 'done',
                }
                results.append(vals)

            except Exception as e:
                _logger.error(e.message, exc_info=True)
                vals = {
                    'type': '-1',
                    'status': '000',
                    'response': 'response',
                    'company_id': item.empresa_id.id,
                    'origin': '[INU] {0} - {1}'.format(str(item.inicio_numeracao),
                                                       str(item.fim_numeracao)),
                    'file_sent': 'False',
                    'file_returned': 'False',
                    'message': 'Erro desconhecido ' + e.message,
                    'state': 'done',
                }
                results.append(vals)

            return results

    def validate_nfe_invalidate_number(self, empresa, record):
        error = u'As seguintes configurações estão faltando:\n'
        if not empresa.estado:
            error += u'Código do estado no endereço da empresa\n'
        if not empresa.cnpj_cpf:
            error += u'CNPJ na configuração da empresa\n'
        if not record.serie_documento:
            error += u'Série no registro de inutilização\n'
        if not record.inicio_numeracao:
            error += u'Número de inicio no registro de inutilização\n'
        if not record.fim_numeracao:
            error += u'Número final no registro de inutilização\n'
        if error != u'As seguintes configurações estão faltando:\n':
            raise Warning(error)

    def validate_nfe_configuration(self, empresa):
        error = u'As seguintes configurações estão faltando:\n'

        if not empresa.certificado_id.arquivo:
            error += u'Empresa - Arquivo NF-e A1\n'
        if not empresa.certificado_id.senha:
            error += u'Empresa - Senha NF-e A1\n'
        if error != u'As seguintes configurações estão faltando:\n':
            raise Warning(error)

    def validar_parametros_inutilizacao_numeracao(self):
        ambiente = self.empresa_id.ambiente_nfe
        codigo_estado = UF_CODIGO[self.empresa_id.estado]
        ano = str(fields.Date.from_string(fields.Datetime.now()).year)[2:]
        cnpj = limpa_formatacao(self.empresa_id.cnpj_cpf)

        return dict(
            ambiente=int(ambiente),
            codigo_estado=codigo_estado,
            ano=ano,
            cnpj=cnpj,
            serie=self.serie_documento,
            numero_inicial=self.inicio_numeracao,
            numero_final=self.fim_numeracao,
            justificativa=str(self.justificativa)
        )
