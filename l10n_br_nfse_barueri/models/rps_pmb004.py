# Copyright 2026 Pop Solutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
# Registros tipo 4 e 5 (Detalhe - repositório ADN / IBS-CBS) do layout PMB004
# do arquivo texto de RPS de Barueri (V4.4, 28/05/2026).
#
# nfselib.barueri 1.0.0 implementa apenas os registros do layout PMB002 (Tipo
# 1/2/3/9). O PMB004 tornou OBRIGATÓRIO um Registro Tipo 4 para cada Registro
# Tipo 2, além de um Registro Tipo 5 condicional. A 1.1.0 os declara com outros
# nomes de campo; declaramos aqui os dois, com a mesma mecânica de campos
# posicionais do nfselib, para o módulo funcionar com as duas versões.
#
# Fonte do layout: https://www.barueri.sp.gov.br/nfe/Manuais/RPS_Layout.pdf

from nfselib.barueri.exportador import CampoPosicional, Registro


class RegistroTipo4(Registro):
    # (nome, valor, obrigatorio, tipo, tamanho, pos_inicial, pos_final)
    campos = [
        CampoPosicional("TipoRegistro", "4", True, "NUM", 1, 1, 1),
        CampoPosicional("EnquadramentoSimplesNacional", None, True, "NUM", 1, 2, 2),
        CampoPosicional("RegimeApuracaoSimplesNacional", None, False, "NUM", 1, 3, 3),
        CampoPosicional("CodigoPaisServicoPrestado", None, False, "NUM", 3, 4, 6),
        CampoPosicional("CodigoCidadeLocalPrestacao", None, False, "NUM", 7, 7, 13),
        CampoPosicional("CodigoCidadeTomador", None, False, "NUM", 7, 14, 20),
        CampoPosicional("NIF", None, False, "ALFA", 40, 21, 60),
        CampoPosicional("CodigoNBS", None, True, "NUM", 9, 61, 69),
        CampoPosicional("CEPTomadorEstrangeiro", None, False, "ALFA", 11, 70, 80),
        CampoPosicional("EstadoTomadorEstrangeiro", None, False, "ALFA", 60, 81, 140),
        CampoPosicional("VinculoPartes", None, False, "NUM", 1, 141, 141),
        CampoPosicional("Reservado", None, False, "ALFA", 30, 142, 171),
        CampoPosicional("CEPServicoExterior", None, False, "ALFA", 11, 172, 182),
        CampoPosicional("EstadoServicoExterior", None, False, "ALFA", 60, 183, 242),
        CampoPosicional("NomeEvento", None, False, "ALFA", 255, 243, 497),
        CampoPosicional("DataInicioEvento", None, False, "NUM", 8, 498, 505),
        CampoPosicional("DataFimEvento", None, False, "NUM", 8, 506, 513),
        CampoPosicional(
            "CodigoJustCancelSubstituicao", None, False, "NUM", 1, 514, 514
        ),
        CampoPosicional("CodigoIndicadorOperacao", None, True, "NUM", 6, 515, 520),
        CampoPosicional(
            "CodigoClassificacaoTributariaIBSCBS", None, True, "NUM", 6, 521, 526
        ),
        CampoPosicional(
            "CodigoSituacaoTributariaIBSCBS", None, True, "NUM", 3, 527, 529
        ),
        CampoPosicional("OperacaoUsoConsumoPessoal", None, True, "NUM", 1, 530, 530),
        CampoPosicional("IndicadorDestinatarioServico", None, True, "NUM", 1, 531, 531),
        CampoPosicional("CaracterFimLinha", "\r\n", True, "ALFA", 1, 532, 532),
    ]


class RegistroTipo5(Registro):
    """Detalhe - ADN, condicional: compra governamental, locacao de bem movel,
    doacao e destinatario diferente do tomador. So os campos de compra
    governamental sao preenchidos pelo modulo."""

    campos = [
        CampoPosicional("TipoRegistro", "5", True, "NUM", 1, 1, 1),
        CampoPosicional("CodigoCreditoPresumidoIBSCBS", None, False, "NUM", 2, 2, 3),
        CampoPosicional("TipoEnteGovernamental", None, False, "NUM", 1, 4, 4),
        CampoPosicional("TipoOperacaoEntesGovernamentais", None, False, "NUM", 1, 5, 5),
        CampoPosicional("ChaveNFSeReferenciada", None, False, "NUM", 50, 6, 55),
        CampoPosicional("NCMBemMovelLocacao", None, False, "NUM", 8, 56, 63),
        CampoPosicional("DescricaoBemMovelLocacao", None, False, "ALFA", 150, 64, 213),
        CampoPosicional("QuantidadeBemMovelLocacao", None, False, "NUM", 3, 214, 216),
        CampoPosicional("IndicadorOperacaoDoacao", None, False, "NUM", 1, 217, 217),
        CampoPosicional("DestinatarioEstrangeiro", None, False, "NUM", 1, 218, 218),
        CampoPosicional("CPFCNPJDestinatario", None, False, "NUM", 14, 219, 232),
        CampoPosicional("RazaoSocialDestinatario", None, False, "ALFA", 60, 233, 292),
        CampoPosicional("EnderecoDestinatario", None, False, "ALFA", 75, 293, 367),
        CampoPosicional("NumeroDestinatario", None, False, "ALFA", 9, 368, 376),
        CampoPosicional("ComplementoDestinatario", None, False, "ALFA", 30, 377, 406),
        CampoPosicional("BairroDestinatario", None, False, "ALFA", 40, 407, 446),
        CampoPosicional("CidadeDestinatario", None, False, "ALFA", 40, 447, 486),
        CampoPosicional("CodigoCidadeDestinatario", None, False, "NUM", 7, 487, 493),
        CampoPosicional("UFDestinatario", None, False, "ALFA", 2, 494, 495),
        CampoPosicional("CodigoPaisDestinatario", None, False, "ALFA", 3, 496, 498),
        CampoPosicional("CEPDestinatario", None, False, "NUM", 8, 499, 506),
        CampoPosicional("EmailDestinatario", None, False, "ALFA", 80, 507, 586),
        CampoPosicional("NIFDestinatario", None, False, "ALFA", 40, 587, 626),
        CampoPosicional(
            "CEPDestinatarioEstrangeiro", None, False, "ALFA", 11, 627, 637
        ),
        CampoPosicional(
            "EstadoDestinatarioEstrangeiro", None, False, "ALFA", 60, 638, 697
        ),
        CampoPosicional("CaracterFimLinha", "\r\n", True, "ALFA", 1, 698, 698),
    ]
