# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario

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
            if esocial.servidor_id:
                codigo += ' - ' if codigo else ''
                codigo += esocial.servidor_id.name or ''
            if esocial.periodo_id:
                codigo += ' ' if codigo else ''
                codigo += '(' + esocial.periodo_id.code or '' + ')'
            esocial.codigo = codigo

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
    def popula_xml(self, ambiente='2', operacao='na'):
        self.ensure_one()

        # Validação
        validacao = ""

        # Cria o registro
        S1202 = pysped.esocial.leiaute.S1202_2()
        S1202.tpInsc = '1'
        S1202.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        # Popula ideEvento
        indRetif = '1'
        if operacao == 'R':
            indRetif = '2'
            S1202.evento.ideEvento.nrRecibo.valor = self.sped_registro.retificado_id.recibo
        S1202.evento.ideEvento.indRetif.valor = indRetif
        S1202.evento.ideEvento.indApuracao.valor = '1'  # TODO Lidar com os holerites de 13º salário
                                                        # '1' - Mensal
                                                        # '2' - Anual (13º salário)
        S1202.evento.ideEvento.perApur.valor = \
            self.periodo_id.code[3:7] + '-' + \
            self.periodo_id.code[0:2]
        S1202.evento.ideEvento.tpAmb.valor = ambiente
        S1202.evento.ideEvento.procEmi.valor = '1'    # Aplicativo do empregador
        S1202.evento.ideEvento.verProc.valor = '8.0'  # Odoo v.8.0

        # Popula ideEmpregador (Dados do Empregador)
        S1202.evento.ideEmpregador.tpInsc.valor = '1'
        S1202.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        # Popula ideTrabalhador (Dados do Trabalhador)
        S1202.evento.ideTrabalhador.cpfTrab.valor = limpa_formatacao(self.servidor_id.cpf)
        S1202.evento.ideTrabalhador.nisTrab.valor = limpa_formatacao(self.servidor_id.pis_pasep)

        # Conta o número de dependentes para fins do regime próprio de previdência social
        dependentes = 0
        for dependente in self.servidor_id.dependent_ids:
            if dependente.dependent_verification:
                dependentes += 1
        S1202.evento.ideTrabalhador.qtdDepFP.valor = dependentes

        # # Popula ideTrabalhador.infoMV (Dados do Empregador Cedente)  # TODO
        # #        ideTrabalhador.infoMV.remunOutrEmpr
        # #
        # # Registro preenchido exclusivamente em caso de servidor que possua outros vínculos/atividades
        # # para definição do limite do salário-de-contribuição e da alíquota a ser aplicada no desconto da
        # # contribuição previdenciária.
        #
        # if self.servidor_id.
        # info_mv = pysped.esocial.leiaute.S1202_InfoMV_2()
        # info_mv

        # # Popula ideTrabalhador.procJudTrab  # TODO
        # #
        # # Informações sobre a existência de processos judiciais do servidor com decisão favorável quanto à não
        # # incidência ou alterações na incidência de contribuições sociais e/ou Imposto de Renda sobre as rubricas
        # # apresentadas nos subregistros de {dmDev}.
        #
        # proc_jud_trab = pysped.esocial.leiaute.S1202_ProcJudTrab_2()
        # proc_jud_trab.

        # Popula dmDev (1 para cada payslip)
        for payslip in self.payslip_ids:
            dm_dev = pysped.esocial.leiaute.S1202_DmDev_2()
            dm_dev.ideDmDev.valor = payslip.number

            # Popula dmDev.infoPerApur
            info_per_apur = pysped.esocial.leiaute.S1202_InfoPerApur_2()
            info_per_apur.ideEstab.tpInsc.valor = '1'  # CNPJ
            info_per_apur.ideEstab.nrInsc.valor = limpa_formatacao(payslip.company_id.cnpj_cpf)

            # Popula dmDev.infoPerApur.ideEstab.remunPerApur
            remun_per_apur = pysped.esocial.leiaute.S1202_RemunPerApur_2()
            remun_per_apur.matricula.valor = payslip.contract_id.matricula
            remun_per_apur.codCateg.valor = payslip.contract_id.categoria  # TODO Integrar com a tabela 01 do e-Social

            # Popula dmDev.infoPerApur.ideEstab.remunPerApur.itensRemun
            for line in payslip.line_ids:

                # Só adiciona a rubrica se o campo nat_rubr estiver definido, isso define que a rubrica deve
                # ser transmitida para o e-Social.
                if line.salary_rule_id.nat_rubr:
                    itens_remun = pysped.esocial.leiaute.S1202_ItensRemun_2()
                    itens_remun.codRubr.valor = line.salary_rule_id.codigo
                    itens_remun.ideTabRubr.valor = line.salary_rule_id.identificador
                    if line.quantity and float(line.quantity) != 1:
                        itens_remun.qtdRubr.valor = float(line.quantity)
                        itens_remun.vrUnit.valor = formata_valor(line.amount)
                    if line.rate and line.rate != 100:
                        itens_remun.fatorRubr.valor = line.rate
                    itens_remun.vrRubr.valor = formata_valor(line.total)
                    remun_per_apur.itensRemun.append(itens_remun)

            # # Popula dmDev.infoPerApur.ideEstab.remunPerApur.infoSaudeColet  # TODO Quando tivermos plano de saúde
            # #                                                                   # coletívo
            # # Informações de plano privado coletivo empresarial de assistência à saúde. Só preencher se houver
            # # {codRubr} em {itensRemun}, cuja natureza de rubrica {natRubr} indicada em S-1010 seja igual a [9219].
            # # Não preencher nos demais casos
            # #
            # info_saude_colet = pysped.esocial.leiaute.S1202_InfoSaudeColet_2()
            # info_saude_colet.

            # # Popula dmDev.infoPerAnt  # TODO Quando tratarmos dos cálculo retroativos por coleção coletiva
            # #
            # # Registro destinado ao registro de:
            # # a) remuneração relativa a diferenças salariais provenientes de acordos coletivos, convenção coletiva
            # #    e dissídio.
            # # b) remuneração relativa a diferenças de vencimento provenientes de disposições legais (órgãos públicos)
            # # c) bases de cálculo para efeitos de apuração de FGTS resultantes de conversão de licença saúde em
            # #    acidente de trabalho
            # # d) verbas de natureza salarial ou não salarial devidas após o desligamento.
            # # OBS.: as informações previstas nos itens "a", "b" e "d" acima podem se referir ao período de apuração
            # #       definido em {perApur} ou a períodos anteriores a {perApur}.
            # #
            # info_per_ant = pysped.esocial.leiaute.S1202_InfoPerAnt_2()
            # info_per_ant.

            # Popula dmDev.infoComplCont  # Não teremos registros no odoo que não tenham um S2300 nesses casos
            #

            # Adiciona o registro nas listas das tags superiores
            info_per_apur.ideEstab.remunPerApur.append(remun_per_apur)
            dm_dev.infoPerApur.append(info_per_apur)
            S1202.evento.dmDev.append(dm_dev)

        return S1202, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

    @api.multi
    def retorna_trabalhador(self):
        self.ensure_one()
        return self.servidor_id
