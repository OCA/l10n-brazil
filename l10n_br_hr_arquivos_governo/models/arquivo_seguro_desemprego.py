# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from .abstract_arquivos_governo import AbstractArquivosGoverno

_logger = logging.getLogger(__name__)

try:
    from pybrasil.data import hoje
except ImportError:
    _logger.info('Cannot import pybrasil')


class SeguroDesemprego(AbstractArquivosGoverno):

    # HEADER
    def _registro_header(self):
        registro_header = self.tipo_de_registro_00
        registro_header += self._validar(self.tipo_identificador, 1, 'N')
        registro_header += self._validar(self.cnpj_empresa, 14, 'N')
        registro_header += self._validar(self.versao_layout, 3, 'N')
        registro_header += ''.ljust(280)
        registro_header += '\r\n'
        return registro_header

    # REQUERIMENTO
    def _registro_requerimento(self):
        registro01 = self.tipo_de_registro_01
        registro01 += self._validar(self.cpf, 11, 'N')
        registro01 += self._validar(self.nome, 40, 'AN')
        registro01 += self._validar(self.endereco, 40, 'AN')
        registro01 += self._validar(self.complemento, 16, 'AN')
        registro01 += self._validar(self.cep, 8, 'N')
        registro01 += self._validar(self.uf, 2, 'A')
        registro01 += self._validar(self.ddd, 2, 'N')
        registro01 += self._validar(self.telefone, 8, 'N')
        registro01 += self._validar(self.nome_mae, 40, 'A')
        registro01 += self._validar(self.pis, 11, 'N')
        registro01 += self._validar(self.carteira_trabalho_numero, 8, 'N')
        registro01 += self._validar(self.carteira_trabalho_serie, 5, 'AN')
        registro01 += self._validar(self.carteira_trabalho_estado, 2, 'A')
        registro01 += self._validar(self.cbo, 6, 'N')
        registro01 += self._validar(self.data_admissao, 8, 'D')
        registro01 += self._validar(self.data_demissao, 8, 'D')
        registro01 += self._validar(self.sexo, 1, 'N')
        registro01 += self._validar(self.grau_instrucao, 2, 'N')
        registro01 += self._validar(self.data_nascimento, 8, 'D')
        registro01 += self._validar(self.horas_trabalhadas_semana, 2, 'N')
        registro01 += \
            self._validar(self.remuneracao_antepenultimo_salario, 10, 'N')
        registro01 += \
            self._validar(self.remuneracao_penultimo_salario, 10, 'N')
        registro01 += self._validar(self.ultimo_salario, 10, 'N')
        registro01 += self._validar(self.numero_meses_trabalhados, 2, 'N')
        registro01 += self._validar(self.recebeu_6_salario, 1, 'N')
        registro01 += self._validar(self.aviso_previo_indenizado, 1, 'N')
        registro01 += self._validar(self.codigo_banco, 3, 'N')
        registro01 += self._validar(self.codigo_agencia, 4, 'N')
        registro01 += self._validar(self.codigo_agencia_digito, 1, 'N')
        registro01 += ''.ljust(28)
        registro01 += '\r\n'
        return registro01

    def _registro_trailler(self):
        registro_trailler = self.tipo_de_registro_99
        registro_trailler += \
            self._validar(self.total_requerimentos_informados, 5, 'N')
        registro_trailler += str.ljust('', 293)
        registro_trailler += '\r\n'
        return registro_trailler

    def _gerar_arquivo_seguro_desemprego(self):
        return \
            self._registro_header() + \
            self._registro_requerimento() + \
            self._registro_trailler()

    def __init__(self, *args, **kwargs):

        # campos do HEADER  ---------------------------------------------------
        self.tipo_de_registro_00 = '00'
        self.tipo_identificador = '1'
        self.cnpj_empresa = ''
        self.versao_layout = '001'
        self.empregados = []
        # ---------------------------------------------------------------------

        # campos do REQUERIMENTO ----------------------------------------------
        self.tipo_de_registro_01 = '01'
        self.cpf = ''
        self.nome = ''
        self.endereco = ''
        self.complemento = ''
        self.cep = ''
        self.uf = ''
        self.ddd = ''
        self.telefone = ''
        self.nome_mae = ''
        self.pis = ''
        self.carteira_trabalho_numero = ''
        self.carteira_trabalho_serie = ''
        self.carteira_trabalho_estado = ''
        self.cbo = ''
        self.data_admissao = hoje()
        self.data_demissao = hoje()
        self.sexo = 'M'
        self.grau_instrucao = '01'
        self.data_nascimento = hoje()
        self.horas_trabalhadas_semana = 44
        self.remuneracao_antepenultimo_salario = 0
        self.remuneracao_penultimo_salario = 0
        self.ultimo_salario = 0
        self.numero_meses_trabalhados = '00'
        self.recebeu_6_salario = '0'
        self.aviso_previo_indenizado = '1'
        self.codigo_banco = ''
        self.codigo_agencia = ''
        self.codigo_agencia_digito = ''
        # ---------------------------------------------------------------------

        # campos do TRAILLER  -------------------------------------------------
        self.tipo_de_registro_99 = '99'
        self.total_requerimentos_informados = u''
        # ---------------------------------------------------------------------
