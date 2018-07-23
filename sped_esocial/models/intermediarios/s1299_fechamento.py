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


class SpedEsocialFechamento(models.Model, SpedRegistroIntermediario):
    _name = "sped.esocial.fechamento"
    _rec_name = "codigo"
    _order = "company_id,periodo_id"

    codigo = fields.Char(
        string='Código',
        compute='_compute_codigo',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    periodo_id = fields.Many2one(
        string='Período',
        comodel_name='account.period',
    )
    evt_remun = fields.Selection(
        string='Possui Remunerações?',
        selection=[
            ('S', 'S-Sim'),
            ('N', 'N-Não'),
        ],
    )
    evt_pgtos = fields.Selection(
        string='Possui Pagamentos?',
        selection=[
            ('S', 'S-Sim'),
            ('N', 'N-Não'),
        ],
    )
    evt_aq_prod = fields.Selection(
        string='Possui Aquisições Rurais?',
        selection=[
            ('S', 'S-Sim'),
            ('N', 'N-Não'),
        ],
    )
    evt_com_prod = fields.Selection(
        string='Possui Comercializações de Produção Rural?',
        selection=[
            ('S', 'S-Sim'),
            ('N', 'N-Não'),
        ],
    )
    evt_contrat_av_np = fields.Selection(
        string='Contratou por Intermédio de Sindicato?',
        selection=[
            ('S', 'S-Sim'),
            ('N', 'N-Não'),
        ],
    )
    evt_infocompl_per = fields.Selection(
        string='Contratou por Intermédio de Sindicato?',
        selection=[
            ('S', 'S-Sim'),
            ('N', 'N-Não'),
        ],
    )
    comp_sem_movto = fields.Many2one(
        string='Primeira competência sem movimento',
        comodel_name='account.period',
    )
    s5011_id = fields.Many2one(
        string='S-5011 (INSS Consolidado)',
        comodel_name='sped.inss.consolidado',
    )

    @api.depends('company_id', 'periodo_id')
    def _compute_codigo(self):
        for esocial in self:
            codigo = ''
            if esocial.company_id:
                codigo += esocial.company_id.name or ''
            if esocial.periodo_id:
                codigo += ' ' if codigo else ''
                codigo += '('
                codigo += esocial.periodo_id.code or ''
                codigo += ')'
            esocial.codigo = codigo

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

        # Criar o registro S-1299
        if not self.sped_registro:
            values = {
                'tipo': 'esocial',
                'registro': 'S-1299',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'operacao': 'na',
                'evento': 'evtFechaEvPer',
                'origem': ('sped.esocial.fechamento,%s' % self.id),
                'origem_intermediario': ('sped.esocial.fechamento,%s' % self.id),
            }

            sped_registro = self.env['sped.registro'].create(values)
            self.sped_registro = sped_registro

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        self.ensure_one()

        # Cria o registro
        S1299 = pysped.esocial.leiaute.S1299_2()
        S1299.tpInsc = '1'
        S1299.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        # Popula ideEvento
        S1299.evento.ideEvento.indApuracao.valor = '1'  # TODO Lidar com os holerites de 13º salário
                                                        # '1' - Mensal
                                                        # '2' - Anual (13º salário)
        S1299.evento.ideEvento.perApur.valor = \
            self.periodo_id.code[3:7] + '-' + \
            self.periodo_id.code[0:2]
        S1299.evento.ideEvento.tpAmb.valor = ambiente
        S1299.evento.ideEvento.procEmi.valor = '1'    # Aplicativo do empregador
        S1299.evento.ideEvento.verProc.valor = '8.0'  # Odoo v.8.0

        # Popula ideEmpregador (Dados do Empregador)
        S1299.evento.ideEmpregador.tpInsc.valor = '1'
        S1299.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        # Popula ideRespInf (Responsável pelas Informações)
        S1299.evento.ideRespInf.nmResp.valor = self.company_id.esocial_nm_ctt
        S1299.evento.ideRespInf.cpfResp.valor = limpa_formatacao(self.company_id.esocial_cpf_ctt)
        S1299.evento.ideRespInf.telefone.valor = limpa_formatacao(self.company_id.esocial_fone_fixo)
        if self.company_id.esocial_email:
            S1299.evento.ideRespInf.email.valor = self.company_id.esocial_email

        # Popula infoFech (Informações do Fechamento)
        S1299.evento.infoFech.evtRemun.valor = self.evt_remun
        S1299.evento.infoFech.evtPgtos.valor = self.evt_pgtos
        S1299.evento.infoFech.evtAqProd.valor = self.evt_aq_prod
        S1299.evento.infoFech.evtComProd.valor = self.evt_com_prod
        S1299.evento.infoFech.evtContratAvNP.valor = self.evt_contrat_av_np
        S1299.evento.infoFech.evtInfoComplPer.valor = self.evt_infocompl_per
        if self.comp_sem_movto:
            S1299.evento.infoFech.compSemMovto.valor = \
                self.comp_sem_movto.code[3:7] + '-' + \
                self.comp_sem_movto.code[0:2]

        return S1299

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        if evento:
            for tot in evento.tot:

                if tot.tipo.valor == 'S5011':

                    # print(tot.xml)
                    # Busca o sped.registro que originou esse totalizador
                    sped_registro = self.env['sped.registro'].search([
                        ('registro', '=', 'S-1299'),
                        ('recibo', '=', tot.eSocial.evento.ideEvento.nrRecArqBase.valor)
                    ])

                    # Busca pelo sped.registro deste totalizador (se ele já existir)
                    sped_s5011 = self.env['sped.registro'].search([
                        ('id_evento', '=', tot.eSocial.evento.Id.valor)
                    ])

                    # Busca pelo registro intermediário (se ele já existir)
                    sped_intermediario = self.env['sped.inss.consolidado'].search([
                        ('id_evento', '=', tot.eSocial.evento.Id.valor)
                    ])

                    # Popula os valores para criar/alterar o registro intermediário do totalizador
                    vals_intermediario_totalizador = {
                        'company_id': sped_registro.company_id.id,
                        'id_evento': tot.eSocial.evento.Id.valor,
                        'periodo_id': sped_registro.origem_intermediario.periodo_id.id,
                        'ind_exist_info': tot.eSocial.evento.infoCS.indExistInfo.valor,
                        # TODO popular os demais campos aqui
                        'sped_registro_s1299': sped_registro.id,
                    }

                    # Cria/Altera o registro intermediário
                    if sped_intermediario:
                        sped_intermediario.write(vals_intermediario_totalizador)
                    else:
                        sped_intermediario = self.env['sped.inss.consolidado'].create(vals_intermediario_totalizador)

                    # Popula os valores para criar/alterar o sped.registro do totalizador
                    vals_registro_totalizador = {
                        'tipo': 'esocial',
                        'registro': 'S-5011',
                        'evento': 'evtCS',
                        'operacao': 'na',
                        'ambiente': sped_registro.ambiente,
                        'origem': ('sped.inss.consolidado,%s' % sped_intermediario.id),
                        'origem_intermediario': ('sped.inss.consolidado,%s' % sped_intermediario.id),
                        'company_id': sped_registro.company_id.id,
                        'id_evento': tot.eSocial.evento.Id.valor,
                        'situacao': '4',
                        'recibo': tot.eSocial.evento.ideEvento.nrRecArqBase.valor,
                    }

                    # Cria/Altera o sped.registro do totalizador
                    if sped_s5011:
                        sped_s5011.write(vals_registro_totalizador)
                    else:
                        sped_s5011 = self.env['sped.registro'].create(vals_registro_totalizador)

                    # Popula o intermediário totalizador com o registro totalizador
                    sped_intermediario.sped_registro_s5011 = sped_s5011

                    # Popula o intermediário S1299 com o intermediário totalizador
                    self.s5011_id = sped_intermediario

                    # Popula o XML em anexo no sped.registro totalizador
                    if sped_s5011.consulta_xml_id:
                        consulta = sped_s5011.consulta_xml_id
                        sped_s5011.consulta_xml_id = False
                        consulta.unlink()
                    consulta_xml = tot.eSocial.xml
                    consulta_xml_nome = sped_s5011.id_evento + '-consulta.xml'
                    anexo_id = sped_registro._grava_anexo(consulta_xml_nome, consulta_xml)
                    sped_s5011.consulta_xml_id = anexo_id

                    # # Limpa a tabela sped.irrf.infoirrf
                    # for irrf in sped_intermediario.infoirrf_ids:
                    #     irrf.unlink()
                    #
                    # # Popula a tabela sped.irrf.basesirrf com os valores apurados no S-5002
                    # for irrf in tot.eSocial.evento.infoIrrf:
                    #     for base in irrf.basesIrrf:
                    #
                    #         vals = {
                    #             'parent_id': sped_intermediario.id,
                    #             'cod_categ': irrf.codCateg.valor,
                    #             'ind_res_br': irrf.indResBr.valor,
                    #             'tp_valor': base.tpValor.valor,
                    #             'valor': float(base.valor.valor),
                    #         }
                    #         self.env['sped.irrf.basesirrf'].create(vals)
                    #
                    # # Popula a tabela sped.irrf.infoirrf com os valores apurados no S-5002
                    # for irrf in tot.eSocial.evento.infoIrrf:
                    #     for info in irrf.irrf:
                    #
                    #         vals = {
                    #             'parent_id': sped_intermediario.id,
                    #             'cod_categ': irrf.codCateg.valor,
                    #             'ind_res_br': irrf.indResBr.valor,
                    #             'tp_cr': info.tpCR.valor,
                    #             'vr_irrf_desc': float(info.vrIrrfDesc.valor),
                    #         }
                    #         self.env['sped.irrf.infoirrf'].create(vals)

                if tot.tipo.valor == 'S5012':

                    print(tot.xml)
