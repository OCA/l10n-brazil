# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Thu Jan 30 10:03:16 2020 by generateDS.py(Akretion's branch).
# Python 3.6.9 (default, Nov  7 2019, 10:44:02)  [GCC 8.3.0]
#
import textwrap
from odoo import fields, models

# Código de Regime Tributário.
# Este campo será obrigatoriamente preenchido com:
CRT_EMIT = [
    ("1", "1 – Simples Nacional"),
    ("2", "2 – Simples Nacional – excesso de sublimite de receita bruta"),
    ("3", "3 – Regime Normal."),
]

CSOSN_ICMSSN101 = [
    ("101", "101- Tributada pelo Simples Nacional com permissão de crédito. "
     "(v.2.0)"),
]

CSOSN_ICMSSN102 = [
    ("102", "102- Tributada pelo Simples Nacional sem permissão de crédito."),
    ("103", "103 – Isenção do ICMS no Simples Nacional para faixa de receita "
     "bruta."),
    ("300", "300 – Imune."),
    ("400", "400 – Não tributda pelo Simples Nacional (v.2.0) (v.2.0)"),
]

CSOSN_ICMSSN201 = [
    ("201", "201- Tributada pelo Simples Nacional com permissão de crédito e "
     "com cobrança do ICMS por Substituição Tributária (v.2.0)"),
]

CSOSN_ICMSSN202 = [
    ("202", "202- Tributada pelo Simples Nacional sem permissão de crédito e "
     "com cobrança do ICMS por Substituição Tributária"),
    ("203", "203- Isenção do ICMS nos Simples Nacional para faixa de receita "
     "bruta e com cobrança do ICMS por Substituição Tributária "
     "(v.2.0)"),
]

# 500 – ICMS cobrado anterirmente por substituição tributária
# (substituído) ou por antecipação
# (v.2.0)
CSOSN_ICMSSN500 = [
    ("500", "500"),
]

# Tributação pelo ICMS 900 - Outros(v2.0)
CSOSN_ICMSSN900 = [
    ("900", "900"),
]

# Tributção pelo ICMS
CST_ICMS00 = [
    ("00", "00 - Tributada integralmente"),
]

# Tributção pelo ICMS
CST_ICMS20 = [
    ("20", "20 - Com redução de base de cálculo"),
]

# Tributção pelo ICMS
CST_ICMS30 = [
    ("30", "30 - Isenta ou não tributada e com cobrança do ICMS por "
     "substituição tributária"),
]

# Tributação pelo ICMS
# 40 - Isenta
# 41 - Não tributada
# 50 - Suspensão
# 51 - Diferimento
CST_ICMS40 = [
    ("40", "40"),
    ("41", "41"),
    ("50", "50"),
]

# Tributção pelo ICMS
# 20 - Com redução de base de cálculo
CST_ICMS51 = [
    ("51", "51"),
]

# Tributação pelo ICMS
CST_ICMS60 = [
    ("60", "60 - ICMS cobrado anteriormente por substituição tributária"),
]

# Tributção pelo ICMS
CST_ICMS70 = [
    ("70", "70 - Com redução de base de cálculo e cobrança do ICMS por "
     "substituição tributária"),
]

# Tributção pelo ICMS
CST_ICMS90 = [
    ("90", "90 - Outras"),
]

# Tributação pelo ICMS
CST_ICMSPART = [
    ("10", "10 - Tributada e com cobrança do ICMS por substituição "
     "tributária"),
    ("90", "90 – Outros."),
]

# Tributção pelo ICMS
CST_ICMSST = [
    ("41", "41-Não Tributado."),
    ("60", "60-Cobrado anteriormente por substituição tributária."),
]

# Código de Situação Tributária do PIS.
CST_PISALIQ = [
    ("01", "01 – Operação Tributável - Base de Cálculo = Valor da Operação "
     "Alíquota Normal (Cumulativo/Não Cumulativo)"),
    ("02", "02 - Operação Tributável - Base de Calculo = Valor da Operação "
     "(Alíquota Diferenciada)"),
]

# Código de Situação Tributária do PIS.
CST_PISQTDE = [
    ("03", "03 - Operação Tributável - Base de Calculo = Quantidade Vendida "
     "x Alíquota por Unidade de Produto"),
]

# Código de Situação Tributária do PIS.
CST_PISNT = [
    ("04", "04 - Operação Tributável - Tributação Monofásica - (Alíquota "
     "Zero)"),
    ("05", "05 - Operação Tributável (ST)"),
    ("06", "06 - Operação Tributável - Alíquota Zero"),
    ("07", "07 - Operação Isenta da contribuição"),
    ("08", "08 - Operação Sem Incidência da contribuição"),
    ("09", "09 - Operação com suspensão da contribuição"),
]

# Código de Situação Tributária do PIS.
# 99 - Outras Operações.
CST_PISOUTR = [
    ("49", "49"),
    ("50", "50"),
    ("51", "51"),
    ("52", "52"),
    ("53", "53"),
    ("54", "54"),
    ("55", "55"),
    ("56", "56"),
    ("60", "60"),
    ("61", "61"),
    ("62", "62"),
    ("63", "63"),
    ("64", "64"),
    ("65", "65"),
    ("66", "66"),
    ("67", "67"),
    ("70", "70"),
    ("71", "71"),
    ("72", "72"),
    ("73", "73"),
    ("74", "74"),
    ("75", "75"),
    ("98", "98"),
    ("99", "99"),
]

# Código de Situação Tributária do COFINS.
CST_COFINSALIQ = [
    ("01", "01 – Operação Tributável - Base de Cálculo = Valor da Operação "
     "Alíquota Normal (Cumulativo/Não Cumulativo)"),
    ("02", "02 - Operação Tributável - Base de Calculo = Valor da Operação "
     "(Alíquota Diferenciada)"),
]

# Código de Situação Tributária do COFINS.
CST_COFINSQTDE = [
    ("03", "03 - Operação Tributável - Base de Calculo = Quantidade Vendida "
     "x Alíquota por Unidade de Produto"),
]

# Código de Situação Tributária do COFINS:
CST_COFINSNT = [
    ("04", "04 - Operação Tributável - Tributação Monofásica - (Alíquota "
     "Zero)"),
    ("05", "05 - Operação Tributável (ST)"),
    ("06", "06 - Operação Tributável - Alíquota Zero"),
    ("07", "07 - Operação Isenta da contribuição"),
    ("08", "08 - Operação Sem Incidência da contribuição"),
    ("09", "09 - Operação com suspensão da contribuição"),
]

# Código de Situação Tributária do COFINS:
CST_COFINSOUTR = [
    ("49", "49 - Outras Operações de Saída"),
    ("50", "50 - Operação com Direito a Crédito - Vinculada Exclusivamente a "
     "Receita Tributada no Mercado Interno"),
    ("51", "51 - Operação com Direito a Crédito – Vinculada Exclusivamente a "
     "Receita Não Tributada no Mercado Interno"),
    ("52", "52 - Operação com Direito a Crédito - Vinculada Exclusivamente a "
     "Receita de Exportação"),
    ("53", "53 - Operação com Direito a Crédito - Vinculada a Receitas "
     "Tributadas e Não-Tributadas no Mercado Interno"),
    ("54", "54 - Operação com Direito a Crédito - Vinculada a Receitas "
     "Tributadas no Mercado Interno e de Exportação"),
    ("55", "55 - Operação com Direito a Crédito - Vinculada a Receitas Não- "
     "Tributadas no Mercado Interno e de Exportação"),
    ("56", "56 - Operação com Direito a Crédito - Vinculada a Receitas "
     "Tributadas e Não-Tributadas no Mercado Interno, e de "
     "Exportação"),
    ("60", "60 - Crédito Presumido - Operação de Aquisição Vinculada "
     "Exclusivamente a Receita Tributada no Mercado Interno"),
    ("61", "61 - Crédito Presumido - Operação de Aquisição Vinculada "
     "Exclusivamente a Receita Não-Tributada no Mercado Interno"),
    ("62", "62 - Crédito Presumido - Operação de Aquisição Vinculada "
     "Exclusivamente a Receita de Exportação"),
    ("63", "63 - Crédito Presumido - Operação de Aquisição Vinculada a "
     "Receitas Tributadas e Não-Tributadas no Mercado Interno"),
    ("64", "64 - Crédito Presumido - Operação de Aquisição Vinculada a "
     "Receitas Tributadas no Mercado Interno e de Exportação"),
    ("65", "65 - Crédito Presumido - Operação de Aquisição Vinculada a "
     "Receitas Não-Tributadas no Mercado Interno e de Exportação"),
    ("66", "66 - Crédito Presumido - Operação de Aquisição Vinculada a "
     "Receitas Tributadas e Não-Tributadas no Mercado Interno, e "
     "de Exportação"),
    ("67", "67 - Crédito Presumido - Outras Operações"),
    ("70", "70 - Operação de Aquisição sem Direito a Crédito"),
    ("71", "71 - Operação de Aquisição com Isenção"),
    ("72", "72 - Operação de Aquisição com Suspensão"),
    ("73", "73 - Operação de Aquisição a Alíquota Zero"),
    ("74", "74 - Operação de Aquisição sem Incidência da Contribuição"),
    ("75", "75 - Operação de Aquisição por Substituição Tributária"),
    ("98", "98 - Outras Operações de Entrada"),
    ("99", "99 - Outras Operações."),
]

CST_ICMS10 = [
    ("10", "10 - Tributada e com cobrança do ICMS por substituição "
     "tributária"),
]

# Código da Situação Tributária do IPI:
CST_IPITRIB = [
    ("00", "00-Entrada com recuperação de crédito"),
    ("49", "49 - Outras entradas"),
    ("50", "50-Saída tributada"),
    ("99", "99-Outras saídas"),
]

# Código da Situação Tributária do IPI:
CST_IPINT = [
    ("01", "01-Entrada tributada com alíquota zero"),
    ("02", "02-Entrada isenta"),
    ("03", "03-Entrada não-tributada"),
    ("04", "04-Entrada imune"),
    ("05", "05-Entrada com suspensão"),
    ("51", "51-Saída tributada com alíquota zero"),
    ("52", "52-Saída isenta"),
    ("53", "53-Saída não-tributada"),
    ("54", "54-Saída imune"),
    ("55", "55-Saída com suspensão"),
]

# Tipo Ambiente
TAMB = [
    ("1", "1"),
    ("2", "2"),
]

# Tipo Código da Lista de Serviços LC 116/2003
TCLISTSERV_ISSQN = [
    ("01.01", "01.01"),
    ("01.02", "01.02"),
    ("01.03", "01.03"),
    ("01.04", "01.04"),
    ("01.05", "01.05"),
    ("01.06", "01.06"),
    ("01.07", "01.07"),
    ("01.08", "01.08"),
    ("01.09", "01.09"),
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
    ("06.06", "06.06"),
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
    ("14.14", "14.14"),
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
    ("16.02", "16.02"),
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
    ("17.25", "17.25"),
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
    ("25.05", "25.05"),
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

# Tipo Código da UF da tabela do IBGE
TCODUFIBGE = [
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

# Tipo Finalidade da NF-e (1=Normal; 2=Complementar; 3=Ajuste;
# 4=Devolução/Retorno)
TFINNFE_IDE = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
]

# Tipo Modelo Documento Fiscal
TMOD_IDE = [
    ("55", "55"),
    ("65", "65"),
]

# Tipo processo de emissão da NF-e
TPROCEMI_IDE = [
    ("0", "0"),
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
]

# Tipo Sigla da UF
TUF = [
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

# Tipo Sigla da UF de emissor // acrescentado em 24/10/08
TUFEMI = [
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

# Tipo Origem da mercadoria CST ICMS origem da mercadoria
TORIG = [
    ("0", "0-Nacional exceto as indicadas nos códigos 3, 4, 5 e 8"),
    ("1", "1-Estrangeira - Importação direta"),
    ("2", "2-Estrangeira - Adquirida no mercado interno"),
    ("3", "3-Nacional, conteudo superior 40% e inferior ou igual a 70%"),
    ("4", "4-Nacional, processos produtivos básicos"),
    ("5", "5-Nacional, conteudo inferior 40%"),
    ("6", "6-Estrangeira - Importação direta, com similar nacional, lista "
     "CAMEX"),
    ("7", "7-Estrangeira - mercado interno, sem simular,lista CAMEX"),
    ("8", "8-Nacional, Conteúdo de Importação superior a 70%."),
]

# Informa-se o veículo tem VIN (chassi) remarcado.
VIN_VEICPROD = [
    ("R", "R-Remarcado"),
    ("N", "N-NormalVIN"),
]

# Código do país
CPAIS_TENDEREMI = [
    ("1058", "1058"),
]

# Código do regime especial de tributação
CREGTRIB_ISSQNTOT = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
    ("6", "6"),
]

# Condição do veículo (1 - acabado; 2 - inacabado; 3 - semi-acabado)
CONDVEIC_VEICPROD = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
]

# Identificador de Local de destino da operação
# (1-Interna;2-Interestadual;3-Exterior)
IDDEST_IDE = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
]

INDESCALA_PROD = [
    ("S", "S"),
    ("N", "N"),
]

# Indica operação com consumidor final (0-Não;1-Consumidor Final)
INDFINAL_IDE = [
    ("0", "0"),
    ("1", "1"),
]

# Indicador da IE do destinatário:
INDIEDEST_DEST = [
    ("1", "1 – Contribuinte ICMSpagamento à vista"),
    ("2", "2 – Contribuinte isento de inscrição"),
    ("9", "9 – Não Contribuinte"),
]

# Exibilidade do ISS
INDISS_ISSQN = [
    ("1", "1-Exigível"),
    ("2", "2-Não incidente"),
    ("3", "3-Isenção"),
    ("4", "4-Exportação"),
    ("5", "5-Imunidade"),
    ("6", "6-Exig.Susp. Judicial"),
    ("7", "7-Exig.Susp. ADM"),
]

# Indicador de Incentivo Fiscal. 1=Sim; 2=Não
INDINCENTIVO_ISSQN = [
    ("1", "1"),
    ("2", "2"),
]

# Indicador da Forma de Pagamento
# 0-Pagamento à Vista
# 1-Pagamento à Prazo
INDPAG_DETPAG = [
    ("0", "0"),
    ("1", "1"),
]

# Indicador de presença do comprador no estabelecimento comercial no
# momento da oepração
# (0-Não se aplica (ex.
# Nota Fiscal complementar ou de ajuste
# 1-Operação presencial
# 2-Não presencial, internet
# 3-Não presencial, teleatendimento
# 4-NFC-e entrega em domicílio
# 5-Operação presencial, fora do estabelecimento
# 9-Não presencial, outros)
INDPRES_IDE = [
    ("0", "0"),
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
    ("9", "9"),
]

# Origem do processo, informar com:
INDPROC_PROCREF = [
    ("0", "0 - SEFAZ"),
    ("1", "1 - Justiça Federal"),
    ("2", "2 - Justiça Estadual"),
    ("3", "3 - Secex/RFB"),
    ("9", "9 - Outros"),
]

# Indicador de processamento síncrono. 0=NÃO; 1=SIM=Síncrono
INDSINC_TENVINFE = [
    ("0", "0"),
    ("1", "1"),
]

# Este campo deverá ser preenchido com:
INDTOT_PROD = [
    ("0", "0 – o valor do item (vProd) não compõe o valor total da NF-e "
     "(vProd)"),
    ("1", "1 – o valor do item (vProd) compõe o valor total da NF-e (vProd)"),
]

# Modalidade de determinação da BC do ICMS ST:
MODBCST_ICMS10 = [
    ("0", "0 – Preço tabelado ou máximo sugerido"),
    ("1", "1 - Lista Negativa (valor)"),
    ("2", "2 - Lista Positiva (valor)"),
    ("3", "3 - Lista Neutra (valor)"),
    ("4", "4 - Margem Valor Agregado (%)"),
    ("5", "5 - Pauta (valor)"),
    ("6", "6-Valor da Operação"),
]

# Modalidade de determinação da BC do ICMS ST:
MODBCST_ICMS30 = [
    ("0", "0 – Preço tabelado ou máximo sugerido"),
    ("1", "1 - Lista Negativa (valor)"),
    ("2", "2 - Lista Positiva (valor)"),
    ("3", "3 - Lista Neutra (valor)"),
    ("4", "4 - Margem Valor Agregado (%)"),
    ("5", "5 - Pauta (valor)."),
    ("6", "6 - Valor da Operação"),
]

# Modalidade de determinação da BC do ICMS ST:
MODBCST_ICMS70 = [
    ("0", "0 – Preço tabelado ou máximo sugerido"),
    ("1", "1 - Lista Negativa (valor)"),
    ("2", "2 - Lista Positiva (valor)"),
    ("3", "3 - Lista Neutra (valor)"),
    ("4", "4 - Margem Valor Agregado (%)"),
    ("5", "5 - Pauta (valor)."),
    ("6", "6 - Valor da Operação"),
]

# Modalidade de determinação da BC do ICMS ST:
MODBCST_ICMS90 = [
    ("0", "0 – Preço tabelado ou máximo sugerido"),
    ("1", "1 - Lista Negativa (valor)"),
    ("2", "2 - Lista Positiva (valor)"),
    ("3", "3 - Lista Neutra (valor)"),
    ("4", "4 - Margem Valor Agregado (%)"),
    ("5", "5 - Pauta (valor)"),
    ("6", "6 - Valor da Operação."),
]

# Modalidade de determinação da BC do ICMS ST:
MODBCST_ICMSPART = [
    ("0", "0 – Preço tabelado ou máximo sugerido"),
    ("1", "1 - Lista Negativa (valor)"),
    ("2", "2 - Lista Positiva (valor)"),
    ("3", "3 - Lista Neutra (valor)"),
    ("4", "4 - Margem Valor Agregado (%)"),
    ("5", "5 - Pauta (valor)."),
    ("6", "6 - Valor da Operação"),
]

# Modalidade de determinação da BC do ICMS ST:
MODBCST_ICMSSN201 = [
    ("0", "0 – Preço tabelado ou máximo sugerido"),
    ("1", "1 - Lista Negativa (valor)"),
    ("2", "2 - Lista Positiva (valor)"),
    ("3", "3 - Lista Neutra (valor)"),
    ("4", "4 - Margem Valor Agregado (%)"),
    ("5", "5 - Pauta (valor). (v2.0)"),
    ("6", "6 - Valor da Operação"),
]

# Modalidade de determinação da BC do ICMS ST:
MODBCST_ICMSSN202 = [
    ("0", "0 – Preço tabelado ou máximo sugerido"),
    ("1", "1 - Lista Negativa (valor)"),
    ("2", "2 - Lista Positiva (valor)"),
    ("3", "3 - Lista Neutra (valor)"),
    ("4", "4 - Margem Valor Agregado (%)"),
    ("5", "5 - Pauta (valor). (v2.0)"),
    ("6", "6 - Valor da Operação"),
]

# Modalidade de determinação da BC do ICMS ST:
MODBCST_ICMSSN900 = [
    ("0", "0 – Preço tabelado ou máximo sugerido"),
    ("1", "1 - Lista Negativa (valor)"),
    ("2", "2 - Lista Positiva (valor)"),
    ("3", "3 - Lista Neutra (valor)"),
    ("4", "4 - Margem Valor Agregado (%)"),
    ("5", "5 - Pauta (valor)."),
    ("6", "6 - Valor da Operação"),
]

# Modalidade de determinação da BC do ICMS:
MODBC_ICMS00 = [
    ("0", "0 - Margem Valor Agregado (%)"),
    ("1", "1 - Pauta (valor)"),
    ("2", "2 - Preço Tabelado Máximo (valor)"),
    ("3", "3 - Valor da Operação."),
]

# Modalidade de determinação da BC do ICMS:
MODBC_ICMS20 = [
    ("0", "0 - Margem Valor Agregado (%)"),
    ("1", "1 - Pauta (valor)"),
    ("2", "2 - Preço Tabelado Máximo (valor)"),
    ("3", "3 - Valor da Operação."),
]

# Modalidade de determinação da BC do ICMS:
MODBC_ICMS51 = [
    ("0", "0 - Margem Valor Agregado (%)"),
    ("1", "1 - Pauta (valor)"),
    ("2", "2 - Preço Tabelado Máximo (valor)"),
    ("3", "3 - Valor da Operação."),
]

# Modalidade de determinação da BC do ICMS:
MODBC_ICMS70 = [
    ("0", "0 - Margem Valor Agregado (%)"),
    ("1", "1 - Pauta (valor)"),
    ("2", "2 - Preço Tabelado Máximo (valor)"),
    ("3", "3 - Valor da Operação."),
]

# Modalidade de determinação da BC do ICMS:
MODBC_ICMS90 = [
    ("0", "0 - Margem Valor Agregado (%)"),
    ("1", "1 - Pauta (valor)"),
    ("2", "2 - Preço Tabelado Máximo (valor)"),
    ("3", "3 - Valor da Operação."),
]

# Modalidade de determinação da BC do ICMS:
MODBC_ICMSPART = [
    ("0", "0 - Margem Valor Agregado (%)"),
    ("1", "1 - Pauta (valor)"),
    ("2", "2 - Preço Tabelado Máximo (valor)"),
    ("3", "3 - Valor da Operação."),
]

# Modalidade de determinação da BC do ICMS:
MODBC_ICMSSN900 = [
    ("0", "0 - Margem Valor Agregado (%)"),
    ("1", "1 - Pauta (valor)"),
    ("2", "2 - Preço Tabelado Máximo (valor)"),
    ("3", "3 - Valor da Operação."),
]

# Modalidade de determinação da BC do ICMS:
MODBC_ICMS10 = [
    ("0", "0 - Margem Valor Agregado (%)"),
    ("1", "1 - Pauta (valor)"),
    ("2", "2 - Preço Tabelado Máximo (valor)"),
    ("3", "3 - Valor da Operação."),
]

# Modalidade do frete
MODFRETE_TRANSP = [
    ("0", "0- Contratação do Frete por conta do Remetente (CIF)"),
    ("1", "1- Contratação do Frete por conta do destinatário/remetente (FOB)"),
    ("2", "2- Contratação do Frete por conta de terceiros"),
    ("3", "3- Transporte próprio por conta do remetente"),
    ("4", "4- Transporte próprio por conta do destinatário"),
    ("9", "9- Sem Ocorrência de transporte."),
]

# Código do modelo do Documento Fiscal. Utilizar 01 para NF modelo 1/1A
# e 02 para NF modelo 02
MOD_REFNF = [
    ("01", "01"),
    ("02", "02"),
]

# Código do modelo do Documento Fiscal - utilizar 04 para NF de
# produtor ou 01 para NF Avulsa
MOD_REFNFP = [
    ("01", "01"),
    ("04", "04"),
]

# Código do modelo do Documento Fiscal
# Preencher com "2B", quando se tratar de Cupom Fiscal emitido por máquina
# registradora (não ECF), com "2C", quando se tratar de Cupom Fiscal PDV,
# ou "2D", quando se tratar de Cupom Fiscal (emitido por ECF)
MOD_REFECF = [
    ("2B", "2B"),
    ("2C", "2C"),
    ("2D", "2D"),
]

# Motivo da desoneração do ICMS
MOTDESICMS_ICMS20 = [
    ("3", "3-Uso na agropecuária"),
    ("9", "9-Outros"),
    ("12", "12-Fomento agropecuário"),
]

# Motivo da desoneração do ICMS
MOTDESICMS_ICMS30 = [
    ("6", "6-Utilitários Motocicleta AÁrea Livre"),
    ("7", "7-SUFRAMA"),
    ("9", "9-Outros"),
]

# Este campo será preenchido quando o campo anterior estiver
# preenchido.
# Informar o motivo da desoneração:
MOTDESICMS_ICMS40 = [
    ("1", "1 – Táxi"),
    ("3", "3 – Produtor Agropecuário"),
    ("4", "4 – Frotista/Locadora"),
    ("5", "5 – Diplomático/Consular"),
    ("6", "6 – Utilitários e Motocicletas da Amazônia Ocidental e Áreas de "
     "Livre Comércio (Resolução 714/88 e 790/94 – CONTRAN e suas "
     "alterações)"),
    ("7", "7 – SUFRAMA"),
    ("8", "8 - Venda a órgão Público"),
    ("9", "9 – Outros"),
    ("10", "10- Deficiente Condutor"),
    ("11", "11- Deficiente não condutor"),
    ("16", "16 - Olimpíadas Rio 2016"),
    ("90", "90 - Solicitado pelo Fisco"),
]

# Motivo da desoneração do ICMS
MOTDESICMS_ICMS70 = [
    ("3", "3-Uso na agropecuária"),
    ("9", "9-Outros"),
    ("12", "12-Fomento agropecuário"),
]

# Motivo da desoneração do ICMS
MOTDESICMS_ICMS90 = [
    ("3", "3-Uso na agropecuária"),
    ("9", "9-Outros"),
    ("12", "12-Fomento agropecuário"),
]

# Alíquota interestadual das UF envolvidas
# - 4% alíquota interestadual para produtos importados
# - 7% para os Estados de origem do Sul e Sudeste (exceto ES), destinado
# para os Estados do Norte e Nordeste ou ES
# - 12% para os demais casos.
PICMSINTER_ICMSUFDEST = [
    ("4.00", "4.00"),
    ("7.00", "7.00"),
    ("12.00", "12.00"),
]

# Bandeira da operadora de cartão de crédito/débito
TBAND_CARD = [
    ("01", "01–Visa"),
    ("02", "02–Mastercard"),
    ("03", "03–American Express"),
    ("04", "04–Sorocred"),
    ("05", "05-Diners Club"),
    ("06", "06-Elo"),
    ("07", "07-Hipercard"),
    ("08", "08-Aura"),
    ("09", "09-Cabal"),
    ("99", "99–Outros"),
]

# Forma de Pagamento
TPAG_DETPAG = [
    ("01", "01-Dinheiro"),
    ("02", "02-Cheque"),
    ("03", "03-Cartão de Crédito"),
    ("04", "04-Cartão de Débito"),
    ("05", "05-Crédito Loja"),
    ("10", "10-Vale Alimentação"),
    ("11", "11-Vale Refeição"),
    ("12", "12-Vale Presente"),
    ("13", "13-Vale Combustível"),
    ("14", "14 - Duplicata Mercantil"),
    ("15", "15 - Boleto Bancario"),
    ("90", "90 - Sem Pagamento"),
    ("99", "99 - Outros"),
]

# Indicador do tipo de arma de fogo (0 - Uso permitido; 1 - Uso
# restrito)
TPARMA_ARMA = [
    ("0", "0"),
    ("1", "1"),
]

# Forma de emissão da NF-e
TPEMIS_IDE = [
    ("1", "1 - Normal"),
    ("2", "2 - Contingência FS"),
    ("3", "3 - Contingência SCAN"),
    ("4", "4 - Contingência DPEC"),
    ("5", "5 - Contingência FSDA"),
    ("6", "6 - Contingência SVC - AN"),
    ("7", "7 - Contingência SVC - RS"),
    ("9", "9 - Contingência off-line NFC-e"),
]

# Formato de impressão do DANFE (0-sem DANFE;1-DANFe Retrato; 2-DANFe
# Paisagem;3-DANFe Simplificado;
# 4-DANFe NFC-e;5-DANFe NFC-e em mensagem eletrônica)
TPIMP_IDE = [
    ("0", "0"),
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
]

# Tipo de Integração do processo de pagamento com o sistema de
# automação da empresa/
TPINTEGRA_CARD = [
    ("1", "1=Pagamento integrado com o sistema de automação da empresa Ex. "
     "equipamento TEF , Comercio Eletronico"),
    ("2", "2=Pagamento não integrado com o sistema de automação da empresa "
     "Ex: equipamento POS"),
]

# Forma de Importação quanto a intermediação
# 1-por conta propria;2-por conta e ordem;3-encomenda
TPINTERMEDIO_DI = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
]

# Tipo do Documento Fiscal (0 - entrada; 1 - saída)
TPNF_IDE = [
    ("0", "0"),
    ("1", "1"),
]

# Tipo da Operação (1 - Venda concessionária; 2 - Faturamento direto; 3
# - Venda direta; 0 - Outros)
TPOP_VEICPROD = [
    ("0", "0"),
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
]

# Restrição
TPREST_VEICPROD = [
    ("0", "0 - Não há"),
    ("1", "1 - Alienação Fiduciária"),
    ("2", "2 - Arrendamento Mercantil"),
    ("3", "3 - Reserva de Domínio"),
    ("4", "4 - Penhor de Veículos"),
    ("9", "9 - outras."),
]

# Via de transporte internacional informada na DI
# 1-Maritima;2-Fluvial;3-Lacustre;4-Aerea;5-Postal;6-Ferroviaria;7-Rodoviar
# ia;8-Conduto;9-Meios Proprios;10-Entrada/Saida Ficta.
TPVIATRANSP_DI = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
    ("6", "6"),
    ("7", "7"),
    ("8", "8"),
    ("9", "9"),
    ("10", "10"),
    ("11", "11"),
    ("12", "12"),
]

# Nome do país
XPAIS_TENDEREMI = [
    ("Brasil", "Brasil"),
    ("BRASIL", "BRASIL"),
]


class CIDE(models.AbstractModel):
    "CIDE Combustíveis"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.cide'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'CIDEType'
    _concrete_rec_name = 'nfe40_qBCProd'

    nfe40_qBCProd = fields.Monetary(currency_field="brl_currency_id",
        digits=4, string="BC do CIDE", xsd=True, xsd_required=True,
        help="BC do CIDE ( Quantidade comercializada)")
    nfe40_vAliqProd = fields.Monetary(currency_field="brl_currency_id",
        digits=4, string="Alíquota do CIDE (em reais)",
        xsd=True,
        xsd_required=True,
        help="Alíquota do CIDE (em reais)")
    nfe40_vCIDE = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do CIDE", xsd=True, xsd_required=True)


class COFINSAliq(models.AbstractModel):
    """Código de Situação Tributária do COFINS.
    01 – Operação Tributável - Base de Cálculo = Valor da Operação Alíquota
    Normal (Cumulativo/Não Cumulativo);
    02 - Operação Tributável - Base de Calculo = Valor da Operação (Alíquota
    Diferenciada);"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.cofinsaliq'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'COFINSAliqType'
    _concrete_rec_name = 'nfe40_CST'

    nfe40_CST = fields.Selection(
        CST_COFINSALIQ,
        string="Código de Situação Tributária do COFINS",
        xsd=True,
        xsd_required=True,
        help="Código de Situação Tributária do COFINS."
        "\n01 – Operação Tributável - Base de Cálculo = Valor da Operação"
        "\nAlíquota Normal (Cumulativo/Não Cumulativo);"
        "\n02 - Operação Tributável - Base de Calculo = Valor da Operação"
        "\n(Alíquota Diferenciada);")
    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do COFINS", xsd=True, xsd_required=True)
    nfe40_pCOFINS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do COFINS (em percentual)",
        xsd=True,
        xsd_required=True)
    nfe40_vCOFINS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do COFINS", xsd=True, xsd_required=True)


class COFINSNT(models.AbstractModel):
    """Código de Situação Tributária do COFINS:
    04 - Operação Tributável - Tributação Monofásica - (Alíquota Zero);
    06 - Operação Tributável - Alíquota Zero;
    07 - Operação Isenta da contribuição;
    08 - Operação Sem Incidência da contribuição;
    09 - Operação com suspensão da contribuição;"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.cofinsnt'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'COFINSNTType'
    _concrete_rec_name = 'nfe40_CST'

    nfe40_CST = fields.Selection(
        CST_COFINSNT,
        string="Código de Situação Tributária do COFINS",
        xsd=True,
        xsd_required=True,
        help="Código de Situação Tributária do COFINS:"
        "\n04 - Operação Tributável - Tributação Monofásica - (Alíquota Zero);"
        "\n05 - Operação Tributável (ST);"
        "\n06 - Operação Tributável - Alíquota Zero;"
        "\n07 - Operação Isenta da contribuição;"
        "\n08 - Operação Sem Incidência da contribuição;"
        "\n09 - Operação com suspensão da contribuição;")


class COFINSOutr(models.AbstractModel):
    """Código de Situação Tributária do COFINS:
    49 - Outras Operações de Saída
    50 - Operação com Direito a Crédito - Vinculada Exclusivamente a Receita
    Tributada no Mercado Interno
    51 - Operação com Direito a Crédito – Vinculada Exclusivamente a Receita
    Não Tributada no Mercado Interno
    52 - Operação com Direito a Crédito - Vinculada Exclusivamente a Receita de
    Exportação
    53 - Operação com Direito a Crédito - Vinculada a Receitas Tributadas e
    Não-Tributadas no Mercado Interno
    54 - Operação com Direito a Crédito - Vinculada a Receitas Tributadas no
    Mercado Interno e de Exportação
    55 - Operação com Direito a Crédito - Vinculada a Receitas Não-Tributadas
    no Mercado Interno e de Exportação
    56 - Operação com Direito a Crédito - Vinculada a Receitas Tributadas e
    Não-Tributadas no Mercado Interno, e de Exportação
    60 - Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a
    Receita Tributada no Mercado Interno
    61 - Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a
    Receita Não-Tributada no Mercado Interno
    62 - Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a
    Receita de Exportação
    63 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas
    Tributadas e Não-Tributadas no Mercado Interno
    64 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas
    Tributadas no Mercado Interno e de Exportação
    65 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Não-
    Tributadas no Mercado Interno e de Exportação
    66 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas
    Tributadas e Não-Tributadas no Mercado Interno, e de Exportação
    67 - Crédito Presumido - Outras Operações
    70 - Operação de Aquisição sem Direito a Crédito
    71 - Operação de Aquisição com Isenção
    72 - Operação de Aquisição com Suspensão
    73 - Operação de Aquisição a Alíquota Zero
    74 - Operação de Aquisição sem Incidência da Contribuição
    75 - Operação de Aquisição por Substituição Tributária
    98 - Outras Operações de Entrada
    99 - Outras Operações."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.cofinsoutr'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'COFINSOutrType'
    _concrete_rec_name = 'nfe40_CST'

    nfe40_choice16 = fields.Selection([
        ('nfe40_vBC', 'vBC'),
        ('nfe40_pCOFINS', 'pCOFINS'),
        ('nfe40_qBCProd', 'qBCProd'),
        ('nfe40_vAliqProd', 'vAliqProd')],
        "vBC/pCOFINS/qBCProd/vAliqProd")
    nfe40_CST = fields.Selection(
        CST_COFINSOUTR,
        string="Código de Situação Tributária do COFINS",
        xsd=True,
        xsd_required=True,
        help="Código de Situação Tributária do COFINS:"
        "\n49 - Outras Operações de Saída"
        "\n50 - Operação com Direito a Crédito - Vinculada Exclusivamente a"
        "\nReceita Tributada no Mercado Interno"
        "\n51 - Operação com Direito a Crédito – Vinculada Exclusivamente a"
        "\nReceita Não Tributada no Mercado Interno"
        "\n52 - Operação com Direito a Crédito - Vinculada Exclusivamente a"
        "\nReceita de Exportação"
        "\n53 - Operação com Direito a Crédito - Vinculada a Receitas"
        "\nTributadas e Não-Tributadas no Mercado Interno"
        "\n54 - Operação com Direito a Crédito - Vinculada a Receitas"
        "\nTributadas no Mercado Interno e de Exportação"
        "\n55 - Operação com Direito a Crédito - Vinculada a Receitas Não-"
        "\nTributadas no Mercado Interno e de Exportação"
        "\n56 - Operação com Direito a Crédito - Vinculada a Receitas"
        "\nTributadas e Não-Tributadas no Mercado Interno, e de"
        "\nExportação"
        "\n60 - Crédito Presumido - Operação de Aquisição Vinculada"
        "\nExclusivamente a Receita Tributada no Mercado Interno"
        "\n61 - Crédito Presumido - Operação de Aquisição Vinculada"
        "\nExclusivamente a Receita Não-Tributada no Mercado Interno"
        "\n62 - Crédito Presumido - Operação de Aquisição Vinculada"
        "\nExclusivamente a Receita de Exportação"
        "\n63 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas"
        "\nTributadas e Não-Tributadas no Mercado Interno"
        "\n64 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas"
        "\nTributadas no Mercado Interno e de Exportação"
        "\n65 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas"
        "\nNão-Tributadas no Mercado Interno e de Exportação"
        "\n66 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas"
        "\nTributadas e Não-Tributadas no Mercado Interno, e de"
        "\nExportação"
        "\n67 - Crédito Presumido - Outras Operações"
        "\n70 - Operação de Aquisição sem Direito a Crédito"
        "\n71 - Operação de Aquisição com Isenção"
        "\n72 - Operação de Aquisição com Suspensão"
        "\n73 - Operação de Aquisição a Alíquota Zero"
        "\n74 - Operação de Aquisição sem Incidência da Contribuição"
        "\n75 - Operação de Aquisição por Substituição Tributária"
        "\n98 - Outras Operações de Entrada"
        "\n99 - Outras Operações.")
    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, choice='16',
        string="Valor da BC do COFINS", xsd=True, xsd_required=True)
    nfe40_pCOFINS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, choice='16',
        string="Alíquota do COFINS (em percentual)",
        xsd=True,
        xsd_required=True)
    nfe40_qBCProd = fields.Monetary(currency_field="brl_currency_id",
        digits=4, choice='16',
        string="Quantidade Vendida (NT2011/004)",
        xsd=True,
        xsd_required=True)
    nfe40_vAliqProd = fields.Monetary(currency_field="brl_currency_id",
        digits=4, choice='16',
        string="Alíquota do COFINS",
        xsd=True,
        xsd_required=True,
        help="Alíquota do COFINS (em reais) (NT2011/004)")
    nfe40_vCOFINS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do COFINS", xsd=True, xsd_required=True)


class COFINSQtde(models.AbstractModel):
    """Código de Situação Tributária do COFINS.
    03 - Operação Tributável - Base de Calculo = Quantidade Vendida x Alíquota
    por Unidade de Produto;"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.cofinsqtde'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'COFINSQtdeType'
    _concrete_rec_name = 'nfe40_CST'

    nfe40_CST = fields.Selection(
        CST_COFINSQTDE,
        string="Código de Situação Tributária do COFINS",
        xsd=True,
        xsd_required=True,
        help="Código de Situação Tributária do COFINS."
        "\n03 - Operação Tributável - Base de Calculo = Quantidade Vendida x"
        "\nAlíquota por Unidade de Produto;")
    nfe40_qBCProd = fields.Monetary(currency_field="brl_currency_id",
        digits=4, string="Quantidade Vendida (NT2011/004)",
        xsd=True,
        xsd_required=True)
    nfe40_vAliqProd = fields.Monetary(currency_field="brl_currency_id",
        digits=4, string="Alíquota do COFINS",
        xsd=True,
        xsd_required=True,
        help="Alíquota do COFINS (em reais) (NT2011/004)")
    nfe40_vCOFINS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do COFINS", xsd=True, xsd_required=True)


class COFINSST(models.AbstractModel):
    """Dados do COFINS da
    Substituição Tributaria;"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.cofinsst'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'COFINSSTType'
    _concrete_rec_name = 'nfe40_vBC'

    nfe40_choice17 = fields.Selection([
        ('nfe40_vBC', 'vBC'),
        ('nfe40_pCOFINS', 'pCOFINS'),
        ('nfe40_qBCProd', 'qBCProd'),
        ('nfe40_vAliqProd', 'vAliqProd')],
        "vBC/pCOFINS/qBCProd/vAliqProd")
    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, choice='17',
        string="Valor da BC do COFINS ST",
        xsd=True,
        xsd_required=True)
    nfe40_pCOFINS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, choice='17',
        string="Alíquota do COFINS ST(em percentual)",
        xsd=True,
        xsd_required=True)
    nfe40_qBCProd = fields.Monetary(currency_field="brl_currency_id",
        digits=4, choice='17',
        string="Quantidade Vendida",
        xsd=True,
        xsd_required=True)
    nfe40_vAliqProd = fields.Monetary(currency_field="brl_currency_id",
        digits=4, choice='17',
        string="Alíquota do COFINS ST(em reais)",
        xsd=True,
        xsd_required=True)
    nfe40_vCOFINS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do COFINS ST",
        xsd=True,
        xsd_required=True)


class COFINS(models.AbstractModel):
    "Dados do COFINS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.cofins'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'COFINSType'
    _concrete_rec_name = 'nfe40_COFINSAliq'

    nfe40_choice15 = fields.Selection([
        ('nfe40_COFINSAliq', 'COFINSAliq'),
        ('nfe40_COFINSQtde', 'COFINSQtde'),
        ('nfe40_COFINSNT', 'COFINSNT'),
        ('nfe40_COFINSOutr', 'COFINSOutr')],
        "COFINSAliq/COFINSQtde/COFINSNT/COFINSOutr")
    nfe40_COFINSAliq = fields.Many2one(
        "nfe.40.cofinsaliq",
        choice='15',
        string="Código de Situação Tributária do COFINS",
        xsd=True,
        xsd_required=True,
        help="Código de Situação Tributária do COFINS."
        "\n01 – Operação Tributável - Base de Cálculo = Valor da Operação"
        "\nAlíquota Normal (Cumulativo/Não Cumulativo);"
        "\n02 - Operação Tributável - Base de Calculo = Valor da Operação"
        "\n(Alíquota Diferenciada);")
    nfe40_COFINSQtde = fields.Many2one(
        "nfe.40.cofinsqtde",
        choice='15',
        string="Código de Situação Tributária do COFINS",
        xsd=True,
        xsd_required=True,
        help="Código de Situação Tributária do COFINS."
        "\n03 - Operação Tributável - Base de Calculo = Quantidade Vendida x"
        "\nAlíquota por Unidade de Produto;")
    nfe40_COFINSNT = fields.Many2one(
        "nfe.40.cofinsnt",
        choice='15',
        string="Código de Situação Tributária do COFINS",
        xsd=True,
        xsd_required=True,
        help="Código de Situação Tributária do COFINS:"
        "\n04 - Operação Tributável - Tributação Monofásica - (Alíquota Zero);"
        "\n06 - Operação Tributável - Alíquota Zero;"
        "\n07 - Operação Isenta da contribuição;"
        "\n08 - Operação Sem Incidência da contribuição;"
        "\n09 - Operação com suspensão da contribuição;")
    nfe40_COFINSOutr = fields.Many2one(
        "nfe.40.cofinsoutr",
        choice='15',
        string="Código de Situação Tributária do COFINS",
        xsd=True,
        xsd_required=True,
        help="Código de Situação Tributária do COFINS:"
        "\n49 - Outras Operações de Saída"
        "\n50 - Operação com Direito a Crédito - Vinculada Exclusivamente a"
        "\nReceita Tributada no Mercado Interno"
        "\n51 - Operação com Direito a Crédito – Vinculada Exclusivamente a"
        "\nReceita Não Tributada no Mercado Interno"
        "\n52 - Operação com Direito a Crédito - Vinculada Exclusivamente a"
        "\nReceita de Exportação"
        "\n53 - Operação com Direito a Crédito - Vinculada a Receitas"
        "\nTributadas e Não-Tributadas no Mercado Interno"
        "\n54 - Operação com Direito a Crédito - Vinculada a Receitas"
        "\nTributadas no Mercado Interno e de Exportação"
        "\n55 - Operação com Direito a Crédito - Vinculada a Receitas Não-"
        "\nTributadas no Mercado Interno e de Exportação"
        "\n56 - Operação com Direito a Crédito - Vinculada a Receitas"
        "\nTributadas e Não-Tributadas no Mercado Interno, e de"
        "\nExportação"
        "\n60 - Crédito Presumido - Operação de Aquisição Vinculada"
        "\nExclusivamente a Receita Tributada no Mercado Interno"
        "\n61 - Crédito Presumido - Operação de Aquisição Vinculada"
        "\nExclusivamente a Receita Não-Tributada no Mercado Interno"
        "\n62 - Crédito Presumido - Operação de Aquisição Vinculada"
        "\nExclusivamente a Receita de Exportação"
        "\n63 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas"
        "\nTributadas e Não-Tributadas no Mercado Interno"
        "\n64 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas"
        "\nTributadas no Mercado Interno e de Exportação"
        "\n65 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas"
        "\nNão-Tributadas no Mercado Interno e de Exportação"
        "\n66 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas"
        "\nTributadas e Não-Tributadas no Mercado Interno, e de"
        "\nExportação"
        "\n67 - Crédito Presumido - Outras Operações"
        "\n70 - Operação de Aquisição sem Direito a Crédito"
        "\n71 - Operação de Aquisição com Isenção"
        "\n72 - Operação de Aquisição com Suspensão"
        "\n73 - Operação de Aquisição a Alíquota Zero"
        "\n74 - Operação de Aquisição sem Incidência da Contribuição"
        "\n75 - Operação de Aquisição por Substituição Tributária"
        "\n98 - Outras Operações de Entrada"
        "\n99 - Outras Operações.")


class DI(models.AbstractModel):
    """Delcaração de Importação
    (NT 2011/004)"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.di'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'DIType'
    _concrete_rec_name = 'nfe40_nDI'

    nfe40_DI_prod_id = fields.Many2one(
        "nfe.40.prod")
    nfe40_nDI = fields.Char(
        string="Numero do Documento de Importação DI/DSI/DA/DRI",
        xsd=True,
        xsd_required=True,
        help="Numero do Documento de Importação DI/DSI/DA/DRI-E"
        "\n(DI/DSI/DA/DRI-E) (NT2011/004)")
    nfe40_dDI = fields.Date(
        string="Data de registro da DI/DSI/DA",
        xsd=True,
        xsd_required=True,
        help="Data de registro da DI/DSI/DA (AAAA-MM-DD)")
    nfe40_xLocDesemb = fields.Char(
        string="Local do desembaraço aduaneiro",
        xsd=True,
        xsd_required=True)
    nfe40_UFDesemb = fields.Selection(
        TUFEMI,
        string="UF onde ocorreu o desembaraço aduaneiro",
        xsd=True,
        xsd_required=True)
    nfe40_dDesemb = fields.Date(
        string="Data do desembaraço aduaneiro",
        xsd=True,
        xsd_required=True,
        help="Data do desembaraço aduaneiro (AAAA-MM-DD)")
    nfe40_tpViaTransp = fields.Selection(
        TPVIATRANSP_DI,
        string="Via de transporte internacional informada na DI",
        xsd=True,
        xsd_required=True,
        help="Via de transporte internacional informada na DI"
        "\n1-Maritima;2-Fluvial;3-Lacustre;4-Aerea;5-Postal;6-Ferroviaria;7-Ro"
        "\ndoviaria;8-Conduto;9-Meios Proprios;10-Entrada/Saida Ficta.")
    nfe40_vAFRMM = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="vAFRMM",
        xsd=True,
        help="Valor Adicional ao frete para renovação de marinha mercante")
    nfe40_tpIntermedio = fields.Selection(
        TPINTERMEDIO_DI,
        string="Forma de Importação quanto a intermediação",
        xsd=True,
        xsd_required=True,
        help="Forma de Importação quanto a intermediação"
        "\n1-por conta propria;2-por conta e ordem;3-encomenda")
    nfe40_CNPJ = fields.Char(
        string="CNPJ do adquirente ou do encomendante",
        xsd=True)
    nfe40_UFTerceiro = fields.Selection(
        TUFEMI,
        string="Sigla da UF do adquirente ou do encomendante",
        xsd=True)
    nfe40_cExportador = fields.Char(
        string="Código do exportador",
        xsd=True,
        xsd_required=True,
        help="Código do exportador (usado nos sistemas internos de"
        "\ninformação do emitente da NF-e)")
    nfe40_adi = fields.One2many(
        "nfe.40.adi",
        "nfe40_adi_DI_id",
        string="Adições (NT 2011/004)", xsd=True, xsd_required=True
    )


class ICMS00(models.AbstractModel):
    """Tributação pelo ICMS
    00 - Tributada integralmente"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icms00'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMS00Type'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="origem da mercadoria: 0 - Nacional",
        xsd=True,
        xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CST = fields.Selection(
        CST_ICMS00,
        string="Tributção pelo ICMS", xsd=True, xsd_required=True,
        help="Tributção pelo ICMS"
        "\n00 - Tributada integralmente")
    nfe40_modBC = fields.Selection(
        MODBC_ICMS00,
        string="Modalidade de determinação da BC do ICMS",
        xsd=True,
        xsd_required=True,
        help="Modalidade de determinação da BC do ICMS:"
        "\n0 - Margem Valor Agregado (%);"
        "\n1 - Pauta (valor);"
        "\n2 - Preço Tabelado Máximo (valor);"
        "\n3 - Valor da Operação.")
    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS", xsd=True, xsd_required=True)
    nfe40_pICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS", xsd=True, xsd_required=True)
    nfe40_vICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS", xsd=True, xsd_required=True)
    nfe40_pFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Percentual de ICMS relativo ao Fundo de Combate à Pobreza",
        xsd=True,
        help="Percentual de ICMS relativo ao Fundo de Combate à Pobreza"
        "\n(FCP).")
    nfe40_vFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Valor do ICMS relativo ao Fundo de Combate à Pobreza",
        xsd=True,
        help="Valor do ICMS relativo ao Fundo de Combate à Pobreza (FCP).")


class ICMS10(models.AbstractModel):
    """Tributação pelo ICMS
    10 - Tributada e com cobrança do ICMS por substituição tributária"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icms10'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMS10Type'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="origem da mercadoria: 0 - Nacional",
        xsd=True,
        xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CST = fields.Selection(
        CST_ICMS10,
        string="10", xsd=True, xsd_required=True,
        help="10 - Tributada e com cobrança do ICMS por substituição"
        "\ntributária")
    nfe40_modBC = fields.Selection(
        MODBC_ICMS10,
        string="Modalidade de determinação da BC do ICMS",
        xsd=True,
        xsd_required=True,
        help="Modalidade de determinação da BC do ICMS:"
        "\n0 - Margem Valor Agregado (%);"
        "\n1 - Pauta (valor);"
        "\n2 - Preço Tabelado Máximo (valor);"
        "\n3 - Valor da Operação.")
    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS", xsd=True, xsd_required=True)
    nfe40_pICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS", xsd=True, xsd_required=True)
    nfe40_vICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS", xsd=True, xsd_required=True)
    nfe40_vBCFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da Base de cálculo do FCP.",
        xsd=True)
    nfe40_pFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Percentual de ICMS relativo ao Fundo de Combate à Pobreza",
        xsd=True,
        help="Percentual de ICMS relativo ao Fundo de Combate à Pobreza"
        "\n(FCP).")
    nfe40_vFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Valor do ICMS relativo ao Fundo de Combate à Pobreza",
        xsd=True,
        help="Valor do ICMS relativo ao Fundo de Combate à Pobreza (FCP).")
    nfe40_modBCST = fields.Selection(
        MODBCST_ICMS10,
        string="Modalidade de determinação da BC do ICMS ST",
        xsd=True,
        xsd_required=True,
        help="Modalidade de determinação da BC do ICMS ST:"
        "\n0 – Preço tabelado ou máximo sugerido;"
        "\n1 - Lista Negativa (valor);"
        "\n2 - Lista Positiva (valor);"
        "\n3 - Lista Neutra (valor);"
        "\n4 - Margem Valor Agregado (%);"
        "\n5 - Pauta (valor)"
        "\n6-Valor da Operação;")
    nfe40_pMVAST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual da Margem de Valor Adicionado ICMS ST",
        xsd=True)
    nfe40_pRedBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da BC ICMS ST",
        xsd=True)
    nfe40_vBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS ST",
        xsd=True,
        xsd_required=True)
    nfe40_pICMSST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS ST",
        xsd=True,
        xsd_required=True)
    nfe40_vICMSST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS ST", xsd=True, xsd_required=True)
    nfe40_vBCFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="vBCFCPST",
        xsd=True,
        help="Valor da Base de cálculo do FCP retido por substituicao"
        "\ntributaria.")
    nfe40_pFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Percentual de FCP retido por substituição tributária",
        xsd=True)
    nfe40_vFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do FCP retido por substituição tributária",
        xsd=True)


class ICMS20(models.AbstractModel):
    """Tributção pelo ICMS
    20 - Com redução de base de cálculoGrupo desoneração"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icms20'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMS20Type'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="origem da mercadoria: 0 - Nacional",
        xsd=True,
        xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CST = fields.Selection(
        CST_ICMS20,
        string="Tributção pelo ICMS", xsd=True, xsd_required=True,
        help="Tributção pelo ICMS"
        "\n20 - Com redução de base de cálculo")
    nfe40_modBC = fields.Selection(
        MODBC_ICMS20,
        string="Modalidade de determinação da BC do ICMS",
        xsd=True,
        xsd_required=True,
        help="Modalidade de determinação da BC do ICMS:"
        "\n0 - Margem Valor Agregado (%);"
        "\n1 - Pauta (valor);"
        "\n2 - Preço Tabelado Máximo (valor);"
        "\n3 - Valor da Operação.")
    nfe40_pRedBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da BC",
        xsd=True,
        xsd_required=True)
    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS", xsd=True, xsd_required=True)
    nfe40_pICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS", xsd=True, xsd_required=True)
    nfe40_vICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS", xsd=True, xsd_required=True)
    nfe40_vBCFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da Base de cálculo do FCP.",
        xsd=True)
    nfe40_pFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Percentual de ICMS relativo ao Fundo de Combate à Pobreza",
        xsd=True,
        help="Percentual de ICMS relativo ao Fundo de Combate à Pobreza"
        "\n(FCP).")
    nfe40_vFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Valor do ICMS relativo ao Fundo de Combate à Pobreza",
        xsd=True,
        help="Valor do ICMS relativo ao Fundo de Combate à Pobreza (FCP).")
    nfe40_vICMSDeson = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS de desoneração",
        xsd=True)
    nfe40_motDesICMS = fields.Selection(
        MOTDESICMS_ICMS20,
        string="Motivo da desoneração do ICMS:3",
        xsd=True,
        help="Motivo da desoneração do ICMS:3-Uso na"
        "\nagropecuária;9-Outros;12-Fomento agropecuário")


class ICMS30(models.AbstractModel):
    """Tributação pelo ICMS
    30 - Isenta ou não tributada e com cobrança do ICMS por substituição
    tributáriaGrupo desoneração"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icms30'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMS30Type'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="origem da mercadoria: 0 - Nacional",
        xsd=True,
        xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CST = fields.Selection(
        CST_ICMS30,
        string="Tributção pelo ICMS", xsd=True, xsd_required=True,
        help="Tributção pelo ICMS"
        "\n30 - Isenta ou não tributada e com cobrança do ICMS por"
        "\nsubstituição tributária")
    nfe40_modBCST = fields.Selection(
        MODBCST_ICMS30,
        string="Modalidade de determinação da BC do ICMS ST",
        xsd=True,
        xsd_required=True,
        help="Modalidade de determinação da BC do ICMS ST:"
        "\n0 – Preço tabelado ou máximo sugerido;"
        "\n1 - Lista Negativa (valor);"
        "\n2 - Lista Positiva (valor);"
        "\n3 - Lista Neutra (valor);"
        "\n4 - Margem Valor Agregado (%);"
        "\n5 - Pauta (valor)."
        "\n6 - Valor da Operação")
    nfe40_pMVAST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual da Margem de Valor Adicionado ICMS ST",
        xsd=True)
    nfe40_pRedBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da BC ICMS ST",
        xsd=True)
    nfe40_vBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS ST",
        xsd=True,
        xsd_required=True)
    nfe40_pICMSST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS ST",
        xsd=True,
        xsd_required=True)
    nfe40_vICMSST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS ST", xsd=True, xsd_required=True)
    nfe40_vBCFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da Base de cálculo do FCP.",
        xsd=True)
    nfe40_pFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Percentual de FCP retido por substituição tributária",
        xsd=True)
    nfe40_vFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do FCP retido por substituição tributária",
        xsd=True)
    nfe40_vICMSDeson = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS de desoneração",
        xsd=True)
    nfe40_motDesICMS = fields.Selection(
        MOTDESICMS_ICMS30,
        string="Motivo da desoneração do ICMS:6",
        xsd=True,
        help="Motivo da desoneração do ICMS:6-Utilitários Motocicleta AÁrea"
        "\nLivre;7-SUFRAMA;9-Outros")


class ICMS40(models.AbstractModel):
    """Tributação pelo ICMS
    40 - Isenta
    41 - Não tributada
    50 - Suspensão"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icms40'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMS40Type'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="origem da mercadoria: 0 - Nacional",
        xsd=True,
        xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CST = fields.Selection(
        CST_ICMS40,
        string="Tributação pelo ICMS", xsd=True, xsd_required=True,
        help="Tributação pelo ICMS"
        "\n40 - Isenta"
        "\n41 - Não tributada"
        "\n50 - Suspensão"
        "\n51 - Diferimento")
    nfe40_vICMSDeson = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="vICMSDeson",
        xsd=True,
        help="O valor do ICMS será informado apenas nas operações com"
        "\nveículos beneficiados com a desoneração condicional"
        "\ndo ICMS.")
    nfe40_motDesICMS = fields.Selection(
        MOTDESICMS_ICMS40,
        string="motDesICMS",
        xsd=True,
        help="Este campo será preenchido quando o campo anterior estiver"
        "\npreenchido."
        "\nInformar o motivo da desoneração:")


class ICMS51(models.AbstractModel):
    """Tributção pelo ICMS
    51 - Diferimento
    A exigência do preenchimento das informações do ICMS diferido fica à
    critério de cada UF."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icms51'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMS51Type'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="origem da mercadoria: 0 - Nacional",
        xsd=True,
        xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CST = fields.Selection(
        CST_ICMS51,
        string="Tributção pelo ICMS", xsd=True, xsd_required=True,
        help="Tributção pelo ICMS"
        "\n20 - Com redução de base de cálculo")
    nfe40_modBC = fields.Selection(
        MODBC_ICMS51,
        string="Modalidade de determinação da BC do ICMS",
        xsd=True,
        help="Modalidade de determinação da BC do ICMS:"
        "\n0 - Margem Valor Agregado (%);"
        "\n1 - Pauta (valor);"
        "\n2 - Preço Tabelado Máximo (valor);"
        "\n3 - Valor da Operação.")
    nfe40_pRedBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da BC",
        xsd=True)
    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS",
        xsd=True)
    nfe40_pICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do imposto",
        xsd=True)
    nfe40_vICMSOp = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS da Operação",
        xsd=True)
    nfe40_pDif = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual do diferemento",
        xsd=True)
    nfe40_vICMSDif = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS da diferido",
        xsd=True)
    nfe40_vICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS",
        xsd=True)
    nfe40_vBCFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da Base de cálculo do FCP.",
        xsd=True)
    nfe40_pFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Percentual de ICMS relativo ao Fundo de Combate à Pobreza",
        xsd=True,
        help="Percentual de ICMS relativo ao Fundo de Combate à Pobreza"
        "\n(FCP).")
    nfe40_vFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Valor do ICMS relativo ao Fundo de Combate à Pobreza",
        xsd=True,
        help="Valor do ICMS relativo ao Fundo de Combate à Pobreza (FCP).")


class ICMS60(models.AbstractModel):
    """Tributação pelo ICMS
    60 - ICMS cobrado anteriormente por substituição tributáriaNT2010/004"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icms60'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMS60Type'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="origem da mercadoria: 0 - Nacional",
        xsd=True,
        xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CST = fields.Selection(
        CST_ICMS60,
        string="Tributação pelo ICMS", xsd=True, xsd_required=True,
        help="Tributação pelo ICMS"
        "\n60 - ICMS cobrado anteriormente por substituição tributária")
    nfe40_vBCSTRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS ST retido anteriormente",
        xsd=True)
    nfe40_pST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Aliquota suportada pelo consumidor final",
        xsd=True)
    nfe40_vICMSSubstituto = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="vICMSSubstituto",
        xsd=True,
        help="Valor do ICMS Próprio do Substituto cobrado em operação"
        "\nanterior")
    nfe40_vICMSSTRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS ST retido anteriormente",
        xsd=True)
    nfe40_vBCFCPSTRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="vBCFCPSTRet",
        xsd=True,
        help="Valor da Base de cálculo do FCP retido anteriormente por ST.")
    nfe40_pFCPSTRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="pFCPSTRet",
        xsd=True,
        help="Percentual de FCP retido anteriormente por substituição"
        "\ntributária.")
    nfe40_vFCPSTRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do FCP retido por substituição tributária",
        xsd=True)
    nfe40_pRedBCEfet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da base de cálculo efetiva",
        xsd=True)
    nfe40_vBCEfet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da base de cálculo efetiva.",
        xsd=True)
    nfe40_pICMSEfet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS efetiva.",
        xsd=True)
    nfe40_vICMSEfet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS efetivo.",
        xsd=True)


class ICMS70(models.AbstractModel):
    """Tributação pelo ICMS
    70 - Com redução de base de cálculo e cobrança do ICMS por substituição
    tributáriaGrupo desoneração"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icms70'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMS70Type'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="origem da mercadoria: 0 - Nacional",
        xsd=True,
        xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CST = fields.Selection(
        CST_ICMS70,
        string="Tributção pelo ICMS", xsd=True, xsd_required=True,
        help="Tributção pelo ICMS"
        "\n70 - Com redução de base de cálculo e cobrança do ICMS por"
        "\nsubstituição tributária")
    nfe40_modBC = fields.Selection(
        MODBC_ICMS70,
        string="Modalidade de determinação da BC do ICMS",
        xsd=True,
        xsd_required=True,
        help="Modalidade de determinação da BC do ICMS:"
        "\n0 - Margem Valor Agregado (%);"
        "\n1 - Pauta (valor);"
        "\n2 - Preço Tabelado Máximo (valor);"
        "\n3 - Valor da Operação.")
    nfe40_pRedBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da BC",
        xsd=True,
        xsd_required=True)
    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS", xsd=True, xsd_required=True)
    nfe40_pICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS", xsd=True, xsd_required=True)
    nfe40_vICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS", xsd=True, xsd_required=True)
    nfe40_vBCFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da Base de cálculo do FCP.",
        xsd=True)
    nfe40_pFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Percentual de ICMS relativo ao Fundo de Combate à Pobreza",
        xsd=True,
        help="Percentual de ICMS relativo ao Fundo de Combate à Pobreza"
        "\n(FCP).")
    nfe40_vFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Valor do ICMS relativo ao Fundo de Combate à Pobreza",
        xsd=True,
        help="Valor do ICMS relativo ao Fundo de Combate à Pobreza (FCP).")
    nfe40_modBCST = fields.Selection(
        MODBCST_ICMS70,
        string="Modalidade de determinação da BC do ICMS ST",
        xsd=True,
        xsd_required=True,
        help="Modalidade de determinação da BC do ICMS ST:"
        "\n0 – Preço tabelado ou máximo sugerido;"
        "\n1 - Lista Negativa (valor);"
        "\n2 - Lista Positiva (valor);"
        "\n3 - Lista Neutra (valor);"
        "\n4 - Margem Valor Agregado (%);"
        "\n5 - Pauta (valor)."
        "\n6 - Valor da Operação")
    nfe40_pMVAST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual da Margem de Valor Adicionado ICMS ST",
        xsd=True)
    nfe40_pRedBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da BC ICMS ST",
        xsd=True)
    nfe40_vBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS ST",
        xsd=True,
        xsd_required=True)
    nfe40_pICMSST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS ST",
        xsd=True,
        xsd_required=True)
    nfe40_vICMSST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS ST", xsd=True, xsd_required=True)
    nfe40_vBCFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="vBCFCPST",
        xsd=True,
        help="Valor da Base de cálculo do FCP retido por substituição"
        "\ntributária.")
    nfe40_pFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Percentual de FCP retido por substituição tributária",
        xsd=True)
    nfe40_vFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do FCP retido por substituição tributária",
        xsd=True)
    nfe40_vICMSDeson = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS de desoneração",
        xsd=True)
    nfe40_motDesICMS = fields.Selection(
        MOTDESICMS_ICMS70,
        string="Motivo da desoneração do ICMS:3",
        xsd=True,
        help="Motivo da desoneração do ICMS:3-Uso na"
        "\nagropecuária;9-Outros;12-Fomento agropecuário")


class ICMS90(models.AbstractModel):
    """Tributação pelo ICMS
    90 - OutrasGrupo desoneração"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icms90'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMS90Type'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="origem da mercadoria: 0 - Nacional",
        xsd=True,
        xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CST = fields.Selection(
        CST_ICMS90,
        string="Tributção pelo ICMS", xsd=True, xsd_required=True,
        help="Tributção pelo ICMS"
        "\n90 - Outras")
    nfe40_modBC = fields.Selection(
        MODBC_ICMS90,
        string="Modalidade de determinação da BC do ICMS",
        xsd=True,
        help="Modalidade de determinação da BC do ICMS:")
    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS",
        xsd=True)
    nfe40_pRedBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da BC",
        xsd=True)
    nfe40_pICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS",
        xsd=True)
    nfe40_vICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS",
        xsd=True)
    nfe40_vBCFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da Base de cálculo do FCP.",
        xsd=True)
    nfe40_pFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Percentual de ICMS relativo ao Fundo de Combate à Pobreza",
        xsd=True,
        help="Percentual de ICMS relativo ao Fundo de Combate à Pobreza"
        "\n(FCP).")
    nfe40_vFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Valor do ICMS relativo ao Fundo de Combate à Pobreza",
        xsd=True,
        help="Valor do ICMS relativo ao Fundo de Combate à Pobreza (FCP).")
    nfe40_modBCST = fields.Selection(
        MODBCST_ICMS90,
        string="Modalidade de determinação da BC do ICMS ST",
        xsd=True,
        help="Modalidade de determinação da BC do ICMS ST:"
        "\n0 – Preço tabelado ou máximo sugerido;"
        "\n1 - Lista Negativa (valor);"
        "\n2 - Lista Positiva (valor);"
        "\n3 - Lista Neutra (valor);"
        "\n4 - Margem Valor Agregado (%);"
        "\n5 - Pauta (valor)"
        "\n6 - Valor da Operação.")
    nfe40_pMVAST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual da Margem de Valor Adicionado ICMS ST",
        xsd=True)
    nfe40_pRedBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da BC ICMS ST",
        xsd=True)
    nfe40_vBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS ST",
        xsd=True)
    nfe40_pICMSST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS ST",
        xsd=True)
    nfe40_vICMSST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS ST",
        xsd=True)
    nfe40_vBCFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da Base de cálculo do FCP.",
        xsd=True)
    nfe40_pFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Percentual de FCP retido por substituição tributária",
        xsd=True)
    nfe40_vFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do FCP retido por substituição tributária",
        xsd=True)
    nfe40_vICMSDeson = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS de desoneração",
        xsd=True)
    nfe40_motDesICMS = fields.Selection(
        MOTDESICMS_ICMS90,
        string="Motivo da desoneração do ICMS:3",
        xsd=True,
        help="Motivo da desoneração do ICMS:3-Uso na"
        "\nagropecuária;9-Outros;12-Fomento agropecuário")


class ICMSPart(models.AbstractModel):
    """Partilha do ICMS entre a UF de origem e UF de destino ou a UF definida
    na legislação
    Operação interestadual para consumidor final com partilha do ICMS devido
    na operação entre a UF de origem e a UF do destinatário ou ou a UF
    definida na legislação. (Ex. UF da concessionária de entrega do
    veículos)"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icmspart'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMSPartType'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="origem da mercadoria: 0 - Nacional",
        xsd=True,
        xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CST = fields.Selection(
        CST_ICMSPART,
        string="Tributação pelo ICMS", xsd=True, xsd_required=True,
        help="Tributação pelo ICMS"
        "\n10 - Tributada e com cobrança do ICMS por substituição tributária;"
        "\n90 – Outros.")
    nfe40_modBC = fields.Selection(
        MODBC_ICMSPART,
        string="Modalidade de determinação da BC do ICMS",
        xsd=True,
        xsd_required=True,
        help="Modalidade de determinação da BC do ICMS:")
    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS", xsd=True, xsd_required=True)
    nfe40_pRedBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da BC",
        xsd=True)
    nfe40_pICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS", xsd=True, xsd_required=True)
    nfe40_vICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS", xsd=True, xsd_required=True)
    nfe40_modBCST = fields.Selection(
        MODBCST_ICMSPART,
        string="Modalidade de determinação da BC do ICMS ST",
        xsd=True,
        xsd_required=True,
        help="Modalidade de determinação da BC do ICMS ST:"
        "\n0 – Preço tabelado ou máximo sugerido;"
        "\n1 - Lista Negativa (valor);"
        "\n2 - Lista Positiva (valor);"
        "\n3 - Lista Neutra (valor);"
        "\n4 - Margem Valor Agregado (%);"
        "\n5 - Pauta (valor)."
        "\n6 - Valor da Operação")
    nfe40_pMVAST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual da Margem de Valor Adicionado ICMS ST",
        xsd=True)
    nfe40_pRedBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da BC ICMS ST",
        xsd=True)
    nfe40_vBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS ST",
        xsd=True,
        xsd_required=True)
    nfe40_pICMSST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS ST",
        xsd=True,
        xsd_required=True)
    nfe40_vICMSST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS ST", xsd=True, xsd_required=True)
    nfe40_pBCOp = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="pBCOp", xsd=True, xsd_required=True,
        help="Percentual para determinação do valor da Base de Cálculo da"
        "\noperação própria.")
    nfe40_UFST = fields.Selection(
        TUF,
        string="Sigla da UF para qual é devido o ICMS ST da operação",
        xsd=True,
        xsd_required=True)


class ICMSSN101(models.AbstractModel):
    "Tributação do ICMS pelo SIMPLES NACIONAL e CSOSN=101 (v.2.0)"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icmssn101'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMSSN101Type'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="origem da mercadoria: 0 - Nacional",
        xsd=True,
        xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CSOSN = fields.Selection(
        CSOSN_ICMSSN101,
        string="101", xsd=True, xsd_required=True,
        help="101- Tributada pelo Simples Nacional com permissão de"
        "\ncrédito. (v.2.0)")
    nfe40_pCredSN = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota aplicável de cálculo do crédito",
        xsd=True,
        xsd_required=True,
        help="Alíquota aplicável de cálculo do crédito (Simples Nacional)."
        "\n(v2.0)")
    nfe40_vCredICMSSN = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="vCredICMSSN", xsd=True, xsd_required=True,
        help="Valor crédito do ICMS que pode ser aproveitado nos termos do"
        "\nart. 23 da LC 123 (Simples Nacional) (v2.0)")


class ICMSSN102(models.AbstractModel):
    """Tributação do ICMS pelo SIMPLES NACIONAL e CSOSN=102, 103, 300 ou 400
    (v.2.0))"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icmssn102'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMSSN102Type'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="origem da mercadoria: 0 - Nacional",
        xsd=True,
        xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CSOSN = fields.Selection(
        CSOSN_ICMSSN102,
        string="102", xsd=True, xsd_required=True,
        help="102- Tributada pelo Simples Nacional sem permissão de"
        "\ncrédito."
        "\n103 – Isenção do ICMS no Simples Nacional para faixa de receita"
        "\nbruta."
        "\n300 – Imune."
        "\n400 – Não tributda pelo Simples Nacional (v.2.0) (v.2.0)")


class ICMSSN201(models.AbstractModel):
    "Tributação do ICMS pelo SIMPLES NACIONAL e CSOSN=201 (v.2.0)"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icmssn201'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMSSN201Type'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="Origem da mercadoria", xsd=True, xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CSOSN = fields.Selection(
        CSOSN_ICMSSN201,
        string="201", xsd=True, xsd_required=True,
        help="201- Tributada pelo Simples Nacional com permissão de crédito"
        "\ne com cobrança do ICMS por Substituição Tributária"
        "\n(v.2.0)")
    nfe40_modBCST = fields.Selection(
        MODBCST_ICMSSN201,
        string="Modalidade de determinação da BC do ICMS ST",
        xsd=True,
        xsd_required=True,
        help="Modalidade de determinação da BC do ICMS ST:"
        "\n0 – Preço tabelado ou máximo sugerido;"
        "\n1 - Lista Negativa (valor);"
        "\n2 - Lista Positiva (valor);"
        "\n3 - Lista Neutra (valor);"
        "\n4 - Margem Valor Agregado (%);"
        "\n5 - Pauta (valor). (v2.0)"
        "\n6 - Valor da Operação")
    nfe40_pMVAST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual da Margem de Valor Adicionado ICMS ST",
        xsd=True,
        help="Percentual da Margem de Valor Adicionado ICMS ST (v2.0)")
    nfe40_pRedBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da BC ICMS ST",
        xsd=True,
        help="Percentual de redução da BC ICMS ST (v2.0)")
    nfe40_vBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS ST (v2.0)",
        xsd=True,
        xsd_required=True)
    nfe40_pICMSST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS ST (v2.0)",
        xsd=True,
        xsd_required=True)
    nfe40_vICMSST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS ST (v2.0)",
        xsd=True,
        xsd_required=True)
    nfe40_vBCFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da Base de cálculo do FCP.",
        xsd=True)
    nfe40_pFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Percentual de FCP retido por substituição tributária",
        xsd=True)
    nfe40_vFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do FCP retido por substituição tributária",
        xsd=True)
    nfe40_pCredSN = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota aplicável de cálculo do crédito",
        xsd=True,
        xsd_required=True,
        help="Alíquota aplicável de cálculo do crédito (Simples Nacional)."
        "\n(v2.0)")
    nfe40_vCredICMSSN = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="vCredICMSSN", xsd=True, xsd_required=True,
        help="Valor crédito do ICMS que pode ser aproveitado nos termos do"
        "\nart. 23 da LC 123 (Simples Nacional) (v2.0)")


class ICMSSN202(models.AbstractModel):
    "Tributação do ICMS pelo SIMPLES NACIONAL e CSOSN=202 ou 203 (v.2.0)"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icmssn202'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMSSN202Type'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="Origem da mercadoria", xsd=True, xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CSOSN = fields.Selection(
        CSOSN_ICMSSN202,
        string="202", xsd=True, xsd_required=True,
        help="202- Tributada pelo Simples Nacional sem permissão de crédito"
        "\ne com cobrança do ICMS por Substituição Tributária;"
        "\n203- Isenção do ICMS nos Simples Nacional para faixa de receita"
        "\nbruta e com cobrança do ICMS por Substituição Tributária"
        "\n(v.2.0)")
    nfe40_modBCST = fields.Selection(
        MODBCST_ICMSSN202,
        string="Modalidade de determinação da BC do ICMS ST",
        xsd=True,
        xsd_required=True,
        help="Modalidade de determinação da BC do ICMS ST:"
        "\n0 – Preço tabelado ou máximo sugerido;"
        "\n1 - Lista Negativa (valor);"
        "\n2 - Lista Positiva (valor);"
        "\n3 - Lista Neutra (valor);"
        "\n4 - Margem Valor Agregado (%);"
        "\n5 - Pauta (valor). (v2.0)"
        "\n6 - Valor da Operação")
    nfe40_pMVAST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual da Margem de Valor Adicionado ICMS ST",
        xsd=True,
        help="Percentual da Margem de Valor Adicionado ICMS ST (v2.0)")
    nfe40_pRedBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da BC ICMS ST",
        xsd=True,
        help="Percentual de redução da BC ICMS ST (v2.0)")
    nfe40_vBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS ST (v2.0)",
        xsd=True,
        xsd_required=True)
    nfe40_pICMSST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS ST (v2.0)",
        xsd=True,
        xsd_required=True)
    nfe40_vICMSST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS ST (v2.0)",
        xsd=True,
        xsd_required=True)
    nfe40_vBCFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da Base de cálculo do FCP.",
        xsd=True)
    nfe40_pFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Percentual de FCP retido por substituição tributária",
        xsd=True)
    nfe40_vFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do FCP retido por substituição tributária",
        xsd=True)


class ICMSSN500(models.AbstractModel):
    """Tributação do ICMS pelo SIMPLES NACIONAL,CRT=1 – Simples Nacional e
    CSOSN=500 (v.2.0)"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icmssn500'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMSSN500Type'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="origem da mercadoria: 0 - Nacional",
        xsd=True,
        xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CSOSN = fields.Selection(
        CSOSN_ICMSSN500,
        string="CSOSN", xsd=True, xsd_required=True,
        help="500 – ICMS cobrado anterirmente por substituição tributária"
        "\n(substituído) ou por antecipação"
        "\n(v.2.0)")
    nfe40_vBCSTRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS ST retido anteriormente",
        xsd=True,
        help="Valor da BC do ICMS ST retido anteriormente (v2.0)")
    nfe40_pST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Aliquota suportada pelo consumidor final",
        xsd=True)
    nfe40_vICMSSubstituto = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS próprio do substituto",
        xsd=True)
    nfe40_vICMSSTRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS ST retido anteriormente",
        xsd=True,
        help="Valor do ICMS ST retido anteriormente (v2.0)")
    nfe40_vBCFCPSTRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Valor da Base de cálculo do FCP retido anteriormente",
        xsd=True)
    nfe40_pFCPSTRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="pFCPSTRet",
        xsd=True,
        help="Percentual de FCP retido anteriormente por substituição"
        "\ntributária.")
    nfe40_vFCPSTRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do FCP retido por substituição tributária",
        xsd=True)
    nfe40_pRedBCEfet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da base de cálculo efetiva",
        xsd=True)
    nfe40_vBCEfet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da base de cálculo efetiva.",
        xsd=True)
    nfe40_pICMSEfet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS efetiva.",
        xsd=True)
    nfe40_vICMSEfet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS efetivo.",
        xsd=True)


class ICMSSN900(models.AbstractModel):
    """Tributação do ICMS pelo SIMPLES NACIONAL, CRT=1 – Simples Nacional e
    CSOSN=900 (v2.0)"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icmssn900'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMSSN900Type'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="origem da mercadoria: 0 - Nacional",
        xsd=True,
        xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CSOSN = fields.Selection(
        CSOSN_ICMSSN900,
        string="Tributação pelo ICMS 900",
        xsd=True,
        xsd_required=True,
        help="Tributação pelo ICMS 900 - Outros(v2.0)")
    nfe40_modBC = fields.Selection(
        MODBC_ICMSSN900,
        string="Modalidade de determinação da BC do ICMS",
        xsd=True,
        help="Modalidade de determinação da BC do ICMS:")
    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS",
        xsd=True)
    nfe40_pRedBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da BC",
        xsd=True)
    nfe40_pICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS",
        xsd=True)
    nfe40_vICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS",
        xsd=True)
    nfe40_modBCST = fields.Selection(
        MODBCST_ICMSSN900,
        string="Modalidade de determinação da BC do ICMS ST",
        xsd=True,
        help="Modalidade de determinação da BC do ICMS ST:"
        "\n0 – Preço tabelado ou máximo sugerido;"
        "\n1 - Lista Negativa (valor);"
        "\n2 - Lista Positiva (valor);"
        "\n3 - Lista Neutra (valor);"
        "\n4 - Margem Valor Agregado (%);"
        "\n5 - Pauta (valor)."
        "\n6 - Valor da Operação")
    nfe40_pMVAST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual da Margem de Valor Adicionado ICMS ST",
        xsd=True)
    nfe40_pRedBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da BC ICMS ST",
        xsd=True)
    nfe40_vBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ICMS ST",
        xsd=True)
    nfe40_pICMSST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS ST",
        xsd=True)
    nfe40_vICMSST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS ST",
        xsd=True)
    nfe40_vBCFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da Base de cálculo do FCP.",
        xsd=True)
    nfe40_pFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Percentual de FCP retido por substituição tributária",
        xsd=True)
    nfe40_vFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do FCP retido por substituição tributária",
        xsd=True)
    nfe40_pCredSN = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota aplicável de cálculo do crédito",
        xsd=True,
        help="Alíquota aplicável de cálculo do crédito (Simples Nacional)."
        "\n(v2.0)")
    nfe40_vCredICMSSN = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="vCredICMSSN",
        xsd=True,
        help="Valor crédito do ICMS que pode ser aproveitado nos termos do"
        "\nart. 23 da LC 123 (Simples Nacional) (v2.0)")


class ICMSST(models.AbstractModel):
    """Grupo de informação do ICMSST devido para a UF de destino, nas operações
    interestaduais de produtos que tiveram retenção antecipada de ICMS
    por ST na UF do remetente. Repasse via Substituto Tributário."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icmsst'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMSSTType'
    _concrete_rec_name = 'nfe40_orig'

    nfe40_orig = fields.Selection(
        TORIG,
        string="origem da mercadoria: 0 - Nacional",
        xsd=True,
        xsd_required=True,
        help="Tipo Origem da mercadoria CST ICMS origem da mercadoria")
    nfe40_CST = fields.Selection(
        CST_ICMSST,
        string="Tributção pelo ICMS", xsd=True, xsd_required=True,
        help="Tributção pelo ICMS"
        "\n41-Não Tributado."
        "\n60-Cobrado anteriormente por substituição tributária.")
    nfe40_vBCSTRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Informar o valor da BC do ICMS ST retido na UF remetente",
        xsd=True,
        xsd_required=True)
    nfe40_pST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Aliquota suportada pelo consumidor final",
        xsd=True)
    nfe40_vICMSSubstituto = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="vICMSSubstituto",
        xsd=True,
        help="Valor do ICMS Próprio do Substituto cobrado em operação"
        "\nanterior")
    nfe40_vICMSSTRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Informar o valor do ICMS ST retido na UF remetente",
        xsd=True,
        xsd_required=True,
        help="Informar o valor do ICMS ST retido na UF remetente (iv2.0))")
    nfe40_vBCFCPSTRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="vBCFCPSTRet",
        xsd=True,
        help="Informar o valor da Base de Cálculo do FCP retido"
        "\nanteriormente por ST.")
    nfe40_pFCPSTRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual relativo ao Fundo de Combate à Pobreza",
        xsd=True,
        help="Percentual relativo ao Fundo de Combate à Pobreza (FCP)"
        "\nretido por substituição tributária.")
    nfe40_vFCPSTRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Valor do ICMS relativo ao Fundo de Combate à Pobreza",
        xsd=True,
        help="Valor do ICMS relativo ao Fundo de Combate à Pobreza (FCP)"
        "\nretido por substituição tributária.")
    nfe40_vBCSTDest = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Informar o valor da BC do ICMS ST da UF destino",
        xsd=True,
        xsd_required=True,
        help="Informar o valor da BC do ICMS ST da UF destino")
    nfe40_vICMSSTDest = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Informar o valor da BC do ICMS ST da UF destino",
        xsd=True,
        xsd_required=True,
        help="Informar o valor da BC do ICMS ST da UF destino (v2.0)")
    nfe40_pRedBCEfet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de redução da base de cálculo efetiva",
        xsd=True)
    nfe40_vBCEfet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da base de cálculo efetiva.",
        xsd=True)
    nfe40_pICMSEfet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ICMS efetivo.",
        xsd=True)
    nfe40_vICMSEfet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS efetivo.",
        xsd=True)


class ICMSTot(models.AbstractModel):
    "Totais referentes ao ICMS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icmstot'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMSTotType'
    _concrete_rec_name = 'nfe40_vBC'

    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="BC do ICMS", xsd=True, xsd_required=True)
    nfe40_vICMS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total do ICMS", xsd=True, xsd_required=True)
    nfe40_vICMSDeson = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total do ICMS desonerado",
        xsd=True,
        xsd_required=True)
    nfe40_vFCPUFDest = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Valor total do ICMS relativo ao Fundo de Combate à Pobreza",
        xsd=True,
        help="Valor total do ICMS relativo ao Fundo de Combate à Pobreza"
        "\n(FCP) para a UF de destino.")
    nfe40_vICMSUFDest = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Valor total do ICMS de partilha para a UF do destinatário",
        xsd=True)
    nfe40_vICMSUFRemet = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Valor total do ICMS de partilha para a UF do remetente",
        xsd=True)
    nfe40_vFCP = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total do FCP", xsd=True, xsd_required=True,
        help="Valor Total do FCP (Fundo de Combate à Pobreza).")
    nfe40_vBCST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="BC do ICMS ST", xsd=True, xsd_required=True)
    nfe40_vST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total do ICMS ST",
        xsd=True,
        xsd_required=True)
    nfe40_vFCPST = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total do FCP", xsd=True, xsd_required=True,
        help="Valor Total do FCP (Fundo de Combate à Pobreza) retido por"
        "\nsubstituição tributária.")
    nfe40_vFCPSTRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total do FCP",
        xsd=True,
        xsd_required=True,
        help="Valor Total do FCP (Fundo de Combate à Pobreza) retido"
        "\nanteriormente por substituição tributária.")
    nfe40_vProd = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total dos produtos e serviços",
        xsd=True,
        xsd_required=True)
    nfe40_vFrete = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total do Frete",
        xsd=True,
        xsd_required=True)
    nfe40_vSeg = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total do Seguro",
        xsd=True,
        xsd_required=True)
    nfe40_vDesc = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total do Desconto",
        xsd=True,
        xsd_required=True)
    nfe40_vII = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total do II", xsd=True, xsd_required=True)
    nfe40_vIPI = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total do IPI", xsd=True, xsd_required=True)
    nfe40_vIPIDevol = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total do IPI devolvido",
        xsd=True,
        xsd_required=True,
        help="Valor Total do IPI devolvido. Deve ser informado quando"
        "\npreenchido o Grupo Tributos Devolvidos na emissão de"
        "\nnota finNFe=4 (devolução) nas operações com não"
        "\ncontribuintes do IPI. Corresponde ao total da soma"
        "\ndos campos id: UA04.")
    nfe40_vPIS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do PIS", xsd=True, xsd_required=True)
    nfe40_vCOFINS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do COFINS", xsd=True, xsd_required=True)
    nfe40_vOutro = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Outras Despesas acessórias",
        xsd=True,
        xsd_required=True)
    nfe40_vNF = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total da NF-e", xsd=True, xsd_required=True)
    nfe40_vTotTrib = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor estimado total de impostos federais",
        xsd=True,
        help="Valor estimado total de impostos federais, estaduais e"
        "\nmunicipais")


class ICMS(models.AbstractModel):
    "Dados do ICMS Normal e ST"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icms'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMSType'
    _concrete_rec_name = 'nfe40_ICMS00'

    nfe40_choice11 = fields.Selection([
        ('nfe40_ICMS00', 'ICMS00'),
        ('nfe40_ICMS10', 'ICMS10'),
        ('nfe40_ICMS20', 'ICMS20'),
        ('nfe40_ICMS30', 'ICMS30'),
        ('nfe40_ICMS40', 'ICMS40'),
        ('nfe40_ICMS51', 'ICMS51'),
        ('nfe40_ICMS60', 'ICMS60'),
        ('nfe40_ICMS70', 'ICMS70'),
        ('nfe40_ICMS90', 'ICMS90'),
        ('nfe40_ICMSPart', 'ICMSPart'),
        ('nfe40_ICMSST', 'ICMSST'),
        ('nfe40_ICMSSN101', 'ICMSSN101'),
        ('nfe40_ICMSSN102', 'ICMSSN102'),
        ('nfe40_ICMSSN201', 'ICMSSN201'),
        ('nfe40_ICMSSN202', 'ICMSSN202'),
        ('nfe40_ICMSSN500', 'ICMSSN500'),
        ('nfe40_ICMSSN900', 'ICMSSN900')],
        "ICMS00/ICMS10/ICMS20/ICMS30/ICMS40/ICMS51/ICMS60/I...")
    nfe40_ICMS00 = fields.Many2one(
        "nfe.40.icms00",
        choice='11',
        string="Tributação pelo ICMS",
        xsd=True,
        xsd_required=True,
        help="Tributação pelo ICMS"
        "\n00 - Tributada integralmente")
    nfe40_ICMS10 = fields.Many2one(
        "nfe.40.icms10",
        choice='11',
        string="Tributação pelo ICMS",
        xsd=True,
        xsd_required=True,
        help="Tributação pelo ICMS"
        "\n10 - Tributada e com cobrança do ICMS por substituição tributária")
    nfe40_ICMS20 = fields.Many2one(
        "nfe.40.icms20",
        choice='11',
        string="Tributção pelo ICMS",
        xsd=True,
        xsd_required=True,
        help="Tributção pelo ICMS"
        "\n20 - Com redução de base de cálculo")
    nfe40_ICMS30 = fields.Many2one(
        "nfe.40.icms30",
        choice='11',
        string="Tributação pelo ICMS",
        xsd=True,
        xsd_required=True,
        help="Tributação pelo ICMS"
        "\n30 - Isenta ou não tributada e com cobrança do ICMS por"
        "\nsubstituição tributária")
    nfe40_ICMS40 = fields.Many2one(
        "nfe.40.icms40",
        choice='11',
        string="Tributação pelo ICMS",
        xsd=True,
        xsd_required=True,
        help="Tributação pelo ICMS"
        "\n40 - Isenta"
        "\n41 - Não tributada"
        "\n50 - Suspensão")
    nfe40_ICMS51 = fields.Many2one(
        "nfe.40.icms51",
        choice='11',
        string="Tributção pelo ICMS",
        xsd=True,
        xsd_required=True,
        help="Tributção pelo ICMS"
        "\n51 - Diferimento"
        "\nA exigência do preenchimento das informações do ICMS diferido fica"
        "\nà critério de cada UF.")
    nfe40_ICMS60 = fields.Many2one(
        "nfe.40.icms60",
        choice='11',
        string="Tributação pelo ICMS",
        xsd=True,
        xsd_required=True,
        help="Tributação pelo ICMS"
        "\n60 - ICMS cobrado anteriormente por substituição tributária")
    nfe40_ICMS70 = fields.Many2one(
        "nfe.40.icms70",
        choice='11',
        string="Tributação pelo ICMS",
        xsd=True,
        xsd_required=True,
        help="Tributação pelo ICMS"
        "\n70 - Com redução de base de cálculo e cobrança do ICMS por"
        "\nsubstituição tributária")
    nfe40_ICMS90 = fields.Many2one(
        "nfe.40.icms90",
        choice='11',
        string="Tributação pelo ICMS",
        xsd=True,
        xsd_required=True,
        help="Tributação pelo ICMS"
        "\n90 - Outras")
    nfe40_ICMSPart = fields.Many2one(
        "nfe.40.icmspart",
        choice='11',
        string="ICMSPart", xsd=True, xsd_required=True,
        help="Partilha do ICMS entre a UF de origem e UF de destino ou a UF"
        "\ndefinida na legislação"
        "\nOperação interestadual para consumidor final com partilha do ICMS"
        "\ndevido na operação entre a UF de origem e a UF do"
        "\ndestinatário ou ou a UF definida na legislação. (Ex. UF da"
        "\nconcessionária de entrega do veículos)")
    nfe40_ICMSST = fields.Many2one(
        "nfe.40.icmsst",
        choice='11',
        string="Grupo de informação do ICMSST devido para a UF de destino",
        xsd=True,
        xsd_required=True,
        help="Grupo de informação do ICMSST devido para a UF de destino,"
        "\nnas operações interestaduais de produtos que tiveram"
        "\nretenção antecipada de ICMS por ST na UF do"
        "\nremetente. Repasse via Substituto Tributário.")
    nfe40_ICMSSN101 = fields.Many2one(
        "nfe.40.icmssn101",
        choice='11',
        string="Tributação do ICMS pelo SIMPLES NACIONAL e CSOSN=101",
        xsd=True,
        xsd_required=True,
        help="Tributação do ICMS pelo SIMPLES NACIONAL e CSOSN=101 (v.2.0)")
    nfe40_ICMSSN102 = fields.Many2one(
        "nfe.40.icmssn102",
        choice='11',
        string="Tributação do ICMS pelo SIMPLES NACIONAL e CSOSN=102",
        xsd=True,
        xsd_required=True,
        help="Tributação do ICMS pelo SIMPLES NACIONAL e CSOSN=102, 103,"
        "\n300 ou 400 (v.2.0))")
    nfe40_ICMSSN201 = fields.Many2one(
        "nfe.40.icmssn201",
        choice='11',
        string="Tributação do ICMS pelo SIMPLES NACIONAL e CSOSN=201",
        xsd=True,
        xsd_required=True,
        help="Tributação do ICMS pelo SIMPLES NACIONAL e CSOSN=201 (v.2.0)")
    nfe40_ICMSSN202 = fields.Many2one(
        "nfe.40.icmssn202",
        choice='11',
        string="ICMSSN202", xsd=True, xsd_required=True,
        help="Tributação do ICMS pelo SIMPLES NACIONAL e CSOSN=202 ou 203"
        "\n(v.2.0)")
    nfe40_ICMSSN500 = fields.Many2one(
        "nfe.40.icmssn500",
        choice='11',
        string="Tributação do ICMS pelo SIMPLES NACIONAL",
        xsd=True,
        xsd_required=True,
        help="Tributação do ICMS pelo SIMPLES NACIONAL,CRT=1 – Simples"
        "\nNacional e CSOSN=500 (v.2.0)")
    nfe40_ICMSSN900 = fields.Many2one(
        "nfe.40.icmssn900",
        choice='11',
        string="Tributação do ICMS pelo SIMPLES NACIONAL",
        xsd=True,
        xsd_required=True,
        help="Tributação do ICMS pelo SIMPLES NACIONAL, CRT=1 – Simples"
        "\nNacional e CSOSN=900 (v2.0)")


class ICMSUFDest(models.AbstractModel):
    """Grupo a ser informado nas vendas interestarduais para consumidor final,
    não contribuinte de ICMS"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.icmsufdest'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ICMSUFDestType'
    _concrete_rec_name = 'nfe40_vBCUFDest'

    nfe40_vBCUFDest = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Valor da Base de Cálculo do ICMS na UF do destinatário",
        xsd=True,
        xsd_required=True)
    nfe40_vBCFCPUFDest = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Valor da Base de Cálculo do FCP na UF do destinatário",
        xsd=True)
    nfe40_pFCPUFDest = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="pFCPUFDest",
        xsd=True,
        help="Percentual adicional inserido na alíquota interna da UF de"
        "\ndestino, relativo ao Fundo de Combate à Pobreza (FCP)"
        "\nnaquela UF.")
    nfe40_pICMSUFDest = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="pICMSUFDest", xsd=True, xsd_required=True,
        help="Alíquota adotada nas operações internas na UF do destinatário"
        "\npara o produto / mercadoria.")
    nfe40_pICMSInter = fields.Selection(
        PICMSINTER_ICMSUFDEST,
        string="Alíquota interestadual das UF envolvidas",
        xsd=True,
        xsd_required=True,
        help="Alíquota interestadual das UF envolvidas"
        "\n- 4% alíquota interestadual para produtos importados"
        "\n- 7% para os Estados de origem do Sul e Sudeste (exceto ES),"
        "\ndestinado para os Estados do Norte e Nordeste ou ES"
        "\n- 12% para os demais casos.")
    nfe40_pICMSInterPart = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de partilha para a UF do destinatário",
        xsd=True,
        xsd_required=True,
        help="Percentual de partilha para a UF do destinatário: - 40% em"
        "\n2016; - 60% em 2017; - 80% em 2018; - 100% a partir"
        "\nde 2019.")
    nfe40_vFCPUFDest = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Valor do ICMS relativo ao Fundo de Combate à Pobreza",
        xsd=True,
        help="Valor do ICMS relativo ao Fundo de Combate à Pobreza (FCP) da"
        "\nUF de destino.")
    nfe40_vICMSUFDest = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Valor do ICMS de partilha para a UF do destinatário",
        xsd=True,
        xsd_required=True)
    nfe40_vICMSUFRemet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS de partilha para a UF do remetente",
        xsd=True,
        xsd_required=True,
        help="Valor do ICMS de partilha para a UF do remetente. Nota: A"
        "\npartir de 2019, este valor será zero.")


class II(models.AbstractModel):
    "Dados do Imposto de Importação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.ii'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'IIType'
    _concrete_rec_name = 'nfe40_vBC'

    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Base da BC do Imposto de Importação",
        xsd=True,
        xsd_required=True)
    nfe40_vDespAdu = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor das despesas aduaneiras",
        xsd=True,
        xsd_required=True)
    nfe40_vII = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do Imposto de Importação",
        xsd=True,
        xsd_required=True)
    nfe40_vIOF = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do Imposto sobre Operações Financeiras",
        xsd=True,
        xsd_required=True)


class IPINT(models.AbstractModel):
    _description = 'ipint'
    _name = 'nfe.40.ipint'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'IPINTType'
    _concrete_rec_name = 'nfe40_CST'

    nfe40_CST = fields.Selection(
        CST_IPINT,
        string="Código da Situação Tributária do IPI",
        xsd=True,
        xsd_required=True,
        help="Código da Situação Tributária do IPI:"
        "\n01-Entrada tributada com alíquota zero"
        "\n02-Entrada isenta"
        "\n03-Entrada não-tributada"
        "\n04-Entrada imune"
        "\n05-Entrada com suspensão"
        "\n51-Saída tributada com alíquota zero"
        "\n52-Saída isenta"
        "\n53-Saída não-tributada"
        "\n54-Saída imune"
        "\n55-Saída com suspensão")


class IPITrib(models.AbstractModel):
    _description = 'ipitrib'
    _name = 'nfe.40.ipitrib'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'IPITribType'
    _concrete_rec_name = 'nfe40_CST'

    nfe40_choice20 = fields.Selection([
        ('nfe40_vBC', 'vBC'),
        ('nfe40_pIPI', 'pIPI'),
        ('nfe40_qUnid', 'qUnid'),
        ('nfe40_vUnid', 'vUnid')],
        "vBC/pIPI/qUnid/vUnid")
    nfe40_CST = fields.Selection(
        CST_IPITRIB,
        string="Código da Situação Tributária do IPI",
        xsd=True,
        xsd_required=True,
        help="Código da Situação Tributária do IPI:"
        "\n00-Entrada com recuperação de crédito"
        "\n49 - Outras entradas"
        "\n50-Saída tributada"
        "\n99-Outras saídas")
    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, choice='20',
        string="Valor da BC do IPI", xsd=True, xsd_required=True)
    nfe40_pIPI = fields.Monetary(currency_field="brl_currency_id",
        digits=2, choice='20',
        string="Alíquota do IPI", xsd=True, xsd_required=True)
    nfe40_qUnid = fields.Monetary(currency_field="brl_currency_id",
        digits=4, choice='20',
        string="Quantidade total na unidade padrão para tributação",
        xsd=True,
        xsd_required=True)
    nfe40_vUnid = fields.Monetary(currency_field="brl_currency_id",
        digits=4, choice='20',
        string="Valor por Unidade Tributável",
        xsd=True,
        xsd_required=True,
        help="Valor por Unidade Tributável. Informar o valor do imposto"
        "\nPauta por unidade de medida.")
    nfe40_vIPI = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do IPI", xsd=True, xsd_required=True)


class IPI(models.AbstractModel):
    "Informação de IPI devolvido"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.ipi'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'IPIType'
    _concrete_rec_name = 'nfe40_vIPIDevol'

    nfe40_vIPIDevol = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do IPI devolvido",
        xsd=True,
        xsd_required=True)


class ISSQN(models.AbstractModel):
    "ISSQN"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.issqn'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ISSQNType'
    _concrete_rec_name = 'nfe40_vBC'

    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do ISSQN", xsd=True, xsd_required=True)
    nfe40_vAliq = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do ISSQN", xsd=True, xsd_required=True)
    nfe40_vISSQN = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da do ISSQN", xsd=True, xsd_required=True)
    nfe40_cMunFG = fields.Char(
        string="cMunFG", xsd=True, xsd_required=True,
        help="Informar o município de ocorrência do fato gerador do ISSQN."
        "\nUtilizar a Tabela do IBGE (Anexo VII - Tabela de UF,"
        "\nMunicípio e País). “Atenção, não vincular com os"
        "\ncampos B12, C10 ou E10” v2.0")
    nfe40_cListServ = fields.Selection(
        TCLISTSERV_ISSQN,
        string="cListServ", xsd=True, xsd_required=True,
        help="Informar o Item da lista de serviços da LC 116/03 em que se"
        "\nclassifica o serviço.")
    nfe40_vDeducao = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor dedução para redução da base de cálculo",
        xsd=True)
    nfe40_vOutro = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor outras retenções",
        xsd=True)
    nfe40_vDescIncond = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor desconto incondicionado",
        xsd=True)
    nfe40_vDescCond = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor desconto condicionado",
        xsd=True)
    nfe40_vISSRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Retenção ISS",
        xsd=True)
    nfe40_indISS = fields.Selection(
        INDISS_ISSQN,
        string="Exibilidade do ISS:1",
        xsd=True,
        xsd_required=True,
        help="Exibilidade do ISS:1-Exigível;2-Não"
        "\nincidente;3-Isenção;4-Exportação;5-Imunidade;6-Exig.S"
        "\nusp. Judicial;7-Exig.Susp. ADM")
    nfe40_cServico = fields.Char(
        string="Código do serviço prestado dentro do município",
        xsd=True)
    nfe40_cMun = fields.Char(
        string="Código do Município de Incidência do Imposto",
        xsd=True)
    nfe40_cPais = fields.Char(
        string="Código de Pais",
        xsd=True)
    nfe40_nProcesso = fields.Char(
        string="nProcesso",
        xsd=True,
        help="Número do Processo administrativo ou judicial de suspenção do"
        "\nprocesso")
    nfe40_indIncentivo = fields.Selection(
        INDINCENTIVO_ISSQN,
        string="Indicador de Incentivo Fiscal",
        xsd=True,
        xsd_required=True,
        help="Indicador de Incentivo Fiscal. 1=Sim; 2=Não")


class ISSQNtot(models.AbstractModel):
    "Totais referentes ao ISSQN"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.issqntot'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ISSQNtotType'
    _concrete_rec_name = 'nfe40_vServ'

    nfe40_vServ = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total dos Serviços sob não",
        xsd=True,
        help="Valor Total dos Serviços sob não-incidência ou não tributados"
        "\npelo ICMS")
    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Base de Cálculo do ISS",
        xsd=True)
    nfe40_vISS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total do ISS",
        xsd=True)
    nfe40_vPIS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do PIS sobre serviços",
        xsd=True)
    nfe40_vCOFINS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do COFINS sobre serviços",
        xsd=True)
    nfe40_dCompet = fields.Date(
        string="Data da prestação do serviço",
        xsd=True,
        xsd_required=True,
        help="Data da prestação do serviço (AAAA-MM-DD)")
    nfe40_vDeducao = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor dedução para redução da base de cálculo",
        xsd=True)
    nfe40_vOutro = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor outras retenções",
        xsd=True)
    nfe40_vDescIncond = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor desconto incondicionado",
        xsd=True)
    nfe40_vDescCond = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor desconto condicionado",
        xsd=True)
    nfe40_vISSRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total Retenção ISS",
        xsd=True)
    nfe40_cRegTrib = fields.Selection(
        CREGTRIB_ISSQNTOT,
        string="Código do regime especial de tributação",
        xsd=True)


class NFref(models.AbstractModel):
    "Grupo de infromações da NF referenciada"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.nfref'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'NFrefType'
    _concrete_rec_name = 'nfe40_refNFe'

    nfe40_NFref_ide_id = fields.Many2one(
        "nfe.40.ide")
    nfe40_choice4 = fields.Selection([
        ('nfe40_refNFe', 'refNFe'),
        ('nfe40_refNF', 'refNF'),
        ('nfe40_refNFP', 'refNFP'),
        ('nfe40_refCTe', 'refCTe'),
        ('nfe40_refECF', 'refECF')],
        "refNFe/refNF/refNFP/refCTe/refECF")
    nfe40_refNFe = fields.Char(
        choice='4',
        string="Chave de acesso das NF",
        xsd=True,
        xsd_required=True,
        help="Chave de acesso das NF-e referenciadas. Chave de acesso"
        "\ncompostas por Código da UF (tabela do IBGE) + AAMM da"
        "\nemissão + CNPJ do Emitente + modelo, série e número"
        "\nda NF-e Referenciada + Código Numérico + DV.")
    nfe40_refNF = fields.Many2one(
        "nfe.40.refnf",
        choice='4',
        string="refNF", xsd=True, xsd_required=True,
        help="Dados da NF modelo 1/1A referenciada ou NF modelo 2"
        "\nreferenciada")
    nfe40_refNFP = fields.Many2one(
        "nfe.40.refnfp",
        choice='4',
        string="Grupo com as informações NF de produtor referenciada",
        xsd=True,
        xsd_required=True)
    nfe40_refCTe = fields.Char(
        choice='4',
        string="Utilizar esta TAG para referenciar um CT",
        xsd=True,
        xsd_required=True,
        help="Utilizar esta TAG para referenciar um CT-e emitido"
        "\nanteriormente, vinculada a NF-e atual")
    nfe40_refECF = fields.Many2one(
        "nfe.40.refecf",
        choice='4',
        string="Grupo do Cupom Fiscal vinculado à NF",
        xsd=True,
        xsd_required=True,
        help="Grupo do Cupom Fiscal vinculado à NF-e")


class PISAliq(models.AbstractModel):
    """Código de Situação Tributária do PIS.
    01 – Operação Tributável - Base de Cálculo = Valor da Operação Alíquota
    Normal (Cumulativo/Não Cumulativo);
    02 - Operação Tributável - Base de Calculo = Valor da Operação (Alíquota
    Diferenciada);"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.pisaliq'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'PISAliqType'
    _concrete_rec_name = 'nfe40_CST'

    nfe40_CST = fields.Selection(
        CST_PISALIQ,
        string="Código de Situação Tributária do PIS",
        xsd=True,
        xsd_required=True,
        help="Código de Situação Tributária do PIS."
        "\n01 – Operação Tributável - Base de Cálculo = Valor da Operação"
        "\nAlíquota Normal (Cumulativo/Não Cumulativo);"
        "\n02 - Operação Tributável - Base de Calculo = Valor da Operação"
        "\n(Alíquota Diferenciada);")
    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da BC do PIS", xsd=True, xsd_required=True)
    nfe40_pPIS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota do PIS (em percentual)",
        xsd=True,
        xsd_required=True)
    nfe40_vPIS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do PIS", xsd=True, xsd_required=True)


class PISNT(models.AbstractModel):
    """Código de Situação Tributária do PIS.
    04 - Operação Tributável - Tributação Monofásica - (Alíquota Zero);
    06 - Operação Tributável - Alíquota Zero;
    07 - Operação Isenta da contribuição;
    08 - Operação Sem Incidência da contribuição;
    09 - Operação com suspensão da contribuição;"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.pisnt'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'PISNTType'
    _concrete_rec_name = 'nfe40_CST'

    nfe40_CST = fields.Selection(
        CST_PISNT,
        string="Código de Situação Tributária do PIS",
        xsd=True,
        xsd_required=True,
        help="Código de Situação Tributária do PIS."
        "\n04 - Operação Tributável - Tributação Monofásica - (Alíquota Zero);"
        "\n05 - Operação Tributável (ST);"
        "\n06 - Operação Tributável - Alíquota Zero;"
        "\n07 - Operação Isenta da contribuição;"
        "\n08 - Operação Sem Incidência da contribuição;"
        "\n09 - Operação com suspensão da contribuição;")


class PISOutr(models.AbstractModel):
    """Código de Situação Tributária do PIS.
    99 - Outras Operações."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.pisoutr'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'PISOutrType'
    _concrete_rec_name = 'nfe40_CST'

    nfe40_choice13 = fields.Selection([
        ('nfe40_vBC', 'vBC'),
        ('nfe40_pPIS', 'pPIS'),
        ('nfe40_qBCProd', 'qBCProd'),
        ('nfe40_vAliqProd', 'vAliqProd')],
        "vBC/pPIS/qBCProd/vAliqProd")
    nfe40_CST = fields.Selection(
        CST_PISOUTR,
        string="Código de Situação Tributária do PIS",
        xsd=True,
        xsd_required=True,
        help="Código de Situação Tributária do PIS."
        "\n99 - Outras Operações.")
    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, choice='13',
        string="Valor da BC do PIS", xsd=True, xsd_required=True)
    nfe40_pPIS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, choice='13',
        string="Alíquota do PIS (em percentual)",
        xsd=True,
        xsd_required=True)
    nfe40_qBCProd = fields.Monetary(currency_field="brl_currency_id",
        digits=4, choice='13',
        string="Quantidade Vendida (NT2011/004)",
        xsd=True,
        xsd_required=True)
    nfe40_vAliqProd = fields.Monetary(currency_field="brl_currency_id",
        digits=4, choice='13',
        string="Alíquota do PIS", xsd=True, xsd_required=True,
        help="Alíquota do PIS (em reais) (NT2011/004)")
    nfe40_vPIS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do PIS", xsd=True, xsd_required=True)


class PISQtde(models.AbstractModel):
    """Código de Situação Tributária do PIS.
    03 - Operação Tributável - Base de Calculo = Quantidade Vendida x Alíquota
    por Unidade de Produto;"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.pisqtde'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'PISQtdeType'
    _concrete_rec_name = 'nfe40_CST'

    nfe40_CST = fields.Selection(
        CST_PISQTDE,
        string="Código de Situação Tributária do PIS",
        xsd=True,
        xsd_required=True,
        help="Código de Situação Tributária do PIS."
        "\n03 - Operação Tributável - Base de Calculo = Quantidade Vendida x"
        "\nAlíquota por Unidade de Produto;")
    nfe40_qBCProd = fields.Monetary(currency_field="brl_currency_id",
        digits=4, string="Quantidade Vendida (NT2011/004)",
        xsd=True,
        xsd_required=True,
        help="Quantidade Vendida (NT2011/004)")
    nfe40_vAliqProd = fields.Monetary(currency_field="brl_currency_id",
        digits=4, string="Alíquota do PIS", xsd=True, xsd_required=True,
        help="Alíquota do PIS (em reais) (NT2011/004)")
    nfe40_vPIS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do PIS", xsd=True, xsd_required=True)


class PISST(models.AbstractModel):
    "Dados do PIS Substituição Tributária"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.pisst'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'PISSTType'
    _concrete_rec_name = 'nfe40_vBC'

    nfe40_choice14 = fields.Selection([
        ('nfe40_vBC', 'vBC'),
        ('nfe40_pPIS', 'pPIS'),
        ('nfe40_qBCProd', 'qBCProd'),
        ('nfe40_vAliqProd', 'vAliqProd')],
        "vBC/pPIS/qBCProd/vAliqProd")
    nfe40_vBC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, choice='14',
        string="Valor da BC do PIS ST", xsd=True, xsd_required=True)
    nfe40_pPIS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, choice='14',
        string="Alíquota do PIS ST (em percentual)",
        xsd=True,
        xsd_required=True)
    nfe40_qBCProd = fields.Monetary(currency_field="brl_currency_id",
        digits=4, choice='14',
        string="Quantidade Vendida",
        xsd=True,
        xsd_required=True)
    nfe40_vAliqProd = fields.Monetary(currency_field="brl_currency_id",
        digits=4, choice='14',
        string="Alíquota do PIS ST (em reais)",
        xsd=True,
        xsd_required=True)
    nfe40_vPIS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do PIS ST", xsd=True, xsd_required=True)


class PIS(models.AbstractModel):
    "Dados do PIS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.pis'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'PISType'
    _concrete_rec_name = 'nfe40_PISAliq'

    nfe40_choice12 = fields.Selection([
        ('nfe40_PISAliq', 'PISAliq'),
        ('nfe40_PISQtde', 'PISQtde'),
        ('nfe40_PISNT', 'PISNT'),
        ('nfe40_PISOutr', 'PISOutr')],
        "PISAliq/PISQtde/PISNT/PISOutr")
    nfe40_PISAliq = fields.Many2one(
        "nfe.40.pisaliq",
        choice='12',
        string="Código de Situação Tributária do PIS",
        xsd=True,
        xsd_required=True,
        help="Código de Situação Tributária do PIS."
        "\n01 – Operação Tributável - Base de Cálculo = Valor da Operação"
        "\nAlíquota Normal (Cumulativo/Não Cumulativo);"
        "\n02 - Operação Tributável - Base de Calculo = Valor da Operação"
        "\n(Alíquota Diferenciada);")
    nfe40_PISQtde = fields.Many2one(
        "nfe.40.pisqtde",
        choice='12',
        string="Código de Situação Tributária do PIS",
        xsd=True,
        xsd_required=True,
        help="Código de Situação Tributária do PIS."
        "\n03 - Operação Tributável - Base de Calculo = Quantidade Vendida x"
        "\nAlíquota por Unidade de Produto;")
    nfe40_PISNT = fields.Many2one(
        "nfe.40.pisnt",
        choice='12',
        string="Código de Situação Tributária do PIS",
        xsd=True,
        xsd_required=True,
        help="Código de Situação Tributária do PIS."
        "\n04 - Operação Tributável - Tributação Monofásica - (Alíquota Zero);"
        "\n06 - Operação Tributável - Alíquota Zero;"
        "\n07 - Operação Isenta da contribuição;"
        "\n08 - Operação Sem Incidência da contribuição;"
        "\n09 - Operação com suspensão da contribuição;")
    nfe40_PISOutr = fields.Many2one(
        "nfe.40.pisoutr",
        choice='12',
        string="Código de Situação Tributária do PIS",
        xsd=True,
        xsd_required=True,
        help="Código de Situação Tributária do PIS."
        "\n99 - Outras Operações.")


class TConsReciNFe(models.AbstractModel):
    """Tipo Pedido de Consulta do Recido do Lote de Notas Fiscais
    Eletrônicas"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.tconsrecinfe'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'TConsReciNFe'
    _concrete_rec_name = 'nfe40_versao'

    nfe40_versao = fields.Char(
        string="versao", xsd=True, xsd_required=True)
    nfe40_tpAmb = fields.Selection(
        TAMB,
        string="Identificação do Ambiente",
        xsd=True,
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    nfe40_nRec = fields.Char(
        string="Número do Recibo", xsd=True, xsd_required=True)


class TEnderEmi(models.AbstractModel):
    """Tipo Dados do Endereço do Emitente // 24/10/08 - desmembrado / tamanho
    mínimo"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.tenderemi'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'TEnderEmi'
    _concrete_rec_name = 'nfe40_xLgr'

    nfe40_xLgr = fields.Char(
        string="Logradouro", xsd=True, xsd_required=True)
    nfe40_nro = fields.Char(
        string="Número", xsd=True, xsd_required=True)
    nfe40_xCpl = fields.Char(
        string="Complemento",
        xsd=True)
    nfe40_xBairro = fields.Char(
        string="Bairro", xsd=True, xsd_required=True)
    nfe40_cMun = fields.Char(
        string="Código do município", xsd=True, xsd_required=True)
    nfe40_xMun = fields.Char(
        string="Nome do município", xsd=True, xsd_required=True)
    nfe40_UF = fields.Selection(
        TUFEMI,
        string="Sigla da UF", xsd=True, xsd_required=True)
    nfe40_CEP = fields.Char(
        string="CEP - NT 2011/004", xsd=True, xsd_required=True)
    nfe40_cPais = fields.Selection(
        CPAIS_TENDEREMI,
        string="Código do país",
        xsd=True)
    nfe40_xPais = fields.Selection(
        XPAIS_TENDEREMI,
        string="Nome do país",
        xsd=True)
    nfe40_fone = fields.Char(
        string="Preencher com Código DDD + número do telefone",
        xsd=True,
        help="Preencher com Código DDD + número do telefone (v.2.0)")


class TEndereco(models.AbstractModel):
    "Tipo Dados do Endereço // 24/10/08 - tamanho mínimo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.tendereco'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'TEndereco'
    _concrete_rec_name = 'nfe40_xLgr'

    nfe40_xLgr = fields.Char(
        string="Logradouro", xsd=True, xsd_required=True)
    nfe40_nro = fields.Char(
        string="Número", xsd=True, xsd_required=True)
    nfe40_xCpl = fields.Char(
        string="Complemento",
        xsd=True)
    nfe40_xBairro = fields.Char(
        string="Bairro", xsd=True, xsd_required=True)
    nfe40_cMun = fields.Char(
        string="Código do município", xsd=True, xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE), informar"
        "\n9999999 para operações com o exterior.")
    nfe40_xMun = fields.Char(
        string="Nome do município", xsd=True, xsd_required=True,
        help="Nome do município, informar EXTERIOR para operações com o"
        "\nexterior.")
    nfe40_UF = fields.Selection(
        TUF,
        string="Sigla da UF", xsd=True, xsd_required=True,
        help="Sigla da UF, informar EX para operações com o exterior.")
    nfe40_CEP = fields.Char(
        string="CEP",
        xsd=True)
    nfe40_cPais = fields.Char(
        string="Código de Pais",
        xsd=True)
    nfe40_xPais = fields.Char(
        string="Nome do país",
        xsd=True)
    nfe40_fone = fields.Char(
        string="Telefone",
        xsd=True,
        help="Telefone, preencher com Código DDD + número do telefone , nas"
        "\noperações com exterior é permtido informar o código"
        "\ndo país + código da localidade + número do telefone")


class TEnviNFe(models.AbstractModel):
    "Tipo Pedido de Concessão de Autorização da Nota Fiscal Eletrônica"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.tenvinfe'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'TEnviNFe'
    _concrete_rec_name = 'nfe40_versao'

    nfe40_versao = fields.Char(
        string="versao", xsd=True, xsd_required=True)
    nfe40_idLote = fields.Char(
        string="idLote", xsd=True, xsd_required=True)
    nfe40_indSinc = fields.Selection(
        INDSINC_TENVINFE,
        string="Indicador de processamento síncrono",
        xsd=True,
        xsd_required=True,
        help="Indicador de processamento síncrono. 0=NÃO; 1=SIM=Síncrono")
    nfe40_NFe = fields.One2many(
        "nfe.40.tnfe",
        "nfe40_NFe_TEnviNFe_id",
        string="NFe", xsd=True, xsd_required=True
    )


class TInfRespTec(models.AbstractModel):
    """Grupo de informações do responsável técnico pelo sistema de emissão de
    DF-e"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.tinfresptec'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'TInfRespTec'
    _concrete_rec_name = 'nfe40_CNPJ'

    nfe40_CNPJ = fields.Char(
        string="CNPJ", xsd=True, xsd_required=True)
    nfe40_xContato = fields.Char(
        string="xContato", xsd=True, xsd_required=True,
        help="Informar o nome da pessoa a ser contatada na empresa"
        "\ndesenvolvedora do sistema utilizado na emissão do"
        "\ndocumento fiscal eletrônico.")
    nfe40_email = fields.Char(
        string="Informar o e", xsd=True, xsd_required=True,
        help="Informar o e-mail da pessoa a ser contatada na empresa"
        "\ndesenvolvedora do sistema.")
    nfe40_fone = fields.Char(
        string="fone", xsd=True, xsd_required=True,
        help="Informar o telefone da pessoa a ser contatada na empresa"
        "\ndesenvolvedora do sistema. Preencher com o Código DDD"
        "\n+ número do telefone.")
    nfe40_idCSRT = fields.Char(
        string="Identificador do CSRT utilizado para montar o hash do CSRT",
        xsd=True)
    nfe40_hashCSRT = fields.Char(
        string="O hashCSRT é o resultado da função hash",
        xsd=True,
        help="O hashCSRT é o resultado da função hash (SHA-1 – Base64) do"
        "\nCSRT fornecido pelo fisco mais a Chave de Acesso da"
        "\nNFe.")


class TIpi(models.AbstractModel):
    "Tipo: Dados do IPI"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.tipi'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'TIpi'
    _concrete_rec_name = 'nfe40_CNPJProd'

    nfe40_choice3 = fields.Selection([
        ('nfe40_IPITrib', 'IPITrib'),
        ('nfe40_IPINT', 'IPINT')],
        "IPITrib/IPINT")
    nfe40_CNPJProd = fields.Char(
        string="CNPJ do produtor da mercadoria",
        xsd=True,
        help="CNPJ do produtor da mercadoria, quando diferente do emitente."
        "\nSomente para os casos de exportação direta ou"
        "\nindireta.")
    nfe40_cSelo = fields.Char(
        string="Código do selo de controle do IPI",
        xsd=True)
    nfe40_qSelo = fields.Char(
        string="Quantidade de selo de controle do IPI",
        xsd=True)
    nfe40_cEnq = fields.Char(
        string="Código de Enquadramento Legal do IPI",
        xsd=True,
        xsd_required=True,
        help="Código de Enquadramento Legal do IPI (tabela a ser criada"
        "\npela RFB)")
    nfe40_IPITrib = fields.Many2one(
        "nfe.40.ipitrib",
        choice='3',
        string="IPITrib", xsd=True, xsd_required=True)
    nfe40_IPINT = fields.Many2one(
        "nfe.40.ipint",
        choice='3',
        string="IPINT", xsd=True, xsd_required=True)


class TLocal(models.AbstractModel):
    """Tipo Dados do Local de Retirada ou Entrega // 24/10/08 - tamanho mínimo
    // v2.0"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.tlocal'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'TLocal'
    _concrete_rec_name = 'nfe40_CNPJ'

    nfe40_choice2 = fields.Selection([
        ('nfe40_CNPJ', 'CNPJ'),
        ('nfe40_CPF', 'CPF')],
        "CNPJ/CPF")
    nfe40_CNPJ = fields.Char(
        choice='2',
        string="CNPJ", xsd=True, xsd_required=True)
    nfe40_CPF = fields.Char(
        choice='2',
        string="CPF (v2.0)", xsd=True, xsd_required=True)
    nfe40_xNome = fields.Char(
        string="Razão Social ou Nome do Expedidor/Recebedor",
        xsd=True)
    nfe40_xLgr = fields.Char(
        string="Logradouro", xsd=True, xsd_required=True)
    nfe40_nro = fields.Char(
        string="Número", xsd=True, xsd_required=True)
    nfe40_xCpl = fields.Char(
        string="Complemento",
        xsd=True)
    nfe40_xBairro = fields.Char(
        string="Bairro", xsd=True, xsd_required=True)
    nfe40_cMun = fields.Char(
        string="Código do município", xsd=True, xsd_required=True,
        help="Código do município (utilizar a tabela do IBGE)")
    nfe40_xMun = fields.Char(
        string="Nome do município", xsd=True, xsd_required=True)
    nfe40_UF = fields.Selection(
        TUF,
        string="Sigla da UF", xsd=True, xsd_required=True)
    nfe40_CEP = fields.Char(
        string="CEP",
        xsd=True)
    nfe40_cPais = fields.Char(
        string="Código de Pais",
        xsd=True)
    nfe40_xPais = fields.Char(
        string="Nome do país",
        xsd=True)
    nfe40_fone = fields.Char(
        string="Telefone",
        xsd=True,
        help="Telefone, preencher com Código DDD + número do telefone , nas"
        "\noperações com exterior é permtido informar o código"
        "\ndo país + código da localidade + número do telefone")
    nfe40_email = fields.Char(
        string="Informar o e",
        xsd=True,
        help="Informar o e-mail do expedidor/Recebedor. O campo pode ser"
        "\nutilizado para informar o e-mail de recepção da NF-e"
        "\nindicada pelo expedidor")
    nfe40_IE = fields.Char(
        string="Inscrição Estadual (v2.0)",
        xsd=True)


class TNFe(models.AbstractModel):
    "Tipo Nota Fiscal Eletrônica"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.tnfe'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'TNFe'
    _concrete_rec_name = 'nfe40_infNFe'

    nfe40_NFe_TEnviNFe_id = fields.Many2one(
        "nfe.40.tenvinfe")
    nfe40_infNFe = fields.Many2one(
        "nfe.40.infnfe",
        string="Informações da Nota Fiscal eletrônica",
        xsd=True,
        xsd_required=True)
    nfe40_infNFeSupl = fields.Many2one(
        "nfe.40.infnfesupl",
        string="Informações suplementares Nota Fiscal",
        xsd=True)


class TNfeProc(models.AbstractModel):
    "Tipo da NF-e processada"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.tnfeproc'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'TNfeProc'
    _concrete_rec_name = 'nfe40_versao'

    nfe40_versao = fields.Char(
        string="versao", xsd=True, xsd_required=True)
    nfe40_NFe = fields.Many2one(
        "nfe.40.tnfe",
        string="NFe", xsd=True, xsd_required=True)
    nfe40_protNFe = fields.Many2one(
        "nfe.40.tprotnfe",
        string="protNFe", xsd=True, xsd_required=True)


class TProtNFe(models.AbstractModel):
    "Tipo Protocolo de status resultado do processamento da NF-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.tprotnfe'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'TProtNFe'
    _concrete_rec_name = 'nfe40_versao'

    nfe40_protNFe_TRetConsReciNFe_id = fields.Many2one(
        "nfe.40.tretconsrecinfe")
    nfe40_versao = fields.Char(
        string="versao", xsd=True, xsd_required=True)
    nfe40_infProt = fields.Many2one(
        "nfe.40.infprot",
        string="Dados do protocolo de status",
        xsd=True,
        xsd_required=True)


class TRetConsReciNFe(models.AbstractModel):
    """Tipo Retorno do Pedido de Consulta do Recido do Lote de Notas Fiscais
    Eletrônicas"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.tretconsrecinfe'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'TRetConsReciNFe'
    _concrete_rec_name = 'nfe40_versao'

    nfe40_versao = fields.Char(
        string="versao", xsd=True, xsd_required=True)
    nfe40_tpAmb = fields.Selection(
        TAMB,
        string="Identificação do Ambiente",
        xsd=True,
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    nfe40_verAplic = fields.Char(
        string="Versão do Aplicativo que processou a NF",
        xsd=True,
        xsd_required=True,
        help="Versão do Aplicativo que processou a NF-e")
    nfe40_nRec = fields.Char(
        string="Número do Recibo Consultado",
        xsd=True,
        xsd_required=True)
    nfe40_cStat = fields.Char(
        string="Código do status da mensagem enviada",
        xsd=True,
        xsd_required=True)
    nfe40_xMotivo = fields.Char(
        string="Descrição literal do status do serviço solicitado",
        xsd=True,
        xsd_required=True)
    nfe40_cUF = fields.Selection(
        TCODUFIBGE,
        string="código da UF de atendimento",
        xsd=True,
        xsd_required=True)
    nfe40_dhRecbto = fields.Datetime(
        string="Data e hora de processamento",
        xsd=True,
        xsd_required=True,
        help="Data e hora de processamento, no formato AAAA-MM-"
        "\nDDTHH:MM:SSTZD. Em caso de Rejeição, com data e hora"
        "\ndo recebimento do Lote de NF-e enviado.")
    nfe40_cMsg = fields.Char(
        string="Código da Mensagem (v2.0)",
        xsd=True,
        help="Código da Mensagem (v2.0)"
        "\nalterado para tamanho variavel 1-4. (NT2011/004)")
    nfe40_xMsg = fields.Char(
        string="Mensagem da SEFAZ para o emissor",
        xsd=True,
        help="Mensagem da SEFAZ para o emissor. (v2.0)")
    nfe40_protNFe = fields.One2many(
        "nfe.40.tprotnfe",
        "nfe40_protNFe_TRetConsReciNFe_id",
        string="Protocolo de status resultado do processamento da NF",
        xsd=True,
        help="Protocolo de status resultado do processamento da NF-e"
    )


class TRetEnviNFe(models.AbstractModel):
    "Tipo Retorno do Pedido de Autorização da Nota Fiscal Eletrônica"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.tretenvinfe'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'TRetEnviNFe'
    _concrete_rec_name = 'nfe40_versao'

    nfe40_choice1 = fields.Selection([
        ('nfe40_infRec', 'infRec'),
        ('nfe40_protNFe', 'protNFe')],
        "infRec/protNFe")
    nfe40_versao = fields.Char(
        string="versao", xsd=True, xsd_required=True)
    nfe40_tpAmb = fields.Selection(
        TAMB,
        string="Identificação do Ambiente",
        xsd=True,
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    nfe40_verAplic = fields.Char(
        string="Versão do Aplicativo que recebeu o Lote",
        xsd=True,
        xsd_required=True)
    nfe40_cStat = fields.Char(
        string="Código do status da mensagem enviada",
        xsd=True,
        xsd_required=True)
    nfe40_xMotivo = fields.Char(
        string="Descrição literal do status do serviço solicitado",
        xsd=True,
        xsd_required=True)
    nfe40_cUF = fields.Selection(
        TCODUFIBGE,
        string="código da UF de atendimento",
        xsd=True,
        xsd_required=True)
    nfe40_dhRecbto = fields.Datetime(
        string="Data e hora do recebimento",
        xsd=True,
        xsd_required=True,
        help="Data e hora do recebimento, no formato AAAA-MM-DDTHH:MM:SSTZD")
    nfe40_infRec = fields.Many2one(
        "nfe.40.infrec",
        choice='1',
        string="Dados do Recibo do Lote",
        xsd=True)
    nfe40_protNFe = fields.Many2one(
        "nfe.40.tprotnfe",
        choice='1',
        string="protNFe",
        xsd=True,
        help="Protocolo de status resultado do processamento sincrono da"
        "\nNFC-e")


class TVeiculo(models.AbstractModel):
    "Tipo Dados do Veículo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.tveiculo'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'TVeiculo'
    _concrete_rec_name = 'nfe40_placa'

    nfe40_reboque_transp_id = fields.Many2one(
        "nfe.40.transp")
    nfe40_placa = fields.Char(
        string="Placa do veículo (NT2011/004)",
        xsd=True,
        xsd_required=True)
    nfe40_UF = fields.Selection(
        TUF,
        string="Sigla da UF", xsd=True, xsd_required=True)
    nfe40_RNTC = fields.Char(
        string="Registro Nacional de Transportador de Carga",
        xsd=True,
        help="Registro Nacional de Transportador de Carga (ANTT)")


class Adi(models.AbstractModel):
    "Adições (NT 2011/004)"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.adi'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'adiType'
    _concrete_rec_name = 'nfe40_nAdicao'

    nfe40_adi_DI_id = fields.Many2one(
        "nfe.40.di")
    nfe40_nAdicao = fields.Char(
        string="Número da Adição", xsd=True, xsd_required=True)
    nfe40_nSeqAdic = fields.Char(
        string="Número seqüencial do item dentro da Adição",
        xsd=True,
        xsd_required=True)
    nfe40_cFabricante = fields.Char(
        string="Código do fabricante estrangeiro",
        xsd=True,
        xsd_required=True,
        help="Código do fabricante estrangeiro (usado nos sistemas internos"
        "\nde informação do emitente da NF-e)")
    nfe40_vDescDI = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do desconto do item da DI – adição",
        xsd=True)
    nfe40_nDraw = fields.Char(
        string="Número do ato concessório de Drawback",
        xsd=True)


class Arma(models.AbstractModel):
    "Armamentos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.arma'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'armaType'
    _concrete_rec_name = 'nfe40_tpArma'

    nfe40_arma_prod_id = fields.Many2one(
        "nfe.40.prod")
    nfe40_tpArma = fields.Selection(
        TPARMA_ARMA,
        string="Indicador do tipo de arma de fogo",
        xsd=True,
        xsd_required=True,
        help="Indicador do tipo de arma de fogo (0 - Uso permitido; 1 - Uso"
        "\nrestrito)")
    nfe40_nSerie = fields.Char(
        string="Número de série da arma",
        xsd=True,
        xsd_required=True)
    nfe40_nCano = fields.Char(
        string="Número de série do cano",
        xsd=True,
        xsd_required=True)
    nfe40_descr = fields.Char(
        string="Descrição completa da arma",
        xsd=True,
        xsd_required=True,
        help="Descrição completa da arma, compreendendo: calibre, marca,"
        "\ncapacidade, tipo de funcionamento, comprimento e"
        "\ndemais elementos que permitam a sua perfeita"
        "\nidentificação.")


class AutXML(models.AbstractModel):
    "Pessoas autorizadas para o download do XML da NF-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.autxml'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'autXMLType'
    _concrete_rec_name = 'nfe40_CNPJ'

    nfe40_autXML_infNFe_id = fields.Many2one(
        "nfe.40.infnfe")
    nfe40_choice8 = fields.Selection([
        ('nfe40_CNPJ', 'CNPJ'),
        ('nfe40_CPF', 'CPF')],
        "CNPJ/CPF")
    nfe40_CNPJ = fields.Char(
        choice='8',
        string="CNPJ Autorizado", xsd=True, xsd_required=True)
    nfe40_CPF = fields.Char(
        choice='8',
        string="CPF Autorizado", xsd=True, xsd_required=True)


class Avulsa(models.AbstractModel):
    "Emissão de avulsa, informar os dados do Fisco emitente"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.avulsa'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'avulsaType'
    _concrete_rec_name = 'nfe40_CNPJ'

    nfe40_CNPJ = fields.Char(
        string="CNPJ do Órgão emissor",
        xsd=True,
        xsd_required=True)
    nfe40_xOrgao = fields.Char(
        string="Órgão emitente", xsd=True, xsd_required=True)
    nfe40_matr = fields.Char(
        string="Matrícula do agente", xsd=True, xsd_required=True)
    nfe40_xAgente = fields.Char(
        string="Nome do agente", xsd=True, xsd_required=True)
    nfe40_fone = fields.Char(
        string="Telefone",
        xsd=True)
    nfe40_UF = fields.Selection(
        TUFEMI,
        string="Sigla da Unidade da Federação",
        xsd=True,
        xsd_required=True)
    nfe40_nDAR = fields.Char(
        string="Número do Documento de Arrecadação de Receita",
        xsd=True)
    nfe40_dEmi = fields.Date(
        string="Data de emissão do DAR (AAAA-MM-DD)",
        xsd=True)
    nfe40_vDAR = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total constante no DAR",
        xsd=True)
    nfe40_repEmi = fields.Char(
        string="Repartição Fiscal emitente",
        xsd=True,
        xsd_required=True)
    nfe40_dPag = fields.Date(
        string="Data de pagamento do DAR",
        xsd=True,
        help="Data de pagamento do DAR (AAAA-MM-DD)")


class Cana(models.AbstractModel):
    "Informações de registro aquisições de cana"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.cana'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'canaType'
    _concrete_rec_name = 'nfe40_safra'

    nfe40_safra = fields.Char(
        string="Identificação da safra",
        xsd=True,
        xsd_required=True)
    nfe40_ref = fields.Char(
        string="Mês e Ano de Referência",
        xsd=True,
        xsd_required=True,
        help="Mês e Ano de Referência, formato: MM/AAAA")
    nfe40_forDia = fields.One2many(
        "nfe.40.fordia",
        "nfe40_forDia_cana_id",
        string="Fornecimentos diários",
        xsd=True,
        xsd_required=True
    )
    nfe40_qTotMes = fields.Monetary(currency_field="brl_currency_id",
        digits=0, string="Total do mês", xsd=True, xsd_required=True)
    nfe40_qTotAnt = fields.Monetary(currency_field="brl_currency_id",
        digits=0, string="Total Anterior", xsd=True, xsd_required=True)
    nfe40_qTotGer = fields.Monetary(currency_field="brl_currency_id",
        digits=0, string="Total Geral", xsd=True, xsd_required=True)
    nfe40_deduc = fields.One2many(
        "nfe.40.deduc",
        "nfe40_deduc_cana_id",
        string="Deduções - Taxas e Contribuições",
        xsd=True
    )
    nfe40_vFor = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor dos fornecimentos",
        xsd=True,
        xsd_required=True,
        help="Valor dos fornecimentos")
    nfe40_vTotDed = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total das Deduções",
        xsd=True,
        xsd_required=True)
    nfe40_vLiqFor = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Líquido dos fornecimentos",
        xsd=True,
        xsd_required=True)


class Card(models.AbstractModel):
    "Grupo de Cartões"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.card'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'cardType'
    _concrete_rec_name = 'nfe40_tpIntegra'

    nfe40_tpIntegra = fields.Selection(
        TPINTEGRA_CARD,
        string="tpIntegra", xsd=True, xsd_required=True,
        help="Tipo de Integração do processo de pagamento com o sistema de"
        "\nautomação da empresa/")
    nfe40_CNPJ = fields.Char(
        string="CNPJ da credenciadora de cartão de crédito/débito",
        xsd=True)
    nfe40_tBand = fields.Selection(
        TBAND_CARD,
        string="tBand",
        xsd=True,
        help="Bandeira da operadora de cartão de crédito/débito:01–Visa;"
        "\n02–Mastercard; 03–American Express;"
        "\n04–Sorocred;05-Diners"
        "\nClub;06-Elo;07-Hipercard;08-Aura;09-Cabal;99–Outros")
    nfe40_cAut = fields.Char(
        string="Número de autorização da operação cartão de crédito/débito",
        xsd=True)


class Cobr(models.AbstractModel):
    "Dados da cobrança da NF-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.cobr'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'cobrType'
    _concrete_rec_name = 'nfe40_fat'

    nfe40_fat = fields.Many2one(
        "nfe.40.fat",
        string="Dados da fatura",
        xsd=True)
    nfe40_dup = fields.One2many(
        "nfe.40.dup",
        "nfe40_dup_cobr_id",
        string="Dados das duplicatas NT 2011/004",
        xsd=True
    )


class Comb(models.AbstractModel):
    "Informar apenas para operações com combustíveis líquidos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.comb'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'combType'
    _concrete_rec_name = 'nfe40_cProdANP'

    nfe40_cProdANP = fields.Char(
        string="Código de produto da ANP",
        xsd=True,
        xsd_required=True,
        help="Código de produto da ANP. codificação de produtos do SIMP"
        "\n(http://www.anp.gov.br)")
    nfe40_descANP = fields.Char(
        string="Descrição do Produto conforme ANP",
        xsd=True,
        xsd_required=True,
        help="Descrição do Produto conforme ANP. Utilizar a descrição de"
        "\nprodutos do Sistema de Informações de Movimentação de"
        "\nProdutos - SIMP (http://www.anp.gov.br/simp/).")
    nfe40_pGLP = fields.Monetary(currency_field="brl_currency_id",
        digits=2,
        string="Percentual do GLP derivado do petróleo no produto GLP",
        xsd=True,
        help="Percentual do GLP derivado do petróleo no produto GLP"
        "\n(cProdANP=210203001). Informar em número decimal o"
        "\npercentual do GLP derivado de petróleo no produto"
        "\nGLP. Valores 0 a 100.")
    nfe40_pGNn = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de gás natural nacional",
        xsd=True,
        help="Percentual de gás natural nacional - GLGNn para o produto GLP"
        "\n(cProdANP=210203001). Informar em número decimal o"
        "\npercentual do Gás Natural Nacional - GLGNn para o"
        "\nproduto GLP. Valores de 0 a 100.")
    nfe40_pGNi = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="pGNi",
        xsd=True,
        help="Percentual de gás natural importado GLGNi para o produto GLP"
        "\n(cProdANP=210203001). Informar em número deciaml o"
        "\npercentual do Gás Natural Importado - GLGNi para o"
        "\nproduto GLP. Valores de 0 a 100.")
    nfe40_vPart = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor de partida",
        xsd=True,
        help="Valor de partida (cProdANP=210203001). Deve ser informado"
        "\nneste campo o valor por quilograma sem ICMS.")
    nfe40_CODIF = fields.Char(
        string="Código de autorização / registro do CODIF",
        xsd=True,
        help="Código de autorização / registro do CODIF. Informar apenas"
        "\nquando a UF utilizar o CODIF (Sistema de Controle do"
        "\nDiferimento do Imposto nas Operações com AEAC -"
        "\nÁlcool Etílico Anidro Combustível).")
    nfe40_qTemp = fields.Monetary(currency_field="brl_currency_id",
        digits=4, string="Quantidade de combustível",
        xsd=True,
        help="Quantidade de combustível"
        "\nfaturada à temperatura ambiente."
        "\nInformar quando a quantidade"
        "\nfaturada informada no campo"
        "\nqCom (I10) tiver sido ajustada para"
        "\numa temperatura diferente da"
        "\nambiente.")
    nfe40_UFCons = fields.Selection(
        TUF,
        string="Sigla da UF de Consumo",
        xsd=True,
        xsd_required=True)
    nfe40_CIDE = fields.Many2one(
        "nfe.40.cide",
        string="CIDE Combustíveis",
        xsd=True)
    nfe40_encerrante = fields.Many2one(
        "nfe.40.encerrante",
        string="Informações do grupo de 'encerrante'",
        xsd=True,
        help="Informações do grupo de 'encerrante'")


class Compra(models.AbstractModel):
    "Informações de compras (Nota de Empenho, Pedido e Contrato)"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.compra'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'compraType'
    _concrete_rec_name = 'nfe40_xNEmp'

    nfe40_xNEmp = fields.Char(
        string="Informação da Nota de Empenho de compras públicas",
        xsd=True,
        help="Informação da Nota de Empenho de compras públicas"
        "\n(NT2011/004)")
    nfe40_xPed = fields.Char(
        string="Informação do pedido",
        xsd=True)
    nfe40_xCont = fields.Char(
        string="Informação do contrato",
        xsd=True)


class Deduc(models.AbstractModel):
    "Deduções - Taxas e Contribuições"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.deduc'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'deducType'
    _concrete_rec_name = 'nfe40_xDed'

    nfe40_deduc_cana_id = fields.Many2one(
        "nfe.40.cana")
    nfe40_xDed = fields.Char(
        string="Descrição da Dedução", xsd=True, xsd_required=True)
    nfe40_vDed = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="valor da dedução", xsd=True, xsd_required=True)


class Dest(models.AbstractModel):
    "Identificação do Destinatário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.dest'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'destType'
    _concrete_rec_name = 'nfe40_CNPJ'

    nfe40_choice7 = fields.Selection([
        ('nfe40_CNPJ', 'CNPJ'),
        ('nfe40_CPF', 'CPF'),
        ('nfe40_idEstrangeiro', 'idEstrangeiro')],
        "CNPJ/CPF/idEstrangeiro")
    nfe40_CNPJ = fields.Char(
        choice='7',
        string="Número do CNPJ", xsd=True, xsd_required=True)
    nfe40_CPF = fields.Char(
        choice='7',
        string="Número do CPF", xsd=True, xsd_required=True)
    nfe40_idEstrangeiro = fields.Char(
        choice='7',
        string="Identificador do destinatário",
        xsd=True,
        xsd_required=True,
        help="Identificador do destinatário, em caso de comprador"
        "\nestrangeiro")
    nfe40_xNome = fields.Char(
        string="Razão Social ou nome do destinatário",
        xsd=True)
    nfe40_enderDest = fields.Many2one(
        "nfe.40.tendereco",
        string="Dados do endereço",
        xsd=True)
    nfe40_indIEDest = fields.Selection(
        INDIEDEST_DEST,
        string="Indicador da IE do destinatário",
        xsd=True,
        xsd_required=True,
        help="Indicador da IE do destinatário:"
        "\n1 – Contribuinte ICMSpagamento à vista;"
        "\n2 – Contribuinte isento de inscrição;"
        "\n9 – Não Contribuinte")
    nfe40_IE = fields.Char(
        string="Inscrição Estadual",
        xsd=True,
        help="Inscrição Estadual (obrigatório nas operações com"
        "\ncontribuintes do ICMS)")
    nfe40_ISUF = fields.Char(
        string="Inscrição na SUFRAMA",
        xsd=True,
        help="Inscrição na SUFRAMA (Obrigatório nas operações com as áreas"
        "\ncom benefícios de incentivos fiscais sob controle da"
        "\nSUFRAMA) PL_005d - 11/08/09 - alterado para aceitar 8"
        "\nou 9 dígitos")
    nfe40_IM = fields.Char(
        string="Inscrição Municipal do tomador do serviço",
        xsd=True)
    nfe40_email = fields.Char(
        string="Informar o e-mail do destinatário",
        xsd=True,
        help="Informar o e-mail do destinatário. O campo pode ser utilizado"
        "\npara informar o e-mail"
        "\nde recepção da NF-e indicada pelo destinatário")


class DetExport(models.AbstractModel):
    "Detalhe da exportação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.detexport'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'detExportType'
    _concrete_rec_name = 'nfe40_nDraw'

    nfe40_detExport_prod_id = fields.Many2one(
        "nfe.40.prod")
    nfe40_nDraw = fields.Char(
        string="Número do ato concessório de Drawback",
        xsd=True)
    nfe40_exportInd = fields.Many2one(
        "nfe.40.exportind",
        string="Exportação indireta",
        xsd=True)


class DetPag(models.AbstractModel):
    "Grupo de detalhamento da forma de pagamento."
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.detpag'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'detPagType'
    _concrete_rec_name = 'nfe40_indPag'

    nfe40_detPag_pag_id = fields.Many2one(
        "nfe.40.pag")
    nfe40_indPag = fields.Selection(
        INDPAG_DETPAG,
        string="Indicador da Forma de Pagamento:0",
        xsd=True,
        help="Indicador da Forma de Pagamento"
        "\n0-Pagamento à Vista"
        "\n1-Pagamento à Prazo")
    nfe40_tPag = fields.Selection(
        TPAG_DETPAG,
        string="Forma de Pagamento:01",
        xsd=True,
        xsd_required=True,
        help="Forma de Pagamento:01-Dinheiro;02-Cheque;03-Cartão de"
        "\nCrédito;04-Cartão de Débito;05-Crédito Loja;10-Vale"
        "\nAlimentação;11-Vale Refeição;12-Vale Presente;13-Vale"
        "\nCombustível;14 - Duplicata Mercantil;15 - Boleto"
        "\nBancario;90 - Sem Pagamento;99 - Outros")
    nfe40_vPag = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do Pagamento", xsd=True, xsd_required=True,
        help="Valor do Pagamento. Esta tag poderá ser omitida quando a tag"
        "\ntPag=90 (Sem Pagamento), caso contrário deverá ser"
        "\npreenchida.")
    nfe40_card = fields.Many2one(
        "nfe.40.card",
        string="Grupo de Cartões",
        xsd=True)


class Det(models.AbstractModel):
    "Dados dos detalhes da NF-eNúmero do item do NF"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.det'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'detType'
    _concrete_rec_name = 'nfe40_nItem'

    nfe40_det_infNFe_id = fields.Many2one(
        "nfe.40.infnfe")
    nfe40_nItem = fields.Char(
        string="nItem", xsd=True, xsd_required=True)
    nfe40_prod = fields.Many2one(
        "nfe.40.prod",
        string="Dados dos produtos e serviços da NF",
        xsd=True,
        xsd_required=True,
        help="Dados dos produtos e serviços da NF-e")
    nfe40_imposto = fields.Many2one(
        "nfe.40.imposto",
        string="Tributos incidentes nos produtos ou serviços da NF",
        xsd=True,
        xsd_required=True,
        help="Tributos incidentes nos produtos ou serviços da NF-e")
    nfe40_impostoDevol = fields.Many2one(
        "nfe.40.impostodevol",
        string="impostoDevol",
        xsd=True)
    nfe40_infAdProd = fields.Char(
        string="Informações adicionais do produto",
        xsd=True,
        help="Informações adicionais do produto (norma referenciada,"
        "\ninformações complementares, etc)")


class Dup(models.AbstractModel):
    "Dados das duplicatas NT 2011/004"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.dup'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'dupType'
    _concrete_rec_name = 'nfe40_nDup'

    nfe40_dup_cobr_id = fields.Many2one(
        "nfe.40.cobr")
    nfe40_nDup = fields.Char(
        string="Número da duplicata",
        xsd=True)
    nfe40_dVenc = fields.Date(
        string="Data de vencimento da duplicata",
        xsd=True,
        help="Data de vencimento da duplicata (AAAA-MM-DD)")
    nfe40_vDup = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da duplicata", xsd=True, xsd_required=True)


class Emit(models.AbstractModel):
    """Identificação do emitenteGrupo de informações de interesse da
    Prefeitura"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.emit'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'emitType'
    _concrete_rec_name = 'nfe40_CNPJ'

    nfe40_choice6 = fields.Selection([
        ('nfe40_CNPJ', 'CNPJ'),
        ('nfe40_CPF', 'CPF')],
        "CNPJ/CPF")
    nfe40_CNPJ = fields.Char(
        choice='6',
        string="Número do CNPJ do emitente",
        xsd=True,
        xsd_required=True)
    nfe40_CPF = fields.Char(
        choice='6',
        string="Número do CPF do emitente",
        xsd=True,
        xsd_required=True)
    nfe40_xNome = fields.Char(
        string="Razão Social ou Nome do emitente",
        xsd=True,
        xsd_required=True)
    nfe40_xFant = fields.Char(
        string="Nome fantasia",
        xsd=True)
    nfe40_enderEmit = fields.Many2one(
        "nfe.40.tenderemi",
        string="Endereço do emitente",
        xsd=True,
        xsd_required=True)
    nfe40_IE = fields.Char(
        string="Inscrição Estadual do Emitente",
        xsd=True,
        xsd_required=True)
    nfe40_IEST = fields.Char(
        string="Inscricao Estadual do Substituto Tributário",
        xsd=True)
    nfe40_IM = fields.Char(
        string="Inscrição Municipal",
        xsd=True)
    nfe40_CNAE = fields.Char(
        string="CNAE Fiscal",
        xsd=True)
    nfe40_CRT = fields.Selection(
        CRT_EMIT,
        string="Código de Regime Tributário.",
        xsd=True,
        xsd_required=True,
        help="Código de Regime Tributário."
        "\nEste campo será obrigatoriamente preenchido com:")


class Encerrante(models.AbstractModel):
    """Informações do grupo de "encerrante" """
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.encerrante'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'encerranteType'
    _concrete_rec_name = 'nfe40_nBico'

    nfe40_nBico = fields.Char(
        string="Numero de identificação do Bico utilizado no abastecimento",
        xsd=True,
        xsd_required=True)
    nfe40_nBomba = fields.Char(
        string="nBomba",
        xsd=True,
        help="Numero de identificação da bomba ao qual o bico está"
        "\ninterligado")
    nfe40_nTanque = fields.Char(
        string="nTanque", xsd=True, xsd_required=True,
        help="Numero de identificação do tanque ao qual o bico está"
        "\ninterligado")
    nfe40_vEncIni = fields.Monetary(currency_field="brl_currency_id",
        digits=3, string="Valor do Encerrante no ínicio do abastecimento",
        xsd=True,
        xsd_required=True)
    nfe40_vEncFin = fields.Monetary(currency_field="brl_currency_id",
        digits=3, string="Valor do Encerrante no final do abastecimento",
        xsd=True,
        xsd_required=True)


class ExportInd(models.AbstractModel):
    "Exportação indireta"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.exportind'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'exportIndType'
    _concrete_rec_name = 'nfe40_nRE'

    nfe40_nRE = fields.Char(
        string="Registro de exportação",
        xsd=True,
        xsd_required=True)
    nfe40_chNFe = fields.Char(
        string="Chave de acesso da NF",
        xsd=True,
        xsd_required=True,
        help="Chave de acesso da NF-e recebida para exportação")
    nfe40_qExport = fields.Monetary(currency_field="brl_currency_id",
        digits=4, string="Quantidade do item efetivamente exportado",
        xsd=True,
        xsd_required=True)


class Exporta(models.AbstractModel):
    "Informações de exportação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.exporta'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'exportaType'
    _concrete_rec_name = 'nfe40_UFSaidaPais'

    nfe40_UFSaidaPais = fields.Selection(
        TUFEMI,
        string="Sigla da UF de Embarque ou de transposição de fronteira",
        xsd=True,
        xsd_required=True)
    nfe40_xLocExporta = fields.Char(
        string="Local de Embarque ou de transposição de fronteira",
        xsd=True,
        xsd_required=True)
    nfe40_xLocDespacho = fields.Char(
        string="Descrição do local de despacho",
        xsd=True)


class Fat(models.AbstractModel):
    "Dados da fatura"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.fat'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'fatType'
    _concrete_rec_name = 'nfe40_nFat'

    nfe40_nFat = fields.Char(
        string="Número da fatura",
        xsd=True)
    nfe40_vOrig = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor original da fatura",
        xsd=True)
    nfe40_vDesc = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do desconto da fatura",
        xsd=True)
    nfe40_vLiq = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor líquido da fatura",
        xsd=True)


class ForDia(models.AbstractModel):
    "Fornecimentos diáriosNúmero do dia"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.fordia'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'forDiaType'
    _concrete_rec_name = 'nfe40_dia'

    nfe40_forDia_cana_id = fields.Many2one(
        "nfe.40.cana")
    nfe40_dia = fields.Char(
        string="dia", xsd=True, xsd_required=True)
    nfe40_qtde = fields.Monetary(currency_field="brl_currency_id",
        digits=0, string="Quantidade em quilogramas",
        xsd=True,
        xsd_required=True,
        help="Quantidade em quilogramas - peso líquido")


class Ide(models.AbstractModel):
    """identificação da NF-eInformar apenas
    para tpEmis diferente de 1"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.ide'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'ideType'
    _concrete_rec_name = 'nfe40_cUF'

    nfe40_cUF = fields.Selection(
        TCODUFIBGE,
        string="Código da UF do emitente do Documento Fiscal",
        xsd=True,
        xsd_required=True,
        help="Código da UF do emitente do Documento Fiscal. Utilizar a"
        "\nTabela do IBGE.")
    nfe40_cNF = fields.Char(
        string="Código numérico que compõe a Chave de Acesso",
        xsd=True,
        xsd_required=True,
        help="Código numérico que compõe a Chave de Acesso. Número"
        "\naleatório gerado pelo emitente para cada NF-e.")
    nfe40_natOp = fields.Char(
        string="Descrição da Natureza da Operação",
        xsd=True,
        xsd_required=True)
    nfe40_mod = fields.Selection(
        TMOD_IDE,
        string="Código do modelo do Documento Fiscal",
        xsd=True,
        xsd_required=True,
        help="Código do modelo do Documento Fiscal. 55 = NF-e; 65 = NFC-e.")
    nfe40_serie = fields.Char(
        string="Série do Documento Fiscal",
        xsd=True,
        xsd_required=True,
        help="Série do Documento Fiscal"
        "\nsérie normal 0-889"
        "\nAvulsa Fisco 890-899"
        "\nSCAN 900-999")
    nfe40_nNF = fields.Char(
        string="Número do Documento Fiscal",
        xsd=True,
        xsd_required=True)
    nfe40_dhEmi = fields.Datetime(
        string="Data e Hora de emissão do Documento Fiscal",
        xsd=True,
        xsd_required=True,
        help="Data e Hora de emissão do Documento Fiscal (AAAA-MM-"
        "\nDDThh:mm:ssTZD) ex.: 2012-09-01T13:00:00-03:00")
    nfe40_dhSaiEnt = fields.Datetime(
        string="Data e Hora da saída ou de entrada da mercadoria / produto",
        xsd=True,
        help="Data e Hora da saída ou de entrada da mercadoria / produto"
        "\n(AAAA-MM-DDTHH:mm:ssTZD)")
    nfe40_tpNF = fields.Selection(
        TPNF_IDE,
        string="Tipo do Documento Fiscal",
        xsd=True,
        xsd_required=True,
        help="Tipo do Documento Fiscal (0 - entrada; 1 - saída)")
    nfe40_idDest = fields.Selection(
        IDDEST_IDE,
        string="Identificador de Local de destino da operação",
        xsd=True,
        xsd_required=True,
        help="Identificador de Local de destino da operação"
        "\n(1-Interna;2-Interestadual;3-Exterior)")
    nfe40_cMunFG = fields.Char(
        string="Código do Município de Ocorrência do Fato Gerador",
        xsd=True,
        xsd_required=True,
        help="Código do Município de Ocorrência do Fato Gerador (utilizar a"
        "\ntabela do IBGE)")
    nfe40_tpImp = fields.Selection(
        TPIMP_IDE,
        string="Formato de impressão do DANFE",
        xsd=True,
        xsd_required=True,
        help="Formato de impressão do DANFE (0-sem DANFE;1-DANFe Retrato;"
        "\n2-DANFe Paisagem;3-DANFe Simplificado;"
        "\n4-DANFe NFC-e;5-DANFe NFC-e em mensagem eletrônica)")
    nfe40_tpEmis = fields.Selection(
        TPEMIS_IDE,
        string="Forma de emissão da NF-e",
        xsd=True,
        xsd_required=True,
        help="Forma de emissão da NF-e"
        "\n1 - Normal;"
        "\n2 - Contingência FS"
        "\n3 - Contingência SCAN"
        "\n4 - Contingência DPEC"
        "\n5 - Contingência FSDA"
        "\n6 - Contingência SVC - AN"
        "\n7 - Contingência SVC - RS"
        "\n9 - Contingência off-line NFC-e")
    nfe40_cDV = fields.Char(
        string="Digito Verificador da Chave de Acesso da NF",
        xsd=True,
        xsd_required=True,
        help="Digito Verificador da Chave de Acesso da NF-e")
    nfe40_tpAmb = fields.Selection(
        TAMB,
        string="Identificação do Ambiente",
        xsd=True,
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    nfe40_finNFe = fields.Selection(
        TFINNFE_IDE,
        string="Finalidade da emissão da NF-e",
        xsd=True,
        xsd_required=True,
        help="Tipo Finalidade da NF-e (1=Normal; 2=Complementar; 3=Ajuste;"
        "\n4=Devolução/Retorno)")
    nfe40_indFinal = fields.Selection(
        INDFINAL_IDE,
        string="Indica operação com consumidor final",
        xsd=True,
        xsd_required=True,
        help="Indica operação com consumidor final (0-Não;1-Consumidor"
        "\nFinal)")
    nfe40_indPres = fields.Selection(
        INDPRES_IDE,
        string="indPres", xsd=True, xsd_required=True,
        help="Indicador de presença do comprador no estabelecimento"
        "\ncomercial no momento da oepração"
        "\n(0-Não se aplica (ex."
        "\nNota Fiscal complementar ou de ajuste"
        "\n1-Operação presencial"
        "\n2-Não presencial, internet"
        "\n3-Não presencial, teleatendimento"
        "\n4-NFC-e entrega em domicílio"
        "\n5-Operação presencial, fora do estabelecimento"
        "\n9-Não presencial, outros)")
    nfe40_procEmi = fields.Selection(
        TPROCEMI_IDE,
        string="Processo de emissão utilizado com a seguinte codificação",
        xsd=True,
        xsd_required=True,
        help="Processo de emissão utilizado com a seguinte codificação:"
        "\n0 - emissão de NF-e com aplicativo do contribuinte;"
        "\n1 - emissão de NF-e avulsa pelo Fisco;"
        "\n2 - emissão de NF-e avulsa, pelo contribuinte com seu certificado"
        "\ndigital, através do site"
        "\ndo Fisco;"
        "\n3- emissão de NF-e pelo contribuinte com aplicativo fornecido pelo"
        "\nFisco.")
    nfe40_verProc = fields.Char(
        string="versão do aplicativo utilizado no processo de",
        xsd=True,
        xsd_required=True,
        help="versão do aplicativo utilizado no processo de"
        "\nemissão")
    nfe40_dhCont = fields.Datetime(
        string="dhCont",
        xsd=True,
        help="Informar a data e hora de entrada em contingência"
        "\ncontingência no formato (AAAA-MM-DDThh:mm:ssTZD) ex.:"
        "\n2012-09-01T13:00:00-03:00.")
    nfe40_xJust = fields.Char(
        string="Informar a Justificativa da entrada",
        xsd=True)
    nfe40_NFref = fields.One2many(
        "nfe.40.nfref",
        "nfe40_NFref_ide_id",
        string="Grupo de infromações da NF referenciada",
        xsd=True
    )


class ImpostoDevol(models.AbstractModel):
    _description = 'impostodevol'
    _name = 'nfe.40.impostodevol'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'impostoDevolType'
    _concrete_rec_name = 'nfe40_pDevol'

    nfe40_pDevol = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Percentual de mercadoria devolvida",
        xsd=True,
        xsd_required=True)
    nfe40_IPI = fields.Many2one(
        "nfe.40.ipi",
        string="Informação de IPI devolvido",
        xsd=True,
        xsd_required=True)


class Imposto(models.AbstractModel):
    "Tributos incidentes nos produtos ou serviços da NF-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.imposto'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'impostoType'
    _concrete_rec_name = 'nfe40_vTotTrib'

    nfe40_choice10 = fields.Selection([
        ('nfe40_ICMS', 'ICMS'),
        ('nfe40_II', 'II'),
        ('nfe40_IPI', 'IPI'),
        ('nfe40_ISSQN', 'ISSQN')],
        "ICMS/II/IPI/ISSQN")
    nfe40_vTotTrib = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor estimado total de impostos federais",
        xsd=True,
        help="Valor estimado total de impostos federais, estaduais e"
        "\nmunicipais")
    nfe40_ICMS = fields.Many2one(
        "nfe.40.icms",
        choice='10',
        string="Dados do ICMS Normal e ST",
        xsd=True,
        xsd_required=True)
    nfe40_II = fields.Many2one(
        "nfe.40.ii",
        choice='10',
        string="Dados do Imposto de Importação",
        xsd=True)
    nfe40_IPI = fields.Many2one(
        "nfe.40.tipi",
        choice='10',
        string="IPI",
        xsd=True)
    nfe40_ISSQN = fields.Many2one(
        "nfe.40.issqn",
        choice='10',
        string="ISSQN", xsd=True, xsd_required=True)
    nfe40_PIS = fields.Many2one(
        "nfe.40.pis",
        string="Dados do PIS",
        xsd=True)
    nfe40_PISST = fields.Many2one(
        "nfe.40.pisst",
        string="Dados do PIS Substituição Tributária",
        xsd=True)
    nfe40_COFINS = fields.Many2one(
        "nfe.40.cofins",
        string="Dados do COFINS",
        xsd=True)
    nfe40_COFINSST = fields.Many2one(
        "nfe.40.cofinsst",
        string="Dados do COFINS da",
        xsd=True,
        help="Dados do COFINS da"
        "\nSubstituição Tributaria;")
    nfe40_ICMSUFDest = fields.Many2one(
        "nfe.40.icmsufdest",
        string="ICMSUFDest",
        xsd=True,
        help="Grupo a ser informado nas vendas interestarduais para"
        "\nconsumidor final, não contribuinte de ICMS")


class InfAdic(models.AbstractModel):
    "Informações adicionais da NF-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.infadic'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'infAdicType'
    _concrete_rec_name = 'nfe40_infAdFisco'

    nfe40_infAdFisco = fields.Char(
        string="Informações adicionais de interesse do Fisco",
        xsd=True,
        help="Informações adicionais de interesse do Fisco (v2.0)")
    nfe40_infCpl = fields.Char(
        string="Informações complementares de interesse do Contribuinte",
        xsd=True)
    nfe40_obsCont = fields.One2many(
        "nfe.40.obscont",
        "nfe40_obsCont_infAdic_id",
        string="Campo de uso livre do contribuinte",
        xsd=True,
        help="Campo de uso livre do contribuinte"
        "\ninformar o nome do campo no atributo xCampo"
        "\ne o conteúdo do campo no xTexto"
    )
    nfe40_obsFisco = fields.One2many(
        "nfe.40.obsfisco",
        "nfe40_obsFisco_infAdic_id",
        string="Campo de uso exclusivo do Fisco",
        xsd=True,
        help="Campo de uso exclusivo do Fisco"
        "\ninformar o nome do campo no atributo xCampo"
        "\ne o conteúdo do campo no xTexto"
    )
    nfe40_procRef = fields.One2many(
        "nfe.40.procref",
        "nfe40_procRef_infAdic_id",
        string="Grupo de informações do processo referenciado",
        xsd=True,
        help="Grupo de informações do processo referenciado"
    )


class InfNFeSupl(models.AbstractModel):
    "Informações suplementares Nota Fiscal"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.infnfesupl'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'infNFeSuplType'
    _concrete_rec_name = 'nfe40_qrCode'

    nfe40_qrCode = fields.Char(
        string="Texto com o QR", xsd=True, xsd_required=True,
        help="Texto com o QR-Code impresso no DANFE NFC-e")
    nfe40_urlChave = fields.Char(
        string="Informar a URL da 'Consulta por chave de acesso da NFC",
        xsd=True,
        xsd_required=True,
        help="Informar a URL da 'Consulta por chave de acesso da NFC-e'. A"
        "\nmesma URL que deve estar informada no DANFE NFC-e"
        "\npara consulta por chave de acesso.")


class InfNFe(models.AbstractModel):
    """Informações da Nota Fiscal eletrônicaVersão do leiaute (v4.00)PL_005d -
    11/08/09 - validação do Id"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.infnfe'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'infNFeType'
    _concrete_rec_name = 'nfe40_versao'

    nfe40_versao = fields.Char(
        string="versao", xsd=True, xsd_required=True)
    nfe40_Id = fields.Char(
        string="Id", xsd=True, xsd_required=True)
    nfe40_ide = fields.Many2one(
        "nfe.40.ide",
        string="identificação da NF-e", xsd=True, xsd_required=True)
    nfe40_emit = fields.Many2one(
        "nfe.40.emit",
        string="Identificação do emitente",
        xsd=True,
        xsd_required=True)
    nfe40_avulsa = fields.Many2one(
        "nfe.40.avulsa",
        string="Emissão de avulsa",
        xsd=True,
        help="Emissão de avulsa, informar os dados do Fisco emitente")
    nfe40_dest = fields.Many2one(
        "nfe.40.dest",
        string="Identificação do Destinatário",
        xsd=True)
    nfe40_retirada = fields.Many2one(
        "nfe.40.tlocal",
        string="Identificação do Local de Retirada",
        xsd=True,
        help="Identificação do Local de Retirada (informar apenas quando"
        "\nfor diferente do endereço do remetente)")
    nfe40_entrega = fields.Many2one(
        "nfe.40.tlocal",
        string="Identificação do Local de Entrega",
        xsd=True,
        help="Identificação do Local de Entrega (informar apenas quando for"
        "\ndiferente do endereço do destinatário)")
    nfe40_autXML = fields.One2many(
        "nfe.40.autxml",
        "nfe40_autXML_infNFe_id",
        string="Pessoas autorizadas para o download do XML da NF",
        xsd=True,
        help="Pessoas autorizadas para o download do XML da NF-e"
    )
    nfe40_det = fields.One2many(
        "nfe.40.det",
        "nfe40_det_infNFe_id",
        string="Dados dos detalhes da NF-e",
        xsd=True,
        xsd_required=True
    )
    nfe40_total = fields.Many2one(
        "nfe.40.total",
        string="Dados dos totais da NF-e",
        xsd=True,
        xsd_required=True)
    nfe40_transp = fields.Many2one(
        "nfe.40.transp",
        string="Dados dos transportes da NF-e",
        xsd=True,
        xsd_required=True)
    nfe40_cobr = fields.Many2one(
        "nfe.40.cobr",
        string="Dados da cobrança da NF-e",
        xsd=True)
    nfe40_pag = fields.Many2one(
        "nfe.40.pag",
        string="Dados de Pagamento", xsd=True, xsd_required=True,
        help="Dados de Pagamento. Obrigatório apenas para (NFC-e) NT"
        "\n2012/004")
    nfe40_infAdic = fields.Many2one(
        "nfe.40.infadic",
        string="Informações adicionais da NF-e",
        xsd=True)
    nfe40_exporta = fields.Many2one(
        "nfe.40.exporta",
        string="Informações de exportação",
        xsd=True)
    nfe40_compra = fields.Many2one(
        "nfe.40.compra",
        string="Informações de compras",
        xsd=True,
        help="Informações de compras (Nota de Empenho, Pedido e Contrato)")
    nfe40_cana = fields.Many2one(
        "nfe.40.cana",
        string="Informações de registro aquisições de cana",
        xsd=True)
    nfe40_infRespTec = fields.Many2one(
        "nfe.40.tinfresptec",
        string="Informações do Responsável Técnico pela emissão do DF",
        xsd=True,
        help="Informações do Responsável Técnico pela emissão do DF-e")


class InfProt(models.AbstractModel):
    "Dados do protocolo de status"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.infprot'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'infProtType'
    _concrete_rec_name = 'nfe40_Id'

    nfe40_Id = fields.Char(
        string="Id",
        xsd=True)
    nfe40_tpAmb = fields.Selection(
        TAMB,
        string="Identificação do Ambiente",
        xsd=True,
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    nfe40_verAplic = fields.Char(
        string="Versão do Aplicativo que processou a NF",
        xsd=True,
        xsd_required=True,
        help="Versão do Aplicativo que processou a NF-e")
    nfe40_chNFe = fields.Char(
        string="Chaves de acesso da NF-e",
        xsd=True,
        xsd_required=True,
        help="Chaves de acesso da NF-e, compostas por: UF do emitente, AAMM"
        "\nda emissão da NFe, CNPJ do emitente, modelo, série e"
        "\nnúmero da NF-e e código numérico+DV.")
    nfe40_dhRecbto = fields.Datetime(
        string="Data e hora de processamento",
        xsd=True,
        xsd_required=True,
        help="Data e hora de processamento, no formato AAAA-MM-"
        "\nDDTHH:MM:SSTZD. Deve ser preenchida com data e hora"
        "\nda gravação no Banco em caso de Confirmação. Em caso"
        "\nde Rejeição, com data e hora do recebimento do Lote"
        "\nde NF-e enviado.")
    nfe40_nProt = fields.Char(
        string="Número do Protocolo de Status da NF",
        xsd=True,
        help="Número do Protocolo de Status da NF-e. 1 posição (1 –"
        "\nSecretaria de Fazenda Estadual 2 – Receita Federal);"
        "\n2 - códiga da UF - 2 posições ano; 10 seqüencial no"
        "\nano.")
    nfe40_digVal = fields.Char(
        string="Digest Value da NF-e processada",
        xsd=True,
        help="Digest Value da NF-e processada. Utilizado para conferir a"
        "\nintegridade da NF-e original.")
    nfe40_cStat = fields.Char(
        string="Código do status da mensagem enviada",
        xsd=True,
        xsd_required=True)
    nfe40_xMotivo = fields.Char(
        string="Descrição literal do status do serviço solicitado",
        xsd=True,
        xsd_required=True)
    nfe40_cMsg = fields.Char(
        string="Código da Mensagem.",
        xsd=True)
    nfe40_xMsg = fields.Char(
        string="Mensagem da SEFAZ para o emissor.",
        xsd=True)


class InfRec(models.AbstractModel):
    "Dados do Recibo do Lote"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.infrec'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'infRecType'
    _concrete_rec_name = 'nfe40_nRec'

    nfe40_nRec = fields.Char(
        string="Número do Recibo", xsd=True, xsd_required=True)
    nfe40_tMed = fields.Char(
        string="Tempo médio de resposta do serviço",
        xsd=True,
        xsd_required=True,
        help="Tempo médio de resposta do serviço (em segundos) dos últimos"
        "\n5 minutos")


class Lacres(models.AbstractModel):
    _description = 'lacres'
    _name = 'nfe.40.lacres'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'lacresType'
    _concrete_rec_name = 'nfe40_nLacre'

    nfe40_lacres_vol_id = fields.Many2one(
        "nfe.40.vol")
    nfe40_nLacre = fields.Char(
        string="Número dos Lacres", xsd=True, xsd_required=True)


class Med(models.AbstractModel):
    """grupo do detalhamento de Medicamentos e de matérias-primas
    farmacêuticas"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.med'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'medType'
    _concrete_rec_name = 'nfe40_cProdANVISA'

    nfe40_cProdANVISA = fields.Char(
        string="cProdANVISA", xsd=True, xsd_required=True,
        help="Utilizar o número do registro ANVISA ou preencher com o"
        "\nliteral “ISENTO”, no caso de medicamento isento de"
        "\nregistro na ANVISA.")
    nfe40_xMotivoIsencao = fields.Char(
        string="Obs",
        xsd=True,
        help="Obs.: Para medicamento isento de registro na ANVISA, informar"
        "\no número da decisão que o isenta, como por exemplo o"
        "\nnúmero da Resolução da Diretoria Colegiada da ANVISA"
        "\n(RDC).")
    nfe40_vPMC = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Preço Máximo ao Consumidor.",
        xsd=True,
        xsd_required=True)


class ObsCont(models.AbstractModel):
    """Campo de uso livre do contribuinte
    informar o nome do campo no atributo xCampo
    e o conteúdo do campo no xTexto"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.obscont'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'obsContType'
    _concrete_rec_name = 'nfe40_xCampo'

    nfe40_obsCont_infAdic_id = fields.Many2one(
        "nfe.40.infadic")
    nfe40_xCampo = fields.Char(
        string="xCampo", xsd=True, xsd_required=True)
    nfe40_xTexto = fields.Char(
        string="xTexto", xsd=True, xsd_required=True)


class ObsFisco(models.AbstractModel):
    """Campo de uso exclusivo do Fisco
    informar o nome do campo no atributo xCampo
    e o conteúdo do campo no xTexto"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.obsfisco'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'obsFiscoType'
    _concrete_rec_name = 'nfe40_xCampo'

    nfe40_obsFisco_infAdic_id = fields.Many2one(
        "nfe.40.infadic")
    nfe40_xCampo = fields.Char(
        string="xCampo", xsd=True, xsd_required=True)
    nfe40_xTexto = fields.Char(
        string="xTexto", xsd=True, xsd_required=True)


class Pag(models.AbstractModel):
    "Dados de Pagamento. Obrigatório apenas para (NFC-e) NT 2012/004"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.pag'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'pagType'
    _concrete_rec_name = 'nfe40_detPag'

    nfe40_detPag = fields.One2many(
        "nfe.40.detpag",
        "nfe40_detPag_pag_id",
        string="Grupo de detalhamento da forma de pagamento",
        xsd=True,
        xsd_required=True
    )
    nfe40_vTroco = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do Troco.",
        xsd=True)


class ProcRef(models.AbstractModel):
    "Grupo de informações do processo referenciado"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.procref'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'procRefType'
    _concrete_rec_name = 'nfe40_nProc'

    nfe40_procRef_infAdic_id = fields.Many2one(
        "nfe.40.infadic")
    nfe40_nProc = fields.Char(
        string="Indentificador do processo ou ato",
        xsd=True,
        xsd_required=True,
        help="Indentificador do processo ou ato"
        "\nconcessório")
    nfe40_indProc = fields.Selection(
        INDPROC_PROCREF,
        string="Origem do processo, informar com",
        xsd=True,
        xsd_required=True,
        help="Origem do processo, informar com:"
        "\n0 - SEFAZ;"
        "\n1 - Justiça Federal;"
        "\n2 - Justiça Estadual;"
        "\n3 - Secex/RFB;"
        "\n9 - Outros")


class Prod(models.AbstractModel):
    """Dados dos produtos e serviços da NF-eInformações específicas de produtos
    e serviços"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.prod'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'prodType'
    _concrete_rec_name = 'nfe40_cProd'

    nfe40_choice9 = fields.Selection([
        ('nfe40_veicProd', 'veicProd'),
        ('nfe40_med', 'med'),
        ('nfe40_arma', 'arma'),
        ('nfe40_comb', 'comb'),
        ('nfe40_nRECOPI', 'nRECOPI')],
        "veicProd/med/arma/comb/nRECOPI")
    nfe40_cProd = fields.Char(
        string="Código do produto ou serviço",
        xsd=True,
        xsd_required=True,
        help="Código do produto ou serviço. Preencher com CFOP caso se"
        "\ntrate de itens não relacionados com"
        "\nmercadorias/produto e que o contribuinte não possua"
        "\ncodificação própria"
        "\nFormato ”CFOP9999”.")
    nfe40_cEAN = fields.Char(
        string="GTIN", xsd=True, xsd_required=True,
        help="GTIN (Global Trade Item Number) do produto, antigo código EAN"
        "\nou código de barras")
    nfe40_xProd = fields.Char(
        string="Descrição do produto ou serviço",
        xsd=True,
        xsd_required=True)
    nfe40_NCM = fields.Char(
        string="Código NCM (8 posições)",
        xsd=True,
        xsd_required=True,
        help="Código NCM (8 posições), será permitida a informação do"
        "\ngênero (posição do capítulo do NCM) quando a operação"
        "\nnão for de comércio exterior (importação/exportação)"
        "\nou o produto não seja tributado pelo IPI. Em caso de"
        "\nitem de serviço ou item que não tenham produto (Ex."
        "\ntransferência de crédito, crédito do ativo"
        "\nimobilizado, etc.), informar o código 00 (zeros)"
        "\n(v2.0)")
    nfe40_NVE = fields.Char(
        string="Nomenclatura de Valor aduaneio e Estatístico",
        xsd=True)
    nfe40_CEST = fields.Char(
        string="Codigo especificador da Substuicao Tributaria",
        xsd=True,
        help="Codigo especificador da Substuicao Tributaria - CEST, que"
        "\nidentifica a mercadoria sujeita aos regimes de"
        "\nsubstituicao tributária e de antecipação do"
        "\nrecolhimento do imposto")
    nfe40_indEscala = fields.Selection(
        INDESCALA_PROD,
        string="indEscala",
        xsd=True)
    nfe40_CNPJFab = fields.Char(
        string="CNPJ do Fabricante da Mercadoria",
        xsd=True,
        help="CNPJ do Fabricante da Mercadoria, obrigatório para produto em"
        "\nescala NÃO relevante.")
    nfe40_cBenef = fields.Char(
        string="cBenef",
        xsd=True)
    nfe40_EXTIPI = fields.Char(
        string="Código EX TIPI (3 posições)",
        xsd=True)
    nfe40_CFOP = fields.Char(
        string="Cfop", xsd=True, xsd_required=True)
    nfe40_uCom = fields.Char(
        string="Unidade comercial", xsd=True, xsd_required=True)
    nfe40_qCom = fields.Monetary(currency_field="brl_currency_id",
        digits=4, string="Quantidade Comercial do produto",
        xsd=True,
        xsd_required=True,
        help="Quantidade Comercial do produto, alterado para aceitar de 0 a"
        "\n4 casas decimais e 11 inteiros.")
    nfe40_vUnCom = fields.Monetary(currency_field="brl_currency_id",
        digits=0, string="Valor unitário de comercialização",
        xsd=True,
        xsd_required=True,
        help="Valor unitário de comercialização - alterado para aceitar 0 a"
        "\n10 casas decimais e 11 inteiros")
    nfe40_vProd = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor bruto do produto ou serviço.",
        xsd=True,
        xsd_required=True)
    nfe40_cEANTrib = fields.Char(
        string="GTIN", xsd=True, xsd_required=True,
        help="GTIN (Global Trade Item Number) da unidade tributável, antigo"
        "\ncódigo EAN ou código de barras")
    nfe40_uTrib = fields.Char(
        string="Unidade Tributável", xsd=True, xsd_required=True)
    nfe40_qTrib = fields.Monetary(currency_field="brl_currency_id",
        digits=4, string="Quantidade Tributável",
        xsd=True,
        xsd_required=True,
        help="Quantidade Tributável - alterado para aceitar de 0 a 4 casas"
        "\ndecimais e 11 inteiros")
    nfe40_vUnTrib = fields.Monetary(currency_field="brl_currency_id",
        digits=0, string="Valor unitário de tributação",
        xsd=True,
        xsd_required=True,
        help="Valor unitário de tributação - - alterado para aceitar 0 a 10"
        "\ncasas decimais e 11 inteiros")
    nfe40_vFrete = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total do Frete",
        xsd=True)
    nfe40_vSeg = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Total do Seguro",
        xsd=True)
    nfe40_vDesc = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do Desconto",
        xsd=True)
    nfe40_vOutro = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Outras despesas acessórias",
        xsd=True)
    nfe40_indTot = fields.Selection(
        INDTOT_PROD,
        string="Este campo deverá ser preenchido com",
        xsd=True,
        xsd_required=True,
        help="Este campo deverá ser preenchido com:"
        "\n0 – o valor do item (vProd) não compõe o valor total da NF-e"
        "\n(vProd)"
        "\n1 – o valor do item (vProd) compõe o valor total da NF-e (vProd)")
    nfe40_DI = fields.One2many(
        "nfe.40.di",
        "nfe40_DI_prod_id",
        string="Delcaração de Importação",
        xsd=True,
        help="Delcaração de Importação"
        "\n(NT 2011/004)"
    )
    nfe40_detExport = fields.One2many(
        "nfe.40.detexport",
        "nfe40_detExport_prod_id",
        string="Detalhe da exportação",
        xsd=True
    )
    nfe40_xPed = fields.Char(
        string="pedido de compra",
        xsd=True,
        help="pedido de compra - Informação de interesse do emissor para"
        "\ncontrole do B2B.")
    nfe40_nItemPed = fields.Char(
        string="Número do Item do Pedido de Compra",
        xsd=True,
        help="Número do Item do Pedido de Compra - Identificação do número"
        "\ndo item do pedido de Compra")
    nfe40_nFCI = fields.Char(
        string="Número de controle da FCI",
        xsd=True,
        help="Número de controle da FCI - Ficha de Conteúdo de Importação.")
    nfe40_rastro = fields.One2many(
        "nfe.40.rastro",
        "nfe40_rastro_prod_id",
        string="rastro",
        xsd=True
    )
    nfe40_veicProd = fields.Many2one(
        "nfe.40.veicprod",
        choice='9',
        string="Veículos novos",
        xsd=True)
    nfe40_med = fields.Many2one(
        "nfe.40.med",
        choice='9',
        string="grupo do detalhamento de Medicamentos e de matérias",
        xsd=True,
        help="grupo do detalhamento de Medicamentos e de matérias-primas"
        "\nfarmacêuticas")
    nfe40_arma = fields.One2many(
        "nfe.40.arma",
        "nfe40_arma_prod_id",
        choice='9',
        string="Armamentos",
        xsd=True
    )
    nfe40_comb = fields.Many2one(
        "nfe.40.comb",
        choice='9',
        string="Informar apenas para operações com combustíveis líquidos",
        xsd=True)
    nfe40_nRECOPI = fields.Char(
        choice='9',
        string="Número do RECOPI",
        xsd=True)


class Rastro(models.AbstractModel):
    _description = 'rastro'
    _name = 'nfe.40.rastro'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'rastroType'
    _concrete_rec_name = 'nfe40_nLote'

    nfe40_rastro_prod_id = fields.Many2one(
        "nfe.40.prod")
    nfe40_nLote = fields.Char(
        string="Número do lote do produto.",
        xsd=True,
        xsd_required=True)
    nfe40_qLote = fields.Monetary(currency_field="brl_currency_id",
        digits=3, string="Quantidade de produto no lote.",
        xsd=True,
        xsd_required=True)
    nfe40_dFab = fields.Date(
        string="Data de fabricação/produção",
        xsd=True,
        xsd_required=True,
        help="Data de fabricação/produção. Formato 'AAAA-MM-DD'.")
    nfe40_dVal = fields.Date(
        string="Data de validade", xsd=True, xsd_required=True,
        help="Data de validade. Informar o último dia do mês caso a"
        "\nvalidade não especifique o dia. Formato 'AAAA-MM-DD'.")
    nfe40_cAgreg = fields.Char(
        string="cAgreg",
        xsd=True)


class RefECF(models.AbstractModel):
    "Grupo do Cupom Fiscal vinculado à NF-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.refecf'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'refECFType'
    _concrete_rec_name = 'nfe40_mod'

    nfe40_mod = fields.Selection(
        MOD_REFECF,
        string="Código do modelo do Documento Fiscal",
        xsd=True,
        xsd_required=True,
        help="Código do modelo do Documento Fiscal"
        "\nPreencher com '2B', quando se tratar de Cupom Fiscal emitido por"
        "\nmáquina registradora (não ECF), com '2C', quando se tratar"
        "\nde Cupom Fiscal PDV, ou '2D', quando se tratar de Cupom"
        "\nFiscal (emitido por ECF)")
    nfe40_nECF = fields.Char(
        string="nECF", xsd=True, xsd_required=True,
        help="Informar o número de ordem seqüencial do ECF que emitiu o"
        "\nCupom Fiscal vinculado à NF-e")
    nfe40_nCOO = fields.Char(
        string="Informar o Número do Contador de Ordem de Operação",
        xsd=True,
        xsd_required=True,
        help="Informar o Número do Contador de Ordem de Operação - COO"
        "\nvinculado à NF-e")


class RefNFP(models.AbstractModel):
    "Grupo com as informações NF de produtor referenciada"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.refnfp'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'refNFPType'
    _concrete_rec_name = 'nfe40_cUF'

    nfe40_choice5 = fields.Selection([
        ('nfe40_CNPJ', 'CNPJ'),
        ('nfe40_CPF', 'CPF')],
        "CNPJ/CPF")
    nfe40_cUF = fields.Selection(
        TCODUFIBGE,
        string="cUF", xsd=True, xsd_required=True,
        help="Código da UF do emitente do Documento FiscalUtilizar a Tabela"
        "\ndo IBGE (Anexo IV - Tabela de UF, Município e País)")
    nfe40_AAMM = fields.Char(
        string="AAMM da emissão da NF de produtor",
        xsd=True,
        xsd_required=True)
    nfe40_CNPJ = fields.Char(
        choice='5',
        string="CNPJ do emitente da NF de produtor",
        xsd=True,
        xsd_required=True)
    nfe40_CPF = fields.Char(
        choice='5',
        string="CPF do emitente da NF de produtor",
        xsd=True,
        xsd_required=True)
    nfe40_IE = fields.Char(
        string="IE do emitente da NF de Produtor",
        xsd=True,
        xsd_required=True)
    nfe40_mod = fields.Selection(
        MOD_REFNFP,
        string="Código do modelo do Documento Fiscal",
        xsd=True,
        xsd_required=True,
        help="Código do modelo do Documento Fiscal - utilizar 04 para NF de"
        "\nprodutor ou 01 para NF Avulsa")
    nfe40_serie = fields.Char(
        string="Série do Documento Fiscal",
        xsd=True,
        xsd_required=True,
        help="Série do Documento Fiscal, informar zero se inexistentesérie")
    nfe40_nNF = fields.Char(
        string="Número do Documento Fiscal",
        xsd=True,
        xsd_required=True,
        help="Número do Documento Fiscal - 1 – 999999999")


class RefNF(models.AbstractModel):
    "Dados da NF modelo 1/1A referenciada ou NF modelo 2 referenciada"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.refnf'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'refNFType'
    _concrete_rec_name = 'nfe40_cUF'

    nfe40_cUF = fields.Selection(
        TCODUFIBGE,
        string="Código da UF do emitente do Documento Fiscal",
        xsd=True,
        xsd_required=True,
        help="Código da UF do emitente do Documento Fiscal. Utilizar a"
        "\nTabela do IBGE.")
    nfe40_AAMM = fields.Char(
        string="AAMM da emissão", xsd=True, xsd_required=True)
    nfe40_CNPJ = fields.Char(
        string="CNPJ do emitente do documento fiscal referenciado",
        xsd=True,
        xsd_required=True)
    nfe40_mod = fields.Selection(
        MOD_REFNF,
        string="Código do modelo do Documento Fiscal",
        xsd=True,
        xsd_required=True,
        help="Código do modelo do Documento Fiscal. Utilizar 01 para NF"
        "\nmodelo 1/1A e 02 para NF modelo 02")
    nfe40_serie = fields.Char(
        string="Série do Documento Fiscal",
        xsd=True,
        xsd_required=True,
        help="Série do Documento Fiscal, informar zero se inexistente")
    nfe40_nNF = fields.Char(
        string="Número do Documento Fiscal",
        xsd=True,
        xsd_required=True)


class RetTransp(models.AbstractModel):
    "Dados da retenção ICMS do Transporte"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.rettransp'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'retTranspType'
    _concrete_rec_name = 'nfe40_vServ'

    nfe40_vServ = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do Serviço", xsd=True, xsd_required=True)
    nfe40_vBCRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="BC da Retenção do ICMS",
        xsd=True,
        xsd_required=True)
    nfe40_pICMSRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Alíquota da Retenção",
        xsd=True,
        xsd_required=True)
    nfe40_vICMSRet = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor do ICMS Retido",
        xsd=True,
        xsd_required=True)
    nfe40_CFOP = fields.Char(
        string="Código Fiscal de Operações e Prestações",
        xsd=True,
        xsd_required=True)
    nfe40_cMunFG = fields.Char(
        string="Código do Município de Ocorrência do Fato Gerador",
        xsd=True,
        xsd_required=True,
        help="Código do Município de Ocorrência do Fato Gerador (utilizar a"
        "\ntabela do IBGE)")


class RetTrib(models.AbstractModel):
    "Retenção de Tributos Federais"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.rettrib'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'retTribType'
    _concrete_rec_name = 'nfe40_vRetPIS'

    nfe40_vRetPIS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Retido de PIS",
        xsd=True)
    nfe40_vRetCOFINS = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Retido de COFINS",
        xsd=True)
    nfe40_vRetCSLL = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Retido de CSLL",
        xsd=True)
    nfe40_vBCIRRF = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Base de Cálculo do IRRF",
        xsd=True)
    nfe40_vIRRF = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor Retido de IRRF",
        xsd=True)
    nfe40_vBCRetPrev = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Base de Cálculo da Retenção da Previdêncica Social",
        xsd=True)
    nfe40_vRetPrev = fields.Monetary(currency_field="brl_currency_id",
        digits=2, string="Valor da Retenção da Previdêncica Social",
        xsd=True)


class Total(models.AbstractModel):
    "Dados dos totais da NF-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.total'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'totalType'
    _concrete_rec_name = 'nfe40_ICMSTot'

    nfe40_ICMSTot = fields.Many2one(
        "nfe.40.icmstot",
        string="Totais referentes ao ICMS",
        xsd=True,
        xsd_required=True)
    nfe40_ISSQNtot = fields.Many2one(
        "nfe.40.issqntot",
        string="Totais referentes ao ISSQN",
        xsd=True)
    nfe40_retTrib = fields.Many2one(
        "nfe.40.rettrib",
        string="Retenção de Tributos Federais",
        xsd=True)


class Transp(models.AbstractModel):
    "Dados dos transportes da NF-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.transp'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'transpType'
    _concrete_rec_name = 'nfe40_modFrete'

    nfe40_choice18 = fields.Selection([
        ('nfe40_veicTransp', 'veicTransp'),
        ('nfe40_reboque', 'reboque'),
        ('nfe40_vagao', 'vagao'),
        ('nfe40_balsa', 'balsa')],
        "veicTransp/reboque/vagao/balsa")
    nfe40_modFrete = fields.Selection(
        MODFRETE_TRANSP,
        string="Modalidade do frete",
        xsd=True,
        xsd_required=True,
        help="Modalidade do frete"
        "\n0- Contratação do Frete por conta do Remetente (CIF);"
        "\n1- Contratação do Frete por conta do destinatário/remetente (FOB);"
        "\n2- Contratação do Frete por conta de terceiros;"
        "\n3- Transporte próprio por conta do remetente;"
        "\n4- Transporte próprio por conta do destinatário;"
        "\n9- Sem Ocorrência de transporte.")
    nfe40_transporta = fields.Many2one(
        "nfe.40.transporta",
        string="Dados do transportador",
        xsd=True)
    nfe40_retTransp = fields.Many2one(
        "nfe.40.rettransp",
        string="Dados da retenção ICMS do Transporte",
        xsd=True,
        help="Dados da retenção ICMS do Transporte")
    nfe40_veicTransp = fields.Many2one(
        "nfe.40.tveiculo",
        choice='18',
        string="Dados do veículo",
        xsd=True)
    nfe40_reboque = fields.One2many(
        "nfe.40.tveiculo",
        "nfe40_reboque_transp_id",
        choice='18',
        string="Dados do reboque/Dolly (v2.0)",
        xsd=True
    )
    nfe40_vagao = fields.Char(
        choice='18',
        string="Identificação do vagão (v2.0)",
        xsd=True)
    nfe40_balsa = fields.Char(
        choice='18',
        string="Identificação da balsa (v2.0)",
        xsd=True)
    nfe40_vol = fields.One2many(
        "nfe.40.vol",
        "nfe40_vol_transp_id",
        string="Dados dos volumes",
        xsd=True
    )


class Transporta(models.AbstractModel):
    "Dados do transportador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.transporta'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'transportaType'
    _concrete_rec_name = 'nfe40_CNPJ'

    nfe40_choice19 = fields.Selection([
        ('nfe40_CNPJ', 'CNPJ'),
        ('nfe40_CPF', 'CPF')],
        "CNPJ/CPF")
    nfe40_CNPJ = fields.Char(
        choice='19',
        string="CNPJ do transportador",
        xsd=True)
    nfe40_CPF = fields.Char(
        choice='19',
        string="CPF do transportador",
        xsd=True)
    nfe40_xNome = fields.Char(
        string="Razão Social ou nome do transportador",
        xsd=True)
    nfe40_IE = fields.Char(
        string="Inscrição Estadual (v2.0)",
        xsd=True)
    nfe40_xEnder = fields.Char(
        string="Endereço completo",
        xsd=True)
    nfe40_xMun = fields.Char(
        string="Nome do munícipio",
        xsd=True)
    nfe40_UF = fields.Selection(
        TUF,
        string="Sigla da UF",
        xsd=True)


class VeicProd(models.AbstractModel):
    "Veículos novos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.veicprod'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'veicProdType'
    _concrete_rec_name = 'nfe40_tpOp'

    nfe40_tpOp = fields.Selection(
        TPOP_VEICPROD,
        string="Tipo da Operação", xsd=True, xsd_required=True,
        help="Tipo da Operação (1 - Venda concessionária; 2 - Faturamento"
        "\ndireto; 3 - Venda direta; 0 - Outros)")
    nfe40_chassi = fields.Char(
        string="Chassi do veículo - VIN",
        xsd=True,
        xsd_required=True,
        help="Chassi do veículo - VIN (código-identificação-veículo)")
    nfe40_cCor = fields.Char(
        string="Cor do veículo", xsd=True, xsd_required=True,
        help="Cor do veículo (código de cada montadora)")
    nfe40_xCor = fields.Char(
        string="Descrição da cor", xsd=True, xsd_required=True)
    nfe40_pot = fields.Char(
        string="Potência máxima do motor do veículo em cavalo vapor",
        xsd=True,
        xsd_required=True,
        help="Potência máxima do motor do veículo em cavalo vapor (CV)."
        "\n(potência-veículo)")
    nfe40_cilin = fields.Char(
        string="cilin", xsd=True, xsd_required=True,
        help="Capacidade voluntária do motor expressa em centímetros"
        "\ncúbicos (CC). (cilindradas)")
    nfe40_pesoL = fields.Char(
        string="Peso líquido", xsd=True, xsd_required=True)
    nfe40_pesoB = fields.Char(
        string="Peso bruto", xsd=True, xsd_required=True)
    nfe40_nSerie = fields.Char(
        string="Serial (série)", xsd=True, xsd_required=True)
    nfe40_tpComb = fields.Char(
        string="Tipo de combustível",
        xsd=True,
        xsd_required=True,
        help="Tipo de combustível-Tabela RENAVAM: 01-Álcool; 02-Gasolina;"
        "\n03-Diesel; 16-Álcool/Gas.; 17-Gas./Álcool/GNV;"
        "\n18-Gasolina/Elétrico")
    nfe40_nMotor = fields.Char(
        string="Número do motor", xsd=True, xsd_required=True)
    nfe40_CMT = fields.Char(
        string="CMT", xsd=True, xsd_required=True,
        help="CMT-Capacidade Máxima de Tração - em Toneladas 4 casas"
        "\ndecimais")
    nfe40_dist = fields.Char(
        string="Distância entre eixos",
        xsd=True,
        xsd_required=True)
    nfe40_anoMod = fields.Char(
        string="Ano Modelo de Fabricação",
        xsd=True,
        xsd_required=True)
    nfe40_anoFab = fields.Char(
        string="Ano de Fabricação", xsd=True, xsd_required=True)
    nfe40_tpPint = fields.Char(
        string="Tipo de pintura", xsd=True, xsd_required=True)
    nfe40_tpVeic = fields.Char(
        string="Tipo de veículo", xsd=True, xsd_required=True,
        help="Tipo de veículo (utilizar tabela RENAVAM)")
    nfe40_espVeic = fields.Char(
        string="Espécie de veículo",
        xsd=True,
        xsd_required=True,
        help="Espécie de veículo (utilizar tabela RENAVAM)")
    nfe40_VIN = fields.Selection(
        VIN_VEICPROD,
        string="Informa-se o veículo tem VIN",
        xsd=True,
        xsd_required=True,
        help="Informa-se o veículo tem VIN (chassi) remarcado.")
    nfe40_condVeic = fields.Selection(
        CONDVEIC_VEICPROD,
        string="Condição do veículo",
        xsd=True,
        xsd_required=True,
        help="Condição do veículo (1 - acabado; 2 - inacabado; 3 - semi-"
        "\nacabado)")
    nfe40_cMod = fields.Char(
        string="Código Marca Modelo", xsd=True, xsd_required=True,
        help="Código Marca Modelo (utilizar tabela RENAVAM)")
    nfe40_cCorDENATRAN = fields.Char(
        string="Código da Cor Segundo as regras de pré",
        xsd=True,
        xsd_required=True,
        help="Código da Cor Segundo as regras de pré-cadastro do DENATRAN:"
        "\n01-AMARELO;02-AZUL;03-BEGE;04-BRANCA;05-CINZA;06-DOUR"
        "\nADA;07-GRENA"
        "\n08-LARANJA;09-MARROM;10-PRATA;11-PRETA;12-ROSA;13-ROXA;14-VERDE;15-"
        "\nVERMELHA;16-FANTASIA")
    nfe40_lota = fields.Char(
        string="Quantidade máxima de permitida de passageiros sentados",
        xsd=True,
        xsd_required=True,
        help="Quantidade máxima de permitida de passageiros sentados,"
        "\ninclusive motorista.")
    nfe40_tpRest = fields.Selection(
        TPREST_VEICPROD,
        string="Restrição", xsd=True, xsd_required=True,
        help="Restrição"
        "\n0 - Não há;"
        "\n1 - Alienação Fiduciária;"
        "\n2 - Arrendamento Mercantil;"
        "\n3 - Reserva de Domínio;"
        "\n4 - Penhor de Veículos;"
        "\n9 - outras.")


class Vol(models.AbstractModel):
    "Dados dos volumes"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.vol'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'volType'
    _concrete_rec_name = 'nfe40_qVol'

    nfe40_vol_transp_id = fields.Many2one(
        "nfe.40.transp")
    nfe40_qVol = fields.Char(
        string="Quantidade de volumes transportados",
        xsd=True)
    nfe40_esp = fields.Char(
        string="Espécie dos volumes transportados",
        xsd=True)
    nfe40_marca = fields.Char(
        string="Marca dos volumes transportados",
        xsd=True)
    nfe40_nVol = fields.Char(
        string="Numeração dos volumes transportados",
        xsd=True)
    nfe40_pesoL = fields.Monetary(currency_field="brl_currency_id",
        digits=3, string="Peso líquido (em kg)",
        xsd=True)
    nfe40_pesoB = fields.Monetary(currency_field="brl_currency_id",
        digits=3, string="Peso bruto (em kg)",
        xsd=True)
    nfe40_lacres = fields.One2many(
        "nfe.40.lacres",
        "nfe40_lacres_vol_id",
        string="lacres",
        xsd=True
    )
