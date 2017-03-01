# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


import logging
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from ...sped.constante_tributaria import *

_logger = logging.getLogger(__name__)

_logger = logging.getLogger(__name__)

try:
    from pysped.nfe import ProcessadorNFe
    from pysped.nfe.webservices_flags import *
    from pysped.nfe.leiaute import *
    from pybrasil.inscricao import limpa_formatacao
    from pybrasil.data import (parse_datetime, UTC, data_hora_horario_brasilia,
                               agora)
    from pybrasil.valor import formata_valor

except (ImportError, IOError) as err:
    _logger.debug(err)


class ConsultaDFe(models.Model):
    _description = u'Consulta DFe'
    _name = 'sped.consulta.dfe'

    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string=u'Empresa',
        required=True,
    )
    ultimo_nsu = fields.Char(
        string=u'Último NSU',
        size=25,
        default='0',
        required=True,
    )
    ultima_consulta = fields.Datetime(
        string=u'Última consulta',
    )

    def busca_documentos(self):
        for consulta in self:
            #import ipdb; ipdb.set_trace();

            processador = self.empresa_id.processador_nfe()
            processador.ambiente = int(AMBIENTE_NFE_PRODUCAO)
            cnpj = limpa_formatacao(self.empresa_id.cnpj_cpf)

            processo = processador.consultar_notas_destinadas(
                cnpj=cnpj,
                ultimo_nsu=self.ultimo_nsu or '0',
                tipo_nfe=CONS_NFE_TODAS,
                tipo_emissao=CONS_NFE_EMISSAO_TODOS_EMITENTES,
            )

            print(processo.envio.xml.encode('utf-8'))
            print('resposta')
            print(processo.resposta.original.encode('utf-8'))

            ##
            ## Nenhum documento encontrado
            ##
            #if processo.resposta.cStat.valor == '137':
                #uu_obj.write({'ultimo_nsu': processo.resposta.ultNSU.valor, 'ultima_consulta': str(UTC.normalize(agora()))})

            ##
            ## Consumo indevido, não tem mais documentos para retornar, deve esperar
            ## 1 hora para a próxima execução
            ##
            #if processo.resposta.cStat.valor == '656':
                #uu_obj.write({'ultima_consulta': str(UTC.normalize(agora()))})
                #cron_id = self.pool.get('ir.cron').search(cr, 1, [('function', '=', 'acao_demorada_busca_documentos')])
                #if cron_id is not None and len(cron_id):
                    #cron_obj = self.pool.get('ir.cron').browse(cr, 1, cron_id[0])
                    #nova_execucao = parse_datetime(cron_obj.nextcall + ' GMT')
                    #nova_execucao += relativedelta(hours=+1)
                    #nova_execucao = UTC.normalize(nova_execucao)
                    #cron_obj.write({'nextcall': str(nova_execucao)[:19]})

            #elif processo.resposta.cStat.valor == '138':
                #uu_obj.write({'ultimo_nsu': processo.resposta.ultNSU.valor, 'ultima_consulta': str(UTC.normalize(agora()))})

                #for rn in processo.resposta.resNFe:
                    #cnpj = formata_cnpj(rn.CNPJ.valor)
                    #data_autorizacao = parse_datetime(rn.dhRecbto.valor)
                    #data_autorizacao = UTC.normalize(data_autorizacao)
                    #dados = {
                        #'company_id': uu_obj.company_id.id,
                        #'cnpj': cnpj,
                        #'nome': rn.xNome.valor,
                        #'ie': rn.IE.valor,
                        #'data_emissao': str(rn.dEmi.valor),
                        #'nsu': rn.NSU.valor,
                        #'data_autorizacao': str(data_autorizacao),
                        #'digest_value': rn.digVal.valor,
                        #'situacao_dfe': rn.cSitNFe.valor,
                        #'situacao_manifestacao': rn.cSitConf.valor,
                        #'chave': rn.chNFe.valor,
                    #}

                    #if rn.chNFe.valor:
                        #dados['serie'] = rn.chNFe.valor[22:25]
                        #dados['numero'] = int(rn.chNFe.valor[25:34])

                    #partner_ids = partner_pool.search(cr, uid, [('cnpj_cpf', '=', cnpj)])
                    #if partner_ids:
                        #dados['partner_id'] = partner_ids[0]

                    #dist_dfe_pool.create(cr, uid, dados)

    #def acao_demorada_busca_documentos(self, cr, uid, ids=[], context={}):
        #if not ids:
            #ids = self.pool.get('sped.ultimo_nsu').search(cr, uid, [])

        #self.pool.get('sped.ultimo_nsu').busca_documentos(cr, uid, ids, context)


