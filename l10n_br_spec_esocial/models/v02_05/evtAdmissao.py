# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:19 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# Estado da Federação emissor da CNH
ufCnh_TCnh = [
    ("AC", "AC"),
    ("AL", "AL"),
    ("AP", "AP"),
    ("AM", "AM"),
    ("BA", "BA"),
    ("CE", "CE"),
    ("DF", "DF"),
    ("ES", "ES"),
    ("GO", "GO"),
    ("MA", "MA"),
    ("MT", "MT"),
    ("MS", "MS"),
    ("MG", "MG"),
    ("PA", "PA"),
    ("PB", "PB"),
    ("PR", "PR"),
    ("PE", "PE"),
    ("PI", "PI"),
    ("RJ", "RJ"),
    ("RN", "RN"),
    ("RS", "RS"),
    ("RO", "RO"),
    ("RR", "RR"),
    ("SC", "SC"),
    ("SP", "SP"),
    ("SE", "SE"),
    ("TO", "TO"),
]

# UF da expedição da CTPS
ufCtps_TCtps = [
    ("AC", "AC"),
    ("AL", "AL"),
    ("AP", "AP"),
    ("AM", "AM"),
    ("BA", "BA"),
    ("CE", "CE"),
    ("DF", "DF"),
    ("ES", "ES"),
    ("GO", "GO"),
    ("MA", "MA"),
    ("MT", "MT"),
    ("MS", "MS"),
    ("MG", "MG"),
    ("PA", "PA"),
    ("PB", "PB"),
    ("PR", "PR"),
    ("PE", "PE"),
    ("PI", "PI"),
    ("RJ", "RJ"),
    ("RN", "RN"),
    ("RS", "RS"),
    ("RO", "RO"),
    ("RR", "RR"),
    ("SC", "SC"),
    ("SP", "SP"),
    ("SE", "SE"),
    ("TO", "TO"),
]

# Sigla da UF
uf_nascimento = [
    ("AC", "AC"),
    ("AL", "AL"),
    ("AP", "AP"),
    ("AM", "AM"),
    ("BA", "BA"),
    ("CE", "CE"),
    ("DF", "DF"),
    ("ES", "ES"),
    ("GO", "GO"),
    ("MA", "MA"),
    ("MT", "MT"),
    ("MS", "MS"),
    ("MG", "MG"),
    ("PA", "PA"),
    ("PB", "PB"),
    ("PR", "PR"),
    ("PE", "PE"),
    ("PI", "PI"),
    ("RJ", "RJ"),
    ("RN", "RN"),
    ("RS", "RS"),
    ("RO", "RO"),
    ("RR", "RR"),
    ("SC", "SC"),
    ("SP", "SP"),
    ("SE", "SE"),
    ("TO", "TO"),
]

# Sigla da UF
uf_TEnderecoBrasil = [
    ("AC", "AC"),
    ("AL", "AL"),
    ("AP", "AP"),
    ("AM", "AM"),
    ("BA", "BA"),
    ("CE", "CE"),
    ("DF", "DF"),
    ("ES", "ES"),
    ("GO", "GO"),
    ("MA", "MA"),
    ("MT", "MT"),
    ("MS", "MS"),
    ("MG", "MG"),
    ("PA", "PA"),
    ("PB", "PB"),
    ("PR", "PR"),
    ("PE", "PE"),
    ("PI", "PI"),
    ("RJ", "RJ"),
    ("RN", "RN"),
    ("RS", "RS"),
    ("RO", "RO"),
    ("RR", "RR"),
    ("SC", "SC"),
    ("SP", "SP"),
    ("SE", "SE"),
    ("TO", "TO"),
]


class TCnh(spec_models.AbstractSpecMixin):
    "Cartera Nacional de Habilitação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.tcnh'
    _generateds_type = 'TCnh'
    _concrete_rec_name = 'esoc_nrRegCnh'

    esoc02_nrRegCnh = fields.Char(
        string="nrRegCnh", xsd_required=True)
    esoc02_dtExped = fields.Date(
        string="dtExped")
    esoc02_ufCnh = fields.Selection(
        ufCnh_TCnh,
        string="ufCnh", xsd_required=True)
    esoc02_dtValid = fields.Date(
        string="dtValid", xsd_required=True)
    esoc02_dtPriHab = fields.Date(
        string="dtPriHab")
    esoc02_categoriaCnh = fields.Char(
        string="categoriaCnh",
        xsd_required=True)


class TContato(spec_models.AbstractSpecMixin):
    "Informações de Contato"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.tcontato'
    _generateds_type = 'TContato'
    _concrete_rec_name = 'esoc_fonePrinc'

    esoc02_fonePrinc = fields.Char(
        string="fonePrinc")
    esoc02_foneAlternat = fields.Char(
        string="foneAlternat")
    esoc02_emailPrinc = fields.Char(
        string="emailPrinc")
    esoc02_emailAlternat = fields.Char(
        string="emailAlternat")


class TCtps(spec_models.AbstractSpecMixin):
    "Carteira de Trabalho e Previdência Social"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.tctps'
    _generateds_type = 'TCtps'
    _concrete_rec_name = 'esoc_nrCtps'

    esoc02_nrCtps = fields.Char(
        string="nrCtps", xsd_required=True)
    esoc02_serieCtps = fields.Char(
        string="serieCtps", xsd_required=True)
    esoc02_ufCtps = fields.Selection(
        ufCtps_TCtps,
        string="ufCtps", xsd_required=True)


class TDependente(spec_models.AbstractSpecMixin):
    _description = 'tdependente'
    _name = 'esoc.02.evtadmissao.tdependente'
    _generateds_type = 'TDependente'
    _concrete_rec_name = 'esoc_tpDep'

    esoc02_dependente_trabalhador_id = fields.Many2one(
        "esoc.02.evtadmissao.trabalhador")
    esoc02_tpDep = fields.Char(
        string="tpDep", xsd_required=True)
    esoc02_nmDep = fields.Char(
        string="nmDep", xsd_required=True)
    esoc02_dtNascto = fields.Date(
        string="dtNascto", xsd_required=True)
    esoc02_cpfDep = fields.Char(
        string="cpfDep")
    esoc02_depIRRF = fields.Char(
        string="depIRRF", xsd_required=True)
    esoc02_depSF = fields.Char(
        string="depSF", xsd_required=True)
    esoc02_incTrab = fields.Char(
        string="incTrab", xsd_required=True)


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtadmissao.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TEnderecoBrasil(spec_models.AbstractSpecMixin):
    "Informações do Endereço no Brasil"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.tenderecobrasil'
    _generateds_type = 'TEnderecoBrasil'
    _concrete_rec_name = 'esoc_tpLograd'

    esoc02_tpLograd = fields.Char(
        string="tpLograd", xsd_required=True)
    esoc02_dscLograd = fields.Char(
        string="dscLograd", xsd_required=True)
    esoc02_nrLograd = fields.Char(
        string="nrLograd", xsd_required=True)
    esoc02_complemento = fields.Char(
        string="complemento")
    esoc02_bairro = fields.Char(
        string="bairro")
    esoc02_cep = fields.Char(
        string="cep", xsd_required=True)
    esoc02_codMunic = fields.Integer(
        string="codMunic", xsd_required=True)
    esoc02_uf = fields.Selection(
        uf_TEnderecoBrasil,
        string="uf", xsd_required=True)


class TEnderecoExterior(spec_models.AbstractSpecMixin):
    "Informações do Endereço no Exterior"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.tenderecoexterior'
    _generateds_type = 'TEnderecoExterior'
    _concrete_rec_name = 'esoc_paisResid'

    esoc02_paisResid = fields.Char(
        string="paisResid", xsd_required=True)
    esoc02_dscLograd = fields.Char(
        string="dscLograd", xsd_required=True)
    esoc02_nrLograd = fields.Char(
        string="nrLograd", xsd_required=True)
    esoc02_complemento = fields.Char(
        string="complemento")
    esoc02_bairro = fields.Char(
        string="bairro")
    esoc02_nmCid = fields.Char(
        string="nmCid", xsd_required=True)
    esoc02_codPostal = fields.Char(
        string="codPostal")


class TFgts(spec_models.AbstractSpecMixin):
    "Informações do FGTS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.tfgts'
    _generateds_type = 'TFgts'
    _concrete_rec_name = 'esoc_opcFGTS'

    esoc02_opcFGTS = fields.Boolean(
        string="opcFGTS", xsd_required=True)
    esoc02_dtOpcFGTS = fields.Date(
        string="dtOpcFGTS")


class THorario(spec_models.AbstractSpecMixin):
    "Informações de Horário Contratual"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.thorario'
    _generateds_type = 'THorario'
    _concrete_rec_name = 'esoc_dia'

    esoc02_horario_horContratual_id = fields.Many2one(
        "esoc.02.evtadmissao.horcontratual")
    esoc02_dia = fields.Boolean(
        string="dia", xsd_required=True)
    esoc02_codHorContrat = fields.Char(
        string="codHorContrat",
        xsd_required=True)


class TIdeEveTrab(spec_models.AbstractSpecMixin):
    "Identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.tideevetrab'
    _generateds_type = 'TIdeEveTrab'
    _concrete_rec_name = 'esoc_indRetif'

    esoc02_indRetif = fields.Boolean(
        string="indRetif", xsd_required=True)
    esoc02_nrRecibo = fields.Char(
        string="nrRecibo")
    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class TLocalTrab(spec_models.AbstractSpecMixin):
    "Informações do Local de Trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.tlocaltrab'
    _generateds_type = 'TLocalTrab'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_descComp = fields.Char(
        string="descComp")


class TOc(spec_models.AbstractSpecMixin):
    "Órgão de Classe"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.toc'
    _generateds_type = 'TOc'
    _concrete_rec_name = 'esoc_nrOc'

    esoc02_nrOc = fields.Char(
        string="nrOc", xsd_required=True)
    esoc02_orgaoEmissor = fields.Char(
        string="orgaoEmissor",
        xsd_required=True)
    esoc02_dtExped = fields.Date(
        string="dtExped")
    esoc02_dtValid = fields.Date(
        string="dtValid")


class TRemun(spec_models.AbstractSpecMixin):
    "Remuneração e periodicidade de pagamento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.tremun'
    _generateds_type = 'TRemun'
    _concrete_rec_name = 'esoc_vrSalFx'

    esoc02_vrSalFx = fields.Monetary(
        string="vrSalFx", xsd_required=True)
    esoc02_undSalFixo = fields.Boolean(
        string="undSalFixo", xsd_required=True)
    esoc02_dscSalVar = fields.Char(
        string="dscSalVar")


class TRg(spec_models.AbstractSpecMixin):
    _description = 'trg'
    _name = 'esoc.02.evtadmissao.trg'
    _generateds_type = 'TRg'
    _concrete_rec_name = 'esoc_nrRg'

    esoc02_nrRg = fields.Char(
        string="nrRg", xsd_required=True)
    esoc02_orgaoEmissor = fields.Char(
        string="orgaoEmissor",
        xsd_required=True)
    esoc02_dtExped = fields.Date(
        string="dtExped")


class TRic(spec_models.AbstractSpecMixin):
    "Registro de Identificação Civil"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.tric'
    _generateds_type = 'TRic'
    _concrete_rec_name = 'esoc_nrRic'

    esoc02_nrRic = fields.Char(
        string="nrRic", xsd_required=True)
    esoc02_orgaoEmissor = fields.Char(
        string="orgaoEmissor",
        xsd_required=True)
    esoc02_dtExped = fields.Date(
        string="dtExped")


class TRne(spec_models.AbstractSpecMixin):
    "Registro Nacional de Estrangeiros"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.trne'
    _generateds_type = 'TRne'
    _concrete_rec_name = 'esoc_nrRne'

    esoc02_nrRne = fields.Char(
        string="nrRne", xsd_required=True)
    esoc02_orgaoEmissor = fields.Char(
        string="orgaoEmissor",
        xsd_required=True)
    esoc02_dtExped = fields.Date(
        string="dtExped")


class TTrabEstrang(spec_models.AbstractSpecMixin):
    "Informações do Trabalhador Estrangeiro"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.ttrabestrang'
    _generateds_type = 'TTrabEstrang'
    _concrete_rec_name = 'esoc_dtChegada'

    esoc02_dtChegada = fields.Date(
        string="dtChegada")
    esoc02_classTrabEstrang = fields.Boolean(
        string="classTrabEstrang",
        xsd_required=True)
    esoc02_casadoBr = fields.Char(
        string="casadoBr", xsd_required=True)
    esoc02_filhosBr = fields.Char(
        string="filhosBr", xsd_required=True)


class Afastamento(spec_models.AbstractSpecMixin):
    "Informações de afastamento do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.afastamento'
    _generateds_type = 'afastamentoType'
    _concrete_rec_name = 'esoc_dtIniAfast'

    esoc02_dtIniAfast = fields.Date(
        string="dtIniAfast", xsd_required=True)
    esoc02_codMotAfast = fields.Char(
        string="codMotAfast", xsd_required=True)


class AlvaraJudicial(spec_models.AbstractSpecMixin):
    "Dados do Alvará Judicial"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.alvarajudicial'
    _generateds_type = 'alvaraJudicialType'
    _concrete_rec_name = 'esoc_nrProcJud'

    esoc02_nrProcJud = fields.Char(
        string="nrProcJud", xsd_required=True)


class Aposentadoria(spec_models.AbstractSpecMixin):
    "Informação de aposentadoria do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.aposentadoria'
    _generateds_type = 'aposentadoriaType'
    _concrete_rec_name = 'esoc_trabAposent'

    esoc02_trabAposent = fields.Char(
        string="trabAposent", xsd_required=True)


class Aprend(spec_models.AbstractSpecMixin):
    "Informações relacionadas ao aprendiz"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.aprend'
    _generateds_type = 'aprendType'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class Desligamento(spec_models.AbstractSpecMixin):
    "Informações de desligamento do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.desligamento'
    _generateds_type = 'desligamentoType'
    _concrete_rec_name = 'esoc_dtDeslig'

    esoc02_dtDeslig = fields.Date(
        string="dtDeslig", xsd_required=True)


class Documentos(spec_models.AbstractSpecMixin):
    "Informações dos documentos pessoais do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.documentos'
    _generateds_type = 'documentosType'
    _concrete_rec_name = 'esoc_CTPS'

    esoc02_CTPS = fields.Many2one(
        "esoc.02.evtadmissao.tctps",
        string="Carteira de Trabalho e Previdência Social")
    esoc02_RIC = fields.Many2one(
        "esoc.02.evtadmissao.tric",
        string="Informações do Documento Nacional de Identidade",
        help="Informações do Documento Nacional de Identidade (DNI)")
    esoc02_RG = fields.Many2one(
        "esoc.02.evtadmissao.trg",
        string="Informações do Registro Geral (RG)")
    esoc02_RNE = fields.Many2one(
        "esoc.02.evtadmissao.trne",
        string="Informações do Registro Nacional de Estrangeiro")
    esoc02_OC = fields.Many2one(
        "esoc.02.evtadmissao.toc",
        string="Informações do número de registro em Órgão de Classe",
        help="Informações do número de registro em Órgão de Classe (OC)")
    esoc02_CNH = fields.Many2one(
        "esoc.02.evtadmissao.tcnh",
        string="Informações da Carteira Nacional de Habilitação",
        help="Informações da Carteira Nacional de Habilitação (CNH)")


class Duracao(spec_models.AbstractSpecMixin):
    "Duração do Contrato de Trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.duracao'
    _generateds_type = 'duracaoType'
    _concrete_rec_name = 'esoc_tpContr'

    esoc02_tpContr = fields.Boolean(
        string="tpContr", xsd_required=True)
    esoc02_dtTerm = fields.Date(
        string="dtTerm")
    esoc02_clauAssec = fields.Char(
        string="clauAssec")
    esoc02_objDet = fields.Char(
        string="objDet")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtadmissao.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtAdmissao'

    esoc02_evtAdmissao = fields.Many2one(
        "esoc.02.evtadmissao.evtadmissao",
        string="evtAdmissao", xsd_required=True)


class Endereco(spec_models.AbstractSpecMixin):
    "Endereço do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.endereco'
    _generateds_type = 'enderecoType'
    _concrete_rec_name = 'esoc_brasil'

    esoc02_choice1 = fields.Selection([
        ('esoc02_brasil', 'brasil'),
        ('esoc02_exterior', 'exterior')],
        "brasil/exterior",
        default="esoc02_brasil")
    esoc02_brasil = fields.Many2one(
        "esoc.02.evtadmissao.tenderecobrasil",
        choice='1',
        string="Endereço no Brasil",
        xsd_required=True)
    esoc02_exterior = fields.Many2one(
        "esoc.02.evtadmissao.tenderecoexterior",
        choice='1',
        string="Endereço no Exterior",
        xsd_required=True)


class EvtAdmissao(spec_models.AbstractSpecMixin):
    """Evento Cadastramento Inicial do Vínculo e Admissão / Ingresso de
    Trabalhador"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.evtadmissao'
    _generateds_type = 'evtAdmissaoType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtadmissao.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtadmissao.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_trabalhador = fields.Many2one(
        "esoc.02.evtadmissao.trabalhador",
        string="Informações Pessoais do Trabalhador",
        xsd_required=True)
    esoc02_vinculo = fields.Many2one(
        "esoc.02.evtadmissao.vinculo",
        string="Informações do Vínculo",
        xsd_required=True)


class FiliacaoSindical(spec_models.AbstractSpecMixin):
    "Filiação Sindical do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.filiacaosindical'
    _generateds_type = 'filiacaoSindicalType'
    _concrete_rec_name = 'esoc_cnpjSindTrab'

    esoc02_filiacaoSindical_infoContrato_id = fields.Many2one(
        "esoc.02.evtadmissao.infocontrato")
    esoc02_cnpjSindTrab = fields.Char(
        string="cnpjSindTrab",
        xsd_required=True)


class HorContratual(spec_models.AbstractSpecMixin):
    "Informações do Horário Contratual do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.horcontratual'
    _generateds_type = 'horContratualType'
    _concrete_rec_name = 'esoc_qtdHrsSem'

    esoc02_qtdHrsSem = fields.Monetary(
        string="qtdHrsSem")
    esoc02_tpJornada = fields.Boolean(
        string="tpJornada", xsd_required=True)
    esoc02_dscTpJorn = fields.Char(
        string="dscTpJorn")
    esoc02_tmpParc = fields.Boolean(
        string="tmpParc", xsd_required=True)
    esoc02_horario = fields.One2many(
        "esoc.02.evtadmissao.thorario",
        "esoc02_horario_horContratual_id",
        string="Informações diárias do horário contratual"
    )


class IdeEstabVinc(spec_models.AbstractSpecMixin):
    """Identificação do estabelecimento ao qual o trabalhador está vinculado"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.ideestabvinc'
    _generateds_type = 'ideEstabVincType'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class IdeTomadorServ(spec_models.AbstractSpecMixin):
    """Identifica a empresa contratante para a qual o trabalhador temporário
    será alocado"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.idetomadorserv'
    _generateds_type = 'ideTomadorServType'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_ideEstabVinc = fields.Many2one(
        "esoc.02.evtadmissao.ideestabvinc",
        string="ideEstabVinc",
        help="Identificação do estabelecimento ao qual o trabalhador está"
        "\nvinculado")


class IdeTrabSubstituido(spec_models.AbstractSpecMixin):
    "Identificação do(s) trabalhador(es) substituído(s)"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.idetrabsubstituido'
    _generateds_type = 'ideTrabSubstituidoType'
    _concrete_rec_name = 'esoc_cpfTrabSubst'

    esoc02_ideTrabSubstituido_trabTemporario_id = fields.Many2one(
        "esoc.02.evtadmissao.trabtemporario")
    esoc02_cpfTrabSubst = fields.Char(
        string="cpfTrabSubst",
        xsd_required=True)


class InfoCeletista(spec_models.AbstractSpecMixin):
    "Informações de Trabalhador Celetista"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.infoceletista'
    _generateds_type = 'infoCeletistaType'
    _concrete_rec_name = 'esoc_dtAdm'

    esoc02_dtAdm = fields.Date(
        string="dtAdm", xsd_required=True)
    esoc02_tpAdmissao = fields.Boolean(
        string="tpAdmissao", xsd_required=True)
    esoc02_indAdmissao = fields.Boolean(
        string="indAdmissao", xsd_required=True)
    esoc02_tpRegJor = fields.Boolean(
        string="tpRegJor", xsd_required=True)
    esoc02_natAtividade = fields.Boolean(
        string="natAtividade",
        xsd_required=True)
    esoc02_dtBase = fields.Boolean(
        string="dtBase")
    esoc02_cnpjSindCategProf = fields.Char(
        string="cnpjSindCategProf",
        xsd_required=True)
    esoc02_FGTS = fields.Many2one(
        "esoc.02.evtadmissao.tfgts",
        string="Informações do Fundo de Garantia do Tempo de Serviço",
        xsd_required=True,
        help="Informações do Fundo de Garantia do Tempo de Serviço - FGTS")
    esoc02_trabTemporario = fields.Many2one(
        "esoc.02.evtadmissao.trabtemporario",
        string="Dados sobre trabalho temporário")
    esoc02_aprend = fields.Many2one(
        "esoc.02.evtadmissao.aprend",
        string="Informações relacionadas ao aprendiz")


class InfoContrato(spec_models.AbstractSpecMixin):
    "Informações do Contrato de Trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.infocontrato'
    _generateds_type = 'infoContratoType'
    _concrete_rec_name = 'esoc_codCargo'

    esoc02_codCargo = fields.Char(
        string="codCargo")
    esoc02_codFuncao = fields.Char(
        string="codFuncao")
    esoc02_codCateg = fields.Integer(
        string="codCateg", xsd_required=True)
    esoc02_codCarreira = fields.Char(
        string="codCarreira")
    esoc02_dtIngrCarr = fields.Date(
        string="dtIngrCarr")
    esoc02_remuneracao = fields.Many2one(
        "esoc.02.evtadmissao.tremun",
        string="Informações da remuneração e periodicidade de pagamento",
        xsd_required=True)
    esoc02_duracao = fields.Many2one(
        "esoc.02.evtadmissao.duracao",
        string="Duração do Contrato de Trabalho",
        xsd_required=True)
    esoc02_localTrabalho = fields.Many2one(
        "esoc.02.evtadmissao.localtrabalho",
        string="Informações do local de trabalho",
        xsd_required=True)
    esoc02_horContratual = fields.Many2one(
        "esoc.02.evtadmissao.horcontratual",
        string="Informações do Horário Contratual do Trabalhador")
    esoc02_filiacaoSindical = fields.One2many(
        "esoc.02.evtadmissao.filiacaosindical",
        "esoc02_filiacaoSindical_infoContrato_id",
        string="Filiação Sindical do Trabalhador"
    )
    esoc02_alvaraJudicial = fields.Many2one(
        "esoc.02.evtadmissao.alvarajudicial",
        string="Dados do Alvará Judicial")
    esoc02_observacoes = fields.One2many(
        "esoc.02.evtadmissao.observacoes",
        "esoc02_observacoes_infoContrato_id",
        string="Observações do contrato de trabalho"
    )


class InfoDecJud(spec_models.AbstractSpecMixin):
    "Informações sobre os dados da decisão judicial"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.infodecjud'
    _generateds_type = 'infoDecJudType'
    _concrete_rec_name = 'esoc_nrProcJud'

    esoc02_nrProcJud = fields.Char(
        string="nrProcJud", xsd_required=True)


class InfoDeficiencia(spec_models.AbstractSpecMixin):
    "Pessoa com Deficiência"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.infodeficiencia'
    _generateds_type = 'infoDeficienciaType'
    _concrete_rec_name = 'esoc_defFisica'

    esoc02_defFisica = fields.Char(
        string="defFisica", xsd_required=True)
    esoc02_defVisual = fields.Char(
        string="defVisual", xsd_required=True)
    esoc02_defAuditiva = fields.Char(
        string="defAuditiva", xsd_required=True)
    esoc02_defMental = fields.Char(
        string="defMental", xsd_required=True)
    esoc02_defIntelectual = fields.Char(
        string="defIntelectual",
        xsd_required=True)
    esoc02_reabReadap = fields.Char(
        string="reabReadap", xsd_required=True)
    esoc02_infoCota = fields.Char(
        string="infoCota", xsd_required=True)
    esoc02_observacao = fields.Char(
        string="observacao")


class InfoEstatutario(spec_models.AbstractSpecMixin):
    "Informações de Trabalhador Estatutário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.infoestatutario'
    _generateds_type = 'infoEstatutarioType'
    _concrete_rec_name = 'esoc_indProvim'

    esoc02_indProvim = fields.Boolean(
        string="indProvim", xsd_required=True)
    esoc02_tpProv = fields.Boolean(
        string="tpProv", xsd_required=True)
    esoc02_dtNomeacao = fields.Date(
        string="dtNomeacao", xsd_required=True)
    esoc02_dtPosse = fields.Date(
        string="dtPosse", xsd_required=True)
    esoc02_dtExercicio = fields.Date(
        string="dtExercicio", xsd_required=True)
    esoc02_tpPlanRP = fields.Boolean(
        string="tpPlanRP")
    esoc02_infoDecJud = fields.Many2one(
        "esoc.02.evtadmissao.infodecjud",
        string="Informações sobre os dados da decisão judicial")


class InfoRegimeTrab(spec_models.AbstractSpecMixin):
    "Informações do regime trabalhista"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.inforegimetrab'
    _generateds_type = 'infoRegimeTrabType'
    _concrete_rec_name = 'esoc_infoCeletista'

    esoc02_choice2 = fields.Selection([
        ('esoc02_infoCeletista', 'infoCeletista'),
        ('esoc02_infoEstatutario', 'infoEstatutario')],
        "infoCeletista/infoEstatutario",
        default="esoc02_infoCeletista")
    esoc02_infoCeletista = fields.Many2one(
        "esoc.02.evtadmissao.infoceletista",
        choice='2',
        string="Informações de Trabalhador Celetista",
        xsd_required=True)
    esoc02_infoEstatutario = fields.Many2one(
        "esoc.02.evtadmissao.infoestatutario",
        choice='2',
        string="Informações de Trabalhador Estatutário",
        xsd_required=True)


class LocalTrabalho(spec_models.AbstractSpecMixin):
    "Informações do local de trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.localtrabalho'
    _generateds_type = 'localTrabalhoType'
    _concrete_rec_name = 'esoc_localTrabGeral'

    esoc02_localTrabGeral = fields.Many2one(
        "esoc.02.evtadmissao.tlocaltrab",
        string="localTrabGeral",
        help="Estabelecimento onde o trabalhador exercerá suas atividades")
    esoc02_localTrabDom = fields.Many2one(
        "esoc.02.evtadmissao.tenderecobrasil",
        string="localTrabDom",
        help="Endereço de trabalho do trabalhador doméstico e trabalhador"
        "\ntemporário")


class MudancaCPF(spec_models.AbstractSpecMixin):
    "Informações de mudança de CPF do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.mudancacpf'
    _generateds_type = 'mudancaCPFType'
    _concrete_rec_name = 'esoc_cpfAnt'

    esoc02_cpfAnt = fields.Char(
        string="cpfAnt", xsd_required=True)
    esoc02_matricAnt = fields.Char(
        string="matricAnt", xsd_required=True)
    esoc02_dtAltCPF = fields.Date(
        string="dtAltCPF", xsd_required=True)
    esoc02_observacao = fields.Char(
        string="observacao")


class Nascimento(spec_models.AbstractSpecMixin):
    "Grupo de informações do nascimento do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.nascimento'
    _generateds_type = 'nascimentoType'
    _concrete_rec_name = 'esoc_dtNascto'

    esoc02_dtNascto = fields.Date(
        string="dtNascto", xsd_required=True)
    esoc02_codMunic = fields.Integer(
        string="codMunic")
    esoc02_uf = fields.Selection(
        uf_nascimento,
        string="uf")
    esoc02_paisNascto = fields.Char(
        string="paisNascto", xsd_required=True)
    esoc02_paisNac = fields.Char(
        string="paisNac", xsd_required=True)
    esoc02_nmMae = fields.Char(
        string="nmMae")
    esoc02_nmPai = fields.Char(
        string="nmPai")


class Observacoes(spec_models.AbstractSpecMixin):
    "Observações do contrato de trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.observacoes'
    _generateds_type = 'observacoesType'
    _concrete_rec_name = 'esoc_observacao'

    esoc02_observacoes_infoContrato_id = fields.Many2one(
        "esoc.02.evtadmissao.infocontrato")
    esoc02_observacao = fields.Char(
        string="observacao", xsd_required=True)


class SucessaoVinc(spec_models.AbstractSpecMixin):
    "Grupo de informações da sucessão de vínculo trabalhista"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.sucessaovinc'
    _generateds_type = 'sucessaoVincType'
    _concrete_rec_name = 'esoc_tpInscAnt'

    esoc02_tpInscAnt = fields.Boolean(
        string="tpInscAnt", xsd_required=True)
    esoc02_cnpjEmpregAnt = fields.Char(
        string="cnpjEmpregAnt",
        xsd_required=True)
    esoc02_matricAnt = fields.Char(
        string="matricAnt")
    esoc02_dtTransf = fields.Date(
        string="dtTransf", xsd_required=True)
    esoc02_observacao = fields.Char(
        string="observacao")


class TrabTemporario(spec_models.AbstractSpecMixin):
    "Dados sobre trabalho temporário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.trabtemporario'
    _generateds_type = 'trabTemporarioType'
    _concrete_rec_name = 'esoc_hipLeg'

    esoc02_hipLeg = fields.Boolean(
        string="hipLeg", xsd_required=True)
    esoc02_justContr = fields.Char(
        string="justContr", xsd_required=True)
    esoc02_tpInclContr = fields.Boolean(
        string="tpInclContr", xsd_required=True)
    esoc02_ideTomadorServ = fields.Many2one(
        "esoc.02.evtadmissao.idetomadorserv",
        string="ideTomadorServ",
        xsd_required=True,
        help="Identifica a empresa contratante para a qual o trabalhador"
        "\ntemporário será alocado")
    esoc02_ideTrabSubstituido = fields.One2many(
        "esoc.02.evtadmissao.idetrabsubstituido",
        "esoc02_ideTrabSubstituido_trabTemporario_id",
        string="Identificação do(s) trabalhador(es) substituído(s)"
    )


class Trabalhador(spec_models.AbstractSpecMixin):
    "Informações Pessoais do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.trabalhador'
    _generateds_type = 'trabalhadorType'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_nisTrab = fields.Char(
        string="nisTrab", xsd_required=True)
    esoc02_nmTrab = fields.Char(
        string="nmTrab", xsd_required=True)
    esoc02_sexo = fields.Char(
        string="sexo", xsd_required=True)
    esoc02_racaCor = fields.Boolean(
        string="racaCor", xsd_required=True)
    esoc02_estCiv = fields.Boolean(
        string="estCiv")
    esoc02_grauInstr = fields.Char(
        string="grauInstr", xsd_required=True)
    esoc02_indPriEmpr = fields.Char(
        string="indPriEmpr")
    esoc02_nmSoc = fields.Char(
        string="nmSoc")
    esoc02_nascimento = fields.Many2one(
        "esoc.02.evtadmissao.nascimento",
        string="Grupo de informações do nascimento do trabalhador",
        xsd_required=True)
    esoc02_documentos = fields.Many2one(
        "esoc.02.evtadmissao.documentos",
        string="Informações dos documentos pessoais do trabalhador")
    esoc02_endereco = fields.Many2one(
        "esoc.02.evtadmissao.endereco",
        string="Endereço do Trabalhador",
        xsd_required=True)
    esoc02_trabEstrangeiro = fields.Many2one(
        "esoc.02.evtadmissao.ttrabestrang",
        string="Informações do Trabalhador Estrangeiro")
    esoc02_infoDeficiencia = fields.Many2one(
        "esoc.02.evtadmissao.infodeficiencia",
        string="Pessoa com Deficiência")
    esoc02_dependente = fields.One2many(
        "esoc.02.evtadmissao.tdependente",
        "esoc02_dependente_trabalhador_id",
        string="Informações dos dependentes"
    )
    esoc02_aposentadoria = fields.Many2one(
        "esoc.02.evtadmissao.aposentadoria",
        string="Informação de aposentadoria do trabalhador")
    esoc02_contato = fields.Many2one(
        "esoc.02.evtadmissao.tcontato",
        string="Informações de Contato")


class TransfDom(spec_models.AbstractSpecMixin):
    """Informações do empregado doméstico transferido de outro representante da
    mesma unidade familiar"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.transfdom'
    _generateds_type = 'transfDomType'
    _concrete_rec_name = 'esoc_cpfSubstituido'

    esoc02_cpfSubstituido = fields.Char(
        string="cpfSubstituido",
        xsd_required=True)
    esoc02_matricAnt = fields.Char(
        string="matricAnt")
    esoc02_dtTransf = fields.Date(
        string="dtTransf", xsd_required=True)


class Vinculo(spec_models.AbstractSpecMixin):
    "Informações do Vínculo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmissao.vinculo'
    _generateds_type = 'vinculoType'
    _concrete_rec_name = 'esoc_matricula'

    esoc02_matricula = fields.Char(
        string="matricula", xsd_required=True)
    esoc02_tpRegTrab = fields.Boolean(
        string="tpRegTrab", xsd_required=True)
    esoc02_tpRegPrev = fields.Boolean(
        string="tpRegPrev", xsd_required=True)
    esoc02_nrRecInfPrelim = fields.Char(
        string="nrRecInfPrelim")
    esoc02_cadIni = fields.Char(
        string="cadIni", xsd_required=True)
    esoc02_infoRegimeTrab = fields.Many2one(
        "esoc.02.evtadmissao.inforegimetrab",
        string="Informações do regime trabalhista",
        xsd_required=True)
    esoc02_infoContrato = fields.Many2one(
        "esoc.02.evtadmissao.infocontrato",
        string="Informações do Contrato de Trabalho",
        xsd_required=True)
    esoc02_sucessaoVinc = fields.Many2one(
        "esoc.02.evtadmissao.sucessaovinc",
        string="Grupo de informações da sucessão de vínculo trabalhista")
    esoc02_transfDom = fields.Many2one(
        "esoc.02.evtadmissao.transfdom",
        string="transfDom",
        help="Informações do empregado doméstico transferido de outro"
        "\nrepresentante da mesma unidade familiar")
    esoc02_mudancaCPF = fields.Many2one(
        "esoc.02.evtadmissao.mudancacpf",
        string="Informações de mudança de CPF do trabalhador")
    esoc02_afastamento = fields.Many2one(
        "esoc.02.evtadmissao.afastamento",
        string="Informações de afastamento do trabalhador")
    esoc02_desligamento = fields.Many2one(
        "esoc.02.evtadmissao.desligamento",
        string="Informações de desligamento do trabalhador")
