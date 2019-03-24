# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Sun Mar 24 01:00:22 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# Tipo Ambiente
TAmb_ide = [
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

# Tipo Emitente
TEmit_ide = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
]

# Tipo Modelo Manifesto de Documento Fiscal Eletrônico
TModMD_ide = [
    ("58", "58"),
]

# Tipo Modal Manifesto
TModalMD_ide = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
]

# Tipo Transportador
TTransp_ide = [
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

# Tipo da Unidade de Carga
TtipoUnidCarga_TUnidCarga = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
]

# Tipo da Unidade de Transporte
TtipoUnidTransp_TUnidadeTransp = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
    ("6", "6"),
    ("7", "7"),
]

# Codigo da unidade de medida do Peso Bruto da Carga / Mercadorias
# transportadas
cUnid_tot = [
    ("01", "01"),
    ("02", "02"),
]

# Indicador de participação do Canal Verde
indCanalVerde_ide = [
    ("1", "1"),
]

# Indicador de Reentrega
indReentrega_infCTe = [
    ("1", "1"),
]

# Indicador de Reentrega
indReentrega_infNFe = [
    ("1", "1"),
]

# Indicador de Reentrega
indReentrega_infMDFeTransp = [
    ("1", "1"),
]

# Responsável pelo seguro
respSeg_infResp = [
    ("1", "1"),
    ("2", "2"),
]

# Forma de emissão do Manifesto (Normal ou Contingência)
tpEmis_ide = [
    ("1", "1"),
    ("2", "2"),
]

# Tipo de Navegação
tpNav_aquav = [
    ("0", "0"),
    ("1", "1"),
]

# Tipo da unidade de carga vazia
tpUnidCargaVazia_infUnidCargaVazia = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
]

# Tipo da unidade de transporte vazia
tpUnidTranspVazia_infUnidTranspVazia = [
    ("1", "1"),
    ("2", "2"),
]


class TEndOrg(spec_models.AbstractSpecMixin):
    "Tipo Dados do Endereço"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.tendorg'
    _generateds_type = 'TEndOrg'
    _concrete_rec_name = 'mdfe_xLgr'

    mdfe30_xLgr = fields.Char(
        string="Logradouro", xsd_required=True)
    mdfe30_nro = fields.Char(
        string="Número", xsd_required=True)
    mdfe30_xCpl = fields.Char(
        string="Complemento")
    mdfe30_xBairro = fields.Char(
        string="Bairro", xsd_required=True)
    mdfe30_cMun = fields.Char(
        string="Código do município", xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE), informar"
        "\n9999999 para operações com o exterior.")
    mdfe30_xMun = fields.Char(
        string="Nome do município", xsd_required=True,
        help="Nome do município, , informar EXTERIOR para operações com o"
        "\nexterior.")
    mdfe30_CEP = fields.Char(
        string="CEP")
    mdfe30_UF = fields.Selection(
        TUf,
        string="Sigla da UF", xsd_required=True,
        help="Sigla da UF, , informar EX para operações com o exterior.")
    mdfe30_cPais = fields.Char(
        string="Código do país")
    mdfe30_xPais = fields.Char(
        string="Nome do país")
    mdfe30_fone = fields.Char(
        string="Telefone")


class TEndReEnt(spec_models.AbstractSpecMixin):
    "Tipo Dados do Local de Retirada ou Entrega"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.tendreent'
    _generateds_type = 'TEndReEnt'
    _concrete_rec_name = 'mdfe_CNPJ'

    mdfe30_choice1 = fields.Selection([
        ('mdfe30_CNPJ', 'CNPJ'),
        ('mdfe30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="mdfe30_CNPJ")
    mdfe30_CNPJ = fields.Char(
        choice='1',
        string="Número do CNPJ", xsd_required=True)
    mdfe30_CPF = fields.Char(
        choice='1',
        string="Número do CPF", xsd_required=True)
    mdfe30_xNome = fields.Char(
        string="Razão Social ou Nome",
        xsd_required=True)
    mdfe30_xLgr = fields.Char(
        string="Logradouro", xsd_required=True)
    mdfe30_nro = fields.Char(
        string="Número", xsd_required=True)
    mdfe30_xCpl = fields.Char(
        string="Complemento")
    mdfe30_xBairro = fields.Char(
        string="Bairro", xsd_required=True)
    mdfe30_cMun = fields.Char(
        string="Código do município", xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE), informar"
        "\n9999999 para operações com o exterior.")
    mdfe30_xMun = fields.Char(
        string="Nome do município", xsd_required=True,
        help="Nome do município, , informar EXTERIOR para operações com o"
        "\nexterior.")
    mdfe30_UF = fields.Selection(
        TUf,
        string="Sigla da UF", xsd_required=True,
        help="Sigla da UF, , informar EX para operações com o exterior.")


class TEndeEmi(spec_models.AbstractSpecMixin):
    "Tipo Dados do Endereço"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.tendeemi'
    _generateds_type = 'TEndeEmi'
    _concrete_rec_name = 'mdfe_xLgr'

    mdfe30_xLgr = fields.Char(
        string="Logradouro", xsd_required=True)
    mdfe30_nro = fields.Char(
        string="Número", xsd_required=True)
    mdfe30_xCpl = fields.Char(
        string="Complemento")
    mdfe30_xBairro = fields.Char(
        string="Bairro", xsd_required=True)
    mdfe30_cMun = fields.Char(
        string="Código do município", xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE), informar"
        "\n9999999 para operações com o exterior.")
    mdfe30_xMun = fields.Char(
        string="Nome do município", xsd_required=True,
        help="Nome do município, , informar EXTERIOR para operações com o"
        "\nexterior.")
    mdfe30_CEP = fields.Char(
        string="CEP")
    mdfe30_UF = fields.Selection(
        TUf,
        string="Sigla da UF", xsd_required=True,
        help="Sigla da UF, , informar EX para operações com o exterior.")
    mdfe30_fone = fields.Char(
        string="Telefone")
    mdfe30_email = fields.Char(
        string="Endereço de E-mail")


class TEnderFer(spec_models.AbstractSpecMixin):
    "Tipo Dados do Endereço"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.tenderfer'
    _generateds_type = 'TEnderFer'
    _concrete_rec_name = 'mdfe_xLgr'

    mdfe30_xLgr = fields.Char(
        string="Logradouro", xsd_required=True)
    mdfe30_nro = fields.Char(
        string="Número")
    mdfe30_xCpl = fields.Char(
        string="Complemento")
    mdfe30_xBairro = fields.Char(
        string="Bairro")
    mdfe30_cMun = fields.Char(
        string="Código do município", xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE), informar"
        "\n9999999 para operações com o exterior.")
    mdfe30_xMun = fields.Char(
        string="Nome do município", xsd_required=True,
        help="Nome do município, , informar EXTERIOR para operações com o"
        "\nexterior.")
    mdfe30_CEP = fields.Char(
        string="CEP", xsd_required=True)
    mdfe30_UF = fields.Selection(
        TUf,
        string="Sigla da UF", xsd_required=True,
        help="Sigla da UF, , informar EX para operações com o exterior.")


class TEndereco(spec_models.AbstractSpecMixin):
    "Tipo Dados do Endereço"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.tendereco'
    _generateds_type = 'TEndereco'
    _concrete_rec_name = 'mdfe_xLgr'

    mdfe30_xLgr = fields.Char(
        string="Logradouro", xsd_required=True)
    mdfe30_nro = fields.Char(
        string="Número", xsd_required=True)
    mdfe30_xCpl = fields.Char(
        string="Complemento")
    mdfe30_xBairro = fields.Char(
        string="Bairro", xsd_required=True)
    mdfe30_cMun = fields.Char(
        string="Código do município", xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE), informar"
        "\n9999999 para operações com o exterior.")
    mdfe30_xMun = fields.Char(
        string="Nome do município", xsd_required=True,
        help="Nome do município, informar EXTERIOR para operações com o"
        "\nexterior.")
    mdfe30_CEP = fields.Char(
        string="CEP")
    mdfe30_UF = fields.Selection(
        TUf,
        string="Sigla da UF", xsd_required=True,
        help="Sigla da UF, informar EX para operações com o exterior.")
    mdfe30_cPais = fields.Char(
        string="Código do país")
    mdfe30_xPais = fields.Char(
        string="Nome do país")


class TEndernac(spec_models.AbstractSpecMixin):
    "Tipo Dados do Endereço"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.tendernac'
    _generateds_type = 'TEndernac'
    _concrete_rec_name = 'mdfe_xLgr'

    mdfe30_xLgr = fields.Char(
        string="Logradouro", xsd_required=True)
    mdfe30_nro = fields.Char(
        string="Número", xsd_required=True)
    mdfe30_xCpl = fields.Char(
        string="Complemento")
    mdfe30_xBairro = fields.Char(
        string="Bairro", xsd_required=True)
    mdfe30_cMun = fields.Char(
        string="Código do município", xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE), informar"
        "\n9999999 para operações com o exterior.")
    mdfe30_xMun = fields.Char(
        string="Nome do município", xsd_required=True,
        help="Nome do município, , informar EXTERIOR para operações com o"
        "\nexterior.")
    mdfe30_CEP = fields.Char(
        string="CEP")
    mdfe30_UF = fields.Selection(
        TUf,
        string="Sigla da UF", xsd_required=True,
        help="Sigla da UF, , informar EX para operações com o exterior.")


class TEnviMDFe(spec_models.AbstractSpecMixin):
    "Tipo Pedido de Concessão de Autorização de MDF-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.tenvimdfe'
    _generateds_type = 'TEnviMDFe'
    _concrete_rec_name = 'mdfe_versao'

    mdfe30_versao = fields.Char(
        string="versao", xsd_required=True)
    mdfe30_idLote = fields.Char(
        string="idLote", xsd_required=True)
    mdfe30_MDFe = fields.Many2one(
        "mdfe.30.tmdfe",
        string="MDFe", xsd_required=True)


class TLocal(spec_models.AbstractSpecMixin):
    "Tipo Dados do Local de Origem ou Destino"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.tlocal'
    _generateds_type = 'TLocal'
    _concrete_rec_name = 'mdfe_cMun'

    mdfe30_cMun = fields.Char(
        string="Código do município", xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE)")
    mdfe30_xMun = fields.Char(
        string="Nome do município", xsd_required=True)
    mdfe30_UF = fields.Selection(
        TUf,
        string="Sigla da UF", xsd_required=True)


class TMDFe(spec_models.AbstractSpecMixin):
    "Tipo Manifesto de Documentos Fiscais Eletrônicos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.tmdfe'
    _generateds_type = 'TMDFe'
    _concrete_rec_name = 'mdfe_infMDFe'

    mdfe30_infMDFe = fields.Many2one(
        "mdfe.30.infmdfe",
        string="Informações do MDF-e",
        xsd_required=True)


class TNFeNF(spec_models.AbstractSpecMixin):
    "Tipo de Dados das Notas Fiscais Papel e Eletrônica"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.tnfenf'
    _generateds_type = 'TNFeNF'
    _concrete_rec_name = 'mdfe_infNFe'

    mdfe30_choice2 = fields.Selection([
        ('mdfe30_infNFe', 'infNFe'),
        ('mdfe30_infNF', 'infNF')],
        "infNFe/infNF",
        default="mdfe30_infNFe")
    mdfe30_infNFe = fields.Many2one(
        "mdfe.30.infnfe51",
        choice='2',
        string="Informações da NF-e",
        xsd_required=True)
    mdfe30_infNF = fields.Many2one(
        "mdfe.30.infnf",
        choice='2',
        string="Informações da NF mod 1 e 1A",
        xsd_required=True)


class TRespTec(spec_models.AbstractSpecMixin):
    "Tipo Dados da Responsável Técnico"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.tresptec'
    _generateds_type = 'TRespTec'
    _concrete_rec_name = 'mdfe_CNPJ'

    mdfe30_CNPJ = fields.Char(
        string="CNPJ", xsd_required=True,
        help="CNPJ da pessoa jurídica responsável técnica pelo sistema"
        "\nutilizado na emissão do documento fiscal eletrônico")
    mdfe30_xContato = fields.Char(
        string="Nome da pessoa a ser contatada",
        xsd_required=True)
    mdfe30_email = fields.Char(
        string="Email da pessoa jurídica a ser contatada",
        xsd_required=True)
    mdfe30_fone = fields.Char(
        string="Telefone da pessoa jurídica a ser contatada",
        xsd_required=True)
    mdfe30_idCSRT = fields.Char(
        string="idCSRT",
        help="Identificador do código de segurança do responsável técnico")
    mdfe30_hashCSRT = fields.Char(
        string="hashCSRT",
        help="Hash do token do código de segurança do responsável técnico")


class TRetEnviMDFe(spec_models.AbstractSpecMixin):
    "Tipo Retorno do Pedido de Concessão de Autorização do MDF-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.tretenvimdfe'
    _generateds_type = 'TRetEnviMDFe'
    _concrete_rec_name = 'mdfe_versao'

    mdfe30_versao = fields.Char(
        string="versao", xsd_required=True)
    mdfe30_tpAmb = fields.Char(
        string="Identificação do Ambiente",
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    mdfe30_cUF = fields.Selection(
        TCodUfIBGE,
        string="Identificação da UF", xsd_required=True)
    mdfe30_verAplic = fields.Char(
        string="Versão do Aplicativo que recebeu o Arquivo",
        xsd_required=True)
    mdfe30_cStat = fields.Char(
        string="Código do status da mensagem enviada",
        xsd_required=True)
    mdfe30_xMotivo = fields.Char(
        string="Descrição literal do status do serviço solicitado",
        xsd_required=True)
    mdfe30_infRec = fields.Many2one(
        "mdfe.30.infrec",
        string="Dados do Recibo do Arquivo")


class TUnidCarga(spec_models.AbstractSpecMixin):
    "Tipo Dados Unidade de Carga"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.tunidcarga'
    _generateds_type = 'TUnidCarga'
    _concrete_rec_name = 'mdfe_tpUnidCarga'

    mdfe30_infUnidCarga_TUnidadeTransp_id = fields.Many2one(
        "mdfe.30.tunidadetransp")
    mdfe30_tpUnidCarga = fields.Selection(
        TtipoUnidCarga_TUnidCarga,
        string="Tipo da Unidade de Carga",
        xsd_required=True)
    mdfe30_idUnidCarga = fields.Char(
        string="Identificação da Unidade de Carga",
        xsd_required=True)
    mdfe30_lacUnidCarga = fields.One2many(
        "mdfe.30.lacunidcarga",
        "mdfe30_lacUnidCarga_TUnidCarga_id",
        string="Lacres das Unidades de Carga"
    )
    mdfe30_qtdRat = fields.Char(
        string="Quantidade rateada (Peso,Volume)")


class TUnidadeTransp(spec_models.AbstractSpecMixin):
    "Tipo Dados Unidade de Transporte"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.tunidadetransp'
    _generateds_type = 'TUnidadeTransp'
    _concrete_rec_name = 'mdfe_tpUnidTransp'

    mdfe30_infUnidTransp_infCTe_id = fields.Many2one(
        "mdfe.30.infcte")
    mdfe30_infUnidTransp_infMDFeTransp_id = fields.Many2one(
        "mdfe.30.infmdfetransp")
    mdfe30_infUnidTransp_infNFe_id = fields.Many2one(
        "mdfe.30.infnfe")
    mdfe30_tpUnidTransp = fields.Selection(
        TtipoUnidTransp_TUnidadeTransp,
        string="Tipo da Unidade de Transporte",
        xsd_required=True)
    mdfe30_idUnidTransp = fields.Char(
        string="Identificação da Unidade de Transporte",
        xsd_required=True)
    mdfe30_lacUnidTransp = fields.One2many(
        "mdfe.30.lacunidtransp",
        "mdfe30_lacUnidTransp_TUnidadeTransp_id",
        string="Lacres das Unidades de Transporte"
    )
    mdfe30_infUnidCarga = fields.One2many(
        "mdfe.30.tunidcarga",
        "mdfe30_infUnidCarga_TUnidadeTransp_id",
        string="Informações das Unidades de Carga",
        help="Informações das Unidades de Carga (Containeres/ULD/Outros)"
    )
    mdfe30_qtdRat = fields.Monetary(
        digits=2, string="Quantidade rateada (Peso,Volume)")


class Aquav(spec_models.AbstractSpecMixin):
    "Informações do modal Aquaviário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.aquav'
    _generateds_type = 'aquav'
    _concrete_rec_name = 'mdfe_irin'

    mdfe30_irin = fields.Char(
        string="irin", xsd_required=True)
    mdfe30_tpEmb = fields.Char(
        string="tpEmb", xsd_required=True)
    mdfe30_cEmbar = fields.Char(
        string="cEmbar", xsd_required=True)
    mdfe30_xEmbar = fields.Char(
        string="xEmbar", xsd_required=True)
    mdfe30_nViag = fields.Char(
        string="nViag", xsd_required=True)
    mdfe30_cPrtEmb = fields.Char(
        string="cPrtEmb", xsd_required=True)
    mdfe30_cPrtDest = fields.Char(
        string="cPrtDest", xsd_required=True)
    mdfe30_prtTrans = fields.Char(
        string="prtTrans")
    mdfe30_tpNav = fields.Selection(
        tpNav_aquav,
        string="tpNav")
    mdfe30_infTermCarreg = fields.One2many(
        "mdfe.30.inftermcarreg",
        "mdfe30_infTermCarreg_aquav_id",
        string="infTermCarreg"
    )
    mdfe30_infTermDescarreg = fields.One2many(
        "mdfe.30.inftermdescarreg",
        "mdfe30_infTermDescarreg_aquav_id",
        string="infTermDescarreg"
    )
    mdfe30_infEmbComb = fields.One2many(
        "mdfe.30.infembcomb",
        "mdfe30_infEmbComb_aquav_id",
        string="infEmbComb"
    )
    mdfe30_infUnidCargaVazia = fields.One2many(
        "mdfe.30.infunidcargavazia",
        "mdfe30_infUnidCargaVazia_aquav_id",
        string="infUnidCargaVazia"
    )
    mdfe30_infUnidTranspVazia = fields.One2many(
        "mdfe.30.infunidtranspvazia",
        "mdfe30_infUnidTranspVazia_aquav_id",
        string="infUnidTranspVazia"
    )


class AutXML(spec_models.AbstractSpecMixin):
    """Autorizados para download do XML do DF-eInformar CNPJ ou CPF. Preencher
    os zeros não significativos."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.autxml'
    _generateds_type = 'autXMLType'
    _concrete_rec_name = 'mdfe_CNPJ'

    mdfe30_autXML_infMDFe_id = fields.Many2one(
        "mdfe.30.infmdfe")
    mdfe30_choice5 = fields.Selection([
        ('mdfe30_CNPJ', 'CNPJ'),
        ('mdfe30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="mdfe30_CNPJ")
    mdfe30_CNPJ = fields.Char(
        choice='5',
        string="CNPJ do autorizado", xsd_required=True)
    mdfe30_CPF = fields.Char(
        choice='5',
        string="CPF do autorizado", xsd_required=True)


class Dest(spec_models.AbstractSpecMixin):
    "Informações do Destinatário da NF"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.dest'
    _generateds_type = 'destType'
    _concrete_rec_name = 'mdfe_CNPJ'

    mdfe30_choice6 = fields.Selection([
        ('mdfe30_CNPJ', 'CNPJ'),
        ('mdfe30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="mdfe30_CNPJ")
    mdfe30_CNPJ = fields.Char(
        choice='6',
        string="CNPJ do Destinatário",
        xsd_required=True)
    mdfe30_CPF = fields.Char(
        choice='6',
        string="CPF do Destinatário", xsd_required=True)
    mdfe30_xNome = fields.Char(
        string="Razão Social ou Nome",
        xsd_required=True)
    mdfe30_UF = fields.Selection(
        TUf,
        string="UF do Destinatário", xsd_required=True)


class Emi(spec_models.AbstractSpecMixin):
    "Informações do Emitente da NF"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.emi'
    _generateds_type = 'emiType'
    _concrete_rec_name = 'mdfe_CNPJ'

    mdfe30_CNPJ = fields.Char(
        string="CNPJ do emitente", xsd_required=True)
    mdfe30_xNome = fields.Char(
        string="Razão Social ou Nome",
        xsd_required=True)
    mdfe30_UF = fields.Selection(
        TUf,
        string="UF do Emitente", xsd_required=True)


class Emit(spec_models.AbstractSpecMixin):
    "Identificação do Emitente do Manifesto"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.emit'
    _generateds_type = 'emitType'
    _concrete_rec_name = 'mdfe_CNPJ'

    mdfe30_choice3 = fields.Selection([
        ('mdfe30_CNPJ', 'CNPJ'),
        ('mdfe30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="mdfe30_CNPJ")
    mdfe30_CNPJ = fields.Char(
        choice='3',
        string="CNPJ do emitente", xsd_required=True)
    mdfe30_CPF = fields.Char(
        choice='3',
        string="CPF do emitente", xsd_required=True)
    mdfe30_IE = fields.Char(
        string="Inscrição Estadual do emitemte",
        xsd_required=True)
    mdfe30_xNome = fields.Char(
        string="Razão social ou Nome do emitente",
        xsd_required=True)
    mdfe30_xFant = fields.Char(
        string="Nome fantasia do emitente")
    mdfe30_enderEmit = fields.Many2one(
        "mdfe.30.tendeemi",
        string="Endereço do emitente",
        xsd_required=True)


class Ide(spec_models.AbstractSpecMixin):
    "Identificação do MDF-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.ide'
    _generateds_type = 'ideType'
    _concrete_rec_name = 'mdfe_cUF'

    mdfe30_cUF = fields.Selection(
        TCodUfIBGE,
        string="Código da UF do emitente do MDF-e",
        xsd_required=True)
    mdfe30_tpAmb = fields.Selection(
        TAmb_ide,
        string="Tipo do Ambiente", xsd_required=True)
    mdfe30_tpEmit = fields.Selection(
        TEmit_ide,
        string="Tipo do Emitente", xsd_required=True)
    mdfe30_tpTransp = fields.Selection(
        TTransp_ide,
        string="Tipo do Transportador")
    mdfe30_mod = fields.Selection(
        TModMD_ide,
        string="Modelo do Manifesto Eletrônico",
        xsd_required=True)
    mdfe30_serie = fields.Char(
        string="Série do Manifesto", xsd_required=True)
    mdfe30_nMDF = fields.Char(
        string="Número do Manifesto", xsd_required=True)
    mdfe30_cMDF = fields.Char(
        string="Código numérico que compõe a Chave de Acesso",
        xsd_required=True,
        help="Código numérico que compõe a Chave de Acesso.")
    mdfe30_cDV = fields.Char(
        string="Digito verificador da chave de acesso do Manifesto",
        xsd_required=True)
    mdfe30_modal = fields.Selection(
        TModalMD_ide,
        string="Modalidade de transporte",
        xsd_required=True)
    mdfe30_dhEmi = fields.Datetime(
        string="Data e hora de emissão do Manifesto",
        xsd_required=True)
    mdfe30_tpEmis = fields.Selection(
        tpEmis_ide,
        string="Forma de emissão do Manifesto",
        xsd_required=True,
        help="Forma de emissão do Manifesto (Normal ou Contingência)")
    mdfe30_procEmi = fields.Char(
        string="Identificação do processo de emissão do Manifesto",
        xsd_required=True)
    mdfe30_verProc = fields.Char(
        string="Versão do processo de emissão",
        xsd_required=True)
    mdfe30_UFIni = fields.Selection(
        TUf,
        string="Sigla da UF do Carregamento",
        xsd_required=True)
    mdfe30_UFFim = fields.Selection(
        TUf,
        string="Sigla da UF do Descarregamento",
        xsd_required=True)
    mdfe30_infMunCarrega = fields.One2many(
        "mdfe.30.infmuncarrega",
        "mdfe30_infMunCarrega_ide_id",
        string="Informações dos Municípios de Carregamento",
        xsd_required=True
    )
    mdfe30_infPercurso = fields.One2many(
        "mdfe.30.infpercurso",
        "mdfe30_infPercurso_ide_id",
        string="Informações do Percurso do MDF-e"
    )
    mdfe30_dhIniViagem = fields.Datetime(
        string="Data e hora previstos de inicio da viagem")
    mdfe30_indCanalVerde = fields.Selection(
        indCanalVerde_ide,
        string="Indicador de participação do Canal Verde")


class InfAdic(spec_models.AbstractSpecMixin):
    "Informações Adicionais"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infadic'
    _generateds_type = 'infAdicType'
    _concrete_rec_name = 'mdfe_infAdFisco'

    mdfe30_infAdFisco = fields.Char(
        string="Informações adicionais de interesse do Fisco")
    mdfe30_infCpl = fields.Char(
        string="Informações complementares de interesse do Contribuinte")


class InfCTe(spec_models.AbstractSpecMixin):
    """Conhecimentos de Tranporte - usar este grupo quando for prestador de
    serviço de transporte"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infcte'
    _generateds_type = 'infCTeType'
    _concrete_rec_name = 'mdfe_chCTe'

    mdfe30_infCTe_infMunDescarga_id = fields.Many2one(
        "mdfe.30.infmundescarga")
    mdfe30_chCTe = fields.Char(
        string="Conhecimento Eletrônico",
        xsd_required=True,
        help="Conhecimento Eletrônico - Chave de Acesso")
    mdfe30_SegCodBarra = fields.Char(
        string="Segundo código de barras")
    mdfe30_indReentrega = fields.Selection(
        indReentrega_infCTe,
        string="Indicador de Reentrega")
    mdfe30_infUnidTransp = fields.One2many(
        "mdfe.30.tunidadetransp",
        "mdfe30_infUnidTransp_infCTe_id",
        string="Informações das Unidades de Transporte",
        help="Informações das Unidades de Transporte"
        "\n(Carreta/Reboque/Vagão)"
    )
    mdfe30_peri = fields.One2many(
        "mdfe.30.peri",
        "mdfe30_peri_infCTe_id",
        string="peri",
        help="Preenchido quando for transporte de produtos classificados"
        "\npela ONU como perigosos."
    )
    mdfe30_infEntregaParcial = fields.Many2one(
        "mdfe.30.infentregaparcial",
        string="Grupo de informações da Entrega Parcial",
        help="Grupo de informações da Entrega Parcial (Corte de Voo)")


class InfDoc(spec_models.AbstractSpecMixin):
    "Informações dos Documentos fiscais vinculados ao manifesto"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infdoc'
    _generateds_type = 'infDocType'
    _concrete_rec_name = 'mdfe_infMunDescarga'

    mdfe30_infMunDescarga = fields.One2many(
        "mdfe.30.infmundescarga",
        "mdfe30_infMunDescarga_infDoc_id",
        string="Informações dos Municípios de descarregamento",
        xsd_required=True
    )


class InfEmbComb(spec_models.AbstractSpecMixin):
    "Informações das Embarcações do Comboio"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infembcomb'
    _generateds_type = 'infEmbCombType'
    _concrete_rec_name = 'mdfe_cEmbComb'

    mdfe30_infEmbComb_aquav_id = fields.Many2one(
        "mdfe.30.aquav")
    mdfe30_cEmbComb = fields.Char(
        string="Código da embarcação do comboio",
        xsd_required=True)
    mdfe30_xBalsa = fields.Char(
        string="Identificador da Balsa",
        xsd_required=True)


class InfEntregaParcial(spec_models.AbstractSpecMixin):
    "Grupo de informações da Entrega Parcial (Corte de Voo)"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infentregaparcial'
    _generateds_type = 'infEntregaParcialType'
    _concrete_rec_name = 'mdfe_qtdTotal'

    mdfe30_qtdTotal = fields.Monetary(
        digits=4, string="Quantidade total de volumes",
        xsd_required=True)
    mdfe30_qtdParcial = fields.Monetary(
        digits=4, string="Quantidade de volumes enviados no MDF",
        xsd_required=True,
        help="Quantidade de volumes enviados no MDF-e")


class InfMDFeTransp(spec_models.AbstractSpecMixin):
    """Manifesto Eletrônico de Documentos Fiscais. Somente para modal
    Aquaviário (vide regras MOC)"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infmdfetransp'
    _generateds_type = 'infMDFeTranspType'
    _concrete_rec_name = 'mdfe_chMDFe'

    mdfe30_infMDFeTransp_infMunDescarga_id = fields.Many2one(
        "mdfe.30.infmundescarga")
    mdfe30_chMDFe = fields.Char(
        string="Manifesto Eletrônico de Documentos Fiscais",
        xsd_required=True)
    mdfe30_indReentrega = fields.Selection(
        indReentrega_infMDFeTransp,
        string="Indicador de Reentrega")
    mdfe30_infUnidTransp = fields.One2many(
        "mdfe.30.tunidadetransp",
        "mdfe30_infUnidTransp_infMDFeTransp_id",
        string="Informações das Unidades de Transporte",
        help="Informações das Unidades de Transporte"
        "\n(Carreta/Reboque/Vagão)"
    )
    mdfe30_peri = fields.One2many(
        "mdfe.30.peri10",
        "mdfe30_peri_infMDFeTransp_id",
        string="peri",
        help="Preenchido quando for transporte de produtos classificados"
        "\npela ONU como perigosos."
    )


class InfMDFe(spec_models.AbstractSpecMixin):
    """Informações do MDF-eVersão do leiauteEx: "3.00"Identificador da tag a
    ser assinadaInformar a chave de acesso do MDF-e e precedida do literal
    "MDFe" """
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infmdfe'
    _generateds_type = 'infMDFeType'
    _concrete_rec_name = 'mdfe_versao'

    mdfe30_versao = fields.Char(
        string="versao", xsd_required=True)
    mdfe30_Id = fields.Char(
        string="Id", xsd_required=True)
    mdfe30_ide = fields.Many2one(
        "mdfe.30.ide",
        string="Identificação do MDF-e",
        xsd_required=True)
    mdfe30_emit = fields.Many2one(
        "mdfe.30.emit",
        string="Identificação do Emitente do Manifesto",
        xsd_required=True)
    mdfe30_infModal = fields.Many2one(
        "mdfe.30.infmodal",
        string="Informações do modal",
        xsd_required=True)
    mdfe30_infDoc = fields.Many2one(
        "mdfe.30.infdoc",
        string="Informações dos Documentos fiscais vinculados ao manifesto",
        xsd_required=True)
    mdfe30_seg = fields.One2many(
        "mdfe.30.seg",
        "mdfe30_seg_infMDFe_id",
        string="Informações de Seguro da Carga"
    )
    mdfe30_tot = fields.Many2one(
        "mdfe.30.tot",
        string="tot", xsd_required=True,
        help="Totalizadores da carga transportada e seus documentos fiscais")
    mdfe30_lacres = fields.One2many(
        "mdfe.30.lacres",
        "mdfe30_lacres_infMDFe_id",
        string="Lacres do MDF-e"
    )
    mdfe30_autXML = fields.One2many(
        "mdfe.30.autxml",
        "mdfe30_autXML_infMDFe_id",
        string="Autorizados para download do XML do DF",
        help="Autorizados para download do XML do DF-e"
    )
    mdfe30_infAdic = fields.Many2one(
        "mdfe.30.infadic",
        string="Informações Adicionais")
    mdfe30_infRespTec = fields.Many2one(
        "mdfe.30.tresptec",
        string="Informações do Responsável Técnico pela emissão do DF",
        help="Informações do Responsável Técnico pela emissão do DF-e")


class InfModal(spec_models.AbstractSpecMixin):
    "Informações do modalVersão do leiaute específico para o Modal"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infmodal'
    _generateds_type = 'infModalType'
    _concrete_rec_name = 'mdfe_versaoModal'

    mdfe30_versaoModal = fields.Char(
        string="versaoModal", xsd_required=True)
    mdfe30___ANY__ = fields.Char(
        string="__ANY__", xsd_required=True)


class InfMunCarrega(spec_models.AbstractSpecMixin):
    "Informações dos Municípios de Carregamento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infmuncarrega'
    _generateds_type = 'infMunCarregaType'
    _concrete_rec_name = 'mdfe_cMunCarrega'

    mdfe30_infMunCarrega_ide_id = fields.Many2one(
        "mdfe.30.ide")
    mdfe30_cMunCarrega = fields.Char(
        string="Código do Município de Carregamento",
        xsd_required=True)
    mdfe30_xMunCarrega = fields.Char(
        string="Nome do Município de Carregamento",
        xsd_required=True)


class InfMunDescarga(spec_models.AbstractSpecMixin):
    "Informações dos Municípios de descarregamento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infmundescarga'
    _generateds_type = 'infMunDescargaType'
    _concrete_rec_name = 'mdfe_cMunDescarga'

    mdfe30_infMunDescarga_infDoc_id = fields.Many2one(
        "mdfe.30.infdoc")
    mdfe30_cMunDescarga = fields.Char(
        string="Código do Município de Descarregamento",
        xsd_required=True)
    mdfe30_xMunDescarga = fields.Char(
        string="Nome do Município de Descarregamento",
        xsd_required=True)
    mdfe30_infCTe = fields.One2many(
        "mdfe.30.infcte",
        "mdfe30_infCTe_infMunDescarga_id",
        string="Conhecimentos de Tranporte",
        help="Conhecimentos de Tranporte - usar este grupo quando for"
        "\nprestador de serviço de transporte"
    )
    mdfe30_infNFe = fields.One2many(
        "mdfe.30.infnfe",
        "mdfe30_infNFe_infMunDescarga_id",
        string="Nota Fiscal Eletronica"
    )
    mdfe30_infMDFeTransp = fields.One2many(
        "mdfe.30.infmdfetransp",
        "mdfe30_infMDFeTransp_infMunDescarga_id",
        string="Manifesto Eletrônico de Documentos Fiscais",
        help="Manifesto Eletrônico de Documentos Fiscais. Somente para"
        "\nmodal Aquaviário (vide regras MOC)"
    )


class InfNF(spec_models.AbstractSpecMixin):
    "Informações da NF mod 1 e 1A"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infnf'
    _generateds_type = 'infNFType'
    _concrete_rec_name = 'mdfe_emi'

    mdfe30_emi = fields.Many2one(
        "mdfe.30.emi",
        string="Informações do Emitente da NF",
        xsd_required=True)
    mdfe30_dest = fields.Many2one(
        "mdfe.30.dest",
        string="Informações do Destinatário da NF",
        xsd_required=True)
    mdfe30_serie = fields.Char(
        string="Série", xsd_required=True)
    mdfe30_nNF = fields.Char(
        string="Número", xsd_required=True)
    mdfe30_dEmi = fields.Date(
        string="Data de Emissão", xsd_required=True)
    mdfe30_vNF = fields.Monetary(
        digits=2, string="Valor Total da NF", xsd_required=True)
    mdfe30_PIN = fields.Char(
        string="PIN SUFRAMA")


class InfNFe(spec_models.AbstractSpecMixin):
    "Nota Fiscal Eletronica"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infnfe'
    _generateds_type = 'infNFeType'
    _concrete_rec_name = 'mdfe_chNFe'

    mdfe30_infNFe_infMunDescarga_id = fields.Many2one(
        "mdfe.30.infmundescarga")
    mdfe30_chNFe = fields.Char(
        string="Nota Fiscal Eletrônica",
        xsd_required=True)
    mdfe30_SegCodBarra = fields.Char(
        string="Segundo código de barras")
    mdfe30_indReentrega = fields.Selection(
        indReentrega_infNFe,
        string="Indicador de Reentrega")
    mdfe30_infUnidTransp = fields.One2many(
        "mdfe.30.tunidadetransp",
        "mdfe30_infUnidTransp_infNFe_id",
        string="Informações das Unidades de Transporte",
        help="Informações das Unidades de Transporte"
        "\n(Carreta/Reboque/Vagão)"
    )
    mdfe30_peri = fields.One2many(
        "mdfe.30.peri2",
        "mdfe30_peri_infNFe_id",
        string="peri",
        help="Preenchido quando for transporte de produtos classificados"
        "\npela ONU como perigosos."
    )


class InfNFe51(spec_models.AbstractSpecMixin):
    "Informações da NF-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infnfe51'
    _generateds_type = 'infNFeType51'
    _concrete_rec_name = 'mdfe_chNFe'

    mdfe30_chNFe = fields.Char(
        string="Chave de acesso da NF-e",
        xsd_required=True)
    mdfe30_PIN = fields.Char(
        string="PIN SUFRAMA")


class InfPercurso(spec_models.AbstractSpecMixin):
    "Informações do Percurso do MDF-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infpercurso'
    _generateds_type = 'infPercursoType'
    _concrete_rec_name = 'mdfe_UFPer'

    mdfe30_infPercurso_ide_id = fields.Many2one(
        "mdfe.30.ide")
    mdfe30_UFPer = fields.Selection(
        TUf,
        string="Sigla das Unidades da Federação do percurso do veículo",
        xsd_required=True)


class InfRec(spec_models.AbstractSpecMixin):
    "Dados do Recibo do Arquivo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infrec'
    _generateds_type = 'infRecType'
    _concrete_rec_name = 'mdfe_nRec'

    mdfe30_nRec = fields.Char(
        string="Número do Recibo", xsd_required=True)
    mdfe30_dhRecbto = fields.Datetime(
        string="Data e hora do recebimento",
        xsd_required=True,
        help="Data e hora do recebimento, no formato AAAA-MM-DDTHH:MM:SS")
    mdfe30_tMed = fields.Integer(
        string="Tempo médio de resposta do serviço",
        xsd_required=True,
        help="Tempo médio de resposta do serviço (em segundos) dos últimos"
        "\n5 minutos")


class InfResp(spec_models.AbstractSpecMixin):
    "Informações do responsável pelo seguro da carga"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infresp'
    _generateds_type = 'infRespType'
    _concrete_rec_name = 'mdfe_respSeg'

    mdfe30_choice4 = fields.Selection([
        ('mdfe30_CNPJ', 'CNPJ'),
        ('mdfe30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="mdfe30_CNPJ")
    mdfe30_respSeg = fields.Selection(
        respSeg_infResp,
        string="Responsável pelo seguro",
        xsd_required=True)
    mdfe30_CNPJ = fields.Char(
        choice='4',
        string="Número do CNPJ do responsável pelo seguro")
    mdfe30_CPF = fields.Char(
        choice='4',
        string="Número do CPF do responsável pelo seguro")


class InfSeg(spec_models.AbstractSpecMixin):
    "Informações da seguradora"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infseg'
    _generateds_type = 'infSegType'
    _concrete_rec_name = 'mdfe_xSeg'

    mdfe30_xSeg = fields.Char(
        string="Nome da Seguradora", xsd_required=True)
    mdfe30_CNPJ = fields.Char(
        string="Número do CNPJ da seguradora",
        xsd_required=True)


class InfTermCarreg(spec_models.AbstractSpecMixin):
    "Grupo de informações dos terminais de carregamento."
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.inftermcarreg'
    _generateds_type = 'infTermCarregType'
    _concrete_rec_name = 'mdfe_cTermCarreg'

    mdfe30_infTermCarreg_aquav_id = fields.Many2one(
        "mdfe.30.aquav")
    mdfe30_cTermCarreg = fields.Char(
        string="Código do Terminal de Carregamento",
        xsd_required=True)
    mdfe30_xTermCarreg = fields.Char(
        string="Nome do Terminal de Carregamento",
        xsd_required=True)


class InfTermDescarreg(spec_models.AbstractSpecMixin):
    "Grupo de informações dos terminais de descarregamento."
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.inftermdescarreg'
    _generateds_type = 'infTermDescarregType'
    _concrete_rec_name = 'mdfe_cTermDescarreg'

    mdfe30_infTermDescarreg_aquav_id = fields.Many2one(
        "mdfe.30.aquav")
    mdfe30_cTermDescarreg = fields.Char(
        string="Código do Terminal de Descarregamento",
        xsd_required=True)
    mdfe30_xTermDescarreg = fields.Char(
        string="Nome do Terminal de Descarregamento",
        xsd_required=True)


class InfUnidCargaVazia(spec_models.AbstractSpecMixin):
    "Informações das Undades de Carga vazias"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infunidcargavazia'
    _generateds_type = 'infUnidCargaVaziaType'
    _concrete_rec_name = 'mdfe_idUnidCargaVazia'

    mdfe30_infUnidCargaVazia_aquav_id = fields.Many2one(
        "mdfe.30.aquav")
    mdfe30_idUnidCargaVazia = fields.Char(
        string="Identificação da unidades de carga vazia",
        xsd_required=True)
    mdfe30_tpUnidCargaVazia = fields.Selection(
        tpUnidCargaVazia_infUnidCargaVazia,
        string="Tipo da unidade de carga vazia",
        xsd_required=True)


class InfUnidTranspVazia(spec_models.AbstractSpecMixin):
    "Informações das Undades de Transporte vazias"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infunidtranspvazia'
    _generateds_type = 'infUnidTranspVaziaType'
    _concrete_rec_name = 'mdfe_idUnidTranspVazia'

    mdfe30_infUnidTranspVazia_aquav_id = fields.Many2one(
        "mdfe.30.aquav")
    mdfe30_idUnidTranspVazia = fields.Char(
        string="Identificação da unidades de transporte vazia",
        xsd_required=True)
    mdfe30_tpUnidTranspVazia = fields.Selection(
        tpUnidTranspVazia_infUnidTranspVazia,
        string="Tipo da unidade de transporte vazia",
        xsd_required=True)


class LacUnidCarga(spec_models.AbstractSpecMixin):
    "Lacres das Unidades de Carga"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.lacunidcarga'
    _generateds_type = 'lacUnidCargaType'
    _concrete_rec_name = 'mdfe_nLacre'

    mdfe30_lacUnidCarga_TUnidCarga_id = fields.Many2one(
        "mdfe.30.tunidcarga")
    mdfe30_nLacre = fields.Char(
        string="Número do lacre", xsd_required=True)


class LacUnidTransp(spec_models.AbstractSpecMixin):
    "Lacres das Unidades de Transporte"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.lacunidtransp'
    _generateds_type = 'lacUnidTranspType'
    _concrete_rec_name = 'mdfe_nLacre'

    mdfe30_lacUnidTransp_TUnidadeTransp_id = fields.Many2one(
        "mdfe.30.tunidadetransp")
    mdfe30_nLacre = fields.Char(
        string="Número do lacre", xsd_required=True)


class Lacres(spec_models.AbstractSpecMixin):
    """Lacres do MDF-ePreechimento opcional para os modais Rodoviário e
    Ferroviário"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.lacres'
    _generateds_type = 'lacresType'
    _concrete_rec_name = 'mdfe_nLacre'

    mdfe30_lacres_infMDFe_id = fields.Many2one(
        "mdfe.30.infmdfe")
    mdfe30_nLacre = fields.Char(
        string="número do lacre", xsd_required=True)


class Peri(spec_models.AbstractSpecMixin):
    """Preenchido quando for transporte de produtos classificados pela ONU como
    perigosos."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.peri'
    _generateds_type = 'periType'
    _concrete_rec_name = 'mdfe_nONU'

    mdfe30_peri_infCTe_id = fields.Many2one(
        "mdfe.30.infcte")
    mdfe30_nONU = fields.Char(
        string="Número ONU/UN", xsd_required=True)
    mdfe30_xNomeAE = fields.Char(
        string="Nome apropriado para embarque do produto")
    mdfe30_xClaRisco = fields.Char(
        string="Classe ou subclasse/divisão",
        help="Classe ou subclasse/divisão, e risco subsidiário/risco"
        "\nsecundário")
    mdfe30_grEmb = fields.Char(
        string="Grupo de Embalagem")
    mdfe30_qTotProd = fields.Char(
        string="Quantidade total por produto",
        xsd_required=True)
    mdfe30_qVolTipo = fields.Char(
        string="Quantidade e Tipo de volumes")


class Peri10(spec_models.AbstractSpecMixin):
    """Preenchido quando for transporte de produtos classificados pela ONU como
    perigosos."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.peri10'
    _generateds_type = 'periType10'
    _concrete_rec_name = 'mdfe_nONU'

    mdfe30_peri_infMDFeTransp_id = fields.Many2one(
        "mdfe.30.infmdfetransp")
    mdfe30_nONU = fields.Char(
        string="Número ONU/UN", xsd_required=True)
    mdfe30_xNomeAE = fields.Char(
        string="Nome apropriado para embarque do produto")
    mdfe30_xClaRisco = fields.Char(
        string="Classe ou subclasse/divisão",
        help="Classe ou subclasse/divisão, e risco subsidiário/risco"
        "\nsecundário")
    mdfe30_grEmb = fields.Char(
        string="Grupo de Embalagem")
    mdfe30_qTotProd = fields.Char(
        string="Quantidade total por produto",
        xsd_required=True)
    mdfe30_qVolTipo = fields.Char(
        string="Quantidade e Tipo de volumes")


class Peri2(spec_models.AbstractSpecMixin):
    """Preenchido quando for transporte de produtos classificados pela ONU como
    perigosos."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.peri2'
    _generateds_type = 'periType2'
    _concrete_rec_name = 'mdfe_nONU'

    mdfe30_peri_infNFe_id = fields.Many2one(
        "mdfe.30.infnfe")
    mdfe30_nONU = fields.Char(
        string="Número ONU/UN", xsd_required=True)
    mdfe30_xNomeAE = fields.Char(
        string="Nome apropriado para embarque do produto")
    mdfe30_xClaRisco = fields.Char(
        string="Classe ou subclasse/divisão",
        help="Classe ou subclasse/divisão, e risco subsidiário/risco"
        "\nsecundário")
    mdfe30_grEmb = fields.Char(
        string="Grupo de Embalagem")
    mdfe30_qTotProd = fields.Char(
        string="Quantidade total por produto",
        xsd_required=True)
    mdfe30_qVolTipo = fields.Char(
        string="Quantidade e Tipo de volumes")


class Seg(spec_models.AbstractSpecMixin):
    "Informações de Seguro da Carga"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.seg'
    _generateds_type = 'segType'
    _concrete_rec_name = 'mdfe_infResp'

    mdfe30_seg_infMDFe_id = fields.Many2one(
        "mdfe.30.infmdfe")
    mdfe30_infResp = fields.Many2one(
        "mdfe.30.infresp",
        string="Informações do responsável pelo seguro da carga",
        xsd_required=True)
    mdfe30_infSeg = fields.Many2one(
        "mdfe.30.infseg",
        string="Informações da seguradora")
    mdfe30_nApol = fields.Char(
        string="Número da Apólice")
    mdfe30_nAver = fields.Char(
        string="Número da Averbação")


class Tot(spec_models.AbstractSpecMixin):
    "Totalizadores da carga transportada e seus documentos fiscais"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.tot'
    _generateds_type = 'totType'
    _concrete_rec_name = 'mdfe_qCTe'

    mdfe30_qCTe = fields.Char(
        string="Quantidade total de CT",
        help="Quantidade total de CT-e relacionados no Manifesto")
    mdfe30_qNFe = fields.Char(
        string="Quantidade total de NF",
        help="Quantidade total de NF-e relacionadas no Manifesto")
    mdfe30_qMDFe = fields.Char(
        string="Quantidade total de MDF",
        help="Quantidade total de MDF-e relacionados no Manifesto"
        "\nAquaviário")
    mdfe30_vCarga = fields.Monetary(
        digits=2, string="Valor total da carga / mercadorias transportadas",
        xsd_required=True)
    mdfe30_cUnid = fields.Selection(
        cUnid_tot,
        string="cUnid", xsd_required=True,
        help="Codigo da unidade de medida do Peso Bruto da Carga /"
        "\nMercadorias transportadas")
    mdfe30_qCarga = fields.Monetary(
        digits=4,
        string="Peso Bruto Total da Carga / Mercadorias transportadas",
        xsd_required=True)
