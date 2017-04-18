# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from .abstract_arquivos_governo import AbstractArquivosGoverno


class Grrf(AbstractArquivosGoverno):

    # Informações do Responsavel
    def _registro_00(self):
        registro_00 = self.tipo_de_registro_00
        registro_00 += str.ljust('', 51)
        registro_00 += self._validar(self.tipo_de_remessa, 1, 'N')
        registro_00 += \
            self._validar(self.tipo_inscricao_responsavel, 1, 'N') \
            if self.tipo_inscricao_responsavel \
            else self._validar(self.self.tipo_de_inscricao_empresa, 1, 'N')
        registro_00 += self._validar(self.inscricao_do_responsavel, 14, 'N') \
            if self.inscricao_do_responsavel \
            else self._validar(self.inscricao_da_empresa, 14, 'N')
        registro_00 += self._validar(self.razao_social_responsavel, 30, 'AN') \
            if self.razao_social_responsavel \
            else self._validar(self.razao_social_empresa, 30, 'AN')
        registro_00 += self._validar(self.nome_do_contato_responsavel, 20, 'A')
        registro_00 += self._validar(self.endereco_responsavel, 50) \
            if self.endereco_responsavel \
            else self._validar(self.endereco_empresa, 50)
        registro_00 += self._validar(self.bairro_responsavel, 20) \
            if self.bairro_responsavel \
            else self._validar(self.bairro_empresa, 20)
        registro_00 += self._validar(self.cep_responsavel, 8, 'N') \
            if self.cep_responsavel \
            else self._validar(self.cep_empresa, 8, 'N')
        registro_00 += self._validar(self.cidade_responsavel, 20, 'AN') \
            if self.cidade_responsavel \
            else self._validar(self.cidade_empresa, 20, 'AN')
        registro_00 += \
            self._validar(self.unidade_federacao_responsavel, 2, 'A') \
            if self.unidade_federacao_responsavel \
            else self._validar(self.unidade_federacao_empresa, 2, 'A')
        registro_00 += \
            self._validar(self.telefone_contato_responsavel, 12, 'N')
        registro_00 += self._validar(self.endereco_internet_responsavel, 60)
        registro_00 += self._validar(self.data_recolhimento_grrf, 8, 'D')
        registro_00 += str.ljust('', 60)
        registro_00 += self.final_de_linha
        return registro_00

    # Informações da Empresa
    def _registro_10(self):
        registro_10 = self.tipo_de_registro_10
        registro_10 += self._validar(self.tipo_de_inscricao_empresa, 1, 'N')
        registro_10 += self._validar(self.inscricao_da_empresa, 14, 'N')
        registro_10 += ''.rjust(36, '0')
        registro_10 += self._validar(self.razao_social_empresa, 40, 'AN')
        registro_10 += self._validar(self.endereco_empresa, 50, 'AN')
        registro_10 += self._validar(self.bairro_empresa, 20, 'AN')
        registro_10 += self._validar(self.cep_empresa, 8, 'N')
        registro_10 += self._validar(self.cidade_empresa, 20, 'AN')
        registro_10 += self._validar(self.unidade_federacao_empresa, 2, 'A')
        registro_10 += self._validar(self.telefone_empresa, 12, 'N')
        registro_10 += self._validar(self.CNAE_fiscal, 7, 'N')
        registro_10 += self._validar(self.simples, 1, 'N')
        registro_10 += self._validar(self.fpas, 3, 'N')
        registro_10 += str.ljust('', 143)
        registro_10 += self.final_de_linha
        return registro_10

    # Informações do trabalhador
    def _registro_40(self):
        registro_40 = self.tipo_de_registro_40
        registro_40 += \
            self._validar(self.tipo_de_inscricao_trabalhador, 1, 'N') \
            if self.tipo_de_inscricao_trabalhador \
            else self._validar(self.tipo_de_inscricao_empresa, 1, 'N')
        registro_40 += self._validar(self.inscricao_do_trabalhador, 14, 'N') \
            if self.inscricao_do_trabalhador \
            else self._validar(self.inscricao_da_empresa, 14, 'N')
        registro_40 += self._validar(self.tipo_inscricao_tomador, 1, 'N')
        registro_40 += self._validar(self.inscricao_tomador, 14, 'N')
        registro_40 += self._validar(self.PIS_PASEP, 11, 'N')
        registro_40 += self._validar(self.data_admissao, 8, 'D')
        registro_40 += self._validar(self.categoria_trabalhador, 2, 'N')
        registro_40 += self._validar(self.nome_do_trabalhador, 70, 'A')
        registro_40 += self._validar(self.numero_ctps, 7, 'N')
        registro_40 += self._validar(self.serie_ctps, 5, 'N')
        registro_40 += self._validar(self.sexo, 1, 'N')
        registro_40 += self._validar(self.grau_de_instrucao, 2, 'N')
        registro_40 += self._validar(self.data_nascimento, 8, 'D')
        registro_40 += self._validar(self.qtd_horas_trabalhadas_semana, 2, 'N')
        registro_40 += self._validar(self.CBO, 6, 'AN')
        registro_40 += self._validar(self.data_opcao, 8, 'D')
        registro_40 += self._validar(self.codigo_da_movimentacao, 2, 'AN')
        registro_40 += self._validar(self.data_movimentacao, 8, 'D')
        registro_40 += self._validar(self.codigo_de_saque, 3, 'AN')
        registro_40 += self._validar(self.aviso_previo, 1, 'N')
        registro_40 += self._validar(self.data_inicio_aviso_previo, 8, 'D')
        registro_40 += self._validar(self.reposicao_de_vaga, 1, 'A')
        registro_40 += self._validar(self.data_homologacao_dissidio, 8, 'D')
        registro_40 += self._validar(self.valor_dissidio, 15, 'V')
        registro_40 += self._validar(self.remuneracao_mes_aterior, 15, 'V')
        registro_40 += self._validar(self.remuneracao_mes_rescisao, 15, 'V')
        registro_40 += self._validar(self.aviso_previo_indenizado, 15, 'V')
        registro_40 += \
            self._validar(self.indicativo_pensao_alimenticia, 1, 'A')
        registro_40 += \
            self._validar(self.percentual_pensao_alimenticia, 5, 'V')
        registro_40 += self._validar(self.valor_pensao_alimenticia, 15, 'V')
        registro_40 += self._validar(self.CPF, 11, 'N')
        registro_40 += self._validar(self.banco_conta_trabalhador, 3, 'N')
        registro_40 += self._validar(self.agencia_trabalhador, 4, 'N')
        registro_40 += self._validar(self.conta_trabalhador, 13, 'N')
        registro_40 += self._validar(self.saldo_para_fins_rescisorios, 15, 'N')
        registro_40 += str.ljust('', 39)
        registro_40 += self.final_de_linha
        return registro_40

    def _registro_90(self):
        registro_90 = self.tipo_de_registro_90
        registro_90 += self.marca_final_de_registro
        registro_90 += str.ljust('', 306)
        registro_90 += self.final_de_linha
        return registro_90

    def _gerar_grrf(self):
        return \
            self._registro_00() + \
            self._registro_10() + \
            self._registro_40() + \
            self._registro_90()

    # campos do registro 00 ---------------------------------------------------
    tipo_de_registro_00 = u'00'         # sempre '00'
    tipo_de_remessa = u'2'              # 2 - GRRF | 4 - Comunicar movimentação
    tipo_inscricao_responsavel = u'1'   # 1 - CNPJ | 2 - CEI
    inscricao_do_responsavel = ''       # CNPJ | CEI
    razao_social_responsavel = ''
    nome_do_contato_responsavel = ''
    endereco_responsavel = ''
    bairro_responsavel = ''
    cep_responsavel = ''
    cidade_responsavel = ''
    unidade_federacao_responsavel = ''
    telefone_contato_responsavel = ''
    endereco_internet_responsavel = ''
    data_recolhimento_grrf = ''
    final_de_linha = u'*'
    # -------------------------------------------------------------------------

    # campos do registro 10 ---------------------------------------------------
    tipo_de_registro_10 = u'10'            # sempre '10'
    tipo_de_inscricao_empresa = u'1'
    inscricao_da_empresa = ''              # CNPJ | CEI
    razao_social_empresa = ''
    endereco_empresa = ''
    bairro_empresa = ''
    cep_empresa = ''
    cidade_empresa = ''
    unidade_federacao_empresa = ''
    telefone_empresa = ''
    CNAE_fiscal = ''
    simples = ''
    fpas = ''
    # ------------------------------------------------------------------------

    # campos do registro 40 ---------------------------------------------------
    tipo_de_registro_40 = u'40'            # sempre '40'
    tipo_de_inscricao_trabalhador = u'1'
    inscricao_do_trabalhador = ''
    tipo_inscricao_tomador = ''
    inscricao_tomador = ''
    PIS_PASEP = ''
    data_admissao = ''                     # DDMMAAAA
    categoria_trabalhador = u'01'
    nome_do_trabalhador = ''
    numero_ctps = ''
    serie_ctps = ''
    sexo = ''
    grau_de_instrucao = ''
    data_nascimento = ''
    qtd_horas_trabalhadas_semana = ''
    CBO = ''
    data_opcao = ''
    codigo_da_movimentacao = ''
    data_movimentacao = ''
    codigo_de_saque = ''
    aviso_previo = ''
    data_inicio_aviso_previo = ''
    reposicao_de_vaga = ''
    data_homologacao_dissidio = ''
    valor_dissidio = ''
    remuneracao_mes_aterior = ''
    remuneracao_mes_rescisao = ''
    aviso_previo_indenizado = ''
    indicativo_pensao_alimenticia = ''
    percentual_pensao_alimenticia = ''
    valor_pensao_alimenticia = ''
    CPF = ''
    banco_conta_trabalhador = ''
    agencia_trabalhador = ''
    conta_trabalhador = ''
    saldo_para_fins_rescisorios = ''
    # ------------------------------------------------------------------------

    # campos do registro 90 ---------------------------------------------------
    tipo_de_registro_90 = u'90'            # sempre '90'
    marca_final_de_registro = ''.rjust(51, '9')
    # ------------------------------------------------------------------------
