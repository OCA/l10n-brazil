# -*- coding: utf-8 -*-
# (c) 2017 KMEE- Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from .abstract_arquivos_governo import AbstractArquivosGoverno


class Caged(AbstractArquivosGoverno):

    # Registro do estabelecimento responsável pela informação no
    # meio magnético (autorizado).
    def _registro_A(self):
        registro_A = self.A_tipo_de_registro
        registro_A += self._validar(self.A_tipo_layout)
        registro_A += self._validar(self.A_alteracao)
        registro_A += self._validar(self.A_sequencia)
        registro_A += self._validar(self.A_tipo_identificador)
        registro_A += self._validar(self.A_identificador_autorizado)
        registro_A += self._validar(self.A_razao_social)
        registro_A += self._validar(self.A_endereco)
        registro_A += self._validar(self.A_cep)
        registro_A += self._validar(self.A_uf)
        registro_A += self._validar(self.A_ddd)
        registro_A += self._validar(self.A_telefone)
        registro_A += self._validar(self.A_ramal)
        registro_A += self._validar(self.A_total_estabelecimento_informados)
        registro_A += self._validar(self.A_total_movimentacoes_informados)
        
    # Informações da Empresa
    def _registro_B(self):
        registro_B = self.B_tipo_de_registro
        registro_B += self._validar(self.B_tipo_identificador)
        registro_B += self._validar(self.B_identificador_estabelecimento)
        registro_B += self._validar(self.B_sequencia)
        registro_B += self._validar(self.B_primeira_declaracao )
        registro_B += self._validar(self.B_alteracao)
        registro_B += self._validar(self.B_cep)
        registro_B += self._validar(self.B_razao_social)
        registro_B += self._validar(self.B_endereco)
        registro_B += self._validar(self.B_bairro)
        registro_B += self._validar(self.B_uf)
        registro_B += self._validar(self.B_total_empregados_existentes )
        registro_B += self._validar(self.B_porte_estabelecimento )
        registro_B += self._validar(self.B_CNAE )
        registro_B += self._validar(self.B_ddd)
        registro_B += self._validar(self.B_telefone)
        registro_B += self._validar(self.B_email)
        return registro_B

    # Informações do trabalhador
    def _registro_C(self):
        registro_C = self.C_tipo_identificador
        registro_C += self._validar(self.C_identificador_estabelecimento)
        registro_C += self._validar(self.C_sequencia)
        registro_C += self._validar(self.C_PIS_PASEP)
        registro_C += self._validar(self.C_sexo)
        registro_C += self._validar(self.C_nascimento)
        registro_C += self._validar(self.C_grau_instrucao)
        registro_C += self._validar(self.C_salario_mensal)
        registro_C += self._validar(self.C_horas_trabalhadas)
        registro_C += self._validar(self.C_admissao)
        registro_C += self._validar(self.C_tipo_de_movimento)
        registro_C += self._validar(self.C_dia_desligamento)
        registro_C += self._validar(self.C_nome_empregado)
        registro_C += self._validar(self.C_numero_ctps)
        registro_C += self._validar(self.C_serie_ctps)
        registro_C += self._validar(self.C_uf_ctps)
        registro_C += self._validar(self.C_raca_cor)
        registro_C += self._validar(self.C_pessoas_com_deficiencia)
        registro_C += self._validar(self.C_cbo2000)
        registro_C += self._validar(self.C_aprendiz)
        registro_C += self._validar(self.C_tipo_deficiencia)
        registro_C += self._validar(self.C_CPF)
        registro_C += self._validar(self.C_cep_residencia)
        return registro_C

    def _registro_X(self):
        registro_X = self.X_tipo_de_registro
        registro_X += self._validar(self.X_tipo_identificador)
        registro_X += self._validar(self.X_identificador_estabelecimento)
        registro_X += self._validar(self.X_sequencia)
        registro_X += self._validar(self.X_PIS_PASEP)
        registro_X += self._validar(self.X_sexo)
        registro_X += self._validar(self.X_nascimento)
        registro_X += self._validar(self.X_grau_instrucao)
        registro_X += self._validar(self.X_salario_mensal)
        registro_X += self._validar(self.X_horas_trabalhadas)
        registro_X += self._validar(self.X_admissao)
        registro_X += self._validar(self.X_tipo_de_movimento)
        registro_X += self._validar(self.X_dia_desligamento)
        registro_X += self._validar(self.X_nome_empregado)
        registro_X += self._validar(self.X_numero_ctps)
        registro_X += self._validar(self.X_serie_ctps)
        registro_X += self._validar(self.X_uf_ctps)
        registro_X += self._validar(self.X_atualizacao)
        registro_X += self._validar(self.X_competencia)
        registro_X += self._validar(self.X_raca_cor)
        registro_X += self._validar(self.X_pessoas_com_deficiencia)
        registro_X += self._validar(self.X_cbo2000)
        registro_X += self._validar(self.X_aprendiz)
        registro_X += self._validar(self.X_tipo_deficiencia)
        registro_X += self._validar(self.X_CPF)
        registro_X += self._validar(self.X_cep_residencia)
        return registro_X

    def _gerar_grrf(self):
        return \
            self._registro_A() + \
            self._registro_B() + \
            self._registro_C() + \
            self._registro_X()

    def __init__(self, *args, **kwargs):

        # campos do Registro A (AUTORIZADO) -----------------------------------
        # Registro do estabelecimento responsável pela informação (Autorizado)
        self.A_tipo_de_registro= 'A'
        self.A_tipo_layout = 'L2009'
        self.A_alteracao= ''
        self.A_sequencia = ''
        self.A_tipo_identificador= ''
        self.A_identificador_autorizado = ''
        self.A_razao_social= ''
        self.A_endereco= ''
        self.A_cep= ''
        self.A_uf= ''
        self.A_ddd= ''
        self.A_telefone = ''
        self.A_ramal = ''
        self.A_total_estabelecimento_informados = ''
        self.A_total_movimentacoes_informados = ''
        # ---------------------------------------------------------------------

        # campos do REGISTRO B (ESTABELECIMENTO) ------------------------------
        self.B_tipo_de_registro= 'B'
        self.B_tipo_identificador= ''
        self.B_identificador_estabelecimento= ''
        self.B_sequencia= ''
        self.B_primeira_declaracao = ''
        self.B_alteracao= ''
        self.B_cep= ''
        self.B_razao_social= ''
        self.B_endereco= ''
        self.B_bairro= ''
        self.B_uf= ''
        self.B_total_empregados_existentes = ''
        self.B_porte_estabelecimento = ''
        self.B_CNAE = ''
        self.B_ddd= ''
        self.B_telefone= ''
        self.B_email= ''
        # ---------------------------------------------------------------------

        # campos do REGISTRO C (MOVIMENTAÇÃO) ---------------------------------
        self.C_tipo_de_registro= 'C'
        self.C_tipo_identificador= ''
        self.C_identificador_estabelecimento= ''
        self.C_sequencia= ''
        self.C_PIS_PASEP= ''
        self.C_sexo= ''
        self.C_nascimento = ''
        self.C_grau_instrucao = ''
        self.C_salario_mensal = ''
        self.C_horas_trabalhadas = ''
        self.C_admissao = ''
        self.C_tipo_de_movimento = ''
        self.C_dia_desligamento = ''
        self.C_nome_empregado = ''
        self.C_numero_ctps = ''
        self.C_serie_ctps = ''
        self.C_uf_ctps = ''
        self.C_raca_cor = ''
        self.C_pessoas_com_deficiencia = ''
        self.C_cbo2000 = ''
        self.C_aprendiz = ''
        self.C_tipo_deficiencia = ''
        self.C_CPF = ''
        self.C_cep_residencia = ''
        # ---------------------------------------------------------------------

        # campos do REGISTRO X (ACERTO) ---------------------------------------
        self.X_tipo_de_registro = 'X'
        self.X_tipo_identificador = ''
        self.X_identificador_estabelecimento = ''
        self.X_sequencia = ''
        self.X_PIS_PASEP = ''
        self.X_sexo = ''
        self.X_nascimento = ''
        self.X_grau_instrucao = ''
        self.X_salario_mensal = ''
        self.X_horas_trabalhadas = ''
        self.X_admissao = ''
        self.X_tipo_de_movimento = ''
        self.X_dia_desligamento = ''
        self.X_nome_empregado = ''
        self.X_numero_ctps = ''
        self.X_serie_ctps = ''
        self.X_uf_ctps = ''
        self.X_atualizacao = ''
        self.X_competencia = ''
        self.X_raca_cor = ''
        self.X_pessoas_com_deficiencia = ''
        self.X_cbo2000 = ''
        self.X_aprendiz = ''
        self.X_tipo_deficiencia = ''
        self.X_CPF = ''
        self.X_cep_residencia = ''
        # ---------------------------------------------------------------------

    def _validar(self, word, tam, tipo='AN'):
        """
        Sobrescrever a função de validacao de palavras da classe abstrata para
         obter todas as palavras do caged em maiusculas.
        """
        if tipo=='AN':
            word = word.upper()
        result = super(Caged, self)._validar(self, word, tam, tipo='AN')