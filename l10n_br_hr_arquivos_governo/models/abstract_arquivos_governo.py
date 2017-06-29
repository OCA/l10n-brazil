# -*- coding: utf-8 -*-
# (c) 2017 KMEE- Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
import re

_logger = logging.getLogger(__name__)

try:
    from pybrasil.base import tira_acentos
    from pybrasil import data
except ImportError:
    _logger.info('Cannot import pybrasil')


class AbstractArquivosGoverno(object):

    def _gerar_arquivo_temp(self, text, tipo):
        """
        Dado um texto, criar um arquivo temporario, escrever nesse arquivo
        fechar o arquivo e retornar o path do arquivo criado
        :param text:
        :param tipo:
        :return:
        """
        arq = open('/tmp/' + tipo, 'w')
        arq.write(text.encode('utf-8'))
        arq.close()
        return '/tmp/' + tipo

    def _validar(self, word, tam, tipo='AN'):
        """
        Função Genérica utilizada para validação de campos que são gerados
        nos arquivos TXT's
        :param tipo: str - Tipo de palavras validadas:
            -   A -> Alfabéticas -> Apenas letras do alfabeto
            -   D -> Data -> Apenas numeral
            -   V -> Valor -> Valores decimais, retirando a virgula
            -   N -> Numerico -> Apenas numeros preechidos com zero a esq.
            -   AN -> Alfanumericos -> Aceita nuemros e caracateres sem acentos
        :param word: str - palavra a ser validada
        :param tam: int - Tamanho que a palavra deve ser
        :return: str - Palavra formatada de acordo com tipo e tamanho
        """
        if not word:
            word = u''

        if tipo == 'A':         # Alfabetico
            word = tira_acentos(word)
            # tirar tudo que nao for letra do alfabeto
            word = re.sub('[^a-zA-Z]', ' ', word)
            # Retirar 2 espaços seguidos
            word = re.sub('[ ]+', ' ', word)
            return unicode.ljust(unicode(word), tam)[:tam]

        elif tipo == 'D':       # Data
            # Retira tudo que nao for numeral
            word = data.formata_data(word)
            word = re.sub(u'[^0-9]', '', str(word))
            return unicode.ljust(unicode(word), tam)[:tam]

        elif tipo == 'V':       # Valor
            # Pega a parte decimal como inteiro e nas duas ultimas casas
            word = int(word * 100) if word else 0
            # Preenche com zeros a esquerda
            word = str(word).zfill(tam)
            return word[:tam]

        elif tipo == 'N':       # Numerico
            # Preenche com zeros a esquerda
            word = re.sub('[^0-9]', '', str(word))
            word = str(word).zfill(tam)
            return word[:tam]

        elif tipo == 'AN':      # Alfanumerico
            # Tira acentos da palavras
            word = tira_acentos(word)
            # Preenche com espaço vazio a esquerda
            return unicode.ljust(unicode(word), tam)[:tam]
