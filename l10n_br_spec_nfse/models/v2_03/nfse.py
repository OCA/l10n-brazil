# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Wed Mar 27 01:44:34 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
from odoo import fields
from .. import spec_models

# Tipo Codigo da Lista de Servicos LC 116/2003
tsItemListaServico_tcDadosServico = [
    ("01.01", "01.01"),
    ("01.02", "01.02"),
    ("01.03", "01.03"),
    ("01.04", "01.04"),
    ("01.05", "01.05"),
    ("01.06", "01.06"),
    ("01.07", "01.07"),
    ("01.08", "01.08"),
    ("02.01", "02.01"),
    ("03.02", "03.02"),
    ("03.03", "03.03"),
    ("03.04", "03.04"),
    ("03.05", "03.05"),
    ("04.01", "04.01"),
    ("04.02", "04.02"),
    ("04.03", "04.03"),
    ("04.04", "04.04"),
    ("04.05", "04.05"),
    ("04.06", "04.06"),
    ("04.07", "04.07"),
    ("04.08", "04.08"),
    ("04.09", "04.09"),
    ("04.10", "04.10"),
    ("04.11", "04.11"),
    ("04.12", "04.12"),
    ("04.13", "04.13"),
    ("04.14", "04.14"),
    ("04.15", "04.15"),
    ("04.16", "04.16"),
    ("04.17", "04.17"),
    ("04.18", "04.18"),
    ("04.19", "04.19"),
    ("04.20", "04.20"),
    ("04.21", "04.21"),
    ("04.22", "04.22"),
    ("04.23", "04.23"),
    ("05.01", "05.01"),
    ("05.02", "05.02"),
    ("05.03", "05.03"),
    ("05.04", "05.04"),
    ("05.05", "05.05"),
    ("05.06", "05.06"),
    ("05.07", "05.07"),
    ("05.08", "05.08"),
    ("05.09", "05.09"),
    ("06.01", "06.01"),
    ("06.02", "06.02"),
    ("06.03", "06.03"),
    ("06.04", "06.04"),
    ("06.05", "06.05"),
    ("07.01", "07.01"),
    ("07.02", "07.02"),
    ("07.03", "07.03"),
    ("07.04", "07.04"),
    ("07.05", "07.05"),
    ("07.06", "07.06"),
    ("07.07", "07.07"),
    ("07.08", "07.08"),
    ("07.09", "07.09"),
    ("07.10", "07.10"),
    ("07.11", "07.11"),
    ("07.12", "07.12"),
    ("07.13", "07.13"),
    ("07.16", "07.16"),
    ("07.17", "07.17"),
    ("07.18", "07.18"),
    ("07.19", "07.19"),
    ("07.20", "07.20"),
    ("07.21", "07.21"),
    ("07.22", "07.22"),
    ("08.01", "08.01"),
    ("08.02", "08.02"),
    ("09.01", "09.01"),
    ("09.02", "09.02"),
    ("09.03", "09.03"),
    ("10.01", "10.01"),
    ("10.02", "10.02"),
    ("10.03", "10.03"),
    ("10.04", "10.04"),
    ("10.05", "10.05"),
    ("10.06", "10.06"),
    ("10.07", "10.07"),
    ("10.08", "10.08"),
    ("10.09", "10.09"),
    ("10.10", "10.10"),
    ("11.01", "11.01"),
    ("11.02", "11.02"),
    ("11.03", "11.03"),
    ("11.04", "11.04"),
    ("12.01", "12.01"),
    ("12.02", "12.02"),
    ("12.03", "12.03"),
    ("12.04", "12.04"),
    ("12.05", "12.05"),
    ("12.06", "12.06"),
    ("12.07", "12.07"),
    ("12.08", "12.08"),
    ("12.09", "12.09"),
    ("12.10", "12.10"),
    ("12.11", "12.11"),
    ("12.12", "12.12"),
    ("12.13", "12.13"),
    ("12.14", "12.14"),
    ("12.15", "12.15"),
    ("12.16", "12.16"),
    ("12.17", "12.17"),
    ("13.02", "13.02"),
    ("13.03", "13.03"),
    ("13.04", "13.04"),
    ("13.05", "13.05"),
    ("14.01", "14.01"),
    ("14.02", "14.02"),
    ("14.03", "14.03"),
    ("14.04", "14.04"),
    ("14.05", "14.05"),
    ("14.06", "14.06"),
    ("14.07", "14.07"),
    ("14.08", "14.08"),
    ("14.09", "14.09"),
    ("14.10", "14.10"),
    ("14.11", "14.11"),
    ("14.12", "14.12"),
    ("14.13", "14.13"),
    ("15.01", "15.01"),
    ("15.02", "15.02"),
    ("15.03", "15.03"),
    ("15.04", "15.04"),
    ("15.05", "15.05"),
    ("15.06", "15.06"),
    ("15.07", "15.07"),
    ("15.08", "15.08"),
    ("15.09", "15.09"),
    ("15.10", "15.10"),
    ("15.11", "15.11"),
    ("15.12", "15.12"),
    ("15.13", "15.13"),
    ("15.14", "15.14"),
    ("15.15", "15.15"),
    ("15.16", "15.16"),
    ("15.17", "15.17"),
    ("15.18", "15.18"),
    ("16.01", "16.01"),
    ("17.01", "17.01"),
    ("17.02", "17.02"),
    ("17.03", "17.03"),
    ("17.04", "17.04"),
    ("17.05", "17.05"),
    ("17.06", "17.06"),
    ("17.08", "17.08"),
    ("17.09", "17.09"),
    ("17.10", "17.10"),
    ("17.11", "17.11"),
    ("17.12", "17.12"),
    ("17.13", "17.13"),
    ("17.14", "17.14"),
    ("17.15", "17.15"),
    ("17.16", "17.16"),
    ("17.17", "17.17"),
    ("17.18", "17.18"),
    ("17.19", "17.19"),
    ("17.20", "17.20"),
    ("17.21", "17.21"),
    ("17.22", "17.22"),
    ("17.23", "17.23"),
    ("17.24", "17.24"),
    ("18.01", "18.01"),
    ("19.01", "19.01"),
    ("20.01", "20.01"),
    ("20.02", "20.02"),
    ("20.03", "20.03"),
    ("21.01", "21.01"),
    ("22.01", "22.01"),
    ("23.01", "23.01"),
    ("24.01", "24.01"),
    ("25.01", "25.01"),
    ("25.02", "25.02"),
    ("25.03", "25.03"),
    ("25.04", "25.04"),
    ("26.01", "26.01"),
    ("27.01", "27.01"),
    ("28.01", "28.01"),
    ("29.01", "29.01"),
    ("30.01", "30.01"),
    ("31.01", "31.01"),
    ("32.01", "32.01"),
    ("33.01", "33.01"),
    ("34.01", "34.01"),
    ("35.01", "35.01"),
    ("36.01", "36.01"),
    ("37.01", "37.01"),
    ("38.01", "38.01"),
    ("39.01", "39.01"),
    ("40.01", "40.01"),
]

# UF (
tsUf = [
    ("AC", "AC - Acre"),
    ("AL", "AL - Alagoas"),
    ("AM", "AM - Amazonas"),
    ("AP", "AP - Amapa"),
    ("BA", "BA - Bahia"),
    ("CE", "CE - Ceara"),
    ("DF", "DF - Distrito Federal"),
    ("ES", "ES - Espirito Santo"),
    ("GO", "GO - Goias"),
    ("MA", "MA - Maranhao"),
    ("MG", "MG - Minas Gerais"),
    ("MS", "MS - Mato Grosso do Sul"),
    ("MT", "MT - Mato Grosso"),
    ("PA", "PA - Para"),
    ("PB", "PB - Paraiba"),
    ("PE", "PE - Pernambuco"),
    ("PI", "PI - Piaui"),
    ("PR", "PR - Parana"),
    ("RJ", "RJ - Rio de Janeiro"),
    ("RN", "RN - Rio Grande do Norte"),
    ("RO", "RO - Rondonia"),
    ("RR", "RR - Roraima"),
    ("RS", "RS - Rio Grande do Sul"),
    ("SC", "SC - Santa Catarina"),
    ("SE", "SE - Sergipe"),
    ("SP", "SP - Sao Paulo"),
    ("TO", "TO - Tocantins)"),
]


class CancelarNfseEnvio(spec_models.AbstractSpecMixin):
    _description = 'cancelarnfseenvio'
    _name = 'nfse.20.cancelarnfseenvio'
    _generateds_type = 'CancelarNfseEnvio'
    _concrete_rec_name = 'nfse_Pedido'

    nfse20_Pedido = fields.Many2one(
        "nfse.20.tcpedidocancelamento",
        string="Pedido", xsd_required=True)


class CancelarNfseResposta(spec_models.AbstractSpecMixin):
    _description = 'cancelarnfseresposta'
    _name = 'nfse.20.cancelarnfseresposta'
    _generateds_type = 'CancelarNfseResposta'
    _concrete_rec_name = 'nfse_RetCancelamento'

    nfse20_choice5 = fields.Selection([
        ('nfse20_RetCancelamento', 'RetCancelamento'),
        ('nfse20_ListaMensagemRetorno', 'ListaMensagemRetorno')],
        "RetCancelamento/ListaMensagemRetorno",
        default="nfse20_RetCancelamento")
    nfse20_RetCancelamento = fields.Many2one(
        "nfse.20.tcretcancelamento",
        choice='5',
        string="RetCancelamento",
        xsd_required=True)
    nfse20_ListaMensagemRetorno = fields.Many2one(
        "nfse.20.listamensagemretorno",
        choice='5',
        string="ListaMensagemRetorno",
        xsd_required=True)


class ConsultarLoteRpsEnvio(spec_models.AbstractSpecMixin):
    _description = 'consultarloterpsenvio'
    _name = 'nfse.20.consultarloterpsenvio'
    _generateds_type = 'ConsultarLoteRpsEnvio'
    _concrete_rec_name = 'nfse_Prestador'

    nfse20_Prestador = fields.Many2one(
        "nfse.20.tcidentificacaoprestador",
        string="Prestador", xsd_required=True)
    nfse20_Protocolo = fields.Char(
        string="Protocolo", xsd_required=True)


class ConsultarLoteRpsResposta(spec_models.AbstractSpecMixin):
    _description = 'consultarloterpsresposta'
    _name = 'nfse.20.consultarloterpsresposta'
    _generateds_type = 'ConsultarLoteRpsResposta'
    _concrete_rec_name = 'nfse_Situacao'

    nfse20_choice7 = fields.Selection([
        ('nfse20_ListaNfse', 'ListaNfse'),
        ('nfse20_ListaMensagemRetorno', 'ListaMensagemRetorno'),
        ('nfse20_ListaMensagemRetornoLote', 'ListaMensagemRetornoLote')],
        "ListaNfse/ListaMensagemRetorno/ListaMensagemRetorn...",
        default="nfse20_ListaNfse")
    nfse20_ListaNfse = fields.Many2one(
        "nfse.20.listanfse2",
        choice='7',
        string="ListaNfse", xsd_required=True)
    nfse20_ListaMensagemRetorno = fields.Many2one(
        "nfse.20.listamensagemretorno",
        choice='7',
        string="ListaMensagemRetorno",
        xsd_required=True)
    nfse20_ListaMensagemRetornoLote = fields.Many2one(
        "nfse.20.listamensagemretornolote",
        choice='7',
        string="ListaMensagemRetornoLote",
        xsd_required=True)


class ConsultarNfseFaixaEnvio(spec_models.AbstractSpecMixin):
    _description = 'consultarnfsefaixaenvio'
    _name = 'nfse.20.consultarnfsefaixaenvio'
    _generateds_type = 'ConsultarNfseFaixaEnvio'
    _concrete_rec_name = 'nfse_Prestador'

    nfse20_Prestador = fields.Many2one(
        "nfse.20.tcidentificacaoprestador",
        string="Prestador", xsd_required=True)
    nfse20_Faixa = fields.Many2one(
        "nfse.20.faixa",
        string="Faixa", xsd_required=True)
    nfse20_Pagina = fields.Integer(
        string="Pagina", xsd_required=True)


class ConsultarNfseFaixaResposta(spec_models.AbstractSpecMixin):
    _description = 'consultarnfsefaixaresposta'
    _name = 'nfse.20.consultarnfsefaixaresposta'
    _generateds_type = 'ConsultarNfseFaixaResposta'
    _concrete_rec_name = 'nfse_ListaNfse'

    nfse20_choice13 = fields.Selection([
        ('nfse20_ListaNfse', 'ListaNfse'),
        ('nfse20_ListaMensagemRetorno', 'ListaMensagemRetorno')],
        "ListaNfse/ListaMensagemRetorno",
        default="nfse20_ListaNfse")
    nfse20_ListaNfse = fields.Many2one(
        "nfse.20.listanfse7",
        choice='13',
        string="ListaNfse", xsd_required=True)
    nfse20_ListaMensagemRetorno = fields.Many2one(
        "nfse.20.listamensagemretorno",
        choice='13',
        string="ListaMensagemRetorno",
        xsd_required=True)


class ConsultarNfseRpsEnvio(spec_models.AbstractSpecMixin):
    _description = 'consultarnfserpsenvio'
    _name = 'nfse.20.consultarnfserpsenvio'
    _generateds_type = 'ConsultarNfseRpsEnvio'
    _concrete_rec_name = 'nfse_IdentificacaoRps'

    nfse20_IdentificacaoRps = fields.Many2one(
        "nfse.20.tcidentificacaorps",
        string="IdentificacaoRps",
        xsd_required=True)
    nfse20_Prestador = fields.Many2one(
        "nfse.20.tcidentificacaoprestador",
        string="Prestador", xsd_required=True)


class ConsultarNfseRpsResposta(spec_models.AbstractSpecMixin):
    _description = 'consultarnfserpsresposta'
    _name = 'nfse.20.consultarnfserpsresposta'
    _generateds_type = 'ConsultarNfseRpsResposta'
    _concrete_rec_name = 'nfse_CompNfse'

    nfse20_choice8 = fields.Selection([
        ('nfse20_CompNfse', 'CompNfse'),
        ('nfse20_ListaMensagemRetorno', 'ListaMensagemRetorno')],
        "CompNfse/ListaMensagemRetorno",
        default="nfse20_CompNfse")
    nfse20_CompNfse = fields.Many2one(
        "nfse.20.tccompnfse",
        choice='8',
        string="CompNfse", xsd_required=True)
    nfse20_ListaMensagemRetorno = fields.Many2one(
        "nfse.20.listamensagemretorno",
        choice='8',
        string="ListaMensagemRetorno",
        xsd_required=True)


class ConsultarNfseServicoPrestadoEnvio(spec_models.AbstractSpecMixin):
    _description = 'consultarnfseservicoprestadoenvio'
    _name = 'nfse.20.consultarnfseservicoprestadoenvio'
    _generateds_type = 'ConsultarNfseServicoPrestadoEnvio'
    _concrete_rec_name = 'nfse_Prestador'

    nfse20_choice9 = fields.Selection([
        ('nfse20_PeriodoEmissao', 'PeriodoEmissao'),
        ('nfse20_PeriodoCompetencia', 'PeriodoCompetencia')],
        "PeriodoEmissao/PeriodoCompetencia",
        default="nfse20_PeriodoEmissao")
    nfse20_Prestador = fields.Many2one(
        "nfse.20.tcidentificacaoprestador",
        string="Prestador", xsd_required=True)
    nfse20_NumeroNfse = fields.Integer(
        string="NumeroNfse")
    nfse20_PeriodoEmissao = fields.Many2one(
        "nfse.20.periodoemissao",
        choice='9',
        string="PeriodoEmissao")
    nfse20_PeriodoCompetencia = fields.Many2one(
        "nfse.20.periodocompetencia",
        choice='9',
        string="PeriodoCompetencia")
    nfse20_Tomador = fields.Many2one(
        "nfse.20.tcidentificacaotomador",
        string="Tomador")
    nfse20_Intermediario = fields.Many2one(
        "nfse.20.tcidentificacaointermediario",
        string="Intermediario")
    nfse20_Pagina = fields.Integer(
        string="Pagina", xsd_required=True)


class ConsultarNfseServicoPrestadoResposta(spec_models.AbstractSpecMixin):
    _description = 'consultarnfseservicoprestadoresposta'
    _name = 'nfse.20.consultarnfseservicoprestadoresposta'
    _generateds_type = 'ConsultarNfseServicoPrestadoResposta'
    _concrete_rec_name = 'nfse_ListaNfse'

    nfse20_choice10 = fields.Selection([
        ('nfse20_ListaNfse', 'ListaNfse'),
        ('nfse20_ListaMensagemRetorno', 'ListaMensagemRetorno')],
        "ListaNfse/ListaMensagemRetorno",
        default="nfse20_ListaNfse")
    nfse20_ListaNfse = fields.Many2one(
        "nfse.20.listanfse3",
        choice='10',
        string="ListaNfse", xsd_required=True)
    nfse20_ListaMensagemRetorno = fields.Many2one(
        "nfse.20.listamensagemretorno",
        choice='10',
        string="ListaMensagemRetorno",
        xsd_required=True)


class ConsultarNfseServicoTomadoEnvio(spec_models.AbstractSpecMixin):
    _description = 'consultarnfseservicotomadoenvio'
    _name = 'nfse.20.consultarnfseservicotomadoenvio'
    _generateds_type = 'ConsultarNfseServicoTomadoEnvio'
    _concrete_rec_name = 'nfse_Consulente'

    nfse20_choice11 = fields.Selection([
        ('nfse20_PeriodoEmissao', 'PeriodoEmissao'),
        ('nfse20_PeriodoCompetencia', 'PeriodoCompetencia')],
        "PeriodoEmissao/PeriodoCompetencia",
        default="nfse20_PeriodoEmissao")
    nfse20_Consulente = fields.Many2one(
        "nfse.20.tcidentificacaoconsulente",
        string="Consulente", xsd_required=True)
    nfse20_NumeroNfse = fields.Integer(
        string="NumeroNfse")
    nfse20_PeriodoEmissao = fields.Many2one(
        "nfse.20.periodoemissao4",
        choice='11',
        string="PeriodoEmissao")
    nfse20_PeriodoCompetencia = fields.Many2one(
        "nfse.20.periodocompetencia5",
        choice='11',
        string="PeriodoCompetencia")
    nfse20_Prestador = fields.Many2one(
        "nfse.20.tcidentificacaoprestador",
        string="Prestador")
    nfse20_Tomador = fields.Many2one(
        "nfse.20.tcidentificacaotomador",
        string="Tomador")
    nfse20_Intermediario = fields.Many2one(
        "nfse.20.tcidentificacaointermediario",
        string="Intermediario")
    nfse20_Pagina = fields.Integer(
        string="Pagina", xsd_required=True)


class ConsultarNfseServicoTomadoResposta(spec_models.AbstractSpecMixin):
    _description = 'consultarnfseservicotomadoresposta'
    _name = 'nfse.20.consultarnfseservicotomadoresposta'
    _generateds_type = 'ConsultarNfseServicoTomadoResposta'
    _concrete_rec_name = 'nfse_ListaNfse'

    nfse20_choice12 = fields.Selection([
        ('nfse20_ListaNfse', 'ListaNfse'),
        ('nfse20_ListaMensagemRetorno', 'ListaMensagemRetorno')],
        "ListaNfse/ListaMensagemRetorno",
        default="nfse20_ListaNfse")
    nfse20_ListaNfse = fields.Many2one(
        "nfse.20.listanfse6",
        choice='12',
        string="ListaNfse", xsd_required=True)
    nfse20_ListaMensagemRetorno = fields.Many2one(
        "nfse.20.listamensagemretorno",
        choice='12',
        string="ListaMensagemRetorno",
        xsd_required=True)


class DSAKeyValue(spec_models.AbstractSpecMixin):
    _description = 'dsakeyvalue'
    _name = 'nfse.20.dsakeyvalue'
    _generateds_type = 'DSAKeyValueType'
    _concrete_rec_name = 'nfse_P'

    nfse20_P = fields.Char(
        string="P")
    nfse20_Q = fields.Char(
        string="Q")
    nfse20_G = fields.Char(
        string="G")
    nfse20_Y = fields.Char(
        string="Y", xsd_required=True)
    nfse20_J = fields.Char(
        string="J")
    nfse20_Seed = fields.Char(
        string="Seed")
    nfse20_PgenCounter = fields.Char(
        string="PgenCounter")


class EnviarLoteRpsEnvio(spec_models.AbstractSpecMixin):
    _description = 'enviarloterpsenvio'
    _name = 'nfse.20.enviarloterpsenvio'
    _generateds_type = 'EnviarLoteRpsEnvio'
    _concrete_rec_name = 'nfse_LoteRps'

    nfse20_LoteRps = fields.Many2one(
        "nfse.20.tcloterps",
        string="LoteRps", xsd_required=True)


class EnviarLoteRpsResposta(spec_models.AbstractSpecMixin):
    _description = 'enviarloterpsresposta'
    _name = 'nfse.20.enviarloterpsresposta'
    _generateds_type = 'EnviarLoteRpsResposta'
    _concrete_rec_name = 'nfse_NumeroLote'

    nfse20_choice2 = fields.Selection([
        ('nfse20_NumeroLote', 'NumeroLote'),
        ('nfse20_DataRecebimento', 'DataRecebimento'),
        ('nfse20_Protocolo', 'Protocolo'),
        ('nfse20_ListaMensagemRetorno', 'ListaMensagemRetorno')],
        "NumeroLote/DataRecebimento/Protocolo/ListaMensagem...",
        default="nfse20_NumeroLote")
    nfse20_NumeroLote = fields.Integer(
        choice='2',
        string="NumeroLote", xsd_required=True)
    nfse20_DataRecebimento = fields.Datetime(
        choice='2',
        string="DataRecebimento",
        xsd_required=True)
    nfse20_Protocolo = fields.Char(
        choice='2',
        string="Protocolo", xsd_required=True)
    nfse20_ListaMensagemRetorno = fields.Many2one(
        "nfse.20.listamensagemretorno",
        choice='2',
        string="ListaMensagemRetorno",
        xsd_required=True)


class EnviarLoteRpsSincronoEnvio(spec_models.AbstractSpecMixin):
    _description = 'enviarloterpssincronoenvio'
    _name = 'nfse.20.enviarloterpssincronoenvio'
    _generateds_type = 'EnviarLoteRpsSincronoEnvio'
    _concrete_rec_name = 'nfse_LoteRps'

    nfse20_LoteRps = fields.Many2one(
        "nfse.20.tcloterps",
        string="LoteRps", xsd_required=True)


class EnviarLoteRpsSincronoResposta(spec_models.AbstractSpecMixin):
    _description = 'enviarloterpssincronoresposta'
    _name = 'nfse.20.enviarloterpssincronoresposta'
    _generateds_type = 'EnviarLoteRpsSincronoResposta'
    _concrete_rec_name = 'nfse_NumeroLote'

    nfse20_choice3 = fields.Selection([
        ('nfse20_ListaNfse', 'ListaNfse'),
        ('nfse20_ListaMensagemRetorno', 'ListaMensagemRetorno'),
        ('nfse20_ListaMensagemRetornoLote', 'ListaMensagemRetornoLote')],
        "ListaNfse/ListaMensagemRetorno/ListaMensagemRetorn...",
        default="nfse20_ListaNfse")
    nfse20_NumeroLote = fields.Integer(
        string="NumeroLote")
    nfse20_DataRecebimento = fields.Datetime(
        string="DataRecebimento")
    nfse20_Protocolo = fields.Char(
        string="Protocolo")
    nfse20_ListaNfse = fields.Many2one(
        "nfse.20.listanfse",
        choice='3',
        string="ListaNfse", xsd_required=True)
    nfse20_ListaMensagemRetorno = fields.Many2one(
        "nfse.20.listamensagemretorno",
        choice='3',
        string="ListaMensagemRetorno",
        xsd_required=True)
    nfse20_ListaMensagemRetornoLote = fields.Many2one(
        "nfse.20.listamensagemretornolote",
        choice='3',
        string="ListaMensagemRetornoLote",
        xsd_required=True)


class Faixa(spec_models.AbstractSpecMixin):
    _description = 'faixa'
    _name = 'nfse.20.faixa'
    _generateds_type = 'FaixaType'
    _concrete_rec_name = 'nfse_NumeroNfseInicial'

    nfse20_NumeroNfseInicial = fields.Integer(
        string="NumeroNfseInicial",
        xsd_required=True)
    nfse20_NumeroNfseFinal = fields.Integer(
        string="NumeroNfseFinal")


class GerarNfseEnvio(spec_models.AbstractSpecMixin):
    _description = 'gerarnfseenvio'
    _name = 'nfse.20.gerarnfseenvio'
    _generateds_type = 'GerarNfseEnvio'
    _concrete_rec_name = 'nfse_Rps'

    nfse20_Rps = fields.Many2one(
        "nfse.20.tcdeclaracaoprestacaoservico",
        string="Rps", xsd_required=True)


class GerarNfseResposta(spec_models.AbstractSpecMixin):
    _description = 'gerarnfseresposta'
    _name = 'nfse.20.gerarnfseresposta'
    _generateds_type = 'GerarNfseResposta'
    _concrete_rec_name = 'nfse_ListaNfse'

    nfse20_choice4 = fields.Selection([
        ('nfse20_ListaNfse', 'ListaNfse'),
        ('nfse20_ListaMensagemRetorno', 'ListaMensagemRetorno')],
        "ListaNfse/ListaMensagemRetorno",
        default="nfse20_ListaNfse")
    nfse20_ListaNfse = fields.Many2one(
        "nfse.20.listanfse1",
        choice='4',
        string="ListaNfse", xsd_required=True)
    nfse20_ListaMensagemRetorno = fields.Many2one(
        "nfse.20.listamensagemretorno",
        choice='4',
        string="ListaMensagemRetorno",
        xsd_required=True)


class KeyValue(spec_models.AbstractSpecMixin):
    _description = 'keyvalue'
    _name = 'nfse.20.keyvalue'
    _generateds_type = 'KeyValueType'
    _concrete_rec_name = 'nfse_DSAKeyValue'

    nfse20_KeyValue_KeyInfo_id = fields.Many2one(
        "nfse.20.keyinfo")
    nfse20_choice16 = fields.Selection([
        ('nfse20_DSAKeyValue', 'DSAKeyValue'),
        ('nfse20_RSAKeyValue', 'RSAKeyValue')],
        "DSAKeyValue/RSAKeyValue",
        default="nfse20_DSAKeyValue")
    nfse20_DSAKeyValue = fields.Many2one(
        "nfse.20.dsakeyvalue",
        choice='16',
        string="DSAKeyValue", xsd_required=True)
    nfse20_RSAKeyValue = fields.Many2one(
        "nfse.20.rsakeyvalue",
        choice='16',
        string="RSAKeyValue", xsd_required=True)
    nfse20___ANY__ = fields.Char(
        string="__ANY__", xsd_required=True)
    nfse20_valueOf_ = fields.Char(
        string="valueOf_", xsd_required=True)


class ListaMensagemAlertaRetorno(spec_models.AbstractSpecMixin):
    _description = 'listamensagemalertaretorno'
    _name = 'nfse.20.listamensagemalertaretorno'
    _generateds_type = 'ListaMensagemAlertaRetorno'
    _concrete_rec_name = 'nfse_MensagemRetorno'

    nfse20_MensagemRetorno = fields.One2many(
        "nfse.20.tcmensagemretorno",
        "nfse20_MensagemRetorno_ListaMensagemAlertaRetorno_id",
        string="MensagemRetorno",
        xsd_required=True
    )


class ListaMensagemRetorno(spec_models.AbstractSpecMixin):
    _description = 'listamensagemretorno'
    _name = 'nfse.20.listamensagemretorno'
    _generateds_type = 'ListaMensagemRetorno'
    _concrete_rec_name = 'nfse_MensagemRetorno'

    nfse20_MensagemRetorno = fields.One2many(
        "nfse.20.tcmensagemretorno",
        "nfse20_MensagemRetorno_ListaMensagemRetorno_id",
        string="MensagemRetorno",
        xsd_required=True
    )


class ListaMensagemRetornoLote(spec_models.AbstractSpecMixin):
    _description = 'listamensagemretornolote'
    _name = 'nfse.20.listamensagemretornolote'
    _generateds_type = 'ListaMensagemRetornoLote'
    _concrete_rec_name = 'nfse_MensagemRetorno'

    nfse20_MensagemRetorno = fields.One2many(
        "nfse.20.tcmensagemretornolote",
        "nfse20_MensagemRetorno_ListaMensagemRetornoLote_id",
        string="MensagemRetorno",
        xsd_required=True
    )


class ListaNfse(spec_models.AbstractSpecMixin):
    _description = 'listanfse'
    _name = 'nfse.20.listanfse'
    _generateds_type = 'ListaNfseType'
    _concrete_rec_name = 'nfse_CompNfse'

    nfse20_CompNfse = fields.One2many(
        "nfse.20.tccompnfse",
        "nfse20_CompNfse_ListaNfse_id",
        string="CompNfse", xsd_required=True
    )
    nfse20_ListaMensagemAlertaRetorno = fields.Many2one(
        "nfse.20.listamensagemalertaretorno",
        string="ListaMensagemAlertaRetorno")


class ListaNfse1(spec_models.AbstractSpecMixin):
    _description = 'listanfse1'
    _name = 'nfse.20.listanfse1'
    _generateds_type = 'ListaNfseType1'
    _concrete_rec_name = 'nfse_CompNfse'

    nfse20_CompNfse = fields.Many2one(
        "nfse.20.tccompnfse",
        string="CompNfse", xsd_required=True)
    nfse20_ListaMensagemAlertaRetorno = fields.Many2one(
        "nfse.20.listamensagemalertaretorno",
        string="ListaMensagemAlertaRetorno")


class ListaNfse2(spec_models.AbstractSpecMixin):
    _description = 'listanfse2'
    _name = 'nfse.20.listanfse2'
    _generateds_type = 'ListaNfseType2'
    _concrete_rec_name = 'nfse_CompNfse'

    nfse20_CompNfse = fields.One2many(
        "nfse.20.tccompnfse",
        "nfse20_CompNfse_ListaNfse2_id",
        string="CompNfse", xsd_required=True
    )
    nfse20_ListaMensagemAlertaRetorno = fields.Many2one(
        "nfse.20.listamensagemalertaretorno",
        string="ListaMensagemAlertaRetorno")


class ListaNfse3(spec_models.AbstractSpecMixin):
    _description = 'listanfse3'
    _name = 'nfse.20.listanfse3'
    _generateds_type = 'ListaNfseType3'
    _concrete_rec_name = 'nfse_CompNfse'

    nfse20_CompNfse = fields.One2many(
        "nfse.20.tccompnfse",
        "nfse20_CompNfse_ListaNfse3_id",
        string="CompNfse", xsd_required=True
    )
    nfse20_ProximaPagina = fields.Integer(
        string="ProximaPagina")


class ListaNfse6(spec_models.AbstractSpecMixin):
    _description = 'listanfse6'
    _name = 'nfse.20.listanfse6'
    _generateds_type = 'ListaNfseType6'
    _concrete_rec_name = 'nfse_CompNfse'

    nfse20_CompNfse = fields.One2many(
        "nfse.20.tccompnfse",
        "nfse20_CompNfse_ListaNfse6_id",
        string="CompNfse", xsd_required=True
    )
    nfse20_ProximaPagina = fields.Integer(
        string="ProximaPagina")


class ListaNfse7(spec_models.AbstractSpecMixin):
    _description = 'listanfse7'
    _name = 'nfse.20.listanfse7'
    _generateds_type = 'ListaNfseType7'
    _concrete_rec_name = 'nfse_CompNfse'

    nfse20_CompNfse = fields.One2many(
        "nfse.20.tccompnfse",
        "nfse20_CompNfse_ListaNfse7_id",
        string="CompNfse", xsd_required=True
    )
    nfse20_ProximaPagina = fields.Integer(
        string="ProximaPagina")


class ListaRps(spec_models.AbstractSpecMixin):
    _description = 'listarps'
    _name = 'nfse.20.listarps'
    _generateds_type = 'ListaRpsType'
    _concrete_rec_name = 'nfse_Rps'

    nfse20_Rps = fields.One2many(
        "nfse.20.tcdeclaracaoprestacaoservico",
        "nfse20_Rps_ListaRps_id",
        string="Rps", xsd_required=True
    )


class Manifest(spec_models.AbstractSpecMixin):
    _description = 'manifest'
    _name = 'nfse.20.manifest'
    _generateds_type = 'ManifestType'
    _concrete_rec_name = 'nfse_Id'

    nfse20_Id = fields.Char(
        string="Id")


class NfseSubstituida(spec_models.AbstractSpecMixin):
    _description = 'nfsesubstituida'
    _name = 'nfse.20.nfsesubstituida'
    _generateds_type = 'NfseSubstituidaType'
    _concrete_rec_name = 'nfse_CompNfse'

    nfse20_CompNfse = fields.Many2one(
        "nfse.20.tccompnfse",
        string="CompNfse", xsd_required=True)
    nfse20_ListaMensagemAlertaRetorno = fields.Many2one(
        "nfse.20.listamensagemalertaretorno",
        string="ListaMensagemAlertaRetorno")


class NfseSubstituidora(spec_models.AbstractSpecMixin):
    _description = 'nfsesubstituidora'
    _name = 'nfse.20.nfsesubstituidora'
    _generateds_type = 'NfseSubstituidoraType'
    _concrete_rec_name = 'nfse_CompNfse'

    nfse20_CompNfse = fields.Many2one(
        "nfse.20.tccompnfse",
        string="CompNfse", xsd_required=True)


class Object(spec_models.AbstractSpecMixin):
    _description = 'object'
    _name = 'nfse.20.object'
    _generateds_type = 'ObjectType'
    _concrete_rec_name = 'nfse_Id'

    nfse20_Object_Signature_id = fields.Many2one(
        "nfse.20.signature")
    nfse20_Id = fields.Char(
        string="Id")
    nfse20_MimeType = fields.Char(
        string="MimeType")
    nfse20_Encoding = fields.Char(
        string="Encoding")
    nfse20___ANY__ = fields.Char(
        string="__ANY__", xsd_required=True)
    nfse20_valueOf_ = fields.Char(
        string="valueOf_", xsd_required=True)


class PGPData(spec_models.AbstractSpecMixin):
    _description = 'pgpdata'
    _name = 'nfse.20.pgpdata'
    _generateds_type = 'PGPDataType'
    _concrete_rec_name = 'nfse_PGPKeyID'

    nfse20_PGPData_KeyInfo_id = fields.Many2one(
        "nfse.20.keyinfo")
    nfse20_choice18 = fields.Selection([
        ('nfse20_PGPKeyID', 'PGPKeyID'),
        ('nfse20_PGPKeyPacket', 'PGPKeyPacket')],
        "PGPKeyID/PGPKeyPacket",
        default="nfse20_PGPKeyID")
    nfse20_PGPKeyID = fields.Char(
        choice='18',
        string="PGPKeyID", xsd_required=True)
    nfse20_PGPKeyPacket = fields.Char(
        choice='18',
        string="PGPKeyPacket",
        xsd_required=True)
    nfse20___ANY__ = fields.Char(
        string="__ANY__")


class PeriodoCompetencia(spec_models.AbstractSpecMixin):
    _description = 'periodocompetencia'
    _name = 'nfse.20.periodocompetencia'
    _generateds_type = 'PeriodoCompetenciaType'
    _concrete_rec_name = 'nfse_DataInicial'

    nfse20_DataInicial = fields.Date(
        string="DataInicial", xsd_required=True)
    nfse20_DataFinal = fields.Date(
        string="DataFinal", xsd_required=True)


class PeriodoCompetencia5(spec_models.AbstractSpecMixin):
    _description = 'periodocompetencia5'
    _name = 'nfse.20.periodocompetencia5'
    _generateds_type = 'PeriodoCompetenciaType5'
    _concrete_rec_name = 'nfse_DataInicial'

    nfse20_DataInicial = fields.Date(
        string="DataInicial", xsd_required=True)
    nfse20_DataFinal = fields.Date(
        string="DataFinal", xsd_required=True)


class PeriodoEmissao(spec_models.AbstractSpecMixin):
    _description = 'periodoemissao'
    _name = 'nfse.20.periodoemissao'
    _generateds_type = 'PeriodoEmissaoType'
    _concrete_rec_name = 'nfse_DataInicial'

    nfse20_DataInicial = fields.Date(
        string="DataInicial", xsd_required=True)
    nfse20_DataFinal = fields.Date(
        string="DataFinal", xsd_required=True)


class PeriodoEmissao4(spec_models.AbstractSpecMixin):
    _description = 'periodoemissao4'
    _name = 'nfse.20.periodoemissao4'
    _generateds_type = 'PeriodoEmissaoType4'
    _concrete_rec_name = 'nfse_DataInicial'

    nfse20_DataInicial = fields.Date(
        string="DataInicial", xsd_required=True)
    nfse20_DataFinal = fields.Date(
        string="DataFinal", xsd_required=True)


class RSAKeyValue(spec_models.AbstractSpecMixin):
    _description = 'rsakeyvalue'
    _name = 'nfse.20.rsakeyvalue'
    _generateds_type = 'RSAKeyValueType'
    _concrete_rec_name = 'nfse_Modulus'

    nfse20_Modulus = fields.Char(
        string="Modulus", xsd_required=True)
    nfse20_Exponent = fields.Char(
        string="Exponent", xsd_required=True)


class RetSubstituicao(spec_models.AbstractSpecMixin):
    _description = 'retsubstituicao'
    _name = 'nfse.20.retsubstituicao'
    _generateds_type = 'RetSubstituicaoType'
    _concrete_rec_name = 'nfse_NfseSubstituida'

    nfse20_NfseSubstituida = fields.Many2one(
        "nfse.20.nfsesubstituida",
        string="NfseSubstituida",
        xsd_required=True)
    nfse20_NfseSubstituidora = fields.Many2one(
        "nfse.20.nfsesubstituidora",
        string="NfseSubstituidora",
        xsd_required=True)


class RetrievalMethod(spec_models.AbstractSpecMixin):
    _description = 'retrievalmethod'
    _name = 'nfse.20.retrievalmethod'
    _generateds_type = 'RetrievalMethodType'
    _concrete_rec_name = 'nfse_URI'

    nfse20_RetrievalMethod_KeyInfo_id = fields.Many2one(
        "nfse.20.keyinfo")
    nfse20_URI = fields.Char(
        string="URI")
    nfse20_Type = fields.Char(
        string="Type")


class SPKIData(spec_models.AbstractSpecMixin):
    _description = 'spkidata'
    _name = 'nfse.20.spkidata'
    _generateds_type = 'SPKIDataType'
    _concrete_rec_name = 'nfse_SPKISexp'

    nfse20_SPKIData_KeyInfo_id = fields.Many2one(
        "nfse.20.keyinfo")
    nfse20_SPKISexp = fields.Char(
        string="SPKISexp", xsd_required=True)
    nfse20___ANY__ = fields.Char(
        string="__ANY__")


class SignatureProperties(spec_models.AbstractSpecMixin):
    _description = 'signatureproperties'
    _name = 'nfse.20.signatureproperties'
    _generateds_type = 'SignaturePropertiesType'
    _concrete_rec_name = 'nfse_Id'

    nfse20_Id = fields.Char(
        string="Id")
    nfse20_SignatureProperty = fields.One2many(
        "nfse.20.signatureproperty",
        "nfse20_SignatureProperty_SignatureProperties_id",
        string="SignatureProperty",
        xsd_required=True
    )


class SignatureProperty(spec_models.AbstractSpecMixin):
    _description = 'signatureproperty'
    _name = 'nfse.20.signatureproperty'
    _generateds_type = 'SignaturePropertyType'
    _concrete_rec_name = 'nfse_Target'

    nfse20_SignatureProperty_SignatureProperties_id = fields.Many2one(
        "nfse.20.signatureproperties")
    nfse20_Target = fields.Char(
        string="Target", xsd_required=True)
    nfse20_Id = fields.Char(
        string="Id")
    nfse20___ANY__ = fields.Char(
        string="__ANY__", xsd_required=True)
    nfse20_valueOf_ = fields.Char(
        string="valueOf_", xsd_required=True)


class SubstituicaoNfse(spec_models.AbstractSpecMixin):
    _description = 'substituicaonfse'
    _name = 'nfse.20.substituicaonfse'
    _generateds_type = 'SubstituicaoNfseType'
    _concrete_rec_name = 'nfse_Id'

    nfse20_Id = fields.Char(
        string="Id")
    nfse20_Pedido = fields.Many2one(
        "nfse.20.tcpedidocancelamento",
        string="Pedido", xsd_required=True)
    nfse20_Rps = fields.Many2one(
        "nfse.20.tcdeclaracaoprestacaoservico",
        string="Rps", xsd_required=True)


class SubstituirNfseEnvio(spec_models.AbstractSpecMixin):
    _description = 'substituirnfseenvio'
    _name = 'nfse.20.substituirnfseenvio'
    _generateds_type = 'SubstituirNfseEnvio'
    _concrete_rec_name = 'nfse_SubstituicaoNfse'

    nfse20_SubstituicaoNfse = fields.Many2one(
        "nfse.20.substituicaonfse",
        string="SubstituicaoNfse",
        xsd_required=True)


class SubstituirNfseResposta(spec_models.AbstractSpecMixin):
    _description = 'substituirnfseresposta'
    _name = 'nfse.20.substituirnfseresposta'
    _generateds_type = 'SubstituirNfseResposta'
    _concrete_rec_name = 'nfse_RetSubstituicao'

    nfse20_choice6 = fields.Selection([
        ('nfse20_RetSubstituicao', 'RetSubstituicao'),
        ('nfse20_ListaMensagemRetorno', 'ListaMensagemRetorno')],
        "RetSubstituicao/ListaMensagemRetorno",
        default="nfse20_RetSubstituicao")
    nfse20_RetSubstituicao = fields.Many2one(
        "nfse.20.retsubstituicao",
        choice='6',
        string="RetSubstituicao",
        xsd_required=True)
    nfse20_ListaMensagemRetorno = fields.Many2one(
        "nfse.20.listamensagemretorno",
        choice='6',
        string="ListaMensagemRetorno",
        xsd_required=True)


class X509IssuerSerial(spec_models.AbstractSpecMixin):
    _description = 'x509issuerserial'
    _name = 'nfse.20.x509issuerserial'
    _generateds_type = 'X509IssuerSerialType'
    _concrete_rec_name = 'nfse_X509IssuerName'

    nfse20_X509IssuerSerial_X509Data_id = fields.Many2one(
        "nfse.20.x509data")
    nfse20_X509IssuerName = fields.Char(
        string="X509IssuerName",
        xsd_required=True)
    nfse20_X509SerialNumber = fields.Char(
        string="X509SerialNumber",
        xsd_required=True)


class Cabecalho(spec_models.AbstractSpecMixin):
    _description = 'cabecalho'
    _name = 'nfse.20.cabecalho'
    _generateds_type = 'cabecalho'
    _concrete_rec_name = 'nfse_versao'

    nfse20_versao = fields.Char(
        string="versao", xsd_required=True)
    nfse20_versaoDados = fields.Char(
        string="versaoDados", xsd_required=True)


class TcCancelamentoNfse(spec_models.AbstractSpecMixin):
    _description = 'tccancelamentonfse'
    _name = 'nfse.20.tccancelamentonfse'
    _generateds_type = 'tcCancelamentoNfse'
    _concrete_rec_name = 'nfse_versao'

    nfse20_versao = fields.Char(
        string="versao", xsd_required=True)
    nfse20_Confirmacao = fields.Many2one(
        "nfse.20.tcconfirmacaocancelamento",
        string="Confirmacao", xsd_required=True)


class TcCompNfse(spec_models.AbstractSpecMixin):
    _description = 'tccompnfse'
    _name = 'nfse.20.tccompnfse'
    _generateds_type = 'tcCompNfse'
    _concrete_rec_name = 'nfse_Nfse'

    nfse20_CompNfse_ListaNfse_id = fields.Many2one(
        "nfse.20.listanfse")
    nfse20_CompNfse_ListaNfse2_id = fields.Many2one(
        "nfse.20.listanfse2")
    nfse20_CompNfse_ListaNfse3_id = fields.Many2one(
        "nfse.20.listanfse3")
    nfse20_CompNfse_ListaNfse6_id = fields.Many2one(
        "nfse.20.listanfse6")
    nfse20_CompNfse_ListaNfse7_id = fields.Many2one(
        "nfse.20.listanfse7")
    nfse20_Nfse = fields.Many2one(
        "nfse.20.tcnfse",
        string="Nfse", xsd_required=True)
    nfse20_NfseCancelamento = fields.Many2one(
        "nfse.20.tccancelamentonfse",
        string="NfseCancelamento")
    nfse20_NfseSubstituicao = fields.Many2one(
        "nfse.20.tcsubstituicaonfse",
        string="NfseSubstituicao")


class TcConfirmacaoCancelamento(spec_models.AbstractSpecMixin):
    _description = 'tcconfirmacaocancelamento'
    _name = 'nfse.20.tcconfirmacaocancelamento'
    _generateds_type = 'tcConfirmacaoCancelamento'
    _concrete_rec_name = 'nfse_Id'

    nfse20_Id = fields.Char(
        string="Id")
    nfse20_Pedido = fields.Many2one(
        "nfse.20.tcpedidocancelamento",
        string="Pedido", xsd_required=True)
    nfse20_DataHora = fields.Datetime(
        string="DataHora", xsd_required=True)


class TcContato(spec_models.AbstractSpecMixin):
    _description = 'tccontato'
    _name = 'nfse.20.tccontato'
    _generateds_type = 'tcContato'
    _concrete_rec_name = 'nfse_Telefone'

    nfse20_Telefone = fields.Char(
        string="Telefone")
    nfse20_Email = fields.Char(
        string="Email")


class TcCpfCnpj(spec_models.AbstractSpecMixin):
    _description = 'tccpfcnpj'
    _name = 'nfse.20.tccpfcnpj'
    _generateds_type = 'tcCpfCnpj'
    _concrete_rec_name = 'nfse_Cpf'

    nfse20_choice1 = fields.Selection([
        ('nfse20_Cpf', 'Cpf'),
        ('nfse20_Cnpj', 'Cnpj')],
        "Cpf/Cnpj",
        default="nfse20_Cpf")
    nfse20_Cpf = fields.Char(
        choice='1',
        string="Cpf", xsd_required=True)
    nfse20_Cnpj = fields.Char(
        choice='1',
        string="Cnpj", xsd_required=True)


class TcDadosConstrucaoCivil(spec_models.AbstractSpecMixin):
    _description = 'tcdadosconstrucaocivil'
    _name = 'nfse.20.tcdadosconstrucaocivil'
    _generateds_type = 'tcDadosConstrucaoCivil'
    _concrete_rec_name = 'nfse_CodigoObra'

    nfse20_CodigoObra = fields.Char(
        string="CodigoObra")
    nfse20_Art = fields.Char(
        string="Art", xsd_required=True)


class TcDadosIntermediario(spec_models.AbstractSpecMixin):
    _description = 'tcdadosintermediario'
    _name = 'nfse.20.tcdadosintermediario'
    _generateds_type = 'tcDadosIntermediario'
    _concrete_rec_name = 'nfse_IdentificacaoIntermediario'

    nfse20_IdentificacaoIntermediario = fields.Many2one(
        "nfse.20.tcidentificacaointermediario",
        string="IdentificacaoIntermediario",
        xsd_required=True)
    nfse20_RazaoSocial = fields.Char(
        string="RazaoSocial", xsd_required=True)
    nfse20_CodigoMunicipio = fields.Integer(
        string="CodigoMunicipio",
        xsd_required=True)


class TcDadosPrestador(spec_models.AbstractSpecMixin):
    _description = 'tcdadosprestador'
    _name = 'nfse.20.tcdadosprestador'
    _generateds_type = 'tcDadosPrestador'
    _concrete_rec_name = 'nfse_IdentificacaoPrestador'

    nfse20_IdentificacaoPrestador = fields.Many2one(
        "nfse.20.tcidentificacaoprestador",
        string="IdentificacaoPrestador",
        xsd_required=True)
    nfse20_RazaoSocial = fields.Char(
        string="RazaoSocial", xsd_required=True)
    nfse20_NomeFantasia = fields.Char(
        string="NomeFantasia")
    nfse20_Endereco = fields.Many2one(
        "nfse.20.tcendereco",
        string="Endereco", xsd_required=True)
    nfse20_Contato = fields.Many2one(
        "nfse.20.tccontato",
        string="Contato")


class TcDadosServico(spec_models.AbstractSpecMixin):
    _description = 'tcdadosservico'
    _name = 'nfse.20.tcdadosservico'
    _generateds_type = 'tcDadosServico'
    _concrete_rec_name = 'nfse_Valores'

    nfse20_Valores = fields.Many2one(
        "nfse.20.tcvaloresdeclaracaoservico",
        string="Valores", xsd_required=True)
    nfse20_ItemListaServico = fields.Selection(
        tsItemListaServico_tcDadosServico,
        string="ItemListaServico",
        xsd_required=True)
    nfse20_CodigoCnae = fields.Integer(
        string="CodigoCnae")
    nfse20_CodigoTributacaoMunicipio = fields.Char(
        string="CodigoTributacaoMunicipio")
    nfse20_CodigoNbs = fields.Char(
        string="CodigoNbs")
    nfse20_Discriminacao = fields.Char(
        string="Discriminacao",
        xsd_required=True)
    nfse20_CodigoMunicipio = fields.Integer(
        string="CodigoMunicipio",
        xsd_required=True)
    nfse20_CodigoPais = fields.Char(
        string="CodigoPais")
    nfse20_MunicipioIncidencia = fields.Integer(
        string="MunicipioIncidencia")
    nfse20_NumeroProcesso = fields.Char(
        string="NumeroProcesso")


class TcDadosTomador(spec_models.AbstractSpecMixin):
    _description = 'tcdadostomador'
    _name = 'nfse.20.tcdadostomador'
    _generateds_type = 'tcDadosTomador'
    _concrete_rec_name = 'nfse_IdentificacaoTomador'

    nfse20_IdentificacaoTomador = fields.Many2one(
        "nfse.20.tcidentificacaotomador",
        string="IdentificacaoTomador")
    nfse20_NifTomador = fields.Char(
        string="NifTomador")
    nfse20_RazaoSocial = fields.Char(
        string="RazaoSocial")
    nfse20_Endereco = fields.Many2one(
        "nfse.20.tcendereco",
        string="Endereco")
    nfse20_Contato = fields.Many2one(
        "nfse.20.tccontato",
        string="Contato")


class TcDeclaracaoPrestacaoServico(spec_models.AbstractSpecMixin):
    _description = 'tcdeclaracaoprestacaoservico'
    _name = 'nfse.20.tcdeclaracaoprestacaoservico'
    _generateds_type = 'tcDeclaracaoPrestacaoServico'
    _concrete_rec_name = 'nfse_InfDeclaracaoPrestacaoServico'

    nfse20_Rps_ListaRps_id = fields.Many2one(
        "nfse.20.listarps")
    nfse20_InfDeclaracaoPrestacaoServico = fields.Many2one(
        "nfse.20.tcinfdeclaracaoprestacaoservico",
        string="InfDeclaracaoPrestacaoServico",
        xsd_required=True)


class TcEndereco(spec_models.AbstractSpecMixin):
    _description = 'tcendereco'
    _name = 'nfse.20.tcendereco'
    _generateds_type = 'tcEndereco'
    _concrete_rec_name = 'nfse_Endereco'

    nfse20_Endereco = fields.Char(
        string="Endereco")
    nfse20_Numero = fields.Char(
        string="Numero")
    nfse20_Complemento = fields.Char(
        string="Complemento")
    nfse20_Bairro = fields.Char(
        string="Bairro")
    nfse20_CodigoMunicipio = fields.Integer(
        string="CodigoMunicipio")
    nfse20_Uf = fields.Selection(
        tsUf,
        string="Uf")
    nfse20_CodigoPais = fields.Char(
        string="CodigoPais")
    nfse20_Cep = fields.Char(
        string="Cep")


class TcIdentificacaoConsulente(spec_models.AbstractSpecMixin):
    _description = 'tcidentificacaoconsulente'
    _name = 'nfse.20.tcidentificacaoconsulente'
    _generateds_type = 'tcIdentificacaoConsulente'
    _concrete_rec_name = 'nfse_CpfCnpj'

    nfse20_CpfCnpj = fields.Many2one(
        "nfse.20.tccpfcnpj",
        string="CpfCnpj", xsd_required=True)
    nfse20_InscricaoMunicipal = fields.Char(
        string="InscricaoMunicipal")


class TcIdentificacaoIntermediario(spec_models.AbstractSpecMixin):
    _description = 'tcidentificacaointermediario'
    _name = 'nfse.20.tcidentificacaointermediario'
    _generateds_type = 'tcIdentificacaoIntermediario'
    _concrete_rec_name = 'nfse_CpfCnpj'

    nfse20_CpfCnpj = fields.Many2one(
        "nfse.20.tccpfcnpj",
        string="CpfCnpj")
    nfse20_InscricaoMunicipal = fields.Char(
        string="InscricaoMunicipal")


class TcIdentificacaoNfse(spec_models.AbstractSpecMixin):
    _description = 'tcidentificacaonfse'
    _name = 'nfse.20.tcidentificacaonfse'
    _generateds_type = 'tcIdentificacaoNfse'
    _concrete_rec_name = 'nfse_Numero'

    nfse20_Numero = fields.Integer(
        string="Numero", xsd_required=True)
    nfse20_CpfCnpj = fields.Many2one(
        "nfse.20.tccpfcnpj",
        string="CpfCnpj", xsd_required=True)
    nfse20_InscricaoMunicipal = fields.Char(
        string="InscricaoMunicipal")
    nfse20_CodigoMunicipio = fields.Integer(
        string="CodigoMunicipio",
        xsd_required=True)


class TcIdentificacaoOrgaoGerador(spec_models.AbstractSpecMixin):
    _description = 'tcidentificacaoorgaogerador'
    _name = 'nfse.20.tcidentificacaoorgaogerador'
    _generateds_type = 'tcIdentificacaoOrgaoGerador'
    _concrete_rec_name = 'nfse_CodigoMunicipio'

    nfse20_CodigoMunicipio = fields.Integer(
        string="CodigoMunicipio",
        xsd_required=True)
    nfse20_Uf = fields.Selection(
        tsUf,
        string="Uf", xsd_required=True)


class TcIdentificacaoPrestador(spec_models.AbstractSpecMixin):
    _description = 'tcidentificacaoprestador'
    _name = 'nfse.20.tcidentificacaoprestador'
    _generateds_type = 'tcIdentificacaoPrestador'
    _concrete_rec_name = 'nfse_CpfCnpj'

    nfse20_CpfCnpj = fields.Many2one(
        "nfse.20.tccpfcnpj",
        string="CpfCnpj")
    nfse20_InscricaoMunicipal = fields.Char(
        string="InscricaoMunicipal")


class TcIdentificacaoRps(spec_models.AbstractSpecMixin):
    _description = 'tcidentificacaorps'
    _name = 'nfse.20.tcidentificacaorps'
    _generateds_type = 'tcIdentificacaoRps'
    _concrete_rec_name = 'nfse_Numero'

    nfse20_Numero = fields.Integer(
        string="Numero", xsd_required=True)
    nfse20_Serie = fields.Char(
        string="Serie", xsd_required=True)


class TcIdentificacaoTomador(spec_models.AbstractSpecMixin):
    _description = 'tcidentificacaotomador'
    _name = 'nfse.20.tcidentificacaotomador'
    _generateds_type = 'tcIdentificacaoTomador'
    _concrete_rec_name = 'nfse_CpfCnpj'

    nfse20_CpfCnpj = fields.Many2one(
        "nfse.20.tccpfcnpj",
        string="CpfCnpj")
    nfse20_InscricaoMunicipal = fields.Char(
        string="InscricaoMunicipal")


class TcInfDeclaracaoPrestacaoServico(spec_models.AbstractSpecMixin):
    _description = 'tcinfdeclaracaoprestacaoservico'
    _name = 'nfse.20.tcinfdeclaracaoprestacaoservico'
    _generateds_type = 'tcInfDeclaracaoPrestacaoServico'
    _concrete_rec_name = 'nfse_Id'

    nfse20_Id = fields.Char(
        string="Id")
    nfse20_Rps = fields.Many2one(
        "nfse.20.tcinfrps",
        string="Rps")
    nfse20_Competencia = fields.Date(
        string="Competencia", xsd_required=True)
    nfse20_Servico = fields.Many2one(
        "nfse.20.tcdadosservico",
        string="Servico", xsd_required=True)
    nfse20_Prestador = fields.Many2one(
        "nfse.20.tcidentificacaoprestador",
        string="Prestador", xsd_required=True)
    nfse20_Tomador = fields.Many2one(
        "nfse.20.tcdadostomador",
        string="Tomador")
    nfse20_Intermediario = fields.Many2one(
        "nfse.20.tcdadosintermediario",
        string="Intermediario")
    nfse20_ConstrucaoCivil = fields.Many2one(
        "nfse.20.tcdadosconstrucaocivil",
        string="ConstrucaoCivil")


class TcInfNfse(spec_models.AbstractSpecMixin):
    _description = 'tcinfnfse'
    _name = 'nfse.20.tcinfnfse'
    _generateds_type = 'tcInfNfse'
    _concrete_rec_name = 'nfse_Id'

    nfse20_Id = fields.Char(
        string="Id")
    nfse20_Numero = fields.Integer(
        string="Numero", xsd_required=True)
    nfse20_CodigoVerificacao = fields.Char(
        string="CodigoVerificacao",
        xsd_required=True)
    nfse20_DataEmissao = fields.Datetime(
        string="DataEmissao", xsd_required=True)
    nfse20_NfseSubstituida = fields.Integer(
        string="NfseSubstituida")
    nfse20_OutrasInformacoes = fields.Char(
        string="OutrasInformacoes")
    nfse20_ValoresNfse = fields.Many2one(
        "nfse.20.tcvaloresnfse",
        string="ValoresNfse", xsd_required=True)
    nfse20_ValorCredito = fields.Monetary(
        string="ValorCredito")
    nfse20_PrestadorServico = fields.Many2one(
        "nfse.20.tcdadosprestador",
        string="PrestadorServico",
        xsd_required=True)
    nfse20_OrgaoGerador = fields.Many2one(
        "nfse.20.tcidentificacaoorgaogerador",
        string="OrgaoGerador",
        xsd_required=True)
    nfse20_DeclaracaoPrestacaoServico = fields.Many2one(
        "nfse.20.tcdeclaracaoprestacaoservico",
        string="DeclaracaoPrestacaoServico",
        xsd_required=True)


class TcInfPedidoCancelamento(spec_models.AbstractSpecMixin):
    _description = 'tcinfpedidocancelamento'
    _name = 'nfse.20.tcinfpedidocancelamento'
    _generateds_type = 'tcInfPedidoCancelamento'
    _concrete_rec_name = 'nfse_Id'

    nfse20_Id = fields.Char(
        string="Id")
    nfse20_IdentificacaoNfse = fields.Many2one(
        "nfse.20.tcidentificacaonfse",
        string="IdentificacaoNfse",
        xsd_required=True)


class TcInfRps(spec_models.AbstractSpecMixin):
    _description = 'tcinfrps'
    _name = 'nfse.20.tcinfrps'
    _generateds_type = 'tcInfRps'
    _concrete_rec_name = 'nfse_Id'

    nfse20_Id = fields.Char(
        string="Id")
    nfse20_IdentificacaoRps = fields.Many2one(
        "nfse.20.tcidentificacaorps",
        string="IdentificacaoRps",
        xsd_required=True)
    nfse20_DataEmissao = fields.Date(
        string="DataEmissao", xsd_required=True)
    nfse20_RpsSubstituido = fields.Many2one(
        "nfse.20.tcidentificacaorps",
        string="RpsSubstituido")


class TcInfSubstituicaoNfse(spec_models.AbstractSpecMixin):
    _description = 'tcinfsubstituicaonfse'
    _name = 'nfse.20.tcinfsubstituicaonfse'
    _generateds_type = 'tcInfSubstituicaoNfse'
    _concrete_rec_name = 'nfse_Id'

    nfse20_Id = fields.Char(
        string="Id")
    nfse20_NfseSubstituidora = fields.Integer(
        string="NfseSubstituidora",
        xsd_required=True)


class TcLoteRps(spec_models.AbstractSpecMixin):
    _description = 'tcloterps'
    _name = 'nfse.20.tcloterps'
    _generateds_type = 'tcLoteRps'
    _concrete_rec_name = 'nfse_Id'

    nfse20_Id = fields.Char(
        string="Id")
    nfse20_versao = fields.Char(
        string="versao", xsd_required=True)
    nfse20_NumeroLote = fields.Integer(
        string="NumeroLote", xsd_required=True)
    nfse20_CpfCnpj = fields.Many2one(
        "nfse.20.tccpfcnpj",
        string="CpfCnpj", xsd_required=True)
    nfse20_InscricaoMunicipal = fields.Char(
        string="InscricaoMunicipal")
    nfse20_QuantidadeRps = fields.Integer(
        string="QuantidadeRps",
        xsd_required=True)
    nfse20_ListaRps = fields.Many2one(
        "nfse.20.listarps",
        string="ListaRps", xsd_required=True)


class TcMensagemRetorno(spec_models.AbstractSpecMixin):
    _description = 'tcmensagemretorno'
    _name = 'nfse.20.tcmensagemretorno'
    _generateds_type = 'tcMensagemRetorno'
    _concrete_rec_name = 'nfse_Codigo'

    nfse20_MensagemRetorno_ListaMensagemAlertaRetorno_id = fields.Many2one(
        "nfse.20.listamensagemalertaretorno")
    nfse20_MensagemRetorno_ListaMensagemRetorno_id = fields.Many2one(
        "nfse.20.listamensagemretorno")
    nfse20_Codigo = fields.Char(
        string="Codigo", xsd_required=True)
    nfse20_Mensagem = fields.Char(
        string="Mensagem", xsd_required=True)
    nfse20_Correcao = fields.Char(
        string="Correcao")


class TcMensagemRetornoLote(spec_models.AbstractSpecMixin):
    _description = 'tcmensagemretornolote'
    _name = 'nfse.20.tcmensagemretornolote'
    _generateds_type = 'tcMensagemRetornoLote'
    _concrete_rec_name = 'nfse_IdentificacaoRps'

    nfse20_MensagemRetorno_ListaMensagemRetornoLote_id = fields.Many2one(
        "nfse.20.listamensagemretornolote")
    nfse20_IdentificacaoRps = fields.Many2one(
        "nfse.20.tcidentificacaorps",
        string="IdentificacaoRps",
        xsd_required=True)
    nfse20_Codigo = fields.Char(
        string="Codigo", xsd_required=True)
    nfse20_Mensagem = fields.Char(
        string="Mensagem", xsd_required=True)


class TcNfse(spec_models.AbstractSpecMixin):
    _description = 'tcnfse'
    _name = 'nfse.20.tcnfse'
    _generateds_type = 'tcNfse'
    _concrete_rec_name = 'nfse_versao'

    nfse20_versao = fields.Char(
        string="versao", xsd_required=True)
    nfse20_InfNfse = fields.Many2one(
        "nfse.20.tcinfnfse",
        string="InfNfse", xsd_required=True)


class TcPedidoCancelamento(spec_models.AbstractSpecMixin):
    _description = 'tcpedidocancelamento'
    _name = 'nfse.20.tcpedidocancelamento'
    _generateds_type = 'tcPedidoCancelamento'
    _concrete_rec_name = 'nfse_InfPedidoCancelamento'

    nfse20_InfPedidoCancelamento = fields.Many2one(
        "nfse.20.tcinfpedidocancelamento",
        string="InfPedidoCancelamento",
        xsd_required=True)


class TcRetCancelamento(spec_models.AbstractSpecMixin):
    _description = 'tcretcancelamento'
    _name = 'nfse.20.tcretcancelamento'
    _generateds_type = 'tcRetCancelamento'
    _concrete_rec_name = 'nfse_NfseCancelamento'

    nfse20_NfseCancelamento = fields.Many2one(
        "nfse.20.tccancelamentonfse",
        string="NfseCancelamento",
        xsd_required=True)


class TcSubstituicaoNfse(spec_models.AbstractSpecMixin):
    _description = 'tcsubstituicaonfse'
    _name = 'nfse.20.tcsubstituicaonfse'
    _generateds_type = 'tcSubstituicaoNfse'
    _concrete_rec_name = 'nfse_versao'

    nfse20_versao = fields.Char(
        string="versao", xsd_required=True)
    nfse20_SubstituicaoNfse = fields.Many2one(
        "nfse.20.tcinfsubstituicaonfse",
        string="SubstituicaoNfse",
        xsd_required=True)


class TcValoresDeclaracaoServico(spec_models.AbstractSpecMixin):
    _description = 'tcvaloresdeclaracaoservico'
    _name = 'nfse.20.tcvaloresdeclaracaoservico'
    _generateds_type = 'tcValoresDeclaracaoServico'
    _concrete_rec_name = 'nfse_ValorServicos'

    nfse20_ValorServicos = fields.Monetary(
        string="ValorServicos",
        xsd_required=True)
    nfse20_ValorDeducoes = fields.Monetary(
        string="ValorDeducoes")
    nfse20_ValorPis = fields.Monetary(
        string="ValorPis")
    nfse20_ValorCofins = fields.Monetary(
        string="ValorCofins")
    nfse20_ValorInss = fields.Monetary(
        string="ValorInss")
    nfse20_ValorIr = fields.Monetary(
        string="ValorIr")
    nfse20_ValorCsll = fields.Monetary(
        string="ValorCsll")
    nfse20_OutrasRetencoes = fields.Monetary(
        string="OutrasRetencoes")
    nfse20_ValTotTributos = fields.Monetary(
        string="ValTotTributos")
    nfse20_ValorIss = fields.Monetary(
        string="ValorIss")
    nfse20_Aliquota = fields.Monetary(
        string="Aliquota")
    nfse20_DescontoIncondicionado = fields.Monetary(
        string="DescontoIncondicionado")
    nfse20_DescontoCondicionado = fields.Monetary(
        string="DescontoCondicionado")


class TcValoresNfse(spec_models.AbstractSpecMixin):
    _description = 'tcvaloresnfse'
    _name = 'nfse.20.tcvaloresnfse'
    _generateds_type = 'tcValoresNfse'
    _concrete_rec_name = 'nfse_BaseCalculo'

    nfse20_BaseCalculo = fields.Monetary(
        string="BaseCalculo")
    nfse20_Aliquota = fields.Monetary(
        string="Aliquota")
    nfse20_ValorIss = fields.Monetary(
        string="ValorIss")
    nfse20_ValorLiquidoNfse = fields.Monetary(
        string="ValorLiquidoNfse",
        xsd_required=True)
