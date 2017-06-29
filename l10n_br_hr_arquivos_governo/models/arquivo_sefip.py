# -*- coding: utf-8 -*-
# (c) 2017 KMEE INFORMATICA LTDA - Daniel Sadamo <sadamo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from .abstract_arquivos_governo import AbstractArquivosGoverno
import re

_logger = logging.getLogger(__name__)

try:
    from pybrasil.base import tira_acentos
    from pybrasil import data
except ImportError:
    _logger.info('Cannot import pybrasil')


class SEFIP(AbstractArquivosGoverno):

    def _registro_00_informacoes_responsavel(self):
        registro_00 = self.tipo_de_registro_00
        registro_00 += self._validar(self.preenche_brancos, 51, 'AN')
        registro_00 += self._validar(self.tipo_remessa, 1, 'N')
        registro_00 += self._validar(self.tipo_inscr_resp, 1, 'N')
        registro_00 += self._validar(self.inscr_resp, 14, 'N')
        registro_00 += self._validar(self.nome_resp, 30, 'AN')
        registro_00 += self._validar(self.nome_contato, 20, 'A')
        registro_00 += self._validar(self.arq_logradouro, 50, 'AN')
        registro_00 += self._validar(self.arq_bairro, 20, 'AN')
        registro_00 += self._validar(self.arq_cep, 8, 'N')
        registro_00 += self._validar(self.arq_cidade, 20, 'AN')
        registro_00 += self._validar(self.arq_uf, 2, 'A')
        registro_00 += self._validar(self.tel_contato, 12, 'N')
        registro_00 += self._validar(self.internet_contato, 60, 'AN')
        registro_00 += self._validar(self.competencia, 6, 'D')
        registro_00 += self._validar(self.cod_recolhimento, 3, 'N')
        registro_00 += self._validar(self.indic_recolhimento_fgts, 1, 'N')
        registro_00 += self._validar(self.modalidade_arq, 1, 'N')
        registro_00 += self._validar(self.data_recolhimento_fgts, 8, 'D')
        registro_00 += self._validar(self.indic_recolh_ps, 1, 'N')
        registro_00 += self._validar(self.data_recolh_ps, 8, 'D')
        registro_00 += self._validar(self.indice_recolh_atraso_ps, 7, 'N')
        registro_00 += self._validar(self.tipo_inscr_fornec, 1, 'N')
        registro_00 += self._validar(self.inscr_fornec, 14, 'N')
        registro_00 += self._validar(self.preenche_brancos, 18, 'AN')
        registro_00 += self._validar(self.fim_linha, 1, 'AN')
        return registro_00

    def _registro_10_informacoes_empresa(self):
        registro_10 = self.tipo_de_registro_10
        registro_10 += self._validar(self.tipo_inscr_empresa, 1, 'N')
        registro_10 += self._validar(self.inscr_empresa, 14, 'N')
        registro_10 += self._validar(self.preenche_zeros, 36, 'V')
        registro_10 += self._validar(self.emp_nome_razao_social, 40, 'AN')
        registro_10 += self._validar(self.emp_logradouro, 50, 'AN')
        registro_10 += self._validar(self.emp_bairro, 20, 'AN')
        registro_10 += self._validar(self.emp_cep, 8, 'N')
        registro_10 += self._validar(self.emp_cidade, 20, 'AN')
        registro_10 += self._validar(self.emp_uf, 2, 'A')
        registro_10 += self._validar(self.emp_tel, 12, 'N')
        registro_10 += self._validar(self.emp_indic_alteracao_endereco, 1, 'A')
        registro_10 += self._validar(self.emp_cnae, 7, 'N')
        registro_10 += self._validar(self.emp_indic_alteracao_cnae, 1, 'A')
        registro_10 += self._validar(self.emp_aliquota_RAT, 2, 'N')
        registro_10 += self._validar(self.emp_cod_centralizacao, 1, 'N')
        registro_10 += self._validar(self.emp_simples, 1, 'N')
        registro_10 += self._validar(self.emp_FPAS, 3, 'N')
        registro_10 += self._validar(self.emp_cod_outras_entidades, 4, 'N')
        registro_10 += self._validar(self.emp_cod_pagamento_GPS, 4, 'N')
        registro_10 += self._validar(
            self.emp_percent_isencao_filantropia, 5, 'N')
        registro_10 += self._validar(self.emp_salario_familia, 15, 'V')
        registro_10 += self._validar(self.emp_salario_maternidade, 15, 'V')
        registro_10 += self._validar(
            self.emp_contrib_descont_empregados, 15, 'V')
        registro_10 += self._validar(self.emp_indic_valor_pos_neg, 1, 'V')
        registro_10 += self._validar(
            self.emp_valor_devido_ps_referente, 14, 'V')
        registro_10 += self._validar(self.emp_banco, 3, 'N')
        registro_10 += self._validar(self.emp_ag, 4, 'N')
        registro_10 += self._validar(self.emp_cc, 9, 'AN')
        registro_10 += self._validar(self.preenche_zeros, 45, 'V')
        registro_10 += self._validar(self.preenche_brancos, 4, 'AN')
        registro_10 += self._validar(self.fim_linha, 1, 'AN')
        return registro_10

    def _registro_12_inf_adic_recolhimento_empresa(self):
        registro_12 = self.tipo_de_registro_12
        registro_12 += self._validar(self.tipo_inscr_empresa, 1, 'N')
        registro_12 += self._validar(self.inscr_empresa, 14, 'N')
        registro_12 += self._validar(self.preenche_zeros, 36, 'V')
        registro_12 += self._validar(self.ded_13_lic_maternidade, 15, 'V')
        registro_12 += self._validar(self.receita_evento_desp_patroc, 15, 'V')
        registro_12 += self._validar(self.indic_orig_receita, 1, 'AN')
        registro_12 += self._validar(self.comercializacao_producao_pf, 15, 'V')
        registro_12 += self._validar(self.comercializacao_producao_pj, 15, 'V')
        registro_12 += self._validar(self.rec_outras_info_processo, 11, 'N')
        registro_12 += self._validar(self.rec_outras_info_processo_ano, 4, 'N')
        registro_12 += self._validar(self.rec_outras_info_vara_JCJ, 5, 'N')
        registro_12 += self._validar(
            self.rec_outras_info_periodo_inicio, 6, 'D')
        registro_12 += self._validar(self.rec_outras_info_periodo_fim, 6, 'D')
        registro_12 += self._validar(self.compensacao_valor_corrigido, 15, 'V')
        registro_12 += self._validar(self.compensacao_periodo_inicio, 6, 'D')
        registro_12 += self._validar(self.compensacao_periodo_fim, 6, 'D')
        registro_12 += self._validar(
            self.recolh_competencias_ant_folha_inss, 15, 'V')
        registro_12 += self._validar(
            self.recolh_competencias_ant_folha_outras_ent, 15, 'V')
        registro_12 += self._validar(
            self.recolh_competencias_ant_comerc_prod_inss, 15, 'V')
        registro_12 += self._validar(
            self.recolh_competencias_ant_comerc_prod_outras_ent, 15, 'V')
        registro_12 += self._validar(
            self.recolh_competencias_ant_eventos_desport_inss, 15, 'V')
        registro_12 += self._validar(
            self.inf_adic_tomador_parc_fgts_cat_01_02_03_05_06, 15, 'V')
        registro_12 += self._validar(
            self.inf_adic_tomador_parc_fgts_cat_04_07, 15, 'V')
        registro_12 += self._validar(self.parc_fgts_valor_recolhido, 15, 'V')
        registro_12 += self._validar(
            self.vlr_pago_cooperativas_trabalho, 15, 'V')
        registro_12 += self._validar(self.preenche_zeros, 45, 'V')
        registro_12 += self._validar(self.preenche_brancos, 6, 'AN')
        registro_12 += self._validar(self.fim_linha, 1, 'AN')
        return registro_12

    def _registro_13_alteracao_cadastral_trabalhador(self):
        registro_13 = self.tipo_de_registro_13
        registro_13 += self._validar(self.tipo_inscr_empresa, 1, 'N')
        registro_13 += self._validar(self.inscr_empresa, 14, 'N')
        registro_13 += self._validar(self.preenche_zeros, 36, 'V')
        registro_13 += self._validar(self.pis_pasep_ci, 11, 'N')
        registro_13 += self._validar(self.data_admissao, 8, 'D')
        registro_13 += self._validar(self.categoria_trabalhador, 2, 'N')
        registro_13 += self._validar(self.matricula_trabalhador, 11, 'N')
        registro_13 += self._validar(self.num_ctps, 7, 'N')
        registro_13 += self._validar(self.serie_ctps, 5, 'N')
        registro_13 += self._validar(self.nome_trabalhador, 70, 'A')
        registro_13 += self._validar(self.codigo_empresa_caixa, 14, 'N')
        registro_13 += self._validar(self.codigo_trabalhador_caixa, 11, 'N')
        registro_13 += self._validar(self.codigo_alteracao_cadastral, 3, 'N')
        registro_13 += self._validar(self.novo_conteudo_campo, 70, 'AN')
        registro_13 += self._validar(self.preenche_brancos, 94, 'AN')
        registro_13 += self._validar(self.fim_linha, 1, 'AN')
        return registro_13

    def _registro_14_inclusao_alteracao_endereco_trabalhador(self):
        registro_14 = self.tipo_de_registro_14
        registro_14 += self._validar(self.tipo_inscr_empresa, 2, 'N')
        registro_14 += self._validar(self.inscr_empresa, 14, 'N')
        registro_14 += self._validar(self.preenche_zeros, 36, 'V')
        registro_14 += self._validar(self.pis_pasep_ci, 11, 'N')
        registro_14 += self._validar(self.data_admissao, 8, 'D')
        registro_14 += self._validar(self.categoria_trabalhador, 2, 'N')
        registro_14 += self._validar(self.nome_trabalhador, 70, 'A')
        registro_14 += self._validar(self.num_ctps, 7, 'N')
        registro_14 += self._validar(self.serie_ctps, 5, 'N')
        registro_14 += self._validar(self.trabalhador_logradouro, 50, 'AN')
        registro_14 += self._validar(self.trabalhador_bairro, 20, 'AN')
        registro_14 += self._validar(self.trabalhador_cep, 8, 'N')
        registro_14 += self._validar(self.trabalhador_cidade, 20, 'AN')
        registro_14 += self._validar(self.trabalhador_uf, 2, 'A')
        registro_14 += self._validar(self.preenche_brancos, 103, 'AN')
        registro_14 += self._validar(self.fim_linha, 1, 'AN')
        return registro_14

    def _registro_20_tomador_de_servico_ou_obra_contrucao_civil(self):
        registro_20 = self.tipo_de_registro_20
        registro_20 += self._validar(self.tipo_inscr_empresa, 1, 'N')
        registro_20 += self._validar(self.inscr_empresa, 14, 'N')
        registro_20 += self._validar(self.tipo_inscr_tomador, 1, 'N')
        registro_20 += self._validar(self.inscr_tomador, 14, 'N')
        registro_20 += self._validar(self.preenche_zeros, 21, 'V')
        registro_20 += self._validar(self.nome_tomador, 40, 'AN')
        registro_20 += self._validar(self.tomador_logradouro, 50, 'AN')
        registro_20 += self._validar(self.tomador_bairro, 20, 'AN')
        registro_20 += self._validar(self.tomador_cep, 8, 'N')
        registro_20 += self._validar(self.tomador_cidade, 20, 'AN')
        registro_20 += self._validar(self.tomador_uf, 2, 'A')
        registro_20 += self._validar(self.tomador_cod_gps, 4, 'N')
        registro_20 += self._validar(self.tomador_salario_familia, 15, 'V')
        registro_20 += self._validar(
            self.preenche_zeros, 15, 'V')
        registro_20 += self._validar(self.preenche_zeros, 1, 'V')
        registro_20 += self._validar(self.preenche_zeros, 14, 'V')
        registro_20 += self._validar(self.tomador_valor_retencao, 15, 'V')
        registro_20 += self._validar(self.tomador_faturas_emitidas, 15, 'V')
        registro_20 += self._validar(self.preenche_zeros, 45, 'V')
        registro_20 += self._validar(self.preenche_brancos, 42, 'AN')
        registro_20 += self._validar(self.fim_linha, 1, 'AN')
        return registro_20

    def _registro_21_informacoes_adicionais_tomador_de_servico(self):
        registro_21 = self.tipo_de_registro_21
        registro_21 += self._validar(self.tipo_inscr_empresa, 1, 'N')
        registro_21 += self._validar(self.inscr_empresa, 14, 'N')
        registro_21 += self._validar(self.tipo_inscr_tomador, 1, 'N')
        registro_21 += self._validar(self.inscr_tomador, 14, 'N')
        registro_21 += self._validar(self.preenche_zeros, 21, 'V')
        registro_21 += self._validar(
            self.inf_adic_tomador_compensacao_corrigido, 15, 'V')
        registro_21 += self._validar(
            self.inf_adic_tomador_compensacao_periodo_inicio, 6, 'D')
        registro_21 += self._validar(
            self.inf_adic_tomador_compensacao_periodo_fim, 6, 'D')
        registro_21 += self._validar(
            self.inf_adic_tomador_recolh_compet_ant_inss, 15, 'V')
        registro_21 += self._validar(
            self.inf_adic_tomador_recolh_compet_ant_outras_ent, 15, 'V')
        registro_21 += self._validar(
            self.inf_adic_tomador_parc_fgts_cat_01_02_03_05_06, 15, 'V')
        registro_21 += self._validar(
            self.inf_adic_tomador_parc_fgts_cat_04_07, 15, 'V')
        registro_21 += self._validar(
            self.inf_adic_tomador_parc_fgts_vlr_recolhido, 15, 'V')
        registro_21 += self._validar(self.preenche_brancos, 204, 'AN')
        registro_21 += self._validar(self.fim_linha, 1, 'AN')
        return registro_21

    def _registro_30_registro_do_trabalhador(self):
        registro_30 = self.tipo_de_registro_30
        registro_30 += self._validar(self.tipo_inscr_empresa, 1, 'N')
        registro_30 += self._validar(self.inscr_empresa, 14, 'N')
        registro_30 += self._validar(self.tipo_inscr_tomador, 1, 'N')
        registro_30 += self._validar(self.inscr_tomador, 14, 'N')
        registro_30 += self._validar(self.pis_pasep_ci, 11, 'N')
        registro_30 += self._validar(self.data_admissao, 8, 'D')
        registro_30 += self._validar(self.categoria_trabalhador, 2, 'N')
        registro_30 += self._validar(self.nome_trabalhador, 70, 'A')
        registro_30 += self._validar(self.matricula_trabalhador, 11, 'N')
        registro_30 += self._validar(self.num_ctps, 7, 'N')
        registro_30 += self._validar(self.serie_ctps, 5, 'N')
        registro_30 += self._validar(self.data_de_opcao, 8, 'D')
        registro_30 += self._validar(self.data_de_nascimento, 8, 'D')
        registro_30 += self._validar(self.trabalhador_cbo, 5, 'AN')
        registro_30 += self._validar(self.trabalhador_remun_sem_13, 15, 'V')
        registro_30 += self._validar(self.trabalhador_remun_13, 15, 'V')
        registro_30 += self._validar(self.trabalhador_classe_contrib, 2, 'N')
        registro_30 += self._validar(self.trabalhador_ocorrencia, 2, 'N')
        registro_30 += self._validar(
            self.trabalhador_valor_desc_segurado, 15, 'V')
        registro_30 += self._validar(
            self.trabalhador_remun_base_calc_contribuicao_previdenciaria,
            15, 'V')
        registro_30 += self._validar(
            self.trabalhador_base_calc_13_previdencia_competencia, 15, 'V')
        registro_30 += self._validar(
            self.trabalhador_base_calc_13_previdencia_GPS, 15, 'V')
        registro_30 += self._validar(self.preenche_brancos, 98, 'AN')
        registro_30 += self._validar(self.fim_linha, 1, 'AN')
        return registro_30

    def _registro_32_movimentacao_do_trabalhador(self):
        registro_32 = self.tipo_de_registro_32
        registro_32 += self._validar(self.tipo_inscr_empresa, 1, 'N')
        registro_32 += self._validar(self.inscr_empresa, 14, 'N')
        registro_32 += self._validar(self.tipo_inscr_tomador, 1, 'N')
        registro_32 += self._validar(self.inscr_tomador, 14, 'N')
        registro_32 += self._validar(self.pis_pasep_ci, 11, 'N')
        registro_32 += self._validar(self.data_admissao, 8, 'D')
        registro_32 += self._validar(self.categoria_trabalhador, 2, 'N')
        registro_32 += self._validar(self.nome_trabalhador, 70, 'A')
        registro_32 += self._validar(
            self.trabalhador_codigo_movimentacao, 2, 'AN')
        registro_32 += self._validar(
            self.trabalhador_data_movimentacao, 8, 'D')
        registro_32 += self._validar(
            self.trabalhador_indic_recolhimento_fgts, 1, 'AN')
        registro_32 += self._validar(self.preenche_brancos, 225, 'AN')
        registro_32 += self._validar(self.fim_linha, 1, 'AN')
        return registro_32

    # PARA IMPLEMENTAÇAO FUTURA
    # def _registro_50_(self):
    #     pass
    #
    # def _registro_51_(self):
    #     pass

    def _registro_90_totalizador_do_arquivo(self):
        registro_90 = self.tipo_de_registro_90
        registro_90 += self._validar(self.marca_de_final_registro, 51, 'AN')
        registro_90 += self._validar(self.preenche_brancos, 306, 'AN')
        registro_90 += self._validar(self.fim_linha, 1, 'AN')
        return registro_90

    def __init__(self, *args, **kwargs):
        # campos gerais--------------------------------------------------------
        self.preenche_zeros = '0' #DEVE SER SEMPRE PASSADO COM TIPO 'V'
        self.preenche_brancos = ''
        self.fim_linha = '*'
        self.tipo_inscr_empresa = '1'
        self.inscr_empresa = ''
        # campos do HEADER  ARQUIVO--------------------------------------------
        self.tipo_de_registro_00 = '00'
        self.tipo_remessa = '1'
        self.tipo_inscr_resp = '1'
        self.inscr_resp = ''
        self.nome_resp = ''
        self.nome_contato = ''
        self.arq_logradouro = ''
        self.arq_bairro = ''
        self.arq_cep = ''
        self.arq_cidade = ''
        self.arq_uf = ''
        self.tel_contato = ''
        self.internet_contato = ''
        self.competencia = ''
        self.cod_recolhimento = ''
        self.indic_recolhimento_fgts = ''
        self.modalidade_arq = ''
        self.data_recolhimento_fgts = '        '
        self.indic_recolh_ps = ''
        self.data_recolh_ps = '        '
        self.indice_recolh_atraso_ps = ''
        self.tipo_inscr_fornec = ''
        self.inscr_fornec = ''
        # campos HEADER EMPRESA------------------------------------------------
        self.tipo_de_registro_10 = '10'
        self.emp_nome_razao_social = ''
        self.emp_logradouro = ''
        self.emp_bairro = ''
        self.emp_cep = ''
        self.emp_cidade = ''
        self.emp_uf = ''
        self.emp_tel = ''
        self.emp_indic_alteracao_endereco = 'N'
        self.emp_cnae = ''
        self.emp_indic_alteracao_cnae = 'N'
        self.emp_aliquota_RAT = ''
        self.emp_cod_centralizacao = ''
        self.emp_simples = '1'
        self.emp_FPAS = ''
        self.emp_cod_outras_entidades = ''
        self.emp_cod_pagamento_GPS = ''
        self.emp_percent_isencao_filantropia = ''
        self.emp_salario_familia = ''
        self.emp_salario_maternidade = ''
        self.emp_contrib_descont_empregados = ''
        self.emp_indic_valor_pos_neg = ''
        self.emp_valor_devido_ps_referente = ''
        self.emp_banco = ''
        self.emp_ag = ''
        self.emp_cc = ''
        # campos do RECOLHIMENTO DA EMPRESA -----------------------------------
        self.tipo_de_registro_12 = '12'
        self.ded_13_lic_maternidade = ''
        self.receita_evento_desp_patroc = ''
        self.indic_orig_receita = ''
        self.comercializacao_producao_pf = ''
        self.comercializacao_producao_pj = ''
        self.rec_outras_info_processo = ''
        self.rec_outras_info_processo_ano = ''
        self.rec_outras_info_vara_JCJ = ''
        self.rec_outras_info_periodo_inicio = ''
        self.rec_outras_info_periodo_fim = ''
        self.compensacao_valor_corrigido = ''
        self.compensacao_periodo_inicio = ''
        self.compensacao_periodo_fim = ''
        self.recolh_competencias_ant_folha_inss = ''
        self.recolh_competencias_ant_folha_outras_ent = ''
        self.recolh_competencias_ant_comerc_prod_inss = ''
        self.recolh_competencias_ant_comerc_prod_outras_ent = ''
        self.recolh_competencias_ant_eventos_desport_inss = ''
        self.parc_fgts_soma_remuneracao = ''
        self.parc_fgts_valor_recolhido = ''
        self.vlr_pago_cooperativas_trabalho = ''
        # campos gerais do TRABALHADOR ----------------------------------------
        self.pis_pasep_ci = ''
        self.data_admissao = '        '
        self.categoria_trabalhador = ''
        self.num_ctps = ''
        self.serie_ctps = ''
        self.nome_trabalhador = ''
        self.matricula_trabalhador = ''
        # campos ALTERACAO CADASTRAL TRABALHADOR ------------------------------
        self.tipo_de_registro_13 = '13'
        self.codigo_empresa_caixa = ''
        self.codigo_trabalhador_caixa = ''
        self.codigo_alteracao_cadastral = ''
        self.novo_conteudo_campo = ''
        # campos INCLUSAO/ALTERACAO ENDERECO TRABALHADOR ----------------------
        self.tipo_de_registro_14 = '14'
        self.trabalhador_logradouro = ''
        self.trabalhador_bairro = ''
        self.trabalhador_cep = ''
        self.trabalhador_cidade = ''
        self.trabalhador_uf = ''
        # campos gerais TOMADOR DE SERVICO/OBRA DE CONSTRUCAO CIVIL------------
        self.tipo_inscr_tomador = ''
        self.inscr_tomador = ''
        # campos TOMADOR DE SERVICO/OBRA DE CONSTRUCAO CIVIL ------------------
        self.tipo_de_registro_20 = '20'
        self.nome_tomador = ''
        self.tomador_logradouro = ''
        self.tomador_bairro = ''
        self.tomador_cep = ''
        self.tomador_cidade = ''
        self.tomador_uf = ''
        self.tomador_cod_gps = ''
        self.tomador_salario_familia = ''
        self.tomador_contrib_desc_empregado_13 = ''
        self.tomador_valor_retencao = ''
        self.tomador_faturas_emitidas = ''
        # campos INFORMACOES ADICIONAIS TOMADOR DE SERVICO/OBRA DE CONST-------
        self.tipo_de_registro_21 = '21'
        self.inf_adic_tomador_compensacao_corrigido = ''
        self.inf_adic_tomador_compensacao_periodo_inicio = ''
        self.inf_adic_tomador_compensacao_periodo_fim = ''
        self.inf_adic_tomador_recolh_compet_ant_inss = ''
        self.inf_adic_tomador_recolh_compet_ant_outras_ent = ''
        self.inf_adic_tomador_parc_fgts_cat_01_02_03_05_06 = ''
        self.inf_adic_tomador_parc_fgts_cat_04_07 = ''
        self.inf_adic_tomador_parc_fgts_vlr_recolhido = ''
        # campos REGISTRO DO TRABALHADOR --------------------------------------
        self.tipo_de_registro_30 = '30'
        self.data_de_opcao = '        '
        self.data_de_nascimento = '        '
        self.trabalhador_cbo = ''
        self.trabalhador_remun_sem_13 = ''
        self.trabalhador_remun_13 = ''
        self.trabalhador_classe_contrib = ''
        self.trabalhador_ocorrencia = ''
        self.trabalhador_valor_desc_segurado = ''
        self.trabalhador_remun_base_calc_contribuicao_previdenciaria = ''
        self.trabalhador_base_calc_13_previdencia_competencia = ''
        self.trabalhador_base_calc_13_previdencia_GPS = ''
        # campos MOVIMENTACAO DO TRABALHADOR
        self.tipo_de_registro_32 = '32'
        self.trabalhador_codigo_movimentacao = ''
        self.trabalhador_data_movimentacao = '        '
        self.trabalhador_indic_recolhimento_fgts = ''
        # campos registro 50 - IMPLEMENTACAO FUTURA
        # campos registro 51  - IMPLEMENTACAO FUTURA

        # campos REGISTRO TOTALIZADOR DO ARQUIVO
        self.tipo_de_registro_90 = '90'
        self.marca_de_final_registro = '9' * 51

    def _validar(self, word, tam, tipo='AN'):
        """
        Função Genérica utilizada para validação de campos que são gerados
        nos arquivos TXT's
        :param word:
        :param tam:
        :param tipo:
        :return:
        """
        if not word:
            word = u''

        if tipo == 'A':         # Alfabetico
            word = tira_acentos(unicode(word))
            # tirar tudo que nao for letra do alfabeto
            word = re.sub('[^a-zA-Z]', ' ', word)
            # Retirar 2 espaços seguidos
            word = re.sub('[ ]+', ' ', word)
            return unicode.ljust(unicode(word), tam)[:tam]

        elif tipo == 'D':       # Data
            # Retira tudo que nao for numeral
            data = re.sub(u'[^0-9]', '', str(word))
            return unicode.ljust(unicode(data), tam)[:tam]

        elif tipo == 'V':       # Valor
            # Pega a parte decimal como inteiro e nas duas ultimas casas
            word = int(word * 100) if word else 0
            # Preenche com zeros a esquerda
            word = str(word).zfill(tam)
            return word[:tam]

        elif tipo == 'N':       # Numerico
            # Preenche com brancos a esquerda
            word = re.sub('[^0-9]', '', str(word))
            # word = str(word).zfill(tam)
            # return word[:tam]
            return unicode.rjust(unicode(word), tam)[:tam]

        elif tipo == 'AN':      # Alfanumerico
            # Tira acentos da palavras
            word = tira_acentos(unicode(word))
            # Preenche com espaço vazio a direita
            return unicode.ljust(unicode(word), tam)[:tam]
