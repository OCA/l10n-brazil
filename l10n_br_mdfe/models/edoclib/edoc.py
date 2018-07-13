# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals
import StringIO
from pynfe.processamento.mdfe import ComunicacaoMDFe


class ChaveCFeSAT(object):
    """Representa a **chave de acesso** do CF-e-SAT conforme descrito na
    Especificação de Requisitos SAT, item 4.7. Os campos são definidos assim:
    .. sourcecode:: text
        0  2    6             20 22        31     37     43  --> índice
        |  |    |              |  |         |      |      |
        35 1508 08723218000186 59 900004019 000024 111425 7  --> campos
        |  |    |              |  |         |      |      |
        |  |    |              |  |         |      |      dígito verificador
        |  |    |              |  |         |      |
        |  |    |              |  |         |      código aleatório
        |  |    |              |  |         |
        |  |    |              |  |         número do cupom fiscal
        |  |    |              |  |
        |  |    |              |  número de série do equipamento SAT
        |  |    |              |
        |  |    |              modelo do documento fiscal
        |  |    |
        |  |    cnpj do emitente
        |  |
        |  ano/mês de emissão
        |
        código da UF
        """


class ChaveMDFe(object):
    """Representa a **chave de acesso** do MDF-e conforme descrito no
    Manual de Orientação do Contribuinte, item 7.5. Os campos são definidos assim:
    .. sourcecode:: text
        0  2    6             20 22   25        34 35       43  --> índice
        |  |    |              |  |   |         |  |        |
        23 1712 41426966002035 58 001 000000337 1  00004894 4 --> campos
        |  |    |              |  |   |         |  |        |
        |  |    |              |  |   |         |  |        dígito verificador
        |  |    |              |  |   |         |  |
        |  |    |              |  |   |         |  Código Numérico que compõe a Chave de Acesso
        |  |    |              |  |   |         |
        |  |    |              |  |   |         forma de emissão
        |  |    |              |  |   |
        |  |    |              |  |   número
        |  |    |              |  |
        |  |    |              |  número de série do equipamento SAT
        |  |    |              |
        |  |    |              modelo do documento fiscal
        |  |    |
        |  |    cnpj do emitente
        |  |
        |  ano/mês de emissão
        |
        código da UF
        """

class Chave(object):
    """Representa a **chave de acesso** do MDF-e conforme descrito no
    Manual de Orientação do Contribuinte, item 7.5. Os campos são definidos assim:
    .. sourcecode:: text
        0  2    6             20 22   25        34 35       43  --> índice
        |  |    |              |  |   |         |  |        |
        23 1712 41426966002035 58 001 000000337 1  00004894 4 --> campos
        |  |    |              |  |   |         |  |        |
        |  |    |              |  |   |         |  |        dígito verificador
        |  |    |              |  |   |         |  |
        |  |    |              |  |   |         |  Código Numérico que compõe a Chave de Acesso
        |  |    |              |  |   |         |
        |  |    |              |  |   |         forma de emissão
        |  |    |              |  |   |
        |  |    |              |  |   número
        |  |    |              |  |
        |  |    |              |  número de série do equipamento SAT
        |  |    |              |
        |  |    |              modelo do documento fiscal
        |  |    |
        |  |    cnpj do emitente
        |  |
        |  ano/mês de emissão
        |
        código da UF
        """


class ChaveEsocial(object):
    """Representa a **chave de acesso** do MDF-e conforme descrito no
    Manual de Orientação do Contribuinte, item 7.5. Os campos são definidos assim:
    .. sourcecode:: text
        0  2    6             20 22   25        34 35       43  --> índice
        |  |    |              |  |   |         |  |        |
        2  33390170000189 20140202134247 00001 --> campos
        |  |    |              |  |   |         |  |        |
        |  |    |              |  |   |         |  |        dígito verificador
        |  |    |              |  |   |         |  |
        |  |    |              |  |   |         |  Código Numérico que compõe a Chave de Acesso
        |  |    |              |  |   |         |
        |  |    |              |  |   |         forma de emissão
        |  |    |              |  |   |
        |  |    |              |  |   número
        |  |    |              |  |
        |  |    |              |  número de série do equipamento SAT
        |  |    |              |
        |  |    |              modelo do documento fiscal
        |  |    |
        |  |    cnpj do emitente
        |  |
        |  ano/mês de emissão
        |
        código da UF
        """

MODELO_FISCAL_EDOC = (
    '55', '57', '58', '65'
)


class DocumentoEletronico(object):

    _edoc_methods = ['export', 'save', 'delete']

    def __init__(
            self, generateds,
            certificado='',
            senha='', uf='', homologacao=True):
        self._edoc = generateds
        self.gera_id()
        self.documento_exportado = False
        self.documento_assinado = False
        self.chave = False
        self.id = False
        self.mdfe = ComunicacaoMDFe(uf, certificado, senha, homologacao)

    def __getattr__(self, attribute):
        if attribute in self._edoc_methods:
            return getattr(self._edoc, attribute)

    def modulo_11(self, valor):
        soma = 0
        m = 2
        for i in range(len(valor)-1, -1, -1):
            c = valor[i]
            soma += int(c) * m
            m += 1
            if m > 9:
                m = 2

        digito = 11 - (soma % 11)
        if digito > 9:
            digito = 0

        return digito

    def gera_id(self):
        if self._edoc.infMDFe.ide.mod == '58':
            inf_edoc = self._edoc.infMDFe
            numero = 'nMDF'
            codigo_numerico = 'cMDF'
            abreviacao_edoc = 'MDFe'
        else:
            return

        chave = unicode(inf_edoc.ide.cUF).zfill(2)
        chave += unicode(inf_edoc.ide.dhEmi[2:7].replace('-', ''))
        chave += unicode(inf_edoc.emit.CNPJ).zfill(14)
        chave += unicode(inf_edoc.ide.mod).zfill(2)
        chave += unicode(inf_edoc.ide.serie).zfill(3)
        chave += unicode(
            getattr(inf_edoc.ide, numero)
        ).zfill(9)
        chave += unicode(inf_edoc.ide.tpEmis).zfill(1)
        soma = 0
        for c in chave:
            soma += int(c) ** 3 ** 2

        codigo = unicode(soma)
        if len(codigo) > 8:
            codigo = codigo[-8:]
        else:
            codigo = codigo.rjust(8, '0')

        chave += codigo
        setattr(inf_edoc.ide, codigo_numerico, codigo)
        digito = self.modulo_11(chave)
        inf_edoc.ide.cDV = digito
        chave += unicode(digito)

        self.chave = chave
        self.id = abreviacao_edoc + chave

        inf_edoc.Id = self.id

    def exporta_documento(self):
        output = StringIO.StringIO()
        self.export(output, 0)
        contents = output.getvalue()
        output.close()

        write_txt = contents.encode('utf8')
        self.documento_exportado = write_txt.decode('utf-8')

        return self.documento_exportado

    def assina_documento(self):
        self.documento_assinado = \
            self.mdfe.assina_documento(self.documento_exportado)
        return self.documento_assinado

    def envia_documento(self):
        if not self.documento_exportado:
            self.exporta_documento()

        if not self.documento_assinado:
            self.assina_documento()

        return self.mdfe.processar_documento(self.documento_assinado)
