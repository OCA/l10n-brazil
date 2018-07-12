# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from .sped_registro_intermediario import SpedRegistroIntermediario

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor
from datetime import datetime
import pysped


class SpedEsocialRemuneracaoRPPS(models.Model, SpedRegistroIntermediario):
    _name = "sped.esocial.remuneracao.rpps"
    _rec_name = "codigo"
    _order = "company_id,periodo_id,servidor_id"

    codigo = fields.Char(
        string='Código',
        compute='_compute_codigo',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    servidor_id = fields.Many2one(
        string='Servidor',
        comodel_name='hr.employee',
    )
    periodo_id = fields.Many2one(
        string='Período',
        comodel_name='account.period',
    )
    contract_ids = fields.Many2many(
        string='Contratos',
        comodel_name='hr.contract',
    )
    payslip_ids = fields.Many2many(
        string='Holerites',
        comodel_name='hr.payslip',
    )
    contratos = fields.Integer(
        string='Contratos',
        compute='_compute_qtd',
    )
    remuneracoes = fields.Integer(
        string='Remunerações',
        compute='_compute_qtd',
    )

    @api.depends('company_id', 'servidor_id', 'periodo_id')
    def _compute_codigo(self):
        for esocial in self:
            codigo = ''
            if esocial.company_id:
                codigo += esocial.company_id.name or ''
            if esocial.trabalhador_id:
                codigo += ' - ' if codigo else ''
                codigo += esocial.servidor_id.name or ''
            if esocial.periodo_id:
                codigo += ' ' if codigo else ''
                codigo += '(' + esocial.periodo_id.code or '' + ')'

    @api.depends('contract_ids', 'payslip_ids')
    def _compute_qtd(self):
        for esocial in self:
            esocial.contratos = 0 if not esocial.contract_ids else len(esocial.contract_ids)
            esocial.remuneracoes = 0 if not esocial.payslip_ids else len(esocial.payslip_ids)

    # Campos de controle e-Social, registros Periódicos
    sped_registro = fields.Many2one(
        string='Registro SPED',
        comodel_name='sped.registro',
    )
    situacao_esocial = fields.Selection(
        string='Situação',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        related='sped_registro.situacao',
    )

    # Roda a atualização do e-Social (não transmite ainda)
    @api.multi
    def atualizar_esocial(self):
        self.ensure_one()

        # Criar o registro S-1202
        if not self.sped_registro:
            values = {
                'tipo': 'esocial',
                'registro': 'S-1202',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'operacao': 'na',
                'evento': 'evtRmnRPPS',
                'origem': ('sped.esocial.remuneracao.rpps,%s' % self.id),
                'origem_intermediario': ('sped.esocial.remuneracao.rpps,%s' % self.id),
            }

            sped_registro = self.env['sped.registro'].create(values)
            self.sped_registro = sped_registro

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        self.ensure_one()

        # # Cria o registro
        # S1200 = pysped.esocial.leiaute.S1200_2()
        # S1200.tpInsc = '1'
        # S1200.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
        #
        # # Popula ideEvento
        # S1200.evento.ideEvento.indRetif.valor = '1'  # TODO Criar meio de enviar um registro retificador
        # # S1200.evento.ideEvento.nrRecibo.valor = '' # Recibo só quando for retificação
        # S1200.evento.ideEvento.indApuracao.valor = '1'  # TODO Lidar com os holerites de 13º salário
        #                                                 # '1' - Mensal
        #                                                 # '2' - Anual (13º salário)
        # S1200.evento.ideEvento.perApur.valor = \
        #     self.periodo_id.code[3:7] + '-' + \
        #     self.periodo_id.code[0:2]
        # S1200.evento.ideEvento.tpAmb.valor = ambiente
        # S1200.evento.ideEvento.procEmi.valor = '1'    # Aplicativo do empregador
        # S1200.evento.ideEvento.verProc.valor = '8.0'  # Odoo v.8.0
        #
        # # Popula ideEmpregador (Dados do Empregador)
        # S1200.evento.ideEmpregador.tpInsc.valor = '1'
        # S1200.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
        #
        # # Popula ideTrabalhador (Dados do Trabalhador)
        # S1200.evento.ideTrabalhador.cpfTrab.valor = limpa_formatacao(self.trabalhador_id.cpf)
        # S1200.evento.ideTrabalhador.nisTrab.valor = limpa_formatacao(self.trabalhador_id.pis_pasep)
        #
        # # # Popula ideTrabalhador.infoMV (Dados do Empregador Cedente)  # TODO
        # # #        ideTrabalhador.infoMV.remunOutrEmpr
        # # #
        # # # Registro preenchido exclusivamente em caso de trabalhador que possua outros vínculos/atividades
        # # # para definição do limite do salário-de-contribuição e da alíquota a ser aplicada no desconto da
        # # # contribuição previdenciária.
        # #
        # # if self.trabalhador_id.
        # # info_mv = pysped.esocial.leiaute.S1200_InfoMV_2()
        # # info_mv
        #
        # # # Popula ideTrabalhador.infoComplem               # TODO
        # # #        ideTrabalhador.infoComplem.sucessaoVinc
        # # #
        # # # Registro preenchido exclusivamente quando o evento de remuneração referir-se a trabalhador cuja
        # # # categoria não está sujeita ao evento de admissão ou ao evento de início de "trabalhador sem vínculo".
        # # # No caso das categorias em que o envio do evento TSV é opcional, o preenchimento do grupo somente é
        # # # exigido se não houver evento TSV Início correspondente (cpf + categoria). As informações
        # # # complementares são necessárias para correta identificação do trabalhador.
        # #
        # # info_complem = pysped.esocial.leiaute.S1200_InfoComplem_2()
        # # info_complem.
        #
        # # # Popula ideTrabalhador.procJudTrab  # TODO
        # # #
        # # # Informações sobre a existência de processos judiciais do trabalhador com decisão favorável quanto à não
        # # # incidência ou alterações na incidência de contribuições sociais e/ou Imposto de Renda sobre as rubricas
        # # # apresentadas nos subregistros de {dmDev}.
        # #
        # # proc_jud_trab = pysped.esocial.leiaute.S1200_ProcJudTrab_2()
        # # proc_jud_trab.
        #
        # # # Popula ideTrabalhador.infoInterm  # TODO
        # # #
        # # # Informações relativas ao trabalho intermitente
        # #
        # # info_interm = pysped.esocial.leiaute.S1200_InfoInterm_2()
        # # info_interm.
        #
        # # Popula dmDev (1 para cada payslip)
        # for payslip in self.payslip_ids:
        #     dm_dev = pysped.esocial.leiaute.S1200_DmDev_2()
        #     dm_dev.ideDmDev.valor = payslip.number
        #     dm_dev.codCateg.valor = payslip.contract_id.categoria  # TODO Integrar com a tabela 01 do e-Social
        #
        #     # Popula dmDev.infoPerApur
        #     info_per_apur = pysped.esocial.leiaute.S1200_InfoPerApur_2()
        #     info_per_apur.ideEstabLot.tpInsc.valor = '1'  # CNPJ
        #     info_per_apur.ideEstabLot.nrInsc.valor = limpa_formatacao(payslip.company_id.cnpj_cpf)
        #     info_per_apur.ideEstabLot.codLotacao.valor = payslip.company_id.cod_lotacao
        #
        #     # Popula dmDev.infoPerApur.ideEstabLot.remunPerApur
        #     remun_per_apur = pysped.esocial.leiaute.S1200_RemunPerApur_2()
        #     remun_per_apur.matricula.valor = payslip.contract_id.matricula
        #     # remun_per_apur.indSimples.valor =  # TODO Somente para quando a empresa for do Simples
        #                                          # lidar com isso na res.company
        #
        #     # Popula dmDev.infoPerApur.ideEstabLot.remunPerApur.itensRemun
        #     for line in payslip.line_ids:
        #
        #         # Só adiciona a rubrica se o campo nat_rubr estiver definido, isso define que a rubrica deve
        #         # ser transmitida para o e-Social.
        #         if line.salary_rule_id.nat_rubr:
        #             itens_remun = pysped.esocial.leiaute.S1200_ItensRemun_2()
        #             itens_remun.codRubr.valor = line.salary_rule_id.codigo
        #             itens_remun.ideTabRubr.valor = line.salary_rule_id.identificador
        #             if line.quantity and float(line.quantity) != 1:
        #                 itens_remun.qtdRubr.valor = float(line.quantity)
        #                 itens_remun.vrUnit.valor = formata_valor(line.amount)
        #             if line.rate and line.rate != 100:
        #                 itens_remun.fatorRubr.valor = line.rate
        #             itens_remun.vrRubr.valor = formata_valor(line.total)
        #             remun_per_apur.itensRemun.append(itens_remun)
        #
        #     # # Popula dmDev.infoPerApur.ideEstabLot.remunPerApur.infoSaudeColet  # TODO Quando tivermos plano de saúde
        #     # #                                                                   # coletívo
        #     # # Informações de plano privado coletivo empresarial de assistência à saúde. Só preencher se houver
        #     # # {codRubr} em {itensRemun}, cuja natureza de rubrica {natRubr} indicada em S-1010 seja igual a [9219].
        #     # # Não preencher nos demais casos
        #     # #
        #     # info_saude_colet = pysped.esocial.leiaute.S1200_InfoSaudeColet_2()
        #     # info_saude_colet.
        #
        #     # # Popula dmDev.infoPerApur.ideEstabLot.remunPerApur.infoAgNocivo  # TODO Quando tivermos controle de
        #     # #                                                                 # agentes nocivos
        #     # # Registro preenchido exclusivamente em relação a remuneração do trabalhador enquadrado em uma das
        #     # # categorias relativas a Empregado, Servidor Público, Avulso, ou na categoria de Cooperado filiado
        #     # # a cooperativa de produção [738] ou Cooperado filiado a cooperativa de trabalho que presta serviço
        #     # # a empresa [731, 734], permitindo o detalhamento do grau de exposição do trabalhador aos agentes
        #     # # nocivos que ensejam cobrança da contribuição adicional para financiamento dos benefícios de
        #     # # aposentadoria especial.
        #     # #
        #     # info_ag_nocivo = pysped.esocial.leiaute.S1200_InfoAgNocivo_2()
        #     # info_ag_nocivo.
        #
        #     # # Popula dmDev.infoPerApur.ideEstabLot.remunPerApur.infoTrabInterm  # TODO Quando tivermos controle
        #     # #                                                                   # trabalho intermitente
        #     # # Informações da(s) convocação(ões) de trabalho intermitente
        #     # #
        #     # info_trab_interm = pysped.esocial.leiaute.S1200_InfoTrabInterm_2()
        #     # info_trab_interm.
        #
        #     # # Popula dmDev.infoPerAnt  # TODO Quando tratarmos dos cálculo retroativos por coleção coletiva
        #     # #
        #     # # Registro destinado ao registro de:
        #     # # a) remuneração relativa a diferenças salariais provenientes de acordos coletivos, convenção coletiva
        #     # #    e dissídio.
        #     # # b) remuneração relativa a diferenças de vencimento provenientes de disposições legais (órgãos públicos)
        #     # # c) bases de cálculo para efeitos de apuração de FGTS resultantes de conversão de licença saúde em
        #     # #    acidente de trabalho
        #     # # d) verbas de natureza salarial ou não salarial devidas após o desligamento.
        #     # # OBS.: as informações previstas nos itens "a", "b" e "d" acima podem se referir ao período de apuração
        #     # #       definido em {perApur} ou a períodos anteriores a {perApur}.
        #     # #
        #     # info_per_ant = pysped.esocial.leiaute.S1200_InfoPerAnt_2()
        #     # info_per_ant.
        #
        #     # Popula dmDev.infoComplCont  # Não teremos registros no odoo que não tenham um S2300 nesses casos
        #     #
        #
        #     # Adiciona o registro nas listas das tags superiores
        #     info_per_apur.ideEstabLot.remunPerApur.append(remun_per_apur)
        #     dm_dev.infoPerApur.append(info_per_apur)
        #     S1200.evento.dmDev.append(dm_dev)
        #
        # return S1200

    @api.multi
    def retorno_sucesso(self):
        self.ensure_one()
