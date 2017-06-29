# -*- coding: utf-8 -*-
# (c) 2017 KMEE- Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

from .abstract_arquivos_governo import AbstractArquivosGoverno


class Caged(AbstractArquivosGoverno):
    # Registro do estabelecimento responsável pela informação no
    # meio magnético (autorizado).

    def _registro_A(self):
        registro_A = self.A_tipo_de_registro
        registro_A += self.A_tipo_layout
        registro_A += str.ljust('', 3)
        registro_A += self._validar(self.A_competencia, 6, 'N')
        registro_A += self._validar(self.A_alteracao, 1, 'N')
        registro_A += self._validar(self.A_sequencia, 5, 'N')
        registro_A += self._validar(self.A_tipo_identificador, 1, 'N')
        registro_A += self._validar(self.A_identificador_autorizado, 14, 'N')
        registro_A += self._validar(self.A_razao_social, 35, 'AN')
        registro_A += self._validar(self.A_endereco, 40, 'AN')
        registro_A += self._validar(self.A_cep, 8, 'N')
        registro_A += self._validar(self.A_uf, 2, 'A')
        registro_A += self._validar(self.A_ddd, 4, 'N')
        registro_A += self._validar(self.A_telefone, 8, 'N')
        registro_A += self._validar(self.A_ramal, 5, 'N')
        registro_A += \
            self._validar(self.A_total_estabelecimento_informados, 5, 'N')
        registro_A += \
            self._validar(self.A_total_movimentacoes_informados, 5, 'N')
        registro_A += str.ljust('', 92)
        registro_A += '\n'
        return registro_A

    # Informações da Empresa
    def _registro_B(self):
        registro_B = self.B_tipo_de_registro
        registro_B += self._validar(self.B_tipo_identificador, 1, 'N')
        registro_B += \
            self._validar(self.B_identificador_estabelecimento, 14, 'N')
        registro_B += self._validar(self.B_sequencia, 5, 'N')
        registro_B += self._validar(self.B_primeira_declaracao, 1, 'N')
        registro_B += self._validar(self.B_alteracao, 1, 'N')
        registro_B += self._validar(self.B_cep, 8, 'N')
        registro_B += str.ljust('', 5)
        registro_B += self._validar(self.B_razao_social, 40, 'A')
        registro_B += self._validar(self.B_endereco, 40, 'AN')
        registro_B += self._validar(self.B_bairro, 20, 'A')
        registro_B += self._validar(self.B_uf, 2, 'A')
        registro_B += self._validar(self.B_total_empregados_existentes, 5, 'N')
        registro_B += self._validar(self.B_porte_estabelecimento, 1, 'N')
        registro_B += self._validar(self.B_CNAE, 7, 'N')
        registro_B += self._validar(self.B_ddd, 4, 'N')
        registro_B += self._validar(self.B_telefone, 8, 'N')
        registro_B += self._validar(self.B_email, 50, 'AN')
        registro_B += str.ljust('', 27)
        registro_B += '\n'
        return registro_B

    # Informações do trabalhador
    def _registro_C(self):
        registro_C = self.C_tipo_de_registro
        registro_C += self._validar(self.C_tipo_identificador, 1, 'N')
        registro_C += \
            self._validar(self.C_identificador_estabelecimento, 14, 'N')
        registro_C += self._validar(self.C_sequencia, 5, 'N')
        registro_C += self._validar(self.C_PIS_PASEP, 11, 'N')
        registro_C += self._validar(self.C_sexo, 1, 'N')
        registro_C += self._validar(self.C_nascimento, 8, 'D')
        registro_C += self._validar(self.C_grau_instrucao, 2, 'N')
        registro_C += str.ljust('', 4)
        registro_C += self._validar(self.C_salario_mensal, 8, 'V')
        registro_C += self._validar(self.C_horas_trabalhadas, 2, 'N')
        registro_C += self._validar(self.C_admissao, 8, 'D')
        registro_C += self._validar(self.C_tipo_de_movimento, 2, 'N')
        registro_C += self._validar(self.C_dia_desligamento, 2, 'N')
        registro_C += self._validar(self.C_nome_empregado, 40, 'A')
        registro_C += self._validar(self.C_numero_ctps, 8, 'N')
        registro_C += self._validar(self.C_serie_ctps, 4, 'N')
        registro_C += str.ljust('', 7)
        registro_C += self._validar(self.C_raca_cor, 1, 'N')
        registro_C += self._validar(self.C_pessoas_com_deficiencia, 1, 'N')
        registro_C += self._validar(self.C_cbo2000, 6, 'N')
        registro_C += self._validar(self.C_aprendiz, 1, 'N')
        registro_C += self._validar(self.C_uf_ctps, 2, 'A')
        registro_C += self._validar(self.C_tipo_deficiencia, 1, 'AN')
        registro_C += self._validar(self.C_CPF, 11, 'N')
        registro_C += self._validar(self.C_cep_residencia, 8, 'N')
        registro_C += str.ljust('', 81)
        registro_C += '\n'
        return registro_C

    def _registro_X(self):
        registro_X = self.X_tipo_de_registro
        registro_X += self._validar(self.X_tipo_identificador, 1, 'N')
        registro_X += self.\
            _validar(self.X_identificador_estabelecimento, 14, 'N')
        registro_X += self._validar(self.X_sequencia, 5, 'N')
        registro_X += self._validar(self.X_PIS_PASEP, 11, 'N')
        registro_X += self._validar(self.X_sexo, 1, 'N')
        registro_X += self._validar(self.X_nascimento, 8, 'N')
        registro_X += self._validar(self.X_grau_instrucao, 2, 'N')
        registro_X += str.ljust('', 4)
        registro_X += self._validar(self.X_salario_mensal, 8, 'V')
        registro_X += self._validar(self.X_horas_trabalhadas, 2, 'N')
        registro_X += self._validar(self.X_admissao, 8, 'D')
        registro_X += self._validar(self.X_tipo_de_movimento, 2, 'N')
        registro_X += self._validar(self.X_dia_desligamento, 2, 'N')
        registro_X += self._validar(self.X_nome_empregado, 40, 'A')
        registro_X += self._validar(self.X_numero_ctps, 8, 'N')
        registro_X += self._validar(self.X_serie_ctps, 4, 'N')
        registro_X += self._validar(self.X_uf_ctps, 2, 'A')
        registro_X += self._validar(self.X_atualizacao, 1, 'N')
        registro_X += self._validar(self.X_competencia, 6, 'N')
        registro_X += self._validar(self.X_raca_cor, 1, 'N')
        registro_X += self._validar(self.X_pessoas_com_deficiencia, 1, 'N')
        registro_X += self._validar(self.X_cbo2000, 6, 'N')
        registro_X += self._validar(self.X_aprendiz, 1, 'N')
        registro_X += self._validar(self.X_tipo_deficiencia, 1, 'A')
        registro_X += self._validar(self.X_CPF, 11, 'N')
        registro_X += self._validar(self.X_cep_residencia, 8, 'AN')
        registro_X += str.ljust('', 81)
        registro_X += '\n'
        return registro_X

    def _registro_Z(self):
        registro_Z = self.Z_tipo_de_registro
        registro_Z += self._validar(self.Z_responsavel, 40, 'AN')
        registro_Z += self._validar(self.Z_email_responsavel, 50, 'AN')
        registro_Z += ''.rjust(7, '0')
        registro_Z += self._validar(self.Z_cpf_responsavel, 11, 'N')
        registro_Z += str.ljust('', 122)
        registro_Z += ''.rjust(9, '0')
        registro_Z += '\n'
        return registro_Z

    def _gerar_grrf(self):
        return \
            self._registro_A() + \
            self._registro_B() + \
            self._registro_C() + \
            self._registro_X() + \
            self._registro_Z()

    def __init__(self, *args, **kwargs):

        # campos do Registro A (AUTORIZADO) -----------------------------------
        # Registro do estabelecimento responsável pela informação (Autorizado)
        self.A_tipo_de_registro = 'A'
        self.A_tipo_layout = 'L2009'
        self.A_competencia = ''
        self.A_alteracao = ''
        self.A_sequencia = ''
        self.A_tipo_identificador = ''
        self.A_identificador_autorizado = ''
        self.A_razao_social = ''
        self.A_endereco = ''
        self.A_cep = ''
        self.A_uf = ''
        self.A_ddd = ''
        self.A_telefone = ''
        self.A_ramal = ''
        self.A_total_estabelecimento_informados = ''
        self.A_total_movimentacoes_informados = ''
        # ---------------------------------------------------------------------

        # campos do REGISTRO B (ESTABELECIMENTO) ------------------------------
        # dados cadastrais do estabelecimento que teve movimentação
        self.B_tipo_de_registro = 'B'
        self.B_tipo_identificador = ''
        self.B_identificador_estabelecimento = ''
        self.B_sequencia = ''
        self.B_primeira_declaracao = ''
        self.B_alteracao = ''
        self.B_cep = ''
        self.B_razao_social = ''
        self.B_endereco = ''
        self.B_bairro = ''
        self.B_uf = ''
        self.B_total_empregados_existentes = ''
        self.B_porte_estabelecimento = ''
        self.B_CNAE = ''
        self.B_ddd = ''
        self.B_telefone = ''
        self.B_email = ''
        # ---------------------------------------------------------------------

        # campos do REGISTRO C (MOVIMENTAÇÃO) ---------------------------------
        self.C_tipo_de_registro = 'C'
        self.C_tipo_identificador = ''
        self.C_identificador_estabelecimento = ''
        self.C_sequencia = ''
        self.C_PIS_PASEP = ''
        self.C_sexo = ''
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

        # campos do REGISTRO Z (Responsavel preenchimento) --------------------
        self.Z_tipo_de_registro = 'Z'
        self.Z_responsavel = ''
        self.Z_email_responsavel = ''
        self.Z_cpf_responsavel = ''

    def _validar(self, word, tam, tipo='AN'):
        """
        Sobrescrever a função de validacao de palavras da classe abstrata para
         obter todas as palavras do caged em maiusculas.
        """
        if tipo in ['AN', 'A'] and word:
            word = word.upper()
        if tipo in ['D'] and not word:
            word = datetime.now().strftime("%Y-%m-%d")
        return super(Caged, self)._validar(word, tam, tipo)
