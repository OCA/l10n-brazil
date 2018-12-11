# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
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
    s5012_id = fields.Many2one(
        string='S-5012 (IRRF Consolidado)',
        comodel_name='sped.irrf.consolidado',
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
        store=True,
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

        # Validação
        validacao = ""

        # Cria o registro
        S1299 = pysped.esocial.leiaute.S1299_2()
        S1299.tpInsc = '1'
        S1299.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        # Popula ideEvento
        if '13/' not in self.periodo_id.code:
            S1299.evento.ideEvento.indApuracao.valor = '1'
            S1299.evento.ideEvento.perApur.valor = \
                self.periodo_id.code[3:7] + '-' + \
                self.periodo_id.code[0:2]
        else:
            S1299.evento.ideEvento.indApuracao.valor = '2'
            S1299.evento.ideEvento.perApur.valor = self.periodo_id.code[3:7]

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

        return S1299, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        if evento:

            # Fecha o periodo relacionado
            periodo = self.env['sped.esocial'].search([
                ('company_id', '=', self.company_id.id),
                ('periodo_id', '=', self.periodo_id.id),
            ])
            periodo.situacao = '3'

            # Cria os registros totalizadores
            for tot in evento.tot:

                if tot.tipo.valor == 'S5011':

                    # Busca o sped.registro que originou esse totalizador
                    sped_registro = self.env['sped.registro'].search([
                        ('registro', '=', 'S-1299'),
                        ('recibo', '=', tot.eSocial.evento.infoCS.nrRecArqBase.valor)
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
                        'recibo': tot.eSocial.evento.infoCS.nrRecArqBase.valor,
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

                    # Limpa a tabela sped.inss.consolidado.ideestab
                    for ideestab in sped_intermediario.ideestab_ids:
                        ideestab.unlink()

                    # Popula a tabela sped.inss.consolidado.ideestab com os valores apurados no S-5011
                    for estabelecimento in tot.eSocial.evento.infoCS.ideEstab:

                        estabelecimento_id = self.env['res.company'].search([
                            ('cnpj_cpf_limpo', '=', estabelecimento.nrInsc.valor),
                        ])

                        if estabelecimento_id:
                            for lotacao in estabelecimento.ideLotacao:

                                lotacao_id = self.env['res.company'].search([
                                    ('cod_lotacao', '=', lotacao.codLotacao.valor),
                                ])

                                if lotacao_id:

                                    fpas = self.env['sped.codigo_aliquota'].search([
                                        ('codigo', '=', lotacao.fpas.valor),
                                    ])

                                    vals = {
                                        'parent_id': sped_intermediario.id,
                                        'estabelecimento_id': estabelecimento_id.id,
                                        'lotacao_id': lotacao_id.id,
                                        'fpas_id': fpas.id,
                                        'cod_tercs': lotacao.codTercs.valor,
                                    }

                                    # Popula se a tag infoEstab foi devolvida pelo registro S-5011
                                    if estabelecimento.infoEstab:
                                        vals['cnae_prep'] = estabelecimento.infoEstab[0].cnaePrep.valor
                                        vals['aliq_rat'] = estabelecimento.infoEstab[0].aliqRat.valor
                                        vals['fap'] = estabelecimento.infoEstab[0].fap.valor
                                        vals['aliq_rat_ajust'] = estabelecimento.infoEstab[0].aliqRatAjust.valor

                                    ideestab_id = self.env['sped.inss.consolidado.ideestab'].create(vals)

                                    # Popula a tabela sped.inss.consolidado.basesremun
                                    for base in lotacao.basesRemun:

                                        cod_categ_id = self.env['sped.categoria_trabalhador'].search([
                                            ('codigo', '=', base.codCateg.valor),
                                        ])

                                        if cod_categ_id:
                                            vals = {
                                                'parent_id': ideestab_id.id,
                                                'ind_incid': base.indIncid.valor,
                                                'cod_categ': cod_categ_id.id,
                                                'vr_bc_cp_00': base.basesCp.vrBcCp00.valor,
                                                'vr_bc_cp_15': base.basesCp.vrBcCp15.valor,
                                                'vr_bc_cp_20': base.basesCp.vrBcCp20.valor,
                                                'vr_bc_cp_25': base.basesCp.vrBcCp25.valor,
                                                'vr_susp_bc_cp_00': base.basesCp.vrSuspBcCp00.valor,
                                                'vr_susp_bc_cp_15': base.basesCp.vrSuspBcCp15.valor,
                                                'vr_susp_bc_cp_20': base.basesCp.vrSuspBcCp20.valor,
                                                'vr_susp_bc_cp_25': base.basesCp.vrSuspBcCp25.valor,
                                                'vr_desc_sest': base.basesCp.vrDescSest.valor,
                                                'vr_calc_sest': base.basesCp.vrCalcSest.valor,
                                                'vr_desc_senat': base.basesCp.vrDescSenat.valor,
                                                'vr_calc_senat': base.basesCp.vrCalcSenat.valor,
                                                'vr_sal_fam': base.basesCp.vrSalFam.valor,
                                                'vr_sal_mat': base.basesCp.vrSalMat.valor,
                                            }

                                            self.env['sped.inss.consolidado.basesremun'].create(vals)

                    # Adiciona o S-5011 ao Período do e-Social que gerou o S-1299 relacionado
                    periodo = self.env['sped.esocial'].search([
                        ('company_id', '=', self.company_id.id),
                        ('periodo_id', '=', self.periodo_id.id),
                    ])
                    periodo.inss_consolidado_ids = [(4, sped_intermediario.id)]

                if tot.tipo.valor == 'S5012':

                    # Busca o sped.registro que originou esse totalizador
                    sped_registro = self.env['sped.registro'].search([
                        ('registro', '=', 'S-1299'),
                        ('recibo', '=', tot.eSocial.evento.infoIRRF.nrRecArqBase.valor)
                    ])

                    # Busca pelo sped.registro deste totalizador (se ele já existir)
                    sped_s5012 = self.env['sped.registro'].search([
                        ('id_evento', '=', tot.eSocial.evento.Id.valor)
                    ])

                    # Busca pelo registro intermediário (se ele já existir)
                    sped_intermediario = self.env['sped.irrf.consolidado'].search([
                        ('id_evento', '=', tot.eSocial.evento.Id.valor)
                    ])

                    # Popula os valores para criar/alterar o registro intermediário do totalizador
                    vals_intermediario_totalizador = {
                        'company_id': sped_registro.company_id.id,
                        'id_evento': tot.eSocial.evento.Id.valor,
                        'periodo_id': sped_registro.origem_intermediario.periodo_id.id,
                        'ind_exist_info': tot.eSocial.evento.infoIRRF.indExistInfo.valor,
                        'sped_registro_s1299': sped_registro.id,
                    }

                    # Cria/Altera o registro intermediário
                    if sped_intermediario:
                        sped_intermediario.write(vals_intermediario_totalizador)
                    else:
                        sped_intermediario = self.env['sped.irrf.consolidado'].create(vals_intermediario_totalizador)

                    # Popula os valores para criar/alterar o sped.registro do totalizador
                    vals_registro_totalizador = {
                        'tipo': 'esocial',
                        'registro': 'S-5012',
                        'evento': 'evtIrrf',
                        'operacao': 'na',
                        'ambiente': sped_registro.ambiente,
                        'origem': ('sped.irrf.consolidado,%s' % sped_intermediario.id),
                        'origem_intermediario': ('sped.irrf.consolidado,%s' % sped_intermediario.id),
                        'company_id': sped_registro.company_id.id,
                        'id_evento': tot.eSocial.evento.Id.valor,
                        'situacao': '4',
                        'recibo': tot.eSocial.evento.infoIRRF.nrRecArqBase.valor,
                    }

                    # Cria/Altera o sped.registro do totalizador
                    if sped_s5012:
                        sped_s5012.write(vals_registro_totalizador)
                    else:
                        sped_s5012 = self.env['sped.registro'].create(vals_registro_totalizador)

                    # Popula o intermediário totalizador com o registro totalizador
                    sped_intermediario.sped_registro_s5012 = sped_s5012

                    # Popula o intermediário S1299 com o intermediário totalizador
                    self.s5012_id = sped_intermediario

                    # Popula o XML em anexo no sped.registro totalizador
                    if sped_s5012.consulta_xml_id:
                        consulta = sped_s5012.consulta_xml_id
                        sped_s5012.consulta_xml_id = False
                        consulta.unlink()
                    consulta_xml = tot.eSocial.xml
                    consulta_xml_nome = sped_s5012.id_evento + '-consulta.xml'
                    anexo_id = sped_registro._grava_anexo(consulta_xml_nome, consulta_xml)
                    sped_s5012.consulta_xml_id = anexo_id

                    # Limpa a tabela sped.irrf.consolidado.infocrcontrib
                    for infocrcontrib in sped_intermediario.infocrcontrib_ids:
                        infocrcontrib.unlink()

                    # Popula a tabela sped.irrf.consolidado.inocrcontrib com os valores apurados no S-5012
                    for infocrcontrib in tot.eSocial.evento.infoIRRF.infoCRContrib:

                        vals = {
                            'parent_id': sped_intermediario.id,
                            'tp_cr': infocrcontrib.tpCR.valor,
                            'vr_cr': infocrcontrib.vrCR.valor,
                        }

                        self.env['sped.irrf.consolidado.infocrcontrib'].create(vals)

                    # Adiciona o S-5012 ao Período do e-Social que gerou o S-1299 relacionado
                    periodo = self.env['sped.esocial'].search([
                        ('company_id', '=', self.company_id.id),
                        ('periodo_id', '=', self.periodo_id.id),
                    ])
                    periodo.irrf_consolidado_ids = [(4, sped_intermediario.id)]
