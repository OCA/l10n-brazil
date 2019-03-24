# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Sun Mar 24 02:47:06 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

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
CST_ICMS60 = [
    ("60", "60"),
]

# Classificação Tributária do Serviço
CST_ICMS90 = [
    ("90", "90"),
]

# Classificação Tributária do Serviço
CST_ICMSOutraUF = [
    ("90", "90"),
]

# Classificação Tributária do Serviço
CST_ICMSSN = [
    ("90", "90"),
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
CST_ICMSOutraUF = [
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

# Tipo Código da Lista de Serviços LC 116/2003
TCListServ = [
    ("101", "101"),
    ("102", "102"),
    ("103", "103"),
    ("104", "104"),
    ("105", "105"),
    ("106", "106"),
    ("107", "107"),
    ("108", "108"),
    ("201", "201"),
    ("302", "302"),
    ("303", "303"),
    ("304", "304"),
    ("305", "305"),
    ("401", "401"),
    ("402", "402"),
    ("403", "403"),
    ("404", "404"),
    ("405", "405"),
    ("406", "406"),
    ("407", "407"),
    ("408", "408"),
    ("409", "409"),
    ("410", "410"),
    ("411", "411"),
    ("412", "412"),
    ("413", "413"),
    ("414", "414"),
    ("415", "415"),
    ("416", "416"),
    ("417", "417"),
    ("418", "418"),
    ("419", "419"),
    ("420", "420"),
    ("421", "421"),
    ("422", "422"),
    ("423", "423"),
    ("501", "501"),
    ("502", "502"),
    ("503", "503"),
    ("504", "504"),
    ("505", "505"),
    ("506", "506"),
    ("507", "507"),
    ("508", "508"),
    ("509", "509"),
    ("601", "601"),
    ("602", "602"),
    ("603", "603"),
    ("604", "604"),
    ("605", "605"),
    ("701", "701"),
    ("702", "702"),
    ("703", "703"),
    ("704", "704"),
    ("705", "705"),
    ("706", "706"),
    ("707", "707"),
    ("708", "708"),
    ("709", "709"),
    ("710", "710"),
    ("711", "711"),
    ("712", "712"),
    ("713", "713"),
    ("716", "716"),
    ("717", "717"),
    ("718", "718"),
    ("719", "719"),
    ("720", "720"),
    ("721", "721"),
    ("722", "722"),
    ("801", "801"),
    ("802", "802"),
    ("901", "901"),
    ("902", "902"),
    ("903", "903"),
    ("1001", "1001"),
    ("1002", "1002"),
    ("1003", "1003"),
    ("1004", "1004"),
    ("1005", "1005"),
    ("1006", "1006"),
    ("1007", "1007"),
    ("1008", "1008"),
    ("1009", "1009"),
    ("1010", "1010"),
    ("1101", "1101"),
    ("1102", "1102"),
    ("1103", "1103"),
    ("1104", "1104"),
    ("1201", "1201"),
    ("1202", "1202"),
    ("1203", "1203"),
    ("1204", "1204"),
    ("1205", "1205"),
    ("1206", "1206"),
    ("1207", "1207"),
    ("1208", "1208"),
    ("1209", "1209"),
    ("1210", "1210"),
    ("1211", "1211"),
    ("1212", "1212"),
    ("1213", "1213"),
    ("1214", "1214"),
    ("1215", "1215"),
    ("1216", "1216"),
    ("1217", "1217"),
    ("1302", "1302"),
    ("1303", "1303"),
    ("1304", "1304"),
    ("1305", "1305"),
    ("1401", "1401"),
    ("1402", "1402"),
    ("1403", "1403"),
    ("1404", "1404"),
    ("1405", "1405"),
    ("1406", "1406"),
    ("1407", "1407"),
    ("1408", "1408"),
    ("1409", "1409"),
    ("1410", "1410"),
    ("1411", "1411"),
    ("1412", "1412"),
    ("1413", "1413"),
    ("1501", "1501"),
    ("1502", "1502"),
    ("1503", "1503"),
    ("1504", "1504"),
    ("1505", "1505"),
    ("1506", "1506"),
    ("1507", "1507"),
    ("1508", "1508"),
    ("1509", "1509"),
    ("1510", "1510"),
    ("1511", "1511"),
    ("1512", "1512"),
    ("1513", "1513"),
    ("1514", "1514"),
    ("1515", "1515"),
    ("1516", "1516"),
    ("1517", "1517"),
    ("1518", "1518"),
    ("1601", "1601"),
    ("1701", "1701"),
    ("1702", "1702"),
    ("1703", "1703"),
    ("1704", "1704"),
    ("1705", "1705"),
    ("1706", "1706"),
    ("1708", "1708"),
    ("1709", "1709"),
    ("1710", "1710"),
    ("1711", "1711"),
    ("1712", "1712"),
    ("1713", "1713"),
    ("1714", "1714"),
    ("1715", "1715"),
    ("1716", "1716"),
    ("1717", "1717"),
    ("1718", "1718"),
    ("1719", "1719"),
    ("1720", "1720"),
    ("1721", "1721"),
    ("1722", "1722"),
    ("1723", "1723"),
    ("1724", "1724"),
    ("1801", "1801"),
    ("1901", "1901"),
    ("2001", "2001"),
    ("2002", "2002"),
    ("2003", "2003"),
    ("2101", "2101"),
    ("2201", "2201"),
    ("2301", "2301"),
    ("2401", "2401"),
    ("2501", "2501"),
    ("2502", "2502"),
    ("2503", "2503"),
    ("2504", "2504"),
    ("2601", "2601"),
    ("2701", "2701"),
    ("2801", "2801"),
    ("2901", "2901"),
    ("3001", "3001"),
    ("3101", "3101"),
    ("3201", "3201"),
    ("3301", "3301"),
    ("3401", "3401"),
    ("3501", "3501"),
    ("3601", "3601"),
    ("3701", "3701"),
    ("3801", "3801"),
    ("3901", "3901"),
    ("4001", "4001"),
]

# Tipo Código de orgão (UF da tabela do IBGE + 90 SUFRAMA + 91 RFB)
TCOrgaoIBGE = [
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
    ("90", "90"),
    ("91", "91"),
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

# Tipo Documento Associado
TDocAssoc = [
    ("07", "07"),
    ("08", "08"),
    ("09", "09"),
    ("10", "10"),
    ("11", "11"),
    ("12", "12"),
    ("13", "13"),
]

# Tipo Finalidade da CT-e
TFinCTe = [
    ("0", "0"),
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
]

# Tipo Finalidade da CT-e Outros Serviços
TFinCTeOS = [
    ("0", "0"),
    ("1", "1"),
]

# Tipo Modelo Documento Fiscal
TModCT_ide = [
    ("57", "57"),
]

# Tipo Modelo Documento Fiscal
TModCTOS_ide = [
    ("67", "67"),
]

# Tipo Modelo Documento Fiscal
TModCT_Carga_OS = [
    ("57", "57"),
    ("67", "67"),
]

# Tipo Modelo do Documento
TModDoc = [
    ("01", "01"),
    ("1B", "1B"),
    ("02", "02"),
    ("2D", "2D"),
    ("2E", "2E"),
    ("04", "04"),
    ("06", "06"),
    ("07", "07"),
    ("08", "08"),
    ("8B", "8B"),
    ("09", "09"),
    ("10", "10"),
    ("11", "11"),
    ("13", "13"),
    ("14", "14"),
    ("15", "15"),
    ("16", "16"),
    ("17", "17"),
    ("18", "18"),
    ("20", "20"),
    ("21", "21"),
    ("22", "22"),
    ("23", "23"),
    ("24", "24"),
    ("25", "25"),
    ("26", "26"),
    ("27", "27"),
    ("28", "28"),
    ("55", "55"),
]

# Tipo Modelo Documento Fiscal - NF Remetente
TModNF_infNF = [
    ("01", "01"),
    ("04", "04"),
]

# Tipo Modal transporte
TModTransp_ide = [
    ("01", "01"),
    ("02", "02"),
    ("03", "03"),
    ("04", "04"),
    ("05", "05"),
    ("06", "06"),
]

# Tipo Modal transporte Outros Serviços
TModTranspOS_ide = [
    ("01", "01"),
    ("02", "02"),
    ("03", "03"),
    ("04", "04"),
]

# Tipo processo de emissão do CT-e
TProcEmi = [
    ("0", "0"),
    ("3", "3"),
]

# Tipo Sigla da UF, sem Exterior
TUF_sem_EX_TEndeEmi = [
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

# Código da Unidade de Medida
cUnid_infQ = [
    ("00", "00"),
    ("01", "01"),
    ("02", "02"),
    ("03", "03"),
    ("04", "04"),
    ("05", "05"),
]

# Indicador de CT-e Alteração de Tomador
indAlteraToma_infCteSub = [
    ("1", "1"),
]

# Indicador de CT-e Globalizado
indGlobalizado_ide = [
    ("1", "1"),
]

# Indicador do papel do tomador na prestação do serviço:
indIEToma_ide = [
    ("1", "1 – Contribuinte ICMS"),
    ("2", "2 – Contribuinte isento de inscrição"),
    ("9", "9 – Não Contribuinte"),
]

# Indicador da IE do tomador:
indIEToma_ide = [
    ("1", "1 – Contribuinte ICMS"),
    ("2", "2 – Contribuinte isento de inscrição"),
    ("9", "9 – Não Contribuinte"),
]

# Indica se o contribuinte é Simples Nacional 1=Sim
indSN_ICMSSN = [
    ("1", "1"),
]

# Indica se o contribuinte é Simples Nacional 1=Sim
indSN_ICMSSN = [
    ("1", "1"),
]

# Responsável pelo seguro
respSeg_seg = [
    ("4", "4"),
    ("5", "5"),
]

# Indicador se o Recebedor retira no Aeroporto, Filial, Porto ou
# Estação de Destino?
retira_ide = [
    ("0", "0"),
    ("1", "1"),
]

# Tomador do Serviço
toma_toma3 = [
    ("0", "0"),
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
]

# Tomador do Serviço
toma_toma4 = [
    ("4", "4"),
]

# Tipo de documento originário
tpDoc_infOutros = [
    ("00", "00"),
    ("10", "10"),
    ("59", "59"),
    ("65", "65"),
    ("99", "99"),
]

# Forma de emissão do CT-e
tpEmis_ide = [
    ("1", "1"),
    ("4", "4"),
    ("5", "5"),
    ("7", "7"),
    ("8", "8"),
]

# Forma de emissão do CT-e
tpEmis_ide = [
    ("1", "1"),
    ("5", "5"),
    ("7", "7"),
    ("8", "8"),
]

# Tipo de hora
tpHor_semHora = [
    ("0", "0"),
]

# Tipo de hora
tpHor_comHora = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
]

# Tipo de hora
tpHor_noInter = [
    ("4", "4"),
]

# Formato de impressão do DACTE
tpImp_ide = [
    ("1", "1"),
    ("2", "2"),
]

# Formato de impressão do DACTE OS
tpImp_ide = [
    ("1", "1"),
    ("2", "2"),
]

# Tipo de data/período programado para entrega
tpPer_semData = [
    ("0", "0"),
]

# Tipo de data/período programado para entrega
tpPer_comData = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
]

# Tipo período
tpPer_noPeriodo = [
    ("4", "4"),
]

# Tipo do Serviço
tpServ_ide = [
    ("0", "0"),
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
]

# Tipo do Serviço
tpServ_ide = [
    ("6", "6"),
    ("7", "7"),
    ("8", "8"),
]


class Comp(spec_models.AbstractSpecMixin):
    "Componentes do Valor da Prestação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.comp'
    _generateds_type = 'CompType'
    _concrete_rec_name = 'cte_xNome'

    cte30_Comp_vPrest_id = fields.Many2one(
        "cte.30.vprest")
    cte30_xNome = fields.Char(
        string="Nome do componente", xsd_required=True)
    cte30_vComp = fields.Monetary(
        digits=2, string="Valor do componente", xsd_required=True)


class Comp65(spec_models.AbstractSpecMixin):
    "Componentes do Valor da Prestação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.comp65'
    _generateds_type = 'CompType65'
    _concrete_rec_name = 'cte_xNome'

    cte30_Comp_vPrest64_id = fields.Many2one(
        "cte.30.vprest64")
    cte30_xNome = fields.Char(
        string="Nome do componente", xsd_required=True)
    cte30_vComp = fields.Monetary(
        digits=2, string="Valor do componente", xsd_required=True)


class Entrega(spec_models.AbstractSpecMixin):
    "Informações ref. a previsão de entrega"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.entrega'
    _generateds_type = 'EntregaType'
    _concrete_rec_name = 'cte_semData'

    cte30_choice7 = fields.Selection([
        ('cte30_semData', 'semData'),
        ('cte30_comData', 'comData'),
        ('cte30_noPeriodo', 'noPeriodo')],
        "semData/comData/noPeriodo",
        default="cte30_semData")
    cte30_choice8 = fields.Selection([
        ('cte30_semHora', 'semHora'),
        ('cte30_comHora', 'comHora'),
        ('cte30_noInter', 'noInter')],
        "semHora/comHora/noInter",
        default="cte30_semHora")
    cte30_semData = fields.Many2one(
        "cte.30.semdata",
        choice='7',
        string="Entrega sem data definida",
        xsd_required=True)
    cte30_comData = fields.Many2one(
        "cte.30.comdata",
        choice='7',
        string="Entrega com data definida",
        xsd_required=True)
    cte30_noPeriodo = fields.Many2one(
        "cte.30.noperiodo",
        choice='7',
        string="Entrega no período definido",
        xsd_required=True)
    cte30_semHora = fields.Many2one(
        "cte.30.semhora",
        choice='8',
        string="Entrega sem hora definida",
        xsd_required=True)
    cte30_comHora = fields.Many2one(
        "cte.30.comhora",
        choice='8',
        string="Entrega com hora definida",
        xsd_required=True)
    cte30_noInter = fields.Many2one(
        "cte.30.nointer",
        choice='8',
        string="Entrega no intervalo de horário definido",
        xsd_required=True)


class ICMS00(spec_models.AbstractSpecMixin):
    "Prestação sujeito à tributação normal do ICMS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.icms00'
    _generateds_type = 'ICMS00Type'
    _concrete_rec_name = 'cte_CST'

    cte30_CST = fields.Selection(
        CST_ICMS00,
        string="classificação Tributária do Serviço",
        xsd_required=True)
    cte30_vBC = fields.Monetary(
        digits=2, string="Valor da BC do ICMS", xsd_required=True)
    cte30_pICMS = fields.Monetary(
        digits=2, string="Alíquota do ICMS", xsd_required=True)
    cte30_vICMS = fields.Monetary(
        digits=2, string="Valor do ICMS", xsd_required=True)


class ICMS00124(spec_models.AbstractSpecMixin):
    "Prestação sujeito à tributação normal do ICMS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.icms00124'
    _generateds_type = 'ICMS00Type124'
    _concrete_rec_name = 'cte_CST'

    cte30_CST = fields.Selection(
        CST_ICMS00,
        string="classificação Tributária do Serviço",
        xsd_required=True)
    cte30_vBC = fields.Monetary(
        digits=2, string="Valor da BC do ICMS", xsd_required=True)
    cte30_pICMS = fields.Monetary(
        digits=2, string="Alíquota do ICMS", xsd_required=True)
    cte30_vICMS = fields.Monetary(
        digits=2, string="Valor do ICMS", xsd_required=True)


class ICMS20(spec_models.AbstractSpecMixin):
    "Prestação sujeito à tributação com redução de BC do ICMS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.icms20'
    _generateds_type = 'ICMS20Type'
    _concrete_rec_name = 'cte_CST'

    cte30_CST = fields.Selection(
        CST_ICMS20,
        string="Classificação Tributária do serviço",
        xsd_required=True)
    cte30_pRedBC = fields.Monetary(
        digits=2, string="Percentual de redução da BC",
        xsd_required=True)
    cte30_vBC = fields.Monetary(
        digits=2, string="Valor da BC do ICMS", xsd_required=True)
    cte30_pICMS = fields.Monetary(
        digits=2, string="Alíquota do ICMS", xsd_required=True)
    cte30_vICMS = fields.Monetary(
        digits=2, string="Valor do ICMS", xsd_required=True)


class ICMS20126(spec_models.AbstractSpecMixin):
    "Prestação sujeito à tributação com redução de BC do ICMS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.icms20126'
    _generateds_type = 'ICMS20Type126'
    _concrete_rec_name = 'cte_CST'

    cte30_CST = fields.Selection(
        CST_ICMS20,
        string="Classificação Tributária do serviço",
        xsd_required=True)
    cte30_pRedBC = fields.Monetary(
        digits=2, string="Percentual de redução da BC",
        xsd_required=True)
    cte30_vBC = fields.Monetary(
        digits=2, string="Valor da BC do ICMS", xsd_required=True)
    cte30_pICMS = fields.Monetary(
        digits=2, string="Alíquota do ICMS", xsd_required=True)
    cte30_vICMS = fields.Monetary(
        digits=2, string="Valor do ICMS", xsd_required=True)


class ICMS45(spec_models.AbstractSpecMixin):
    "ICMS Isento, não Tributado ou diferido"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.icms45'
    _generateds_type = 'ICMS45Type'
    _concrete_rec_name = 'cte_CST'

    cte30_CST = fields.Selection(
        CST_ICMS45,
        string="Classificação Tributária do Serviço",
        xsd_required=True)


class ICMS45128(spec_models.AbstractSpecMixin):
    "ICMS Isento, não Tributado ou diferido"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.icms45128'
    _generateds_type = 'ICMS45Type128'
    _concrete_rec_name = 'cte_CST'

    cte30_CST = fields.Selection(
        CST_ICMS45,
        string="Classificação Tributária do Serviço",
        xsd_required=True)


class ICMS60(spec_models.AbstractSpecMixin):
    """Tributação pelo ICMS60 - ICMS cobrado por substituição
    tributária.Responsabilidade do recolhimento do ICMS atribuído ao
    tomador ou 3º por ST"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.icms60'
    _generateds_type = 'ICMS60Type'
    _concrete_rec_name = 'cte_CST'

    cte30_CST = fields.Selection(
        CST_ICMS60,
        string="Classificação Tributária do Serviço",
        xsd_required=True)
    cte30_vBCSTRet = fields.Monetary(
        digits=2, string="Valor da BC do ICMS ST retido",
        xsd_required=True)
    cte30_vICMSSTRet = fields.Monetary(
        digits=2, string="Valor do ICMS ST retido",
        xsd_required=True)
    cte30_pICMSSTRet = fields.Monetary(
        digits=2, string="Alíquota do ICMS",
        xsd_required=True)
    cte30_vCred = fields.Monetary(
        digits=2, string="Valor do Crédito outorgado/Presumido")


class ICMS90(spec_models.AbstractSpecMixin):
    "ICMS Outros"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.icms90'
    _generateds_type = 'ICMS90Type'
    _concrete_rec_name = 'cte_CST'

    cte30_CST = fields.Selection(
        CST_ICMS90,
        string="Classificação Tributária do Serviço",
        xsd_required=True)
    cte30_pRedBC = fields.Monetary(
        digits=2, string="Percentual de redução da BC")
    cte30_vBC = fields.Monetary(
        digits=2, string="Valor da BC do ICMS", xsd_required=True)
    cte30_pICMS = fields.Monetary(
        digits=2, string="Alíquota do ICMS", xsd_required=True)
    cte30_vICMS = fields.Monetary(
        digits=2, string="Valor do ICMS", xsd_required=True)
    cte30_vCred = fields.Monetary(
        digits=2, string="Valor do Crédito Outorgado/Presumido")


class ICMS90130(spec_models.AbstractSpecMixin):
    "ICMS Outros"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.icms90130'
    _generateds_type = 'ICMS90Type130'
    _concrete_rec_name = 'cte_CST'

    cte30_CST = fields.Selection(
        CST_ICMS90,
        string="Classificação Tributária do Serviço",
        xsd_required=True)
    cte30_pRedBC = fields.Monetary(
        digits=2, string="Percentual de redução da BC")
    cte30_vBC = fields.Monetary(
        digits=2, string="Valor da BC do ICMS", xsd_required=True)
    cte30_pICMS = fields.Monetary(
        digits=2, string="Alíquota do ICMS", xsd_required=True)
    cte30_vICMS = fields.Monetary(
        digits=2, string="Valor do ICMS", xsd_required=True)
    cte30_vCred = fields.Monetary(
        digits=2, string="Valor do Crédito Outorgado/Presumido")


class ICMSOutraUF(spec_models.AbstractSpecMixin):
    """ICMS devido à UF de origem da prestação, quando diferente da UF do
    emitente"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.icmsoutrauf'
    _generateds_type = 'ICMSOutraUFType'
    _concrete_rec_name = 'cte_CST'

    cte30_CST = fields.Selection(
        CST_ICMSOutraUF,
        string="Classificação Tributária do Serviço",
        xsd_required=True)
    cte30_pRedBCOutraUF = fields.Monetary(
        digits=2, string="Percentual de redução da BC")
    cte30_vBCOutraUF = fields.Monetary(
        digits=2, string="Valor da BC do ICMS",
        xsd_required=True)
    cte30_pICMSOutraUF = fields.Monetary(
        digits=2, string="Alíquota do ICMS",
        xsd_required=True)
    cte30_vICMSOutraUF = fields.Monetary(
        digits=2, string="Valor do ICMS devido outra UF",
        xsd_required=True)


class ICMSOutraUF132(spec_models.AbstractSpecMixin):
    """ICMS devido à UF de origem da prestação, quando diferente da UF do
    emitente"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.icmsoutrauf132'
    _generateds_type = 'ICMSOutraUFType132'
    _concrete_rec_name = 'cte_CST'

    cte30_CST = fields.Selection(
        CST_ICMSOutraUF,
        string="Classificação Tributária do Serviço",
        xsd_required=True)
    cte30_pRedBCOutraUF = fields.Monetary(
        digits=2, string="Percentual de redução da BC")
    cte30_vBCOutraUF = fields.Monetary(
        digits=2, string="Valor da BC do ICMS",
        xsd_required=True)
    cte30_pICMSOutraUF = fields.Monetary(
        digits=2, string="Alíquota do ICMS",
        xsd_required=True)
    cte30_vICMSOutraUF = fields.Monetary(
        digits=2, string="Valor do ICMS devido outra UF",
        xsd_required=True)


class ICMSSN(spec_models.AbstractSpecMixin):
    "Simples Nacional"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.icmssn'
    _generateds_type = 'ICMSSNType'
    _concrete_rec_name = 'cte_CST'

    cte30_CST = fields.Selection(
        CST_ICMSSN,
        string="Classificação Tributária do Serviço",
        xsd_required=True)
    cte30_indSN = fields.Selection(
        indSN_ICMSSN,
        string="Indica se o contribuinte é Simples Nacional 1=Sim",
        xsd_required=True,
        help="Indica se o contribuinte é Simples Nacional 1=Sim")


class ICMSSN134(spec_models.AbstractSpecMixin):
    "Simples Nacional"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.icmssn134'
    _generateds_type = 'ICMSSNType134'
    _concrete_rec_name = 'cte_CST'

    cte30_CST = fields.Selection(
        CST_ICMSSN,
        string="Classificação Tributária do Serviço",
        xsd_required=True)
    cte30_indSN = fields.Selection(
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
    _name = 'cte.30.icmsuffim'
    _generateds_type = 'ICMSUFFimType'
    _concrete_rec_name = 'cte_vBCUFFim'

    cte30_vBCUFFim = fields.Monetary(
        digits=2, string="vBCUFFim", xsd_required=True,
        help="Valor da BC do ICMS na UF de término da prestação do serviço"
        "\nde transporte")
    cte30_pFCPUFFim = fields.Monetary(
        digits=2,
        string="Percentual do ICMS relativo ao Fundo de Combate à pobreza",
        xsd_required=True,
        help="Percentual do ICMS relativo ao Fundo de Combate à pobreza"
        "\n(FCP) na UF de término da prestação do serviço de"
        "\ntransporte")
    cte30_pICMSUFFim = fields.Monetary(
        digits=2, string="pICMSUFFim", xsd_required=True,
        help="Alíquota interna da UF de término da prestação do serviço de"
        "\ntransporte")
    cte30_pICMSInter = fields.Monetary(
        digits=2, string="Alíquota interestadual das UF envolvidas",
        xsd_required=True)
    cte30_pICMSInterPart = fields.Monetary(
        digits=2, string="Percentual provisório de partilha entre os estados",
        xsd_required=True)
    cte30_vFCPUFFim = fields.Monetary(
        digits=2,
        string="Valor do ICMS relativo ao Fundo de Combate á Pobreza",
        xsd_required=True,
        help="Valor do ICMS relativo ao Fundo de Combate á Pobreza (FCP) da"
        "\nUF de término da prestação")
    cte30_vICMSUFFim = fields.Monetary(
        digits=2, string="vICMSUFFim", xsd_required=True,
        help="Valor do ICMS de partilha para a UF de término da prestação"
        "\ndo serviço de transporte")
    cte30_vICMSUFIni = fields.Monetary(
        digits=2, string="vICMSUFIni", xsd_required=True,
        help="Valor do ICMS de partilha para a UF de início da prestação do"
        "\nserviço de transporte")


class ICMSUFFim69(spec_models.AbstractSpecMixin):
    """Informações do ICMS de partilha com a UF de término do serviço de
    transporte na operação interestadualGrupo a ser informado nas
    prestações interestaduais para consumidor final, não contribuinte do
    ICMS"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.icmsuffim69'
    _generateds_type = 'ICMSUFFimType69'
    _concrete_rec_name = 'cte_vBCUFFim'

    cte30_vBCUFFim = fields.Monetary(
        digits=2, string="vBCUFFim", xsd_required=True,
        help="Valor da BC do ICMS na UF de término da prestação do serviço"
        "\nde transporte")
    cte30_pFCPUFFim = fields.Monetary(
        digits=2,
        string="Percentual do ICMS relativo ao Fundo de Combate à pobreza",
        xsd_required=True,
        help="Percentual do ICMS relativo ao Fundo de Combate à pobreza"
        "\n(FCP) na UF de término da prestação do serviço de"
        "\ntransporte")
    cte30_pICMSUFFim = fields.Monetary(
        digits=2, string="pICMSUFFim", xsd_required=True,
        help="Alíquota interna da UF de término da prestação do serviço de"
        "\ntransporte")
    cte30_pICMSInter = fields.Monetary(
        digits=2, string="Alíquota interestadual das UF envolvidas",
        xsd_required=True)
    cte30_pICMSInterPart = fields.Monetary(
        digits=2, string="Percentual provisório de partilha entre os estados",
        xsd_required=True)
    cte30_vFCPUFFim = fields.Monetary(
        digits=2,
        string="Valor do ICMS relativo ao Fundo de Combate á Pobreza",
        xsd_required=True,
        help="Valor do ICMS relativo ao Fundo de Combate á Pobreza (FCP) da"
        "\nUF de término da prestação")
    cte30_vICMSUFFim = fields.Monetary(
        digits=2, string="vICMSUFFim", xsd_required=True,
        help="Valor do ICMS de partilha para a UF de término da prestação"
        "\ndo serviço de transporte")
    cte30_vICMSUFIni = fields.Monetary(
        digits=2, string="vICMSUFIni", xsd_required=True,
        help="Valor do ICMS de partilha para a UF de início da prestação do"
        "\nserviço de transporte")


class ObsCont(spec_models.AbstractSpecMixin):
    """Campo de uso livre do contribuinteInformar o nome do campo no atributo
    xCampo e o conteúdo do campo no XTextoIdentificação do campo"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.obscont'
    _generateds_type = 'ObsContType'
    _concrete_rec_name = 'cte_xCampo'

    cte30_ObsCont_compl_id = fields.Many2one(
        "cte.30.compl")
    cte30_xCampo = fields.Char(
        string="xCampo", xsd_required=True)
    cte30_xTexto = fields.Char(
        string="Conteúdo do campo", xsd_required=True)


class ObsCont50(spec_models.AbstractSpecMixin):
    """Campo de uso livre do contribuinteInformar o nome do campo no atributo
    xCampo e o conteúdo do campo no XTextoIdentificação do campo"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.obscont50'
    _generateds_type = 'ObsContType50'
    _concrete_rec_name = 'cte_xCampo'

    cte30_ObsCont_compl45_id = fields.Many2one(
        "cte.30.compl45")
    cte30_xCampo = fields.Char(
        string="xCampo", xsd_required=True)
    cte30_xTexto = fields.Char(
        string="Conteúdo do campo", xsd_required=True)


class ObsFisco(spec_models.AbstractSpecMixin):
    """Campo de uso livre do contribuinteInformar o nome do campo no atributo
    xCampo e o conteúdo do campo no XTextoIdentificação do campo"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.obsfisco'
    _generateds_type = 'ObsFiscoType'
    _concrete_rec_name = 'cte_xCampo'

    cte30_ObsFisco_compl_id = fields.Many2one(
        "cte.30.compl")
    cte30_xCampo = fields.Char(
        string="xCampo", xsd_required=True)
    cte30_xTexto = fields.Char(
        string="Conteúdo do campo", xsd_required=True)


class ObsFisco52(spec_models.AbstractSpecMixin):
    """Campo de uso livre do contribuinteInformar o nome do campo no atributo
    xCampo e o conteúdo do campo no XTextoIdentificação do campo"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.obsfisco52'
    _generateds_type = 'ObsFiscoType52'
    _concrete_rec_name = 'cte_xCampo'

    cte30_ObsFisco_compl45_id = fields.Many2one(
        "cte.30.compl45")
    cte30_xCampo = fields.Char(
        string="xCampo", xsd_required=True)
    cte30_xTexto = fields.Char(
        string="Conteúdo do campo", xsd_required=True)


class TCTe(spec_models.AbstractSpecMixin):
    "Tipo Conhecimento de Transporte Eletrônico (Modelo 57)"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tcte'
    _generateds_type = 'TCTe'
    _concrete_rec_name = 'cte_infCte'

    cte30_CTe_TEnviCTe_id = fields.Many2one(
        "cte.30.tenvicte")
    cte30_infCte = fields.Many2one(
        "cte.30.infcte",
        string="Informações do CT-e",
        xsd_required=True)


class TCTeOS(spec_models.AbstractSpecMixin):
    """Tipo Conhecimento de Transporte Eletrônico Outros Serviços (Modelo
    67)Versão do leiaute"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tcteos'
    _generateds_type = 'TCTeOS'
    _concrete_rec_name = 'cte_versao'

    cte30_versao = fields.Char(
        string="versao", xsd_required=True)
    cte30_infCte = fields.Many2one(
        "cte.30.infcte29",
        string="Informações do CT-e Outros Serviços",
        xsd_required=True)


class TEndOrg(spec_models.AbstractSpecMixin):
    "Tipo Dados do Endereço"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tendorg'
    _generateds_type = 'TEndOrg'
    _concrete_rec_name = 'cte_xLgr'

    cte30_xLgr = fields.Char(
        string="Logradouro", xsd_required=True)
    cte30_nro = fields.Char(
        string="Número", xsd_required=True)
    cte30_xCpl = fields.Char(
        string="Complemento")
    cte30_xBairro = fields.Char(
        string="Bairro", xsd_required=True)
    cte30_cMun = fields.Char(
        string="Código do município", xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE), informar"
        "\n9999999 para operações com o exterior.")
    cte30_xMun = fields.Char(
        string="Nome do município", xsd_required=True)
    cte30_CEP = fields.Char(
        string="CEP")
    cte30_UF = fields.Selection(
        TUf,
        string="Sigla da UF", xsd_required=True)
    cte30_cPais = fields.Char(
        string="Código do país")
    cte30_xPais = fields.Char(
        string="Nome do país")
    cte30_fone = fields.Char(
        string="Telefone")


class TEndReEnt(spec_models.AbstractSpecMixin):
    "Tipo Dados do Local de Retirada ou Entrega"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tendreent'
    _generateds_type = 'TEndReEnt'
    _concrete_rec_name = 'cte_CNPJ'

    cte30_choice1 = fields.Selection([
        ('cte30_CNPJ', 'CNPJ'),
        ('cte30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="cte30_CNPJ")
    cte30_CNPJ = fields.Char(
        choice='1',
        string="Número do CNPJ", xsd_required=True)
    cte30_CPF = fields.Char(
        choice='1',
        string="Número do CPF", xsd_required=True)
    cte30_xNome = fields.Char(
        string="Razão Social ou Nome",
        xsd_required=True)
    cte30_xLgr = fields.Char(
        string="Logradouro", xsd_required=True)
    cte30_nro = fields.Char(
        string="Número", xsd_required=True)
    cte30_xCpl = fields.Char(
        string="Complemento")
    cte30_xBairro = fields.Char(
        string="Bairro", xsd_required=True)
    cte30_cMun = fields.Char(
        string="Código do município", xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE)")
    cte30_xMun = fields.Char(
        string="Nome do município", xsd_required=True)
    cte30_UF = fields.Selection(
        TUf,
        string="Sigla da UF", xsd_required=True)


class TEndeEmi(spec_models.AbstractSpecMixin):
    "Tipo Dados do Endereço"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tendeemi'
    _generateds_type = 'TEndeEmi'
    _concrete_rec_name = 'cte_xLgr'

    cte30_xLgr = fields.Char(
        string="Logradouro", xsd_required=True)
    cte30_nro = fields.Char(
        string="Número", xsd_required=True)
    cte30_xCpl = fields.Char(
        string="Complemento")
    cte30_xBairro = fields.Char(
        string="Bairro", xsd_required=True)
    cte30_cMun = fields.Char(
        string="Código do município", xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE)")
    cte30_xMun = fields.Char(
        string="Nome do município", xsd_required=True)
    cte30_CEP = fields.Char(
        string="CEP")
    cte30_UF = fields.Selection(
        TUF_sem_EX_TEndeEmi,
        string="Sigla da UF", xsd_required=True)
    cte30_fone = fields.Char(
        string="Telefone")


class TEndereco(spec_models.AbstractSpecMixin):
    "Tipo Dados do Endereço"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tendereco'
    _generateds_type = 'TEndereco'
    _concrete_rec_name = 'cte_xLgr'

    cte30_xLgr = fields.Char(
        string="Logradouro", xsd_required=True)
    cte30_nro = fields.Char(
        string="Número", xsd_required=True)
    cte30_xCpl = fields.Char(
        string="Complemento")
    cte30_xBairro = fields.Char(
        string="Bairro", xsd_required=True)
    cte30_cMun = fields.Char(
        string="Código do município", xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE)")
    cte30_xMun = fields.Char(
        string="Nome do município", xsd_required=True)
    cte30_CEP = fields.Char(
        string="CEP")
    cte30_UF = fields.Selection(
        TUf,
        string="Sigla da UF", xsd_required=True)
    cte30_cPais = fields.Char(
        string="Código do país")
    cte30_xPais = fields.Char(
        string="Nome do país")


class TEndernac(spec_models.AbstractSpecMixin):
    "Tipo Dados do Endereço"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tendernac'
    _generateds_type = 'TEndernac'
    _concrete_rec_name = 'cte_xLgr'

    cte30_xLgr = fields.Char(
        string="Logradouro", xsd_required=True)
    cte30_nro = fields.Char(
        string="Número", xsd_required=True)
    cte30_xCpl = fields.Char(
        string="Complemento")
    cte30_xBairro = fields.Char(
        string="Bairro", xsd_required=True)
    cte30_cMun = fields.Char(
        string="Código do município", xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE), informar"
        "\n9999999 para operações com o exterior.")
    cte30_xMun = fields.Char(
        string="Nome do município", xsd_required=True,
        help="Nome do município, , informar EXTERIOR para operações com o"
        "\nexterior.")
    cte30_CEP = fields.Char(
        string="CEP")
    cte30_UF = fields.Selection(
        TUf,
        string="Sigla da UF", xsd_required=True)


class TEnviCTe(spec_models.AbstractSpecMixin):
    "Tipo Pedido de Concessão de Autorização da CT-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tenvicte'
    _generateds_type = 'TEnviCTe'
    _concrete_rec_name = 'cte_versao'

    cte30_versao = fields.Char(
        string="versao", xsd_required=True)
    cte30_idLote = fields.Char(
        string="idLote", xsd_required=True)
    cte30_CTe = fields.One2many(
        "cte.30.tcte",
        "cte30_CTe_TEnviCTe_id",
        string="CTe", xsd_required=True
    )


class TImp(spec_models.AbstractSpecMixin):
    "Tipo Dados do Imposto CT-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.timp'
    _generateds_type = 'TImp'
    _concrete_rec_name = 'cte_ICMS00'

    cte30_choice2 = fields.Selection([
        ('cte30_ICMS00', 'ICMS00'),
        ('cte30_ICMS20', 'ICMS20'),
        ('cte30_ICMS45', 'ICMS45'),
        ('cte30_ICMS60', 'ICMS60'),
        ('cte30_ICMS90', 'ICMS90'),
        ('cte30_ICMSOutraUF', 'ICMSOutraUF'),
        ('cte30_ICMSSN', 'ICMSSN')],
        "ICMS00/ICMS20/ICMS45/ICMS60/ICMS90/ICMSOutraUF/ICM...",
        default="cte30_ICMS00")
    cte30_ICMS00 = fields.Many2one(
        "cte.30.icms00",
        choice='2',
        string="Prestação sujeito à tributação normal do ICMS",
        xsd_required=True)
    cte30_ICMS20 = fields.Many2one(
        "cte.30.icms20",
        choice='2',
        string="Prestação sujeito à tributação com redução de BC do ICMS",
        xsd_required=True)
    cte30_ICMS45 = fields.Many2one(
        "cte.30.icms45",
        choice='2',
        string="ICMS Isento", xsd_required=True,
        help="ICMS Isento, não Tributado ou diferido")
    cte30_ICMS60 = fields.Many2one(
        "cte.30.icms60",
        choice='2',
        string="Tributação pelo ICMS60",
        xsd_required=True,
        help="Tributação pelo ICMS60 - ICMS cobrado por substituição"
        "\ntributária.Responsabilidade do recolhimento do ICMS"
        "\natribuído ao tomador ou 3º por ST")
    cte30_ICMS90 = fields.Many2one(
        "cte.30.icms90",
        choice='2',
        string="ICMS Outros", xsd_required=True)
    cte30_ICMSOutraUF = fields.Many2one(
        "cte.30.icmsoutrauf",
        choice='2',
        string="ICMS devido à UF de origem da prestação",
        xsd_required=True,
        help="ICMS devido à UF de origem da prestação, quando diferente da"
        "\nUF do emitente")
    cte30_ICMSSN = fields.Many2one(
        "cte.30.icmssn",
        choice='2',
        string="Simples Nacional", xsd_required=True)


class TImpOS(spec_models.AbstractSpecMixin):
    "Tipo Dados do Imposto para CT-e OS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.timpos'
    _generateds_type = 'TImpOS'
    _concrete_rec_name = 'cte_ICMS00'

    cte30_choice3 = fields.Selection([
        ('cte30_ICMS00', 'ICMS00'),
        ('cte30_ICMS20', 'ICMS20'),
        ('cte30_ICMS45', 'ICMS45'),
        ('cte30_ICMS90', 'ICMS90'),
        ('cte30_ICMSOutraUF', 'ICMSOutraUF'),
        ('cte30_ICMSSN', 'ICMSSN')],
        "ICMS00/ICMS20/ICMS45/ICMS90/ICMSOutraUF/ICMSSN",
        default="cte30_ICMS00")
    cte30_ICMS00 = fields.Many2one(
        "cte.30.icms00124",
        choice='3',
        string="Prestação sujeito à tributação normal do ICMS",
        xsd_required=True)
    cte30_ICMS20 = fields.Many2one(
        "cte.30.icms20126",
        choice='3',
        string="Prestação sujeito à tributação com redução de BC do ICMS",
        xsd_required=True)
    cte30_ICMS45 = fields.Many2one(
        "cte.30.icms45128",
        choice='3',
        string="ICMS Isento", xsd_required=True,
        help="ICMS Isento, não Tributado ou diferido")
    cte30_ICMS90 = fields.Many2one(
        "cte.30.icms90130",
        choice='3',
        string="ICMS Outros", xsd_required=True)
    cte30_ICMSOutraUF = fields.Many2one(
        "cte.30.icmsoutrauf132",
        choice='3',
        string="ICMS devido à UF de origem da prestação",
        xsd_required=True,
        help="ICMS devido à UF de origem da prestação, quando diferente da"
        "\nUF do emitente")
    cte30_ICMSSN = fields.Many2one(
        "cte.30.icmssn134",
        choice='3',
        string="Simples Nacional", xsd_required=True)


class TLocal(spec_models.AbstractSpecMixin):
    "Tipo Dados do Local de Origem ou Destino"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tlocal'
    _generateds_type = 'TLocal'
    _concrete_rec_name = 'cte_cMun'

    cte30_cMun = fields.Char(
        string="Código do município", xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE)")
    cte30_xMun = fields.Char(
        string="Nome do município", xsd_required=True)
    cte30_UF = fields.Selection(
        TUf,
        string="Sigla da UF", xsd_required=True)


class TProtCTeOS(spec_models.AbstractSpecMixin):
    """Tipo Protocolo de status resultado do processamento do CT-e OS (Modelo
    67)"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tprotcteos'
    _generateds_type = 'TProtCTeOS'
    _concrete_rec_name = 'cte_versao'

    cte30_versao = fields.Char(
        string="versao", xsd_required=True)
    cte30_infProt = fields.Many2one(
        "cte.30.infprot",
        string="Dados do protocolo de status",
        xsd_required=True)


class TRespTec(spec_models.AbstractSpecMixin):
    "Tipo Dados da Responsável Técnico"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tresptec'
    _generateds_type = 'TRespTec'
    _concrete_rec_name = 'cte_CNPJ'

    cte30_CNPJ = fields.Char(
        string="CNPJ", xsd_required=True,
        help="CNPJ da pessoa jurídica responsável técnica pelo sistema"
        "\nutilizado na emissão do documento fiscal eletrônico")
    cte30_xContato = fields.Char(
        string="Nome da pessoa a ser contatada",
        xsd_required=True)
    cte30_email = fields.Char(
        string="Email da pessoa jurídica a ser contatada",
        xsd_required=True)
    cte30_fone = fields.Char(
        string="Telefone da pessoa jurídica a ser contatada",
        xsd_required=True)
    cte30_idCSRT = fields.Char(
        string="idCSRT",
        help="Identificador do código de segurança do responsável técnico")
    cte30_hashCSRT = fields.Char(
        string="hashCSRT",
        help="Hash do token do código de segurança do responsável técnico")


class TRetCTeOS(spec_models.AbstractSpecMixin):
    "Tipo Retorno do Pedido de Autorização de CT-e OS (Modelo 67)"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tretcteos'
    _generateds_type = 'TRetCTeOS'
    _concrete_rec_name = 'cte_versao'

    cte30_versao = fields.Char(
        string="versao", xsd_required=True)
    cte30_tpAmb = fields.Selection(
        TAmb,
        string="Identificação do Ambiente",
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    cte30_cUF = fields.Selection(
        TCodUfIBGE,
        string="Identificação da UF", xsd_required=True)
    cte30_verAplic = fields.Char(
        string="Versão do Aplicativo que processou a CT",
        xsd_required=True,
        help="Versão do Aplicativo que processou a CT-e")
    cte30_cStat = fields.Char(
        string="código do status do retorno da consulta",
        xsd_required=True)
    cte30_xMotivo = fields.Char(
        string="Descrição literal do status do do retorno da consulta",
        xsd_required=True)
    cte30_protCTe = fields.Many2one(
        "cte.30.tprotcteos",
        string="Reposta ao processamento do CT-e")


class TRetEnviCTe(spec_models.AbstractSpecMixin):
    "Tipo Retorno do Pedido de Concessão de Autorização da CT-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tretenvicte'
    _generateds_type = 'TRetEnviCTe'
    _concrete_rec_name = 'cte_versao'

    cte30_versao = fields.Char(
        string="versao", xsd_required=True)
    cte30_tpAmb = fields.Selection(
        TAmb,
        string="Identificação do Ambiente:1",
        xsd_required=True,
        help="Identificação do Ambiente:1 - Produção; 2 - Homologação")
    cte30_cUF = fields.Selection(
        TCodUfIBGE,
        string="Identificação da UF", xsd_required=True)
    cte30_verAplic = fields.Char(
        string="Versão do Aplicativo que recebeu o Lote",
        xsd_required=True)
    cte30_cStat = fields.Char(
        string="Código do status da mensagem enviada",
        xsd_required=True)
    cte30_xMotivo = fields.Char(
        string="Descrição literal do status do serviço solicitado",
        xsd_required=True)
    cte30_infRec = fields.Many2one(
        "cte.30.infrec",
        string="Dados do Recibo do Lote")


class TUnidCarga(spec_models.AbstractSpecMixin):
    "Tipo Dados Unidade de Carga"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tunidcarga'
    _generateds_type = 'TUnidCarga'
    _concrete_rec_name = 'cte_tpUnidCarga'

    cte30_infUnidCarga_TUnidadeTransp_id = fields.Many2one(
        "cte.30.tunidadetransp")
    cte30_infUnidCarga_infNF_id = fields.Many2one(
        "cte.30.infnf")
    cte30_infUnidCarga_infNFe_id = fields.Many2one(
        "cte.30.infnfe")
    cte30_infUnidCarga_infOutros_id = fields.Many2one(
        "cte.30.infoutros")
    cte30_tpUnidCarga = fields.Selection(
        TtipoUnidCarga_TUnidCarga,
        string="Tipo da Unidade de Carga",
        xsd_required=True)
    cte30_idUnidCarga = fields.Char(
        string="Identificação da Unidade de Carga",
        xsd_required=True)
    cte30_lacUnidCarga = fields.One2many(
        "cte.30.lacunidcarga",
        "cte30_lacUnidCarga_TUnidCarga_id",
        string="Lacres das Unidades de Carga"
    )
    cte30_qtdRat = fields.Monetary(
        digits=2, string="Quantidade rateada (Peso,Volume)")


class TUnidadeTransp(spec_models.AbstractSpecMixin):
    "Tipo Dados Unidade de Transporte"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tunidadetransp'
    _generateds_type = 'TUnidadeTransp'
    _concrete_rec_name = 'cte_tpUnidTransp'

    cte30_infUnidTransp_infNF_id = fields.Many2one(
        "cte.30.infnf")
    cte30_infUnidTransp_infNFe_id = fields.Many2one(
        "cte.30.infnfe")
    cte30_infUnidTransp_infOutros_id = fields.Many2one(
        "cte.30.infoutros")
    cte30_tpUnidTransp = fields.Selection(
        TtipoUnidTransp_TUnidadeTransp,
        string="Tipo da Unidade de Transporte",
        xsd_required=True)
    cte30_idUnidTransp = fields.Char(
        string="Identificação da Unidade de Transporte",
        xsd_required=True)
    cte30_lacUnidTransp = fields.One2many(
        "cte.30.lacunidtransp",
        "cte30_lacUnidTransp_TUnidadeTransp_id",
        string="Lacres das Unidades de Transporte"
    )
    cte30_infUnidCarga = fields.One2many(
        "cte.30.tunidcarga",
        "cte30_infUnidCarga_TUnidadeTransp_id",
        string="Informações das Unidades de Carga",
        help="Informações das Unidades de Carga (Containeres/ULD/Outros)"
    )
    cte30_qtdRat = fields.Monetary(
        digits=2, string="Quantidade rateada (Peso,Volume)")


class AutXML(spec_models.AbstractSpecMixin):
    """Autorizados para download do XML do DF-eInformar CNPJ ou CPF. Preencher
    os zeros não significativos."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.autxml'
    _generateds_type = 'autXMLType'
    _concrete_rec_name = 'cte_CNPJ'

    cte30_autXML_infCte_id = fields.Many2one(
        "cte.30.infcte")
    cte30_choice22 = fields.Selection([
        ('cte30_CNPJ', 'CNPJ'),
        ('cte30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="cte30_CNPJ")
    cte30_CNPJ = fields.Char(
        choice='22',
        string="CNPJ do autorizado", xsd_required=True)
    cte30_CPF = fields.Char(
        choice='22',
        string="CPF do autorizado", xsd_required=True)


class AutXML89(spec_models.AbstractSpecMixin):
    """Autorizados para download do XML do DF-eInformar CNPJ ou CPF. Preencher
    os zeros não significativos."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.autxml89'
    _generateds_type = 'autXMLType89'
    _concrete_rec_name = 'cte_CNPJ'

    cte30_autXML_infCte29_id = fields.Many2one(
        "cte.30.infcte29")
    cte30_choice28 = fields.Selection([
        ('cte30_CNPJ', 'CNPJ'),
        ('cte30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="cte30_CNPJ")
    cte30_CNPJ = fields.Char(
        choice='28',
        string="CNPJ do autorizado", xsd_required=True)
    cte30_CPF = fields.Char(
        choice='28',
        string="CPF do autorizado", xsd_required=True)


class Cobr(spec_models.AbstractSpecMixin):
    "Dados da cobrança do CT-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.cobr'
    _generateds_type = 'cobrType'
    _concrete_rec_name = 'cte_fat'

    cte30_fat = fields.Many2one(
        "cte.30.fat",
        string="Dados da fatura")
    cte30_dup = fields.One2many(
        "cte.30.dup",
        "cte30_dup_cobr_id",
        string="Dados das duplicatas"
    )


class Cobr81(spec_models.AbstractSpecMixin):
    "Dados da cobrança do CT-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.cobr81'
    _generateds_type = 'cobrType81'
    _concrete_rec_name = 'cte_fat'

    cte30_fat = fields.Many2one(
        "cte.30.fat82",
        string="Dados da fatura")
    cte30_dup = fields.One2many(
        "cte.30.dup84",
        "cte30_dup_cobr81_id",
        string="Dados das duplicatas"
    )


class ComData(spec_models.AbstractSpecMixin):
    "Entrega com data definida"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.comdata'
    _generateds_type = 'comDataType'
    _concrete_rec_name = 'cte_tpPer'

    cte30_tpPer = fields.Selection(
        tpPer_comData,
        string="Tipo de data/período programado para entrega",
        xsd_required=True)
    cte30_dProg = fields.Date(
        string="Data programada", xsd_required=True)


class ComHora(spec_models.AbstractSpecMixin):
    "Entrega com hora definida"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.comhora'
    _generateds_type = 'comHoraType'
    _concrete_rec_name = 'cte_tpHor'

    cte30_tpHor = fields.Selection(
        tpHor_comHora,
        string="Tipo de hora", xsd_required=True)
    cte30_hProg = fields.Char(
        string="Hora programada", xsd_required=True)


class Compl(spec_models.AbstractSpecMixin):
    "Dados complementares do CT-e para fins operacionais ou comerciais"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.compl'
    _generateds_type = 'complType'
    _concrete_rec_name = 'cte_xCaracAd'

    cte30_xCaracAd = fields.Char(
        string="Característica adicional do transporte")
    cte30_xCaracSer = fields.Char(
        string="Característica adicional do serviço")
    cte30_xEmi = fields.Char(
        string="Funcionário emissor do CTe")
    cte30_fluxo = fields.Many2one(
        "cte.30.fluxo",
        string="Previsão do fluxo da carga")
    cte30_Entrega = fields.Many2one(
        "cte.30.entrega",
        string="Informações ref",
        help="Informações ref. a previsão de entrega")
    cte30_origCalc = fields.Char(
        string="Município de origem para efeito de cálculo do frete")
    cte30_destCalc = fields.Char(
        string="Município de destino para efeito de cálculo do frete")
    cte30_xObs = fields.Char(
        string="Observações Gerais")
    cte30_ObsCont = fields.One2many(
        "cte.30.obscont",
        "cte30_ObsCont_compl_id",
        string="Campo de uso livre do contribuinte"
    )
    cte30_ObsFisco = fields.One2many(
        "cte.30.obsfisco",
        "cte30_ObsFisco_compl_id",
        string="Campo de uso livre do contribuinte"
    )


class Compl45(spec_models.AbstractSpecMixin):
    "Dados complementares do CT-e para fins operacionais ou comerciais"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.compl45'
    _generateds_type = 'complType45'
    _concrete_rec_name = 'cte_xCaracAd'

    cte30_xCaracAd = fields.Char(
        string="Característica adicional do transporte")
    cte30_xCaracSer = fields.Char(
        string="Característica adicional do serviço")
    cte30_xEmi = fields.Char(
        string="Funcionário emissor do CTe")
    cte30_xObs = fields.Char(
        string="Observações Gerais")
    cte30_ObsCont = fields.One2many(
        "cte.30.obscont50",
        "cte30_ObsCont_compl45_id",
        string="Campo de uso livre do contribuinte"
    )
    cte30_ObsFisco = fields.One2many(
        "cte.30.obsfisco52",
        "cte30_ObsFisco_compl45_id",
        string="Campo de uso livre do contribuinte"
    )


class Dest(spec_models.AbstractSpecMixin):
    """Informações do Destinatário do CT-eSó pode ser omitido em caso de
    redespacho intermediário"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.dest'
    _generateds_type = 'destType'
    _concrete_rec_name = 'cte_CNPJ'

    cte30_choice12 = fields.Selection([
        ('cte30_CNPJ', 'CNPJ'),
        ('cte30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="cte30_CNPJ")
    cte30_CNPJ = fields.Char(
        choice='12',
        string="Número do CNPJ", xsd_required=True)
    cte30_CPF = fields.Char(
        choice='12',
        string="Número do CPF", xsd_required=True)
    cte30_IE = fields.Char(
        string="Inscrição Estadual")
    cte30_xNome = fields.Char(
        string="Razão Social ou Nome do destinatário",
        xsd_required=True)
    cte30_fone = fields.Char(
        string="Telefone")
    cte30_ISUF = fields.Char(
        string="Inscrição na SUFRAMA")
    cte30_enderDest = fields.Many2one(
        "cte.30.tendereco",
        string="Dados do endereço",
        xsd_required=True)
    cte30_email = fields.Char(
        string="Endereço de email")


class DocAnt(spec_models.AbstractSpecMixin):
    "Documentos de Transporte Anterior"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.docant'
    _generateds_type = 'docAntType'
    _concrete_rec_name = 'cte_emiDocAnt'

    cte30_emiDocAnt = fields.One2many(
        "cte.30.emidocant",
        "cte30_emiDocAnt_docAnt_id",
        string="Emissor do documento anterior",
        xsd_required=True
    )


class Dup(spec_models.AbstractSpecMixin):
    "Dados das duplicatas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.dup'
    _generateds_type = 'dupType'
    _concrete_rec_name = 'cte_nDup'

    cte30_dup_cobr_id = fields.Many2one(
        "cte.30.cobr")
    cte30_nDup = fields.Char(
        string="Número da duplicata")
    cte30_dVenc = fields.Date(
        string="Data de vencimento da duplicata",
        help="Data de vencimento da duplicata (AAAA-MM-DD)")
    cte30_vDup = fields.Monetary(
        digits=2, string="Valor da duplicata")


class Dup84(spec_models.AbstractSpecMixin):
    "Dados das duplicatas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.dup84'
    _generateds_type = 'dupType84'
    _concrete_rec_name = 'cte_nDup'

    cte30_dup_cobr81_id = fields.Many2one(
        "cte.30.cobr81")
    cte30_nDup = fields.Char(
        string="Número da duplicata")
    cte30_dVenc = fields.Date(
        string="Data de vencimento da duplicata",
        help="Data de vencimento da duplicata (AAAA-MM-DD)")
    cte30_vDup = fields.Monetary(
        digits=2, string="Valor da duplicata")


class EmiDocAnt(spec_models.AbstractSpecMixin):
    "Emissor do documento anterior"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.emidocant'
    _generateds_type = 'emiDocAntType'
    _concrete_rec_name = 'cte_CNPJ'

    cte30_emiDocAnt_docAnt_id = fields.Many2one(
        "cte.30.docant")
    cte30_choice17 = fields.Selection([
        ('cte30_CNPJ', 'CNPJ'),
        ('cte30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="cte30_CNPJ")
    cte30_CNPJ = fields.Char(
        choice='17',
        string="Número do CNPJ", xsd_required=True)
    cte30_CPF = fields.Char(
        choice='17',
        string="Número do CPF", xsd_required=True)
    cte30_IE = fields.Char(
        string="Inscrição Estadual")
    cte30_UF = fields.Selection(
        TUf,
        string="Sigla da UF")
    cte30_xNome = fields.Char(
        string="Razão Social ou Nome do expedidor",
        xsd_required=True)
    cte30_idDocAnt = fields.One2many(
        "cte.30.iddocant",
        "cte30_idDocAnt_emiDocAnt_id",
        string="idDocAnt", xsd_required=True,
        help="Informações de identificação dos documentos de Transporte"
        "\nAnterior"
    )


class Emit(spec_models.AbstractSpecMixin):
    "Identificação do Emitente do CT-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.emit'
    _generateds_type = 'emitType'
    _concrete_rec_name = 'cte_CNPJ'

    cte30_CNPJ = fields.Char(
        string="CNPJ do emitente", xsd_required=True)
    cte30_IE = fields.Char(
        string="Inscrição Estadual do Emitente",
        xsd_required=True)
    cte30_IEST = fields.Char(
        string="Inscrição Estadual do Substituto Tributário")
    cte30_xNome = fields.Char(
        string="Razão social ou Nome do emitente",
        xsd_required=True)
    cte30_xFant = fields.Char(
        string="Nome fantasia")
    cte30_enderEmit = fields.Many2one(
        "cte.30.tendeemi",
        string="Endereço do emitente",
        xsd_required=True)


class Emit54(spec_models.AbstractSpecMixin):
    "Identificação do Emitente do CT-e OS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.emit54'
    _generateds_type = 'emitType54'
    _concrete_rec_name = 'cte_CNPJ'

    cte30_CNPJ = fields.Char(
        string="CNPJ do emitente", xsd_required=True)
    cte30_IE = fields.Char(
        string="Inscrição Estadual do Emitente",
        xsd_required=True)
    cte30_IEST = fields.Char(
        string="Inscrição Estadual do Substituto Tributário")
    cte30_xNome = fields.Char(
        string="Razão social ou Nome do emitente",
        xsd_required=True)
    cte30_xFant = fields.Char(
        string="Nome fantasia")
    cte30_enderEmit = fields.Many2one(
        "cte.30.tendeemi",
        string="Endereço do emitente",
        xsd_required=True)


class Exped(spec_models.AbstractSpecMixin):
    "Informações do Expedidor da Carga"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.exped'
    _generateds_type = 'expedType'
    _concrete_rec_name = 'cte_CNPJ'

    cte30_choice10 = fields.Selection([
        ('cte30_CNPJ', 'CNPJ'),
        ('cte30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="cte30_CNPJ")
    cte30_CNPJ = fields.Char(
        choice='10',
        string="Número do CNPJ", xsd_required=True)
    cte30_CPF = fields.Char(
        choice='10',
        string="Número do CPF", xsd_required=True)
    cte30_IE = fields.Char(
        string="Inscrição Estadual")
    cte30_xNome = fields.Char(
        string="Razão Social ou Nome",
        xsd_required=True)
    cte30_fone = fields.Char(
        string="Telefone")
    cte30_enderExped = fields.Many2one(
        "cte.30.tendereco",
        string="Dados do endereço",
        xsd_required=True)
    cte30_email = fields.Char(
        string="Endereço de email")


class Fat(spec_models.AbstractSpecMixin):
    "Dados da fatura"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.fat'
    _generateds_type = 'fatType'
    _concrete_rec_name = 'cte_nFat'

    cte30_nFat = fields.Char(
        string="Número da fatura")
    cte30_vOrig = fields.Monetary(
        digits=2, string="Valor original da fatura")
    cte30_vDesc = fields.Monetary(
        digits=2, string="Valor do desconto da fatura")
    cte30_vLiq = fields.Monetary(
        digits=2, string="Valor líquido da fatura")


class Fat82(spec_models.AbstractSpecMixin):
    "Dados da fatura"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.fat82'
    _generateds_type = 'fatType82'
    _concrete_rec_name = 'cte_nFat'

    cte30_nFat = fields.Char(
        string="Número da fatura")
    cte30_vOrig = fields.Monetary(
        digits=2, string="Valor original da fatura")
    cte30_vDesc = fields.Monetary(
        digits=2, string="Valor do desconto da fatura")
    cte30_vLiq = fields.Monetary(
        digits=2, string="Valor líquido da fatura")


class Fluxo(spec_models.AbstractSpecMixin):
    """Previsão do fluxo da cargaPreenchimento obrigatório para o modal
    aéreo."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.fluxo'
    _generateds_type = 'fluxoType'
    _concrete_rec_name = 'cte_xOrig'

    cte30_xOrig = fields.Char(
        string="xOrig",
        help="Sigla ou código interno da Filial/Porto/Estação/ Aeroporto de"
        "\nOrigem")
    cte30_pass_ = fields.One2many(
        "cte.30.pass",
        "cte30_pass__fluxo_id",
        string="pass_"
    )
    cte30_xDest = fields.Char(
        string="xDest",
        help="Sigla ou código interno da Filial/Porto/Estação/Aeroporto de"
        "\nDestino")
    cte30_xRota = fields.Char(
        string="Código da Rota de Entrega")


class IdDocAntEle(spec_models.AbstractSpecMixin):
    "Documentos de transporte anterior eletrônicos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.iddocantele'
    _generateds_type = 'idDocAntEleType'
    _concrete_rec_name = 'cte_chCTe'

    cte30_idDocAntEle_idDocAnt_id = fields.Many2one(
        "cte.30.iddocant")
    cte30_chCTe = fields.Char(
        string="Chave de acesso do CT-e",
        xsd_required=True)


class IdDocAntPap(spec_models.AbstractSpecMixin):
    "Documentos de transporte anterior em papel"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.iddocantpap'
    _generateds_type = 'idDocAntPapType'
    _concrete_rec_name = 'cte_tpDoc'

    cte30_idDocAntPap_idDocAnt_id = fields.Many2one(
        "cte.30.iddocant")
    cte30_tpDoc = fields.Char(
        string="Tipo do Documento de Transporte Anterior",
        xsd_required=True)
    cte30_serie = fields.Char(
        string="Série do Documento Fiscal",
        xsd_required=True)
    cte30_subser = fields.Char(
        string="Série do Documento Fiscal")
    cte30_nDoc = fields.Char(
        string="Número do Documento Fiscal",
        xsd_required=True)
    cte30_dEmi = fields.Date(
        string="Data de emissão (AAAA-MM-DD)",
        xsd_required=True)


class IdDocAnt(spec_models.AbstractSpecMixin):
    "Informações de identificação dos documentos de Transporte Anterior"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.iddocant'
    _generateds_type = 'idDocAntType'
    _concrete_rec_name = 'cte_idDocAntPap'

    cte30_idDocAnt_emiDocAnt_id = fields.Many2one(
        "cte.30.emidocant")
    cte30_choice18 = fields.Selection([
        ('cte30_idDocAntPap', 'idDocAntPap'),
        ('cte30_idDocAntEle', 'idDocAntEle')],
        "idDocAntPap/idDocAntEle",
        default="cte30_idDocAntPap")
    cte30_idDocAntPap = fields.One2many(
        "cte.30.iddocantpap",
        "cte30_idDocAntPap_idDocAnt_id",
        choice='18',
        string="Documentos de transporte anterior em papel",
        xsd_required=True
    )
    cte30_idDocAntEle = fields.One2many(
        "cte.30.iddocantele",
        "cte30_idDocAntEle_idDocAnt_id",
        choice='18',
        string="Documentos de transporte anterior eletrônicos",
        xsd_required=True
    )


class Ide(spec_models.AbstractSpecMixin):
    """Identificação do CT-eInformar apenas
    para tpEmis diferente de 1"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.ide'
    _generateds_type = 'ideType'
    _concrete_rec_name = 'cte_cUF'

    cte30_choice5 = fields.Selection([
        ('cte30_toma3', 'toma3'),
        ('cte30_toma4', 'toma4')],
        "toma3/toma4",
        default="cte30_toma3")
    cte30_cUF = fields.Selection(
        TCodUfIBGE,
        string="Código da UF do emitente do CT-e.",
        xsd_required=True)
    cte30_cCT = fields.Char(
        string="Código numérico que compõe a Chave de Acesso",
        xsd_required=True,
        help="Código numérico que compõe a Chave de Acesso.")
    cte30_CFOP = fields.Char(
        string="Código Fiscal de Operações e Prestações",
        xsd_required=True)
    cte30_natOp = fields.Char(
        string="Natureza da Operação",
        xsd_required=True)
    cte30_mod = fields.Selection(
        TModCT_ide,
        string="Modelo do documento fiscal",
        xsd_required=True)
    cte30_serie = fields.Char(
        string="Série do CT-e", xsd_required=True)
    cte30_nCT = fields.Char(
        string="Número do CT-e", xsd_required=True)
    cte30_dhEmi = fields.Char(
        string="Data e hora de emissão do CT-e",
        xsd_required=True)
    cte30_tpImp = fields.Selection(
        tpImp_ide,
        string="Formato de impressão do DACTE",
        xsd_required=True)
    cte30_tpEmis = fields.Selection(
        tpEmis_ide,
        string="Forma de emissão do CT-e",
        xsd_required=True)
    cte30_cDV = fields.Char(
        string="Digito Verificador da chave de acesso do CT",
        xsd_required=True,
        help="Digito Verificador da chave de acesso do CT-e")
    cte30_tpAmb = fields.Selection(
        TAmb,
        string="Tipo do Ambiente", xsd_required=True)
    cte30_tpCTe = fields.Selection(
        TFinCTe,
        string="Tipo do CT-e", xsd_required=True)
    cte30_procEmi = fields.Selection(
        TProcEmi,
        string="Identificador do processo de emissão do CT",
        xsd_required=True,
        help="Identificador do processo de emissão do CT-e")
    cte30_verProc = fields.Char(
        string="Versão do processo de emissão",
        xsd_required=True)
    cte30_indGlobalizado = fields.Selection(
        indGlobalizado_ide,
        string="Indicador de CT-e Globalizado")
    cte30_cMunEnv = fields.Char(
        string="Código do Município de envio do CT-e",
        xsd_required=True,
        help="Código do Município de envio do CT-e (de onde o documento foi"
        "\ntransmitido)")
    cte30_xMunEnv = fields.Char(
        string="Nome do Município de envio do CT-e",
        xsd_required=True,
        help="Nome do Município de envio do CT-e (de onde o documento foi"
        "\ntransmitido)")
    cte30_UFEnv = fields.Selection(
        TUf,
        string="Sigla da UF de envio do CT-e",
        xsd_required=True,
        help="Sigla da UF de envio do CT-e (de onde o documento foi"
        "\ntransmitido)")
    cte30_modal = fields.Selection(
        TModTransp_ide,
        string="Modal", xsd_required=True)
    cte30_tpServ = fields.Selection(
        tpServ_ide,
        string="Tipo do Serviço", xsd_required=True)
    cte30_cMunIni = fields.Char(
        string="Código do Município de início da prestação",
        xsd_required=True)
    cte30_xMunIni = fields.Char(
        string="Nome do Município do início da prestação",
        xsd_required=True)
    cte30_UFIni = fields.Selection(
        TUf,
        string="UF do início da prestação",
        xsd_required=True)
    cte30_cMunFim = fields.Char(
        string="Código do Município de término da prestação",
        xsd_required=True)
    cte30_xMunFim = fields.Char(
        string="Nome do Município do término da prestação",
        xsd_required=True)
    cte30_UFFim = fields.Selection(
        TUf,
        string="UF do término da prestação",
        xsd_required=True)
    cte30_retira = fields.Selection(
        retira_ide,
        string="Indicador se o Recebedor retira no Aeroporto",
        xsd_required=True,
        help="Indicador se o Recebedor retira no Aeroporto, Filial, Porto"
        "\nou Estação de Destino?")
    cte30_xDetRetira = fields.Char(
        string="Detalhes do retira")
    cte30_indIEToma = fields.Selection(
        indIEToma_ide,
        string="Indicador do papel do tomador na prestação do serviço",
        xsd_required=True,
        help="Indicador do papel do tomador na prestação do serviço:"
        "\n1 – Contribuinte ICMS;"
        "\n2 – Contribuinte isento de inscrição;"
        "\n9 – Não Contribuinte")
    cte30_toma3 = fields.Many2one(
        "cte.30.toma3",
        choice='5',
        string="Indicador do 'papel' do tomador do serviço no CT",
        xsd_required=True,
        help="Indicador do 'papel' do tomador do serviço no CT-e")
    cte30_toma4 = fields.Many2one(
        "cte.30.toma4",
        choice='5',
        string="Indicador do 'papel' do tomador do serviço no CT",
        xsd_required=True,
        help="Indicador do 'papel' do tomador do serviço no CT-e")
    cte30_dhCont = fields.Datetime(
        string="Data e Hora da entrada em contingência")
    cte30_xJust = fields.Char(
        string="Justificativa da entrada em contingência")


class Ide30(spec_models.AbstractSpecMixin):
    """Identificação do CT-e Outros ServiçosInformar apenas
    para tpEmis diferente de 1"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.ide30'
    _generateds_type = 'ideType30'
    _concrete_rec_name = 'cte_cUF'

    cte30_cUF = fields.Selection(
        TCodUfIBGE,
        string="Código da UF do emitente do CT-e.",
        xsd_required=True)
    cte30_cCT = fields.Char(
        string="Código numérico que compõe a Chave de Acesso",
        xsd_required=True,
        help="Código numérico que compõe a Chave de Acesso.")
    cte30_CFOP = fields.Char(
        string="Código Fiscal de Operações e Prestações",
        xsd_required=True)
    cte30_natOp = fields.Char(
        string="Natureza da Operação",
        xsd_required=True)
    cte30_mod = fields.Selection(
        TModCTOS_ide,
        string="Modelo do documento fiscal",
        xsd_required=True)
    cte30_serie = fields.Char(
        string="Série do CT-e OS", xsd_required=True)
    cte30_nCT = fields.Char(
        string="Número do CT-e OS", xsd_required=True)
    cte30_dhEmi = fields.Char(
        string="Data e hora de emissão do CT-e OS",
        xsd_required=True)
    cte30_tpImp = fields.Selection(
        tpImp_ide,
        string="Formato de impressão do DACTE OS",
        xsd_required=True)
    cte30_tpEmis = fields.Selection(
        tpEmis_ide,
        string="Forma de emissão do CT-e",
        xsd_required=True)
    cte30_cDV = fields.Char(
        string="Digito Verificador da chave de acesso do CT",
        xsd_required=True,
        help="Digito Verificador da chave de acesso do CT-e")
    cte30_tpAmb = fields.Selection(
        TAmb,
        string="Tipo do Ambiente", xsd_required=True)
    cte30_tpCTe = fields.Selection(
        TFinCTe,
        string="Tipo do CT-e OS", xsd_required=True)
    cte30_procEmi = fields.Selection(
        TProcEmi,
        string="Identificador do processo de emissão do CT",
        xsd_required=True,
        help="Identificador do processo de emissão do CT-e OS")
    cte30_verProc = fields.Char(
        string="Versão do processo de emissão",
        xsd_required=True)
    cte30_cMunEnv = fields.Char(
        string="Código do Município de envio do CT-e",
        xsd_required=True,
        help="Código do Município de envio do CT-e (de onde o documento foi"
        "\ntransmitido)")
    cte30_xMunEnv = fields.Char(
        string="Nome do Município de envio do CT-e",
        xsd_required=True,
        help="Nome do Município de envio do CT-e (de onde o documento foi"
        "\ntransmitido)")
    cte30_UFEnv = fields.Selection(
        TUf,
        string="Sigla da UF de envio do CT-e",
        xsd_required=True,
        help="Sigla da UF de envio do CT-e (de onde o documento foi"
        "\ntransmitido)")
    cte30_modal = fields.Selection(
        TModTranspOS_ide,
        string="Modal do CT-e OS", xsd_required=True)
    cte30_tpServ = fields.Selection(
        tpServ_ide,
        string="Tipo do Serviço", xsd_required=True)
    cte30_indIEToma = fields.Selection(
        indIEToma_ide,
        string="Indicador da IE do tomador",
        xsd_required=True,
        help="Indicador da IE do tomador:"
        "\n1 – Contribuinte ICMS;"
        "\n2 – Contribuinte isento de inscrição;"
        "\n9 – Não Contribuinte")
    cte30_cMunIni = fields.Char(
        string="Código do Município de início da prestação")
    cte30_xMunIni = fields.Char(
        string="Nome do Município do início da prestação")
    cte30_UFIni = fields.Selection(
        TUf,
        string="UF do início da prestação")
    cte30_cMunFim = fields.Char(
        string="Código do Município de término da prestação")
    cte30_xMunFim = fields.Char(
        string="Nome do Município do término da prestação")
    cte30_UFFim = fields.Selection(
        TUf,
        string="UF do término da prestação")
    cte30_infPercurso = fields.One2many(
        "cte.30.infpercurso",
        "cte30_infPercurso_ide30_id",
        string="Informações do Percurso do CT",
        help="Informações do Percurso do CT-e Outros Serviços"
    )
    cte30_dhCont = fields.Datetime(
        string="Data e Hora da entrada em contingência")
    cte30_xJust = fields.Char(
        string="Justificativa da entrada em contingência")


class Imp(spec_models.AbstractSpecMixin):
    "Informações relativas aos Impostos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.imp'
    _generateds_type = 'impType'
    _concrete_rec_name = 'cte_ICMS'

    cte30_ICMS = fields.Many2one(
        "cte.30.timp",
        string="Informações relativas ao ICMS",
        xsd_required=True)
    cte30_vTotTrib = fields.Monetary(
        digits=2, string="Valor Total dos Tributos")
    cte30_infAdFisco = fields.Char(
        string="Informações adicionais de interesse do Fisco")
    cte30_ICMSUFFim = fields.Many2one(
        "cte.30.icmsuffim",
        string="ICMSUFFim",
        help="Informações do ICMS de partilha com a UF de término do"
        "\nserviço de transporte na operação interestadual")


class Imp67(spec_models.AbstractSpecMixin):
    "Informações relativas aos Impostos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.imp67'
    _generateds_type = 'impType67'
    _concrete_rec_name = 'cte_ICMS'

    cte30_ICMS = fields.Many2one(
        "cte.30.timpos",
        string="Informações relativas ao ICMS",
        xsd_required=True)
    cte30_vTotTrib = fields.Monetary(
        digits=2, string="Valor Total dos Tributos")
    cte30_infAdFisco = fields.Char(
        string="Informações adicionais de interesse do Fisco")
    cte30_ICMSUFFim = fields.Many2one(
        "cte.30.icmsuffim69",
        string="ICMSUFFim",
        help="Informações do ICMS de partilha com a UF de término do"
        "\nserviço de transporte na operação interestadual")
    cte30_infTribFed = fields.Many2one(
        "cte.30.inftribfed",
        string="Informações dos tributos federais")


class InfCTeMultimodal(spec_models.AbstractSpecMixin):
    "informações do CT-e multimodal vinculado"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infctemultimodal'
    _generateds_type = 'infCTeMultimodalType'
    _concrete_rec_name = 'cte_chCTeMultimodal'

    cte30_infCTeMultimodal_infServVinc_id = fields.Many2one(
        "cte.30.infservvinc")
    cte30_chCTeMultimodal = fields.Char(
        string="Chave de acesso do CT-e Multimodal",
        xsd_required=True)


class InfCTeNorm(spec_models.AbstractSpecMixin):
    "Grupo de informações do CT-e Normal e Substituto"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infctenorm'
    _generateds_type = 'infCTeNormType'
    _concrete_rec_name = 'cte_infCarga'

    cte30_infCarga = fields.Many2one(
        "cte.30.infcarga",
        string="Informações da Carga do CT-e",
        xsd_required=True)
    cte30_infDoc = fields.Many2one(
        "cte.30.infdoc",
        string="Informações dos documentos transportados pelo CT",
        help="Informações dos documentos transportados pelo CT-e"
        "\nOpcional para Redespacho Intermediario e Serviço vinculado a"
        "\nmultimodal.")
    cte30_docAnt = fields.Many2one(
        "cte.30.docant",
        string="Documentos de Transporte Anterior")
    cte30_infModal = fields.Many2one(
        "cte.30.infmodal",
        string="Informações do modal",
        xsd_required=True)
    cte30_veicNovos = fields.One2many(
        "cte.30.veicnovos",
        "cte30_veicNovos_infCTeNorm_id",
        string="informações dos veículos transportados"
    )
    cte30_cobr = fields.Many2one(
        "cte.30.cobr",
        string="Dados da cobrança do CT-e")
    cte30_infCteSub = fields.Many2one(
        "cte.30.infctesub",
        string="Informações do CT-e de substituição")
    cte30_infGlobalizado = fields.Many2one(
        "cte.30.infglobalizado",
        string="Informações do CT-e Globalizado")
    cte30_infServVinc = fields.Many2one(
        "cte.30.infservvinc",
        string="Informações do Serviço Vinculado a Multimodal")


class InfCTeNorm70(spec_models.AbstractSpecMixin):
    "Grupo de informações do CT-e OS Normal"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infctenorm70'
    _generateds_type = 'infCTeNormType70'
    _concrete_rec_name = 'cte_infServico'

    cte30_infServico = fields.Many2one(
        "cte.30.infservico",
        string="Informações da Prestação do Serviço",
        xsd_required=True)
    cte30_infDocRef = fields.One2many(
        "cte.30.infdocref",
        "cte30_infDocRef_infCTeNorm70_id",
        string="Informações dos documentos referenciados"
    )
    cte30_seg = fields.One2many(
        "cte.30.seg",
        "cte30_seg_infCTeNorm70_id",
        string="Informações de Seguro da Carga"
    )
    cte30_infModal = fields.Many2one(
        "cte.30.infmodal74",
        string="Informações do modal",
        help="Informações do modal"
        "\nObrigatório para Pessoas e Bagagem")
    cte30_infCteSub = fields.Many2one(
        "cte.30.infctesub75",
        string="Informações do CT-e de substituição")
    cte30_refCTeCanc = fields.Char(
        string="Chave de acesso do CT-e Cancelado",
        help="Chave de acesso do CT-e Cancelado"
        "\nSomente para Transporte de Valores")
    cte30_cobr = fields.Many2one(
        "cte.30.cobr81",
        string="Dados da cobrança do CT-e")


class InfCarga(spec_models.AbstractSpecMixin):
    "Informações da Carga do CT-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infcarga'
    _generateds_type = 'infCargaType'
    _concrete_rec_name = 'cte_vCarga'

    cte30_vCarga = fields.Monetary(
        digits=2, string="Valor total da carga")
    cte30_proPred = fields.Char(
        string="Produto predominante",
        xsd_required=True)
    cte30_xOutCat = fields.Char(
        string="Outras características da carga")
    cte30_infQ = fields.One2many(
        "cte.30.infq",
        "cte30_infQ_infCarga_id",
        string="Informações de quantidades da Carga do CT",
        xsd_required=True,
        help="Informações de quantidades da Carga do CT-e"
    )
    cte30_vCargaAverb = fields.Monetary(
        digits=2, string="Valor da Carga para efeito de averbação")


class InfCteAnu(spec_models.AbstractSpecMixin):
    "Detalhamento do CT-e do tipo Anulação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infcteanu'
    _generateds_type = 'infCteAnuType'
    _concrete_rec_name = 'cte_chCte'

    cte30_chCte = fields.Char(
        string="Chave de acesso do CT",
        xsd_required=True,
        help="Chave de acesso do CT-e original a ser anulado e substituído")
    cte30_dEmi = fields.Date(
        string="dEmi", xsd_required=True,
        help="Data de emissão da declaração do tomador não contribuinte do"
        "\nICMS")


class InfCteAnu87(spec_models.AbstractSpecMixin):
    "Detalhamento do CT-e do tipo Anulação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infcteanu87'
    _generateds_type = 'infCteAnuType87'
    _concrete_rec_name = 'cte_chCte'

    cte30_chCte = fields.Char(
        string="Chave de acesso do CT",
        xsd_required=True,
        help="Chave de acesso do CT-e original a ser anulado e substituído")
    cte30_dEmi = fields.Date(
        string="dEmi", xsd_required=True,
        help="Data de emissão da declaração do tomador não contribuinte do"
        "\nICMS")


class InfCteComp(spec_models.AbstractSpecMixin):
    "Detalhamento do CT-e complementado"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infctecomp'
    _generateds_type = 'infCteCompType'
    _concrete_rec_name = 'cte_chCTe'

    cte30_chCTe = fields.Char(
        string="Chave do CT-e complementado",
        xsd_required=True)


class InfCteComp86(spec_models.AbstractSpecMixin):
    "Detalhamento do CT-e complementado"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infctecomp86'
    _generateds_type = 'infCteCompType86'
    _concrete_rec_name = 'cte_chCTe'

    cte30_chCTe = fields.Char(
        string="Chave do CT-e complementado",
        xsd_required=True)


class InfCteSub(spec_models.AbstractSpecMixin):
    "Informações do CT-e de substituição"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infctesub'
    _generateds_type = 'infCteSubType'
    _concrete_rec_name = 'cte_chCte'

    cte30_choice19 = fields.Selection([
        ('cte30_refCteAnu', 'refCteAnu'),
        ('cte30_tomaICMS', 'tomaICMS')],
        "refCteAnu/tomaICMS",
        default="cte30_refCteAnu")
    cte30_chCte = fields.Char(
        string="Chave de acesso do CT",
        xsd_required=True,
        help="Chave de acesso do CT-e a ser substituído (original)")
    cte30_refCteAnu = fields.Char(
        choice='19',
        string="Chave de acesso do CT-e de Anulação",
        xsd_required=True)
    cte30_tomaICMS = fields.Many2one(
        "cte.30.tomaicms",
        choice='19',
        string="Tomador é contribuinte do ICMS",
        xsd_required=True,
        help="Tomador é contribuinte do ICMS, mas não é emitente de"
        "\ndocumento fiscal eletrônico")
    cte30_indAlteraToma = fields.Selection(
        indAlteraToma_infCteSub,
        string="Indicador de CT",
        help="Indicador de CT-e Alteração de Tomador")


class InfCteSub75(spec_models.AbstractSpecMixin):
    "Informações do CT-e de substituição"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infctesub75'
    _generateds_type = 'infCteSubType75'
    _concrete_rec_name = 'cte_chCte'

    cte30_choice25 = fields.Selection([
        ('cte30_refCteAnu', 'refCteAnu'),
        ('cte30_tomaICMS', 'tomaICMS')],
        "refCteAnu/tomaICMS",
        default="cte30_refCteAnu")
    cte30_chCte = fields.Char(
        string="Chave de acesso do CT",
        xsd_required=True,
        help="Chave de acesso do CT-e a ser substituído (original)")
    cte30_refCteAnu = fields.Char(
        choice='25',
        string="Chave de acesso do CT-e de Anulação",
        xsd_required=True)
    cte30_tomaICMS = fields.Many2one(
        "cte.30.tomaicms78",
        choice='25',
        string="Tomador é contribuinte do ICMS",
        xsd_required=True,
        help="Tomador é contribuinte do ICMS, mas não é emitente de"
        "\ndocumento fiscal eletrônico")


class InfCte(spec_models.AbstractSpecMixin):
    """Informações do CT-eVersão do leiauteEx: "3.00"Identificador da tag a ser
    assinadaInformar a chave de acesso do CT-e e precedida do literal "CTe" """
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infcte'
    _generateds_type = 'infCteType'
    _concrete_rec_name = 'cte_versao'

    cte30_choice4 = fields.Selection([
        ('cte30_infCTeNorm', 'infCTeNorm'),
        ('cte30_infCteComp', 'infCteComp'),
        ('cte30_infCteAnu', 'infCteAnu')],
        "infCTeNorm/infCteComp/infCteAnu",
        default="cte30_infCTeNorm")
    cte30_versao = fields.Char(
        string="versao", xsd_required=True)
    cte30_Id = fields.Char(
        string="Id", xsd_required=True)
    cte30_ide = fields.Many2one(
        "cte.30.ide",
        string="Identificação do CT-e", xsd_required=True)
    cte30_compl = fields.Many2one(
        "cte.30.compl",
        string="Dados complementares do CT",
        help="Dados complementares do CT-e para fins operacionais ou"
        "\ncomerciais")
    cte30_emit = fields.Many2one(
        "cte.30.emit",
        string="Identificação do Emitente do CT-e",
        xsd_required=True)
    cte30_rem = fields.Many2one(
        "cte.30.rem",
        string="rem",
        help="Informações do Remetente das mercadorias transportadas pelo"
        "\nCT-e")
    cte30_exped = fields.Many2one(
        "cte.30.exped",
        string="Informações do Expedidor da Carga")
    cte30_receb = fields.Many2one(
        "cte.30.receb",
        string="Informações do Recebedor da Carga")
    cte30_dest = fields.Many2one(
        "cte.30.dest",
        string="Informações do Destinatário do CT-e")
    cte30_vPrest = fields.Many2one(
        "cte.30.vprest",
        string="Valores da Prestação de Serviço",
        xsd_required=True)
    cte30_imp = fields.Many2one(
        "cte.30.imp",
        string="Informações relativas aos Impostos",
        xsd_required=True)
    cte30_infCTeNorm = fields.Many2one(
        "cte.30.infctenorm",
        choice='4',
        string="Grupo de informações do CT",
        xsd_required=True,
        help="Grupo de informações do CT-e Normal e Substituto")
    cte30_infCteComp = fields.Many2one(
        "cte.30.infctecomp",
        choice='4',
        string="Detalhamento do CT-e complementado",
        xsd_required=True)
    cte30_infCteAnu = fields.Many2one(
        "cte.30.infcteanu",
        choice='4',
        string="Detalhamento do CT",
        xsd_required=True,
        help="Detalhamento do CT-e do tipo Anulação")
    cte30_autXML = fields.One2many(
        "cte.30.autxml",
        "cte30_autXML_infCte_id",
        string="Autorizados para download do XML do DF",
        help="Autorizados para download do XML do DF-e"
    )
    cte30_infRespTec = fields.Many2one(
        "cte.30.tresptec",
        string="Informações do Responsável Técnico pela emissão do DF",
        help="Informações do Responsável Técnico pela emissão do DF-e")


class InfCte29(spec_models.AbstractSpecMixin):
    """Informações do CT-e Outros ServiçosVersão do leiauteEx:
    "3.00"Identificador da tag a ser assinadaInformar a chave de acesso do
    CT-e e precedida do literal "CTe" """
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infcte29'
    _generateds_type = 'infCteType29'
    _concrete_rec_name = 'cte_versao'

    cte30_choice23 = fields.Selection([
        ('cte30_infCTeNorm', 'infCTeNorm'),
        ('cte30_infCteComp', 'infCteComp'),
        ('cte30_infCteAnu', 'infCteAnu')],
        "infCTeNorm/infCteComp/infCteAnu",
        default="cte30_infCTeNorm")
    cte30_versao = fields.Char(
        string="versao", xsd_required=True)
    cte30_Id = fields.Char(
        string="Id", xsd_required=True)
    cte30_ide = fields.Many2one(
        "cte.30.ide30",
        string="Identificação do CT", xsd_required=True,
        help="Identificação do CT-e Outros Serviços")
    cte30_compl = fields.Many2one(
        "cte.30.compl45",
        string="Dados complementares do CT",
        help="Dados complementares do CT-e para fins operacionais ou"
        "\ncomerciais")
    cte30_emit = fields.Many2one(
        "cte.30.emit54",
        string="Identificação do Emitente do CT-e OS",
        xsd_required=True)
    cte30_toma = fields.Many2one(
        "cte.30.toma59",
        string="Informações do Tomador/Usuário do Serviço")
    cte30_vPrest = fields.Many2one(
        "cte.30.vprest64",
        string="Valores da Prestação de Serviço",
        xsd_required=True)
    cte30_imp = fields.Many2one(
        "cte.30.imp67",
        string="Informações relativas aos Impostos",
        xsd_required=True)
    cte30_infCTeNorm = fields.Many2one(
        "cte.30.infctenorm70",
        choice='23',
        string="Grupo de informações do CT",
        xsd_required=True,
        help="Grupo de informações do CT-e OS Normal")
    cte30_infCteComp = fields.Many2one(
        "cte.30.infctecomp86",
        choice='23',
        string="Detalhamento do CT-e complementado",
        xsd_required=True)
    cte30_infCteAnu = fields.Many2one(
        "cte.30.infcteanu87",
        choice='23',
        string="Detalhamento do CT",
        xsd_required=True,
        help="Detalhamento do CT-e do tipo Anulação")
    cte30_autXML = fields.One2many(
        "cte.30.autxml89",
        "cte30_autXML_infCte29_id",
        string="Autorizados para download do XML do DF",
        help="Autorizados para download do XML do DF-e"
    )
    cte30_infRespTec = fields.Many2one(
        "cte.30.tresptec",
        string="Informações do Responsável Técnico pela emissão do DF",
        help="Informações do Responsável Técnico pela emissão do DF-e")


class InfDocRef(spec_models.AbstractSpecMixin):
    "Informações dos documentos referenciados"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infdocref'
    _generateds_type = 'infDocRefType'
    _concrete_rec_name = 'cte_nDoc'

    cte30_infDocRef_infCTeNorm70_id = fields.Many2one(
        "cte.30.infctenorm70")
    cte30_nDoc = fields.Char(
        string="Número", xsd_required=True)
    cte30_serie = fields.Char(
        string="Série")
    cte30_subserie = fields.Char(
        string="Subsérie")
    cte30_dEmi = fields.Date(
        string="Data de Emissão", xsd_required=True)
    cte30_vDoc = fields.Monetary(
        digits=2, string="Valor Transportado")


class InfDoc(spec_models.AbstractSpecMixin):
    """Informações dos documentos transportados pelo CT-e
    Opcional para Redespacho Intermediario e Serviço vinculado a
    multimodal.Poderá não ser informado para os CT-e de redespacho
    intermediário. Nos demais casos deverá sempre ser informado."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infdoc'
    _generateds_type = 'infDocType'
    _concrete_rec_name = 'cte_infNF'

    cte30_choice13 = fields.Selection([
        ('cte30_infNF', 'infNF'),
        ('cte30_infNFe', 'infNFe'),
        ('cte30_infOutros', 'infOutros')],
        "infNF/infNFe/infOutros",
        default="cte30_infNF")
    cte30_infNF = fields.One2many(
        "cte.30.infnf",
        "cte30_infNF_infDoc_id",
        choice='13',
        string="Informações das NF", xsd_required=True
    )
    cte30_infNFe = fields.One2many(
        "cte.30.infnfe",
        "cte30_infNFe_infDoc_id",
        choice='13',
        string="Informações das NF-e",
        xsd_required=True
    )
    cte30_infOutros = fields.One2many(
        "cte.30.infoutros",
        "cte30_infOutros_infDoc_id",
        choice='13',
        string="Informações dos demais documentos",
        xsd_required=True
    )


class InfGlobalizado(spec_models.AbstractSpecMixin):
    "Informações do CT-e Globalizado"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infglobalizado'
    _generateds_type = 'infGlobalizadoType'
    _concrete_rec_name = 'cte_xObs'

    cte30_xObs = fields.Char(
        string="Preencher com informações adicionais",
        xsd_required=True,
        help="Preencher com informações adicionais, legislação do regime"
        "\nespecial, etc")


class InfModal(spec_models.AbstractSpecMixin):
    "Informações do modalVersão do leiaute específico para o Modal"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infmodal'
    _generateds_type = 'infModalType'
    _concrete_rec_name = 'cte_versaoModal'

    cte30_versaoModal = fields.Char(
        string="versaoModal", xsd_required=True)
    cte30___ANY__ = fields.Char(
        string="__ANY__", xsd_required=True)


class InfModal74(spec_models.AbstractSpecMixin):
    """Informações do modal
    Obrigatório para Pessoas e BagagemVersão do leiaute específico para o
    Modal"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infmodal74'
    _generateds_type = 'infModalType74'
    _concrete_rec_name = 'cte_versaoModal'

    cte30_versaoModal = fields.Char(
        string="versaoModal", xsd_required=True)
    cte30___ANY__ = fields.Char(
        string="__ANY__", xsd_required=True)


class InfNF(spec_models.AbstractSpecMixin):
    """Informações das NFEste grupo deve ser informado quando o documento
    originário for NF"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infnf'
    _generateds_type = 'infNFType'
    _concrete_rec_name = 'cte_nRoma'

    cte30_infNF_infDoc_id = fields.Many2one(
        "cte.30.infdoc")
    cte30_choice14 = fields.Selection([
        ('cte30_infUnidCarga', 'infUnidCarga'),
        ('cte30_infUnidTransp', 'infUnidTransp')],
        "infUnidCarga/infUnidTransp",
        default="cte30_infUnidCarga")
    cte30_nRoma = fields.Char(
        string="Número do Romaneio da NF")
    cte30_nPed = fields.Char(
        string="Número do Pedido da NF")
    cte30_mod = fields.Selection(
        TModNF_infNF,
        string="Modelo da Nota Fiscal", xsd_required=True,
        help="Tipo Modelo Documento Fiscal - NF Remetente")
    cte30_serie = fields.Char(
        string="Série", xsd_required=True)
    cte30_nDoc = fields.Char(
        string="Número", xsd_required=True)
    cte30_dEmi = fields.Date(
        string="Data de Emissão", xsd_required=True)
    cte30_vBC = fields.Monetary(
        digits=2, string="Valor da Base de Cálculo do ICMS",
        xsd_required=True)
    cte30_vICMS = fields.Monetary(
        digits=2, string="Valor Total do ICMS", xsd_required=True)
    cte30_vBCST = fields.Monetary(
        digits=2, string="Valor da Base de Cálculo do ICMS ST",
        xsd_required=True)
    cte30_vST = fields.Monetary(
        digits=2, string="Valor Total do ICMS ST",
        xsd_required=True)
    cte30_vProd = fields.Monetary(
        digits=2, string="Valor Total dos Produtos",
        xsd_required=True)
    cte30_vNF = fields.Monetary(
        digits=2, string="Valor Total da NF", xsd_required=True)
    cte30_nCFOP = fields.Char(
        string="CFOP Predominante", xsd_required=True)
    cte30_nPeso = fields.Monetary(
        digits=3, string="Peso total em Kg")
    cte30_PIN = fields.Char(
        string="PIN SUFRAMA")
    cte30_dPrev = fields.Date(
        string="Data prevista de entrega")
    cte30_infUnidCarga = fields.One2many(
        "cte.30.tunidcarga",
        "cte30_infUnidCarga_infNF_id",
        choice='14',
        string="Informações das Unidades de Carga",
        help="Informações das Unidades de Carga (Containeres/ULD/Outros)"
    )
    cte30_infUnidTransp = fields.One2many(
        "cte.30.tunidadetransp",
        "cte30_infUnidTransp_infNF_id",
        choice='14',
        string="Informações das Unidades de Transporte",
        help="Informações das Unidades de Transporte"
        "\n(Carreta/Reboque/Vagão)"
    )


class InfNFe(spec_models.AbstractSpecMixin):
    "Informações das NF-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infnfe'
    _generateds_type = 'infNFeType'
    _concrete_rec_name = 'cte_chave'

    cte30_infNFe_infDoc_id = fields.Many2one(
        "cte.30.infdoc")
    cte30_choice15 = fields.Selection([
        ('cte30_infUnidCarga', 'infUnidCarga'),
        ('cte30_infUnidTransp', 'infUnidTransp')],
        "infUnidCarga/infUnidTransp",
        default="cte30_infUnidCarga")
    cte30_chave = fields.Char(
        string="Chave de acesso da NF-e",
        xsd_required=True)
    cte30_PIN = fields.Char(
        string="PIN SUFRAMA")
    cte30_dPrev = fields.Date(
        string="Data prevista de entrega")
    cte30_infUnidCarga = fields.One2many(
        "cte.30.tunidcarga",
        "cte30_infUnidCarga_infNFe_id",
        choice='15',
        string="Informações das Unidades de Carga",
        help="Informações das Unidades de Carga (Containeres/ULD/Outros)"
    )
    cte30_infUnidTransp = fields.One2many(
        "cte.30.tunidadetransp",
        "cte30_infUnidTransp_infNFe_id",
        choice='15',
        string="Informações das Unidades de Transporte",
        help="Informações das Unidades de Transporte"
        "\n(Carreta/Reboque/Vagão)"
    )


class InfOutros(spec_models.AbstractSpecMixin):
    "Informações dos demais documentos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infoutros'
    _generateds_type = 'infOutrosType'
    _concrete_rec_name = 'cte_tpDoc'

    cte30_infOutros_infDoc_id = fields.Many2one(
        "cte.30.infdoc")
    cte30_choice16 = fields.Selection([
        ('cte30_infUnidCarga', 'infUnidCarga'),
        ('cte30_infUnidTransp', 'infUnidTransp')],
        "infUnidCarga/infUnidTransp",
        default="cte30_infUnidCarga")
    cte30_tpDoc = fields.Selection(
        tpDoc_infOutros,
        string="Tipo de documento originário",
        xsd_required=True)
    cte30_descOutros = fields.Char(
        string="Descrição do documento")
    cte30_nDoc = fields.Char(
        string="Número")
    cte30_dEmi = fields.Date(
        string="Data de Emissão")
    cte30_vDocFisc = fields.Monetary(
        digits=2, string="Valor do documento")
    cte30_dPrev = fields.Date(
        string="Data prevista de entrega")
    cte30_infUnidCarga = fields.One2many(
        "cte.30.tunidcarga",
        "cte30_infUnidCarga_infOutros_id",
        choice='16',
        string="Informações das Unidades de Carga",
        help="Informações das Unidades de Carga (Containeres/ULD/Outros)"
    )
    cte30_infUnidTransp = fields.One2many(
        "cte.30.tunidadetransp",
        "cte30_infUnidTransp_infOutros_id",
        choice='16',
        string="Informações das Unidades de Transporte",
        help="Informações das Unidades de Transporte"
        "\n(Carreta/Reboque/Vagão)"
    )


class InfPercurso(spec_models.AbstractSpecMixin):
    "Informações do Percurso do CT-e Outros Serviços"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infpercurso'
    _generateds_type = 'infPercursoType'
    _concrete_rec_name = 'cte_UFPer'

    cte30_infPercurso_ide30_id = fields.Many2one(
        "cte.30.ide30")
    cte30_UFPer = fields.Selection(
        TUf,
        string="Sigla das Unidades da Federação do percurso do veículo",
        xsd_required=True)


class InfProt(spec_models.AbstractSpecMixin):
    "Dados do protocolo de status"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infprot'
    _generateds_type = 'infProtType'
    _concrete_rec_name = 'cte_Id'

    cte30_Id = fields.Char(
        string="Id")
    cte30_tpAmb = fields.Selection(
        TAmb,
        string="Identificação do Ambiente",
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    cte30_verAplic = fields.Char(
        string="Versão do Aplicativo que processou a NF",
        xsd_required=True,
        help="Versão do Aplicativo que processou a NF-e")
    cte30_chCTe = fields.Char(
        string="Chaves de acesso da CT-e",
        xsd_required=True,
        help="Chaves de acesso da CT-e, compostas por: UF do emitente, AAMM"
        "\nda emissão da NFe, CNPJ do emitente, modelo, subsérie"
        "\ne número da CT-e e código numérico+DV.")
    cte30_dhRecbto = fields.Datetime(
        string="Data e hora de processamento",
        xsd_required=True,
        help="Data e hora de processamento, no formato AAAA-MM-DDTHH:MM:SS"
        "\nTZD. Deve ser preenchida com data e hora da gravação"
        "\nno Banco em caso de Confirmação. Em caso de Rejeição,"
        "\ncom data e hora do recebimento do Lote de CT-e"
        "\nenviado.")
    cte30_nProt = fields.Char(
        string="Número do Protocolo de Status do CT",
        help="Número do Protocolo de Status do CT-e. 1 posição tipo de"
        "\nautorizador (1 – Secretaria de Fazenda Estadual, 3 -"
        "\nSEFAZ Virtual RS, 5 - SEFAZ Virtual SP ); 2 posições"
        "\nano; 10 seqüencial no ano.")
    cte30_digVal = fields.Char(
        string="Digest Value da CT-e processado",
        help="Digest Value da CT-e processado. Utilizado para conferir a"
        "\nintegridade do CT-e original.")
    cte30_cStat = fields.Char(
        string="Código do status do CT-e.",
        xsd_required=True)
    cte30_xMotivo = fields.Char(
        string="Descrição literal do status do CT-e.",
        xsd_required=True)


class InfQ(spec_models.AbstractSpecMixin):
    """Informações de quantidades da Carga do CT-ePara o Aéreo é obrigatório o
    preenchimento desse campo da seguinte forma.
    1 - Peso Bruto, sempre em quilogramas (obrigatório);
    2 - Peso Cubado; sempre em quilogramas;
    3 - Quantidade de volumes, sempre em unidades (obrigatório);
    4 - Cubagem, sempre em metros cúbicos (obrigatório apenas quando for
    impossível preencher as dimensões da(s) embalagem(ens) na tag xDime do
    leiaute do Aéreo)."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infq'
    _generateds_type = 'infQType'
    _concrete_rec_name = 'cte_cUnid'

    cte30_infQ_infCarga_id = fields.Many2one(
        "cte.30.infcarga")
    cte30_cUnid = fields.Selection(
        cUnid_infQ,
        string="Código da Unidade de Medida",
        xsd_required=True)
    cte30_tpMed = fields.Char(
        string="Tipo da Medida", xsd_required=True)
    cte30_qCarga = fields.Monetary(
        digits=4, string="Quantidade", xsd_required=True)


class InfQ71(spec_models.AbstractSpecMixin):
    """Informações de quantidades da Carga do CT-ePara Transporte de Pessoas
    indicar núimero de passageiros, para excesso de bagagem e transporte de
    valores indicar Nro de Volumes/Malotes"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infq71'
    _generateds_type = 'infQType71'
    _concrete_rec_name = 'cte_qCarga'

    cte30_qCarga = fields.Monetary(
        digits=4, string="Quantidade", xsd_required=True)


class InfRec(spec_models.AbstractSpecMixin):
    "Dados do Recibo do Lote"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infrec'
    _generateds_type = 'infRecType'
    _concrete_rec_name = 'cte_nRec'

    cte30_nRec = fields.Char(
        string="Número do Recibo", xsd_required=True)
    cte30_dhRecbto = fields.Datetime(
        string="Data e hora do recebimento",
        xsd_required=True,
        help="Data e hora do recebimento, no formato AAAA-MM-DDTHH:MM:SS"
        "\nTZD")
    cte30_tMed = fields.Integer(
        string="Tempo médio de resposta do serviço",
        xsd_required=True,
        help="Tempo médio de resposta do serviço (em segundos) dos últimos"
        "\n5 minutos")


class InfServVinc(spec_models.AbstractSpecMixin):
    "Informações do Serviço Vinculado a Multimodal"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infservvinc'
    _generateds_type = 'infServVincType'
    _concrete_rec_name = 'cte_infCTeMultimodal'

    cte30_infCTeMultimodal = fields.One2many(
        "cte.30.infctemultimodal",
        "cte30_infCTeMultimodal_infServVinc_id",
        string="informações do CT",
        xsd_required=True,
        help="informações do CT-e multimodal vinculado"
    )


class InfServico(spec_models.AbstractSpecMixin):
    "Informações da Prestação do Serviço"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.infservico'
    _generateds_type = 'infServicoType'
    _concrete_rec_name = 'cte_xDescServ'

    cte30_xDescServ = fields.Char(
        string="Descrição do Serviço prestado",
        xsd_required=True)
    cte30_infQ = fields.Many2one(
        "cte.30.infq71",
        string="Informações de quantidades da Carga do CT",
        help="Informações de quantidades da Carga do CT-e")


class InfTribFed(spec_models.AbstractSpecMixin):
    """Informações dos tributos federaisGrupo a ser informado nas prestações
    interestaduais para consumidor final, não contribuinte do ICMS"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.inftribfed'
    _generateds_type = 'infTribFedType'
    _concrete_rec_name = 'cte_vPIS'

    cte30_vPIS = fields.Monetary(
        digits=2, string="Valor do PIS")
    cte30_vCOFINS = fields.Monetary(
        digits=2, string="Valor COFINS")
    cte30_vIR = fields.Monetary(
        digits=2, string="Valor de Imposto de Renda")
    cte30_vINSS = fields.Monetary(
        digits=2, string="Valor do INSS")
    cte30_vCSLL = fields.Monetary(
        digits=2, string="Valor do CSLL")


class LacUnidCarga(spec_models.AbstractSpecMixin):
    "Lacres das Unidades de Carga"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.lacunidcarga'
    _generateds_type = 'lacUnidCargaType'
    _concrete_rec_name = 'cte_nLacre'

    cte30_lacUnidCarga_TUnidCarga_id = fields.Many2one(
        "cte.30.tunidcarga")
    cte30_nLacre = fields.Char(
        string="Número do lacre", xsd_required=True)


class LacUnidTransp(spec_models.AbstractSpecMixin):
    "Lacres das Unidades de Transporte"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.lacunidtransp'
    _generateds_type = 'lacUnidTranspType'
    _concrete_rec_name = 'cte_nLacre'

    cte30_lacUnidTransp_TUnidadeTransp_id = fields.Many2one(
        "cte.30.tunidadetransp")
    cte30_nLacre = fields.Char(
        string="Número do lacre", xsd_required=True)


class NoInter(spec_models.AbstractSpecMixin):
    "Entrega no intervalo de horário definido"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.nointer'
    _generateds_type = 'noInterType'
    _concrete_rec_name = 'cte_tpHor'

    cte30_tpHor = fields.Selection(
        tpHor_noInter,
        string="Tipo de hora", xsd_required=True,
        help="Tipo de hora")
    cte30_hIni = fields.Char(
        string="Hora inicial", xsd_required=True)
    cte30_hFim = fields.Char(
        string="Hora final", xsd_required=True)


class NoPeriodo(spec_models.AbstractSpecMixin):
    "Entrega no período definido"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.noperiodo'
    _generateds_type = 'noPeriodoType'
    _concrete_rec_name = 'cte_tpPer'

    cte30_tpPer = fields.Selection(
        tpPer_noPeriodo,
        string="Tipo período", xsd_required=True)
    cte30_dIni = fields.Date(
        string="Data inicial", xsd_required=True)
    cte30_dFim = fields.Date(
        string="Data final", xsd_required=True)


class Pass(spec_models.AbstractSpecMixin):
    _description = 'pass'
    _name = 'cte.30.pass'
    _generateds_type = 'passType'
    _concrete_rec_name = 'cte_xPass'

    cte30_pass__fluxo_id = fields.Many2one(
        "cte.30.fluxo")
    cte30_xPass = fields.Char(
        string="xPass",
        help="Sigla ou código interno da Filial/Porto/Estação/Aeroporto de"
        "\nPassagem")


class Receb(spec_models.AbstractSpecMixin):
    "Informações do Recebedor da Carga"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.receb'
    _generateds_type = 'recebType'
    _concrete_rec_name = 'cte_CNPJ'

    cte30_choice11 = fields.Selection([
        ('cte30_CNPJ', 'CNPJ'),
        ('cte30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="cte30_CNPJ")
    cte30_CNPJ = fields.Char(
        choice='11',
        string="Número do CNPJ", xsd_required=True)
    cte30_CPF = fields.Char(
        choice='11',
        string="Número do CPF", xsd_required=True)
    cte30_IE = fields.Char(
        string="Inscrição Estadual")
    cte30_xNome = fields.Char(
        string="Razão Social ou Nome",
        xsd_required=True)
    cte30_fone = fields.Char(
        string="Telefone")
    cte30_enderReceb = fields.Many2one(
        "cte.30.tendereco",
        string="Dados do endereço",
        xsd_required=True)
    cte30_email = fields.Char(
        string="Endereço de email")


class RefNF(spec_models.AbstractSpecMixin):
    "Informação da NF ou CT emitido pelo Tomador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.refnf'
    _generateds_type = 'refNFType'
    _concrete_rec_name = 'cte_CNPJ'

    cte30_choice21 = fields.Selection([
        ('cte30_CNPJ', 'CNPJ'),
        ('cte30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="cte30_CNPJ")
    cte30_CNPJ = fields.Char(
        choice='21',
        string="CNPJ do Emitente", xsd_required=True)
    cte30_CPF = fields.Char(
        choice='21',
        string="Número do CPF", xsd_required=True)
    cte30_mod = fields.Selection(
        TModDoc,
        string="Modelo do Documento Fiscal",
        xsd_required=True)
    cte30_serie = fields.Char(
        string="Serie do documento fiscal",
        xsd_required=True)
    cte30_subserie = fields.Char(
        string="Subserie do documento fiscal")
    cte30_nro = fields.Char(
        string="Número do documento fiscal",
        xsd_required=True)
    cte30_valor = fields.Monetary(
        digits=2, string="Valor do documento fiscal.",
        xsd_required=True)
    cte30_dEmi = fields.Date(
        string="Data de emissão do documento fiscal.",
        xsd_required=True)


class RefNF79(spec_models.AbstractSpecMixin):
    "Informação da NF ou CT emitido pelo Tomador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.refnf79'
    _generateds_type = 'refNFType79'
    _concrete_rec_name = 'cte_CNPJ'

    cte30_choice27 = fields.Selection([
        ('cte30_CNPJ', 'CNPJ'),
        ('cte30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="cte30_CNPJ")
    cte30_CNPJ = fields.Char(
        choice='27',
        string="CNPJ do Emitente", xsd_required=True)
    cte30_CPF = fields.Char(
        choice='27',
        string="Número do CPF", xsd_required=True)
    cte30_mod = fields.Selection(
        TModDoc,
        string="Modelo do Documento Fiscal",
        xsd_required=True)
    cte30_serie = fields.Char(
        string="Serie do documento fiscal",
        xsd_required=True)
    cte30_subserie = fields.Char(
        string="Subserie do documento fiscal")
    cte30_nro = fields.Char(
        string="Número do documento fiscal",
        xsd_required=True)
    cte30_valor = fields.Monetary(
        digits=2, string="Valor do documento fiscal.",
        xsd_required=True)
    cte30_dEmi = fields.Date(
        string="Data de emissão do documento fiscal.",
        xsd_required=True)


class Rem(spec_models.AbstractSpecMixin):
    """Informações do Remetente das mercadorias transportadas pelo CT-ePoderá
    não ser informado para os CT-e de redespacho intermediário e serviço
    vinculado a multimodal. Nos demais casos deverá sempre ser
    informado."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.rem'
    _generateds_type = 'remType'
    _concrete_rec_name = 'cte_CNPJ'

    cte30_choice9 = fields.Selection([
        ('cte30_CNPJ', 'CNPJ'),
        ('cte30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="cte30_CNPJ")
    cte30_CNPJ = fields.Char(
        choice='9',
        string="Número do CNPJ", xsd_required=True)
    cte30_CPF = fields.Char(
        choice='9',
        string="Número do CPF", xsd_required=True)
    cte30_IE = fields.Char(
        string="Inscrição Estadual")
    cte30_xNome = fields.Char(
        string="Razão social ou nome do remetente",
        xsd_required=True)
    cte30_xFant = fields.Char(
        string="Nome fantasia")
    cte30_fone = fields.Char(
        string="Telefone")
    cte30_enderReme = fields.Many2one(
        "cte.30.tendereco",
        string="Dados do endereço",
        xsd_required=True)
    cte30_email = fields.Char(
        string="Endereço de email")


class Seg(spec_models.AbstractSpecMixin):
    "Informações de Seguro da Carga"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.seg'
    _generateds_type = 'segType'
    _concrete_rec_name = 'cte_respSeg'

    cte30_seg_infCTeNorm70_id = fields.Many2one(
        "cte.30.infctenorm70")
    cte30_respSeg = fields.Selection(
        respSeg_seg,
        string="Responsável pelo seguro",
        xsd_required=True)
    cte30_xSeg = fields.Char(
        string="Nome da Seguradora")
    cte30_nApol = fields.Char(
        string="Número da Apólice")


class SemData(spec_models.AbstractSpecMixin):
    "Entrega sem data definidaEsta opção é proibida para o modal aéreo."
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.semdata'
    _generateds_type = 'semDataType'
    _concrete_rec_name = 'cte_tpPer'

    cte30_tpPer = fields.Selection(
        tpPer_semData,
        string="Tipo de data/período programado para entrega",
        xsd_required=True)


class SemHora(spec_models.AbstractSpecMixin):
    "Entrega sem hora definida"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.semhora'
    _generateds_type = 'semHoraType'
    _concrete_rec_name = 'cte_tpHor'

    cte30_tpHor = fields.Selection(
        tpHor_semHora,
        string="Tipo de hora", xsd_required=True)


class Toma3(spec_models.AbstractSpecMixin):
    """Indicador do "papel" do tomador do serviço no CT-e"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.toma3'
    _generateds_type = 'toma3Type'
    _concrete_rec_name = 'cte_toma'

    cte30_toma = fields.Selection(
        toma_toma3,
        string="Tomador do Serviço", xsd_required=True)


class Toma4(spec_models.AbstractSpecMixin):
    """Indicador do "papel" do tomador do serviço no CT-e"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.toma4'
    _generateds_type = 'toma4Type'
    _concrete_rec_name = 'cte_toma'

    cte30_choice6 = fields.Selection([
        ('cte30_CNPJ', 'CNPJ'),
        ('cte30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="cte30_CNPJ")
    cte30_toma = fields.Selection(
        toma_toma4,
        string="Tomador do Serviço", xsd_required=True)
    cte30_CNPJ = fields.Char(
        choice='6',
        string="Número do CNPJ", xsd_required=True)
    cte30_CPF = fields.Char(
        choice='6',
        string="Número do CPF", xsd_required=True)
    cte30_IE = fields.Char(
        string="Inscrição Estadual")
    cte30_xNome = fields.Char(
        string="Razão Social ou Nome",
        xsd_required=True)
    cte30_xFant = fields.Char(
        string="Nome Fantasia")
    cte30_fone = fields.Char(
        string="Telefone")
    cte30_enderToma = fields.Many2one(
        "cte.30.tendereco",
        string="Dados do endereço",
        xsd_required=True)
    cte30_email = fields.Char(
        string="Endereço de email")


class TomaICMS(spec_models.AbstractSpecMixin):
    """Tomador é contribuinte do ICMS, mas não é emitente de documento fiscal
    eletrônico"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tomaicms'
    _generateds_type = 'tomaICMSType'
    _concrete_rec_name = 'cte_refNFe'

    cte30_choice20 = fields.Selection([
        ('cte30_refNFe', 'refNFe'),
        ('cte30_refNF', 'refNF'),
        ('cte30_refCte', 'refCte')],
        "refNFe/refNF/refCte",
        default="cte30_refNFe")
    cte30_refNFe = fields.Char(
        choice='20',
        string="Chave de acesso da NF",
        xsd_required=True,
        help="Chave de acesso da NF-e emitida pelo Tomador")
    cte30_refNF = fields.Many2one(
        "cte.30.refnf",
        choice='20',
        string="Informação da NF ou CT emitido pelo Tomador",
        xsd_required=True)
    cte30_refCte = fields.Char(
        choice='20',
        string="Chave de acesso do CT",
        xsd_required=True,
        help="Chave de acesso do CT-e emitido pelo Tomador")


class TomaICMS78(spec_models.AbstractSpecMixin):
    """Tomador é contribuinte do ICMS, mas não é emitente de documento fiscal
    eletrônico"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.tomaicms78'
    _generateds_type = 'tomaICMSType78'
    _concrete_rec_name = 'cte_refNFe'

    cte30_choice26 = fields.Selection([
        ('cte30_refNFe', 'refNFe'),
        ('cte30_refNF', 'refNF'),
        ('cte30_refCte', 'refCte')],
        "refNFe/refNF/refCte",
        default="cte30_refNFe")
    cte30_refNFe = fields.Char(
        choice='26',
        string="Chave de acesso da NF",
        xsd_required=True,
        help="Chave de acesso da NF-e emitida pelo Tomador")
    cte30_refNF = fields.Many2one(
        "cte.30.refnf79",
        choice='26',
        string="Informação da NF ou CT emitido pelo Tomador",
        xsd_required=True)
    cte30_refCte = fields.Char(
        choice='26',
        string="Chave de acesso do CT",
        xsd_required=True,
        help="Chave de acesso do CT-e emitido pelo Tomador")


class Toma59(spec_models.AbstractSpecMixin):
    """Informações do Tomador/Usuário do ServiçoOpcional para Excesso de
    Bagagem"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.toma59'
    _generateds_type = 'tomaType59'
    _concrete_rec_name = 'cte_CNPJ'

    cte30_choice24 = fields.Selection([
        ('cte30_CNPJ', 'CNPJ'),
        ('cte30_CPF', 'CPF')],
        "CNPJ/CPF",
        default="cte30_CNPJ")
    cte30_CNPJ = fields.Char(
        choice='24',
        string="Número do CNPJ", xsd_required=True)
    cte30_CPF = fields.Char(
        choice='24',
        string="Número do CPF", xsd_required=True)
    cte30_IE = fields.Char(
        string="Inscrição Estadual")
    cte30_xNome = fields.Char(
        string="Razão social ou nome do tomador",
        xsd_required=True)
    cte30_xFant = fields.Char(
        string="Nome fantasia")
    cte30_fone = fields.Char(
        string="Telefone")
    cte30_enderToma = fields.Many2one(
        "cte.30.tendereco",
        string="Dados do endereço",
        xsd_required=True)
    cte30_email = fields.Char(
        string="Endereço de email")


class VPrest(spec_models.AbstractSpecMixin):
    "Valores da Prestação de Serviço"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.vprest'
    _generateds_type = 'vPrestType'
    _concrete_rec_name = 'cte_vTPrest'

    cte30_vTPrest = fields.Monetary(
        digits=2, string="Valor Total da Prestação do Serviço",
        xsd_required=True)
    cte30_vRec = fields.Monetary(
        digits=2, string="Valor a Receber", xsd_required=True)
    cte30_Comp = fields.One2many(
        "cte.30.comp",
        "cte30_Comp_vPrest_id",
        string="Componentes do Valor da Prestação"
    )


class VPrest64(spec_models.AbstractSpecMixin):
    "Valores da Prestação de Serviço"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.vprest64'
    _generateds_type = 'vPrestType64'
    _concrete_rec_name = 'cte_vTPrest'

    cte30_vTPrest = fields.Monetary(
        digits=2, string="Valor Total da Prestação do Serviço",
        xsd_required=True)
    cte30_vRec = fields.Monetary(
        digits=2, string="Valor a Receber", xsd_required=True)
    cte30_Comp = fields.One2many(
        "cte.30.comp65",
        "cte30_Comp_vPrest64_id",
        string="Componentes do Valor da Prestação"
    )


class VeicNovos(spec_models.AbstractSpecMixin):
    "informações dos veículos transportados"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cte.30.veicnovos'
    _generateds_type = 'veicNovosType'
    _concrete_rec_name = 'cte_chassi'

    cte30_veicNovos_infCTeNorm_id = fields.Many2one(
        "cte.30.infctenorm")
    cte30_chassi = fields.Char(
        string="Chassi do veículo", xsd_required=True)
    cte30_cCor = fields.Char(
        string="Cor do veículo", xsd_required=True)
    cte30_xCor = fields.Char(
        string="Descrição da cor", xsd_required=True)
    cte30_cMod = fields.Char(
        string="Código Marca Modelo", xsd_required=True)
    cte30_vUnit = fields.Monetary(
        digits=2, string="Valor Unitário do Veículo",
        xsd_required=True)
    cte30_vFrete = fields.Monetary(
        digits=2, string="Frete Unitário", xsd_required=True)
