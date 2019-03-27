# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Wed Mar 27 02:20:53 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# Código de Regime Tributário.
CRT_emit = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
]

# classificação Tributária do Serviço
CST_ICMS00 = [
    ("00", "00"),
]

# Classificação Tributária do serviço
CST_ICMS20 = [
    ("20", "20"),
]

# Classificação Tributária do Serviço
CST_ICMS45 = [
    ("40", "40"),
    ("41", "41"),
    ("51", "51"),
]

# Classificação Tributária do Serviço
CST_ICMS90 = [
    ("90", "90"),
]

# Classificação Tributária do Serviço
CST_ICMSSN = [
    ("90", "90"),
]

# Tipo Ambiente
TAmb = [
    ("1", "1"),
    ("2", "2"),
]

# Tipo Código da UF da tabela do IBGE
TCodUfIBGE = [
    ("11", "11"),
    ("12", "12"),
    ("13", "13"),
    ("14", "14"),
    ("15", "15"),
    ("16", "16"),
    ("17", "17"),
    ("21", "21"),
    ("22", "22"),
    ("23", "23"),
    ("24", "24"),
    ("25", "25"),
    ("26", "26"),
    ("27", "27"),
    ("28", "28"),
    ("29", "29"),
    ("31", "31"),
    ("32", "32"),
    ("33", "33"),
    ("35", "35"),
    ("41", "41"),
    ("42", "42"),
    ("43", "43"),
    ("50", "50"),
    ("51", "51"),
    ("52", "52"),
    ("53", "53"),
]

# Tipo de Documento de Identificação
TDoc_infPassageiro = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
]

# Tipo de Indicador de Presença
TIndPres_ide = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
    ("9", "9"),
]

# Tipo Modelo Bilhete Passagem Eletrônico
TModBPe_ide = [
    ("63", "63"),
]

# Tipo de Substituição
TTipoSubstituicao_infBPeSub = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
]

# Tipo Sigla da UF
TUf = [
    ("AC", "AC"),
    ("AL", "AL"),
    ("AM", "AM"),
    ("AP", "AP"),
    ("BA", "BA"),
    ("CE", "CE"),
    ("DF", "DF"),
    ("ES", "ES"),
    ("GO", "GO"),
    ("MA", "MA"),
    ("MG", "MG"),
    ("MS", "MS"),
    ("MT", "MT"),
    ("PA", "PA"),
    ("PB", "PB"),
    ("PE", "PE"),
    ("PI", "PI"),
    ("PR", "PR"),
    ("RJ", "RJ"),
    ("RN", "RN"),
    ("RO", "RO"),
    ("RR", "RR"),
    ("RS", "RS"),
    ("SC", "SC"),
    ("SE", "SE"),
    ("SP", "SP"),
    ("TO", "TO"),
    ("EX", "EX"),
]

# Tipo Sigla da UF - Sem Exterior
TUf_sem_EX = [
    ("AC", "AC"),
    ("AL", "AL"),
    ("AM", "AM"),
    ("AP", "AP"),
    ("BA", "BA"),
    ("CE", "CE"),
    ("DF", "DF"),
    ("ES", "ES"),
    ("GO", "GO"),
    ("MA", "MA"),
    ("MG", "MG"),
    ("MS", "MS"),
    ("MT", "MT"),
    ("PA", "PA"),
    ("PB", "PB"),
    ("PE", "PE"),
    ("PI", "PI"),
    ("PR", "PR"),
    ("RJ", "RJ"),
    ("RN", "RN"),
    ("RO", "RO"),
    ("RR", "RR"),
    ("RS", "RS"),
    ("SC", "SC"),
    ("SE", "SE"),
    ("SP", "SP"),
    ("TO", "TO"),
]

# Indica se o contribuinte é Simples Nacional 1=Sim
indSN_ICMSSN = [
    ("1", "1"),
]

# Situação do veículo transportado
sitVeiculo_infTravessia = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
]

# Bandeira da operadora de cartão de crédito/débito
tBand_card = [
    ("01", "01–Visa"),
    ("02", "02–Mastercard"),
    ("03", "03–American Express"),
    ("04", "04–Sorocred"),
    ("05", "05 - Elo"),
    ("06", "06 - Diners"),
    ("99", "99–Outros"),
]

# Forma de Pagamento
tPag_pag = [
    ("01", "01-Dinheiro"),
    ("02", "02-Cheque"),
    ("03", "03-Cartão de Crédito"),
    ("04", "04-Cartão de Débito"),
    ("05", "05-Vale Transportel"),
    ("99", "99 - Outros"),
]

# Tipo de Acomodação
tpAcomodacao_infViagem = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
]

# Tipo do Componente
tpComp_Comp = [
    ("01", "01"),
    ("02", "02"),
    ("03", "03"),
    ("04", "04"),
    ("05", "05"),
    ("06", "06"),
    ("99", "99"),
]

# Tipo de desconto/benefício para o BP-e
tpDesconto_infValorBPe = [
    ("01", "01"),
    ("02", "02"),
    ("03", "03"),
    ("04", "04"),
    ("05", "05"),
    ("06", "06"),
    ("07", "07"),
    ("08", "08"),
    ("09", "09"),
    ("10", "10"),
    ("99", "99"),
]

# Forma de emissão do Bilhete (Normal ou Contingência Off-Line)
tpEmis_ide = [
    ("1", "1"),
    ("2", "2"),
]

# Tipo de Integração do processo de pagamento com o sistema de
# automação da empresa 1=Pagamento integrado com o sistema de automação
# da empresa Ex. equipamento TEF , Comercio Eletronico 2=Pagamento não
# integrado com o sistema de automação da empresa Ex
# equipamento POS
tpIntegra_card = [
    ("1", "1"),
    ("2", "2"),
]

# Tipo de Serviço
tpServ_infViagem = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
    ("6", "6"),
    ("7", "7"),
    ("8", "8"),
    ("9", "9"),
]

# Tipo de trecho da viagem
tpTrecho_infViagem = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
]

# Tipo do veículo transportado
tpVeiculo_infTravessia = [
    ("01", "01"),
    ("02", "02"),
    ("03", "03"),
    ("04", "04"),
    ("05", "05"),
    ("06", "06"),
    ("07", "07"),
    ("08", "08"),
    ("09", "09"),
    ("10", "10"),
    ("11", "11"),
    ("12", "12"),
    ("13", "13"),
    ("14", "14"),
    ("15", "15"),
    ("16", "16"),
    ("17", "17"),
    ("18", "18"),
    ("19", "19"),
    ("20", "20"),
    ("21", "21"),
    ("22", "22"),
    ("23", "23"),
    ("24", "24"),
    ("25", "25"),
    ("26", "26"),
    ("27", "27"),
    ("28", "28"),
    ("29", "29"),
    ("99", "99"),
]

# Tipo de Viagem
tpViagem_infViagem = [
    ("00", "00"),
    ("01", "01"),
]


class Comp(spec_models.AbstractSpecMixin):
    "Componentes do Valor do Bilhete"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.comp'
    _generateds_type = 'CompType'
    _concrete_rec_name = 'bpe_tpComp'

    bpe10_Comp_infValorBPe_id = fields.Many2one(
        "bpe.10.infvalorbpe")
    bpe10_tpComp = fields.Selection(
        tpComp_Comp,
        string="Tipo do Componente", xsd_required=True)
    bpe10_vComp = fields.Monetary(
        digits=2, string="Valor do componente", xsd_required=True)


class ICMS00(spec_models.AbstractSpecMixin):
    "Prestação sujeito à tributação normal do ICMS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.icms00'
    _generateds_type = 'ICMS00Type'
    _concrete_rec_name = 'bpe_CST'

    bpe10_CST = fields.Selection(
        CST_ICMS00,
        string="classificação Tributária do Serviço",
        xsd_required=True)
    bpe10_vBC = fields.Monetary(
        digits=2, string="Valor da BC do ICMS", xsd_required=True)
    bpe10_pICMS = fields.Monetary(
        digits=2, string="Alíquota do ICMS", xsd_required=True)
    bpe10_vICMS = fields.Monetary(
        digits=2, string="Valor do ICMS", xsd_required=True)


class ICMS20(spec_models.AbstractSpecMixin):
    "Prestação sujeito à tributação com redução de BC do ICMS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.icms20'
    _generateds_type = 'ICMS20Type'
    _concrete_rec_name = 'bpe_CST'

    bpe10_CST = fields.Selection(
        CST_ICMS20,
        string="Classificação Tributária do serviço",
        xsd_required=True)
    bpe10_pRedBC = fields.Monetary(
        digits=2, string="Percentual de redução da BC",
        xsd_required=True)
    bpe10_vBC = fields.Monetary(
        digits=2, string="Valor da BC do ICMS", xsd_required=True)
    bpe10_pICMS = fields.Monetary(
        digits=2, string="Alíquota do ICMS", xsd_required=True)
    bpe10_vICMS = fields.Monetary(
        digits=2, string="Valor do ICMS", xsd_required=True)


class ICMS45(spec_models.AbstractSpecMixin):
    "ICMS Isento, não Tributado ou diferido"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.icms45'
    _generateds_type = 'ICMS45Type'
    _concrete_rec_name = 'bpe_CST'

    bpe10_CST = fields.Selection(
        CST_ICMS45,
        string="Classificação Tributária do Serviço",
        xsd_required=True)


class ICMS90(spec_models.AbstractSpecMixin):
    "ICMS Outros"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.icms90'
    _generateds_type = 'ICMS90Type'
    _concrete_rec_name = 'bpe_CST'

    bpe10_CST = fields.Selection(
        CST_ICMS90,
        string="Classificação Tributária do Serviço",
        xsd_required=True)
    bpe10_pRedBC = fields.Monetary(
        digits=2, string="Percentual de redução da BC")
    bpe10_vBC = fields.Monetary(
        digits=2, string="Valor da BC do ICMS", xsd_required=True)
    bpe10_pICMS = fields.Monetary(
        digits=2, string="Alíquota do ICMS", xsd_required=True)
    bpe10_vICMS = fields.Monetary(
        digits=2, string="Valor do ICMS", xsd_required=True)
    bpe10_vCred = fields.Monetary(
        digits=2, string="Valor do Crédito Outorgado/Presumido")


class ICMSSN(spec_models.AbstractSpecMixin):
    "Simples Nacional"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.icmssn'
    _generateds_type = 'ICMSSNType'
    _concrete_rec_name = 'bpe_CST'

    bpe10_CST = fields.Selection(
        CST_ICMSSN,
        string="Classificação Tributária do Serviço",
        xsd_required=True)
    bpe10_indSN = fields.Selection(
        indSN_ICMSSN,
        string="Indica se o contribuinte é Simples Nacional 1=Sim",
        xsd_required=True,
        help="Indica se o contribuinte é Simples Nacional 1=Sim")


class ICMSUFFim(spec_models.AbstractSpecMixin):
    """Informações do ICMS de partilha com a UF de término do serviço de
    transporte na operação interestadualGrupo a ser informado nas
    prestações interestaduais para consumidor final, não contribuinte do
    ICMS"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.icmsuffim'
    _generateds_type = 'ICMSUFFimType'
    _concrete_rec_name = 'bpe_vBCUFFim'

    bpe10_vBCUFFim = fields.Monetary(
        digits=2, string="Valor da BC do ICMS na UF fim da viagem",
        xsd_required=True)
    bpe10_pFCPUFFim = fields.Monetary(
        digits=2,
        string="Percentual do ICMS relativo ao Fundo de Combate à pobreza",
        xsd_required=True,
        help="Percentual do ICMS relativo ao Fundo de Combate à pobreza"
        "\n(FCP) na UF fim da viagem")
    bpe10_pICMSUFFim = fields.Monetary(
        digits=2, string="Alíquota interna da UF fim da viagem",
        xsd_required=True)
    bpe10_pICMSInter = fields.Monetary(
        digits=2, string="Alíquota interestadual das UF envolvidas",
        xsd_required=True)
    bpe10_pICMSInterPart = fields.Monetary(
        digits=2, string="Percentual provisório de partilha entre os estados",
        xsd_required=True)
    bpe10_vFCPUFFim = fields.Monetary(
        digits=2,
        string="Valor do ICMS relativo ao Fundo de Combate á Pobreza",
        xsd_required=True,
        help="Valor do ICMS relativo ao Fundo de Combate á Pobreza (FCP) da"
        "\nUF fim da viagem")
    bpe10_vICMSUFFim = fields.Monetary(
        digits=2, string="Valor do ICMS de partilha para a UF fim da viagem",
        xsd_required=True)
    bpe10_vICMSUFIni = fields.Monetary(
        digits=2,
        string="Valor do ICMS de partilha para a UF início da viagem",
        xsd_required=True)


class TBPe(spec_models.AbstractSpecMixin):
    "Tipo Bilhete de Passagem Eletrônico"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.tbpe'
    _generateds_type = 'TBPe'
    _concrete_rec_name = 'bpe_infBPe'

    bpe10_infBPe = fields.Many2one(
        "bpe.10.infbpe",
        string="Informações do BP-e",
        xsd_required=True)
    bpe10_infBPeSupl = fields.Many2one(
        "bpe.10.infbpesupl",
        string="Informações suplementares do BP-e",
        xsd_required=True)


class TEndeEmi(spec_models.AbstractSpecMixin):
    "Tipo Dados do Endereço"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.tendeemi'
    _generateds_type = 'TEndeEmi'
    _concrete_rec_name = 'bpe_xLgr'

    bpe10_xLgr = fields.Char(
        string="Logradouro", xsd_required=True)
    bpe10_nro = fields.Char(
        string="Número", xsd_required=True)
    bpe10_xCpl = fields.Char(
        string="Complemento")
    bpe10_xBairro = fields.Char(
        string="Bairro", xsd_required=True)
    bpe10_cMun = fields.Char(
        string="Código do município", xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE)")
    bpe10_xMun = fields.Char(
        string="Nome do município", xsd_required=True)
    bpe10_CEP = fields.Char(
        string="CEP")
    bpe10_UF = fields.Selection(
        TUf_sem_EX,
        string="Sigla da UF", xsd_required=True)
    bpe10_fone = fields.Char(
        string="Telefone")
    bpe10_email = fields.Char(
        string="Endereço de E-mail")


class TEndereco(spec_models.AbstractSpecMixin):
    "Tipo Dados do Endereço"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.tendereco'
    _generateds_type = 'TEndereco'
    _concrete_rec_name = 'bpe_xLgr'

    bpe10_xLgr = fields.Char(
        string="Logradouro", xsd_required=True)
    bpe10_nro = fields.Char(
        string="Número", xsd_required=True)
    bpe10_xCpl = fields.Char(
        string="Complemento")
    bpe10_xBairro = fields.Char(
        string="Bairro", xsd_required=True)
    bpe10_cMun = fields.Char(
        string="Código do município", xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE), informar"
        "\n9999999 para operações com o exterior.")
    bpe10_xMun = fields.Char(
        string="Nome do município", xsd_required=True,
        help="Nome do município, informar EXTERIOR para operações com o"
        "\nexterior.")
    bpe10_CEP = fields.Char(
        string="CEP")
    bpe10_UF = fields.Selection(
        TUf,
        string="Sigla da UF", xsd_required=True,
        help="Sigla da UF, informar EX para operações com o exterior.")
    bpe10_cPais = fields.Char(
        string="Código do país")
    bpe10_xPais = fields.Char(
        string="Nome do país")
    bpe10_fone = fields.Char(
        string="Telefone")
    bpe10_email = fields.Char(
        string="Endereço de E-mail")


class TEnviBPe(spec_models.AbstractSpecMixin):
    "Tipo Pedido de Concessão de Autorização de BP-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.tenvibpe'
    _generateds_type = 'TEnviBPe'
    _concrete_rec_name = 'bpe_versao'

    bpe10_versao = fields.Char(
        string="versao", xsd_required=True)
    bpe10_idLote = fields.Char(
        string="idLote", xsd_required=True)
    bpe10_BPe = fields.Many2one(
        "bpe.10.tbpe",
        string="BPe", xsd_required=True)


class TImp(spec_models.AbstractSpecMixin):
    "Tipo Dados do Imposto BP-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.timp'
    _generateds_type = 'TImp'
    _concrete_rec_name = 'bpe_ICMS00'

    bpe10_choice1 = fields.Selection([
        ('bpe10_ICMS00', 'ICMS00'),
        ('bpe10_ICMS20', 'ICMS20'),
        ('bpe10_ICMS45', 'ICMS45'),
        ('bpe10_ICMS90', 'ICMS90'),
        ('bpe10_ICMSSN', 'ICMSSN')],
        "ICMS00/ICMS20/ICMS45/ICMS90/ICMSSN",
        default="bpe10_ICMS00")
    bpe10_ICMS00 = fields.Many2one(
        "bpe.10.icms00",
        choice='1',
        string="Prestação sujeito à tributação normal do ICMS",
        xsd_required=True)
    bpe10_ICMS20 = fields.Many2one(
        "bpe.10.icms20",
        choice='1',
        string="Prestação sujeito à tributação com redução de BC do ICMS",
        xsd_required=True)
    bpe10_ICMS45 = fields.Many2one(
        "bpe.10.icms45",
        choice='1',
        string="ICMS Isento", xsd_required=True,
        help="ICMS Isento, não Tributado ou diferido")
    bpe10_ICMS90 = fields.Many2one(
        "bpe.10.icms90",
        choice='1',
        string="ICMS Outros", xsd_required=True)
    bpe10_ICMSSN = fields.Many2one(
        "bpe.10.icmssn",
        choice='1',
        string="Simples Nacional", xsd_required=True)


class TProtBPe(spec_models.AbstractSpecMixin):
    """Tipo Protocolo de status resultado do processamento do BP-e (Modelo
    63)"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.tprotbpe'
    _generateds_type = 'TProtBPe'
    _concrete_rec_name = 'bpe_versao'

    bpe10_versao = fields.Char(
        string="versao", xsd_required=True)
    bpe10_infProt = fields.Many2one(
        "bpe.10.infprot",
        string="Dados do protocolo de status",
        xsd_required=True)


class TRetBPe(spec_models.AbstractSpecMixin):
    "Tipo Retorno do Pedido de Autorização de BP-e (Modelo 63)"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.tretbpe'
    _generateds_type = 'TRetBPe'
    _concrete_rec_name = 'bpe_versao'

    bpe10_versao = fields.Char(
        string="versao", xsd_required=True)
    bpe10_tpAmb = fields.Selection(
        TAmb,
        string="Identificação do Ambiente",
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    bpe10_cUF = fields.Selection(
        TCodUfIBGE,
        string="Identificação da UF", xsd_required=True)
    bpe10_verAplic = fields.Char(
        string="Versão do Aplicativo que processou o BP",
        xsd_required=True,
        help="Versão do Aplicativo que processou o BP-e")
    bpe10_cStat = fields.Char(
        string="código do status do retorno da consulta",
        xsd_required=True)
    bpe10_xMotivo = fields.Char(
        string="Descrição literal do status do do retorno da consulta",
        xsd_required=True)
    bpe10_protBPe = fields.Many2one(
        "bpe.10.tprotbpe",
        string="Reposta ao processamento do BP-e")


class Agencia(spec_models.AbstractSpecMixin):
    "Identificação da agência/preposto/terceiro que comercializou o BP-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.agencia'
    _generateds_type = 'agenciaType'
    _concrete_rec_name = 'bpe_xNome'

    bpe10_xNome = fields.Char(
        string="Razão social ou Nome da Agência",
        xsd_required=True)
    bpe10_CNPJ = fields.Char(
        string="Número do CNPJ", xsd_required=True)
    bpe10_enderAgencia = fields.Many2one(
        "bpe.10.tendereco",
        string="Endereço da agência",
        xsd_required=True)


class AutXML(spec_models.AbstractSpecMixin):
    """Autorizados para download do XML do DF-eInformar CNPJ ou CPF. Preencher
    os zeros não significativos."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.autxml'
    _generateds_type = 'autXMLType'
    _concrete_rec_name = 'bpe_CNPJ'

    bpe10_autXML_infBPe_id = fields.Many2one(
        "bpe.10.infbpe")
    bpe10_choice3 = fields.Selection([
        ('bpe10_CNPJ', 'CNPJ'),
        ('bpe10_CPF', 'CPF')],
        "CNPJ/CPF",
        default="bpe10_CNPJ")
    bpe10_CNPJ = fields.Char(
        choice='3',
        string="CNPJ do autorizado", xsd_required=True)
    bpe10_CPF = fields.Char(
        choice='3',
        string="CPF do autorizado", xsd_required=True)


class Card(spec_models.AbstractSpecMixin):
    "Grupo de Cartões"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.card'
    _generateds_type = 'cardType'
    _concrete_rec_name = 'bpe_tpIntegra'

    bpe10_tpIntegra = fields.Selection(
        tpIntegra_card,
        string="tpIntegra", xsd_required=True,
        help="Tipo de Integração do processo de pagamento com o sistema de"
        "\nautomação da empresa 1=Pagamento integrado com o"
        "\nsistema de automação da empresa Ex. equipamento TEF ,"
        "\nComercio Eletronico 2=Pagamento não integrado com o"
        "\nsistema de automação da empresa Ex"
        "\nequipamento POS")
    bpe10_CNPJ = fields.Char(
        string="CNPJ da credenciadora de cartão de crédito/débito")
    bpe10_tBand = fields.Selection(
        tBand_card,
        string="tBand",
        help="Bandeira da operadora de cartão de crédito/débito:01–Visa;"
        "\n02–Mastercard; 03–American Express; 04–Sorocred; 05 -"
        "\nElo; 06 - Diners; 99–Outros")
    bpe10_xBand = fields.Char(
        string="Descrição da operador de cartão para 99",
        help="Descrição da operador de cartão para 99 - Outros")
    bpe10_cAut = fields.Char(
        string="Número de autorização da operação cartão de crédito/débito")
    bpe10_nsuTrans = fields.Char(
        string="Número sequencial único da transação")
    bpe10_nsuHost = fields.Char(
        string="Número sequencial único do Host")
    bpe10_nParcelas = fields.Char(
        string="Número de parcelas")


class Comp_1(spec_models.AbstractSpecMixin):
    "Identificação do Comprador do BP-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.comp_1'
    _generateds_type = 'compType'
    _concrete_rec_name = 'bpe_xNome'

    bpe10_choice2 = fields.Selection([
        ('bpe10_CNPJ', 'CNPJ'),
        ('bpe10_CPF', 'CPF'),
        ('bpe10_idEstrangeiro', 'idEstrangeiro')],
        "CNPJ/CPF/idEstrangeiro",
        default="bpe10_CNPJ")
    bpe10_xNome = fields.Char(
        string="xNome", xsd_required=True)
    bpe10_CNPJ = fields.Char(
        choice='2',
        string="CNPJ", xsd_required=True)
    bpe10_CPF = fields.Char(
        choice='2',
        string="CPF", xsd_required=True)
    bpe10_idEstrangeiro = fields.Char(
        choice='2',
        string="idEstrangeiro",
        xsd_required=True)
    bpe10_IE = fields.Char(
        string="IE")
    bpe10_enderComp = fields.Many2one(
        "bpe.10.tendereco",
        string="enderComp", xsd_required=True)


class Emit(spec_models.AbstractSpecMixin):
    """Identificação do Emitente do BP-eGrupo de informações de interesse da
    PrefeituraEste campo deve ser informado, quando ocorrer a emissão de
    BP-e conjugado, com prestação de serviços sujeitos ao ISSQN."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.emit'
    _generateds_type = 'emitType'
    _concrete_rec_name = 'bpe_CNPJ'

    bpe10_CNPJ = fields.Char(
        string="CNPJ do emitente", xsd_required=True)
    bpe10_IE = fields.Char(
        string="Inscrição Estadual do emitemte",
        xsd_required=True)
    bpe10_IEST = fields.Char(
        string="Inscrição Estadual do Substituto Tributário")
    bpe10_xNome = fields.Char(
        string="Razão social ou Nome do emitente",
        xsd_required=True)
    bpe10_xFant = fields.Char(
        string="Nome fantasia do emitente")
    bpe10_IM = fields.Char(
        string="Inscrição Municipal")
    bpe10_CNAE = fields.Char(
        string="CNAE Fiscal")
    bpe10_CRT = fields.Selection(
        CRT_emit,
        string="Código de Regime Tributário.",
        xsd_required=True)
    bpe10_enderEmit = fields.Many2one(
        "bpe.10.tendeemi",
        string="Endereço do emitente",
        xsd_required=True)
    bpe10_TAR = fields.Char(
        string="Termo de Autorização de Serviço Regular")


class Ide(spec_models.AbstractSpecMixin):
    """Identificação do BP-eInformar apenas
    para tpEmis diferente de 1"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.ide'
    _generateds_type = 'ideType'
    _concrete_rec_name = 'bpe_cUF'

    bpe10_cUF = fields.Selection(
        TCodUfIBGE,
        string="Código da UF do emitente do BP-e",
        xsd_required=True)
    bpe10_tpAmb = fields.Selection(
        TAmb,
        string="Tipo do Ambiente", xsd_required=True)
    bpe10_mod = fields.Selection(
        TModBPe_ide,
        string="Modelo do Bilhete de Passagem",
        xsd_required=True)
    bpe10_serie = fields.Char(
        string="Série do documento fiscal",
        xsd_required=True)
    bpe10_nBP = fields.Char(
        string="Número do bilhete de passagem",
        xsd_required=True)
    bpe10_cBP = fields.Char(
        string="Código numérico que compõe a Chave de Acesso",
        xsd_required=True,
        help="Código numérico que compõe a Chave de Acesso.")
    bpe10_cDV = fields.Char(
        string="Digito verificador da chave de acesso",
        xsd_required=True)
    bpe10_modal = fields.Char(
        string="Modalidade de transporte",
        xsd_required=True)
    bpe10_dhEmi = fields.Datetime(
        string="Data e hora de emissão do Bilhete de Passagem",
        xsd_required=True)
    bpe10_tpEmis = fields.Selection(
        tpEmis_ide,
        string="Forma de emissão do Bilhete",
        xsd_required=True,
        help="Forma de emissão do Bilhete (Normal ou Contingência Off-Line)")
    bpe10_verProc = fields.Char(
        string="Versão do processo de emissão",
        xsd_required=True)
    bpe10_tpBPe = fields.Char(
        string="Tipo do BP-e", xsd_required=True)
    bpe10_indPres = fields.Selection(
        TIndPres_ide,
        string="indPres", xsd_required=True,
        help="Indicador de presença do comprador no estabelecimento"
        "\ncomercial no momento da operação")
    bpe10_UFIni = fields.Selection(
        TUf_sem_EX,
        string="Sigla da UF Início da Viagem",
        xsd_required=True)
    bpe10_cMunIni = fields.Char(
        string="Código do município do início da viagem",
        xsd_required=True)
    bpe10_UFFim = fields.Selection(
        TUf,
        string="Sigla da UF do Fim da Viagem",
        xsd_required=True)
    bpe10_cMunFim = fields.Char(
        string="Código do município do fim da viagem",
        xsd_required=True)
    bpe10_dhCont = fields.Datetime(
        string="Data e Hora da entrada em contingência")
    bpe10_xJust = fields.Char(
        string="Justificativa da entrada em contingência")


class Imp(spec_models.AbstractSpecMixin):
    "Informações relativas aos Impostos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.imp'
    _generateds_type = 'impType'
    _concrete_rec_name = 'bpe_ICMS'

    bpe10_ICMS = fields.Many2one(
        "bpe.10.timp",
        string="Informações relativas ao ICMS",
        xsd_required=True)
    bpe10_vTotTrib = fields.Monetary(
        digits=2, string="Valor Total dos Tributos")
    bpe10_infAdFisco = fields.Char(
        string="Informações adicionais de interesse do Fisco")
    bpe10_ICMSUFFim = fields.Many2one(
        "bpe.10.icmsuffim",
        string="ICMSUFFim",
        help="Informações do ICMS de partilha com a UF de término do"
        "\nserviço de transporte na operação interestadual")


class InfAdic(spec_models.AbstractSpecMixin):
    "Informações Adicionais"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.infadic'
    _generateds_type = 'infAdicType'
    _concrete_rec_name = 'bpe_infAdFisco'

    bpe10_infAdFisco = fields.Char(
        string="Informações adicionais de interesse do Fisco")
    bpe10_infCpl = fields.Char(
        string="Informações complementares de interesse do Contribuinte")


class InfBPeSub(spec_models.AbstractSpecMixin):
    """Informações dos BP-e de Substituição para remarcação e/ou
    transferência"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.infbpesub'
    _generateds_type = 'infBPeSubType'
    _concrete_rec_name = 'bpe_chBPe'

    bpe10_chBPe = fields.Char(
        string="Chave do Bilhete de Passagem Substituido",
        xsd_required=True)
    bpe10_tpSub = fields.Selection(
        TTipoSubstituicao_infBPeSub,
        string="Tipo de Substituição",
        xsd_required=True)


class InfBPeSupl(spec_models.AbstractSpecMixin):
    "Informações suplementares do BP-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.infbpesupl'
    _generateds_type = 'infBPeSuplType'
    _concrete_rec_name = 'bpe_qrCodBPe'

    bpe10_qrCodBPe = fields.Char(
        string="Texto com o QR", xsd_required=True,
        help="Texto com o QR-Code impresso no DABPE")
    bpe10_boardPassBPe = fields.Char(
        string="Texto contendo o boarding Pass impresso no DABPE",
        help="Texto contendo o boarding Pass impresso no DABPE (padrão"
        "\nPDF417)")


class InfBPe(spec_models.AbstractSpecMixin):
    """Informações do BP-eVersão do leiauteEx: "3.00"Identificador da tag a ser
    assinadaInformar a chave de acesso do BP-e e precedida do literal "BPe" """
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.infbpe'
    _generateds_type = 'infBPeType'
    _concrete_rec_name = 'bpe_versao'

    bpe10_versao = fields.Char(
        string="versao", xsd_required=True)
    bpe10_Id = fields.Char(
        string="Id", xsd_required=True)
    bpe10_ide = fields.Many2one(
        "bpe.10.ide",
        string="Identificação do BP-e", xsd_required=True)
    bpe10_emit = fields.Many2one(
        "bpe.10.emit",
        string="Identificação do Emitente do BP-e",
        xsd_required=True)
    bpe10_comp = fields.Many2one(
        "bpe.10.comp_1",
        string="Identificação do Comprador do BP-e")
    bpe10_agencia = fields.Many2one(
        "bpe.10.agencia",
        string="agencia",
        help="Identificação da agência/preposto/terceiro que comercializou"
        "\no BP-e")
    bpe10_infBPeSub = fields.Many2one(
        "bpe.10.infbpesub",
        string="Informações dos BP",
        help="Informações dos BP-e de Substituição para remarcação e/ou"
        "\ntransferência")
    bpe10_infPassagem = fields.Many2one(
        "bpe.10.infpassagem",
        string="Informações do detalhamento da Passagem",
        xsd_required=True)
    bpe10_infViagem = fields.One2many(
        "bpe.10.infviagem",
        "bpe10_infViagem_infBPe_id",
        string="Grupo de informações da viagem do BP",
        xsd_required=True,
        help="Grupo de informações da viagem do BP-e"
    )
    bpe10_infValorBPe = fields.Many2one(
        "bpe.10.infvalorbpe",
        string="Informações dos valores do Bilhete de Passagem",
        xsd_required=True)
    bpe10_imp = fields.Many2one(
        "bpe.10.imp",
        string="Informações relativas aos Impostos",
        xsd_required=True)
    bpe10_pag = fields.One2many(
        "bpe.10.pag",
        "bpe10_pag_infBPe_id",
        string="Dados de Pagamento.", xsd_required=True
    )
    bpe10_autXML = fields.One2many(
        "bpe.10.autxml",
        "bpe10_autXML_infBPe_id",
        string="Autorizados para download do XML do DF",
        help="Autorizados para download do XML do DF-e"
    )
    bpe10_infAdic = fields.Many2one(
        "bpe.10.infadic",
        string="Informações Adicionais")


class InfPassageiro(spec_models.AbstractSpecMixin):
    "Informações do passageiro"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.infpassageiro'
    _generateds_type = 'infPassageiroType'
    _concrete_rec_name = 'bpe_xNome'

    bpe10_xNome = fields.Char(
        string="Nome do Passageiro", xsd_required=True)
    bpe10_CPF = fields.Char(
        string="Número do CPF")
    bpe10_tpDoc = fields.Selection(
        TDoc_infPassageiro,
        string="Tipo do Documento de identificação",
        xsd_required=True)
    bpe10_nDoc = fields.Char(
        string="Número do Documento do passageiro",
        xsd_required=True)
    bpe10_dNasc = fields.Char(
        string="Data de Nascimento")
    bpe10_fone = fields.Char(
        string="Telefone")
    bpe10_email = fields.Char(
        string="Endereço de E-mail")


class InfPassagem(spec_models.AbstractSpecMixin):
    "Informações do detalhamento da Passagem"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.infpassagem'
    _generateds_type = 'infPassagemType'
    _concrete_rec_name = 'bpe_cLocOrig'

    bpe10_cLocOrig = fields.Char(
        string="Código da Localidade de Origem",
        xsd_required=True)
    bpe10_xLocOrig = fields.Char(
        string="Descrição da Localidade de Origem",
        xsd_required=True)
    bpe10_cLocDest = fields.Char(
        string="None", xsd_required=True)
    bpe10_xLocDest = fields.Char(
        string="Descrição da Localidade de Destino",
        xsd_required=True)
    bpe10_dhEmb = fields.Datetime(
        string="Data e hora de embarque",
        xsd_required=True)
    bpe10_dhValidade = fields.Datetime(
        string="Data e hora de validade do bilhete",
        xsd_required=True)
    bpe10_infPassageiro = fields.Many2one(
        "bpe.10.infpassageiro",
        string="Informações do passageiro")


class InfProt(spec_models.AbstractSpecMixin):
    "Dados do protocolo de status"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.infprot'
    _generateds_type = 'infProtType'
    _concrete_rec_name = 'bpe_Id'

    bpe10_Id = fields.Char(
        string="Id")
    bpe10_tpAmb = fields.Selection(
        TAmb,
        string="Identificação do Ambiente",
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    bpe10_verAplic = fields.Char(
        string="Versão do Aplicativo que processou o BP",
        xsd_required=True,
        help="Versão do Aplicativo que processou o BP-e")
    bpe10_chBPe = fields.Char(
        string="Chave de acesso do BP-e",
        xsd_required=True)
    bpe10_dhRecbto = fields.Datetime(
        string="Data e hora de processamento",
        xsd_required=True,
        help="Data e hora de processamento, no formato AAAA-MM-DDTHH:MM:SS"
        "\nTZD.")
    bpe10_nProt = fields.Char(
        string="Número do Protocolo de Status do BP",
        help="Número do Protocolo de Status do BP-e.")
    bpe10_digVal = fields.Char(
        string="Digest Value do BP-e processado",
        help="Digest Value do BP-e processado. Utilizado para conferir a"
        "\nintegridade do BP-e original.")
    bpe10_cStat = fields.Char(
        string="Código do status do BP-e.",
        xsd_required=True)
    bpe10_xMotivo = fields.Char(
        string="Descrição literal do status do BP-e.",
        xsd_required=True)


class InfTravessia(spec_models.AbstractSpecMixin):
    "Informações do transporte aquaviário de travessia"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.inftravessia'
    _generateds_type = 'infTravessiaType'
    _concrete_rec_name = 'bpe_tpVeiculo'

    bpe10_tpVeiculo = fields.Selection(
        tpVeiculo_infTravessia,
        string="Tipo do veículo transportado",
        xsd_required=True)
    bpe10_sitVeiculo = fields.Selection(
        sitVeiculo_infTravessia,
        string="Situação do veículo transportado",
        xsd_required=True)


class InfValorBPe(spec_models.AbstractSpecMixin):
    "Informações dos valores do Bilhete de Passagem"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.infvalorbpe'
    _generateds_type = 'infValorBPeType'
    _concrete_rec_name = 'bpe_vBP'

    bpe10_vBP = fields.Monetary(
        digits=2, string="Valor do Bilhete de Passagem",
        xsd_required=True)
    bpe10_vDesconto = fields.Monetary(
        digits=2, string="Valor do desconto concedido ao comprador",
        xsd_required=True)
    bpe10_vPgto = fields.Monetary(
        digits=2, string="Valor pago pelo BP-e",
        xsd_required=True,
        help="Valor pago pelo BP-e (vBP - vDesconto)")
    bpe10_vTroco = fields.Monetary(
        digits=2, string="Valor do troco", xsd_required=True)
    bpe10_tpDesconto = fields.Selection(
        tpDesconto_infValorBPe,
        string="Tipo de desconto/benefício para o BP",
        help="Tipo de desconto/benefício para o BP-e")
    bpe10_xDesconto = fields.Char(
        string="Descrição do tipo de desconto/benefício concedido")
    bpe10_Comp = fields.One2many(
        "bpe.10.comp",
        "bpe10_Comp_infValorBPe_id",
        string="Componentes do Valor do Bilhete",
        xsd_required=True
    )


class InfViagem(spec_models.AbstractSpecMixin):
    "Grupo de informações da viagem do BP-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.infviagem'
    _generateds_type = 'infViagemType'
    _concrete_rec_name = 'bpe_cPercurso'

    bpe10_infViagem_infBPe_id = fields.Many2one(
        "bpe.10.infbpe")
    bpe10_cPercurso = fields.Char(
        string="Código do percurso da viagem",
        xsd_required=True)
    bpe10_xPercurso = fields.Char(
        string="Descrição do Percurso da viagem",
        xsd_required=True)
    bpe10_tpViagem = fields.Selection(
        tpViagem_infViagem,
        string="Tipo de Viagem", xsd_required=True)
    bpe10_tpServ = fields.Selection(
        tpServ_infViagem,
        string="Tipo de Serviço", xsd_required=True)
    bpe10_tpAcomodacao = fields.Selection(
        tpAcomodacao_infViagem,
        string="Tipo de Acomodação",
        xsd_required=True)
    bpe10_tpTrecho = fields.Selection(
        tpTrecho_infViagem,
        string="Tipo de trecho da viagem",
        xsd_required=True)
    bpe10_dhViagem = fields.Datetime(
        string="Data e hora de referencia para a viagem",
        xsd_required=True)
    bpe10_dhConexao = fields.Datetime(
        string="Data e hora da conexão",
        help="Data e hora da conexão"
        "\nInformar se tpTrecho = 3")
    bpe10_prefixo = fields.Char(
        string="Prefixo da linha")
    bpe10_poltrona = fields.Char(
        string="Número da Poltrona / assento / cabine")
    bpe10_plataforma = fields.Char(
        string="Plataforma/carro/barco de Embarque")
    bpe10_infTravessia = fields.Many2one(
        "bpe.10.inftravessia",
        string="Informações do transporte aquaviário de travessia")


class Pag(spec_models.AbstractSpecMixin):
    "Dados de Pagamento."
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.pag'
    _generateds_type = 'pagType'
    _concrete_rec_name = 'bpe_tPag'

    bpe10_pag_infBPe_id = fields.Many2one(
        "bpe.10.infbpe")
    bpe10_tPag = fields.Selection(
        tPag_pag,
        string="Forma de Pagamento:01",
        xsd_required=True,
        help="Forma de Pagamento:01-Dinheiro;02-Cheque;03-Cartão de"
        "\nCrédito;04-Cartão de Débito;05-Vale Transportel;99 -"
        "\nOutros")
    bpe10_xPag = fields.Char(
        string="Descrição da forma de pagamento 99",
        help="Descrição da forma de pagamento 99 - Outros")
    bpe10_vPag = fields.Monetary(
        digits=2, string="Valor do Pagamento", xsd_required=True)
    bpe10_card = fields.Many2one(
        "bpe.10.card",
        string="Grupo de Cartões")
