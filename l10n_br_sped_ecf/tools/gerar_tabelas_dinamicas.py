#!/usr/bin/env python3
# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
"""Gera models/tabelas_dinamicas.py a partir do pacote oficial da RFB.

Uso:
    python3 gerar_tabelas_dinamicas.py TABELAS.xlsx --leiaute 12 \
        --saida ../models/tabelas_dinamicas.py

A planilha e o pacote "Tabelas Dinamicas e Planos de Contas Referenciais"
publicado em http://sped.rfb.gov.br (ECF). Cada aba corresponde a um registro
de valores (P200, P300, P400, P500...) e traz, por linha: CODIGO, DESCRICAO,
vigencia (DT_INI/DT_FIM), TIPO e a FORMULA oficial.

TIPO:
    R    rotulo (linha de titulo, sem valor)
    E    editavel (o valor vem da escrituracao)
    CA   calculado a partir de outra linha (transporte)
    CNA  calculado nao alteravel (formula propria)

O modulo gerado guarda a tabela como dado inerte; quem sabe calcular e o
apurador em models/apuracao_presumido.py. Regerar com uma planilha nova e o
diff do git mostra o que a RFB mudou.
"""

import argparse
import sys
from datetime import date

ABAS_PADRAO = ["P130", "P200", "P230", "P300", "P400", "P500"]

CABECALHO = '''# Copyright 2026 - TODAY, Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Gerado por tools/gerar_tabelas_dinamicas.py a partir do pacote oficial de
# tabelas dinamicas do SPED (leiaute {leiaute}). Nao editar a mao: regerar.
# ruff: noqa: E501
"""Tabelas dinamicas oficiais dos registros de valores da ECF.

Cada entrada e uma linha da tabela publicada pela RFB, na ordem oficial:
``(CODIGO, DESCRICAO, TIPO, DT_INI, DT_FIM)``, onde TIPO e ``R`` (rotulo),
``E`` (editavel), ``CA`` (calculado por transporte) ou ``CNA`` (calculado nao
alteravel). As datas sao ``None`` quando a vigencia e aberta.

A FORMULA oficial de cada linha calculada esta no docstring do metodo
correspondente em ``apuracao_presumido.py``, junto da implementacao.
"""

from datetime import date

'''


def _data(valor):
    """DT no formato ddmmaaaa (ou datetime do openpyxl) para date()."""
    if valor is None or valor == "":
        return None
    if hasattr(valor, "year"):
        return date(valor.year, valor.month, valor.day)
    digitos = "".join(c for c in str(valor) if c.isdigit())
    if len(digitos) == 8:
        return date(int(digitos[4:]), int(digitos[2:4]), int(digitos[:2]))
    return None


def _limpa(texto):
    return " ".join(str(texto or "").split())


def _codigo(valor):
    """Codigo como a RFB o escreve: '2', '20.01', '25.110'.

    O openpyxl devolve inteiro quando a celula e numerica e string quando tem
    ponto; os codigos longos ('25110') sao escritos '25.110' no arquivo.
    """
    texto = _limpa(valor)
    if not texto:
        return ""
    if texto.isdigit() and len(texto) > 4:
        return f"{texto[:2]}.{texto[2:]}"
    return texto


def ler_aba(wb, aba):
    ws = wb[aba]
    linhas = []
    for row in list(ws.iter_rows(values_only=True))[1:]:
        codigo = _codigo(row[0])
        if not codigo:
            continue
        linhas.append(
            (
                codigo,
                _limpa(row[1]),
                (_limpa(row[4]) or "E").upper(),
                _data(row[2]),
                _data(row[3]),
            )
        )
    return linhas


def _repr_data(valor):
    if valor is None:
        return "None"
    return f"date({valor.year}, {valor.month}, {valor.day})"


def gerar(xlsx, abas, leiaute, saida):
    import openpyxl

    wb = openpyxl.load_workbook(xlsx, read_only=True)
    partes = [CABECALHO.format(leiaute=leiaute)]
    partes.append(f'LEIAUTE = "{leiaute}"\n\n')
    total = 0
    for aba in abas:
        linhas = ler_aba(wb, aba)
        total += len(linhas)
        partes.append(f"TABELA_{aba} = [\n")
        for codigo, descricao, tipo, dt_ini, dt_fim in linhas:
            partes.append(
                f'    ("{codigo}", "{descricao}", "{tipo}", '
                f"{_repr_data(dt_ini)}, {_repr_data(dt_fim)}),\n"
            )
        partes.append("]\n\n")
    partes.append("TABELAS = {\n")
    for aba in abas:
        partes.append(f'    "{aba}": TABELA_{aba},\n')
    partes.append("}\n\n\n")
    partes.append(
        "def linhas_vigentes(registro, data_inicio, data_fim):\n"
        '    """Linhas da tabela de ``registro`` vigentes no periodo informado."""\n'
        "    vigentes = []\n"
        "    for codigo, descricao, tipo, dt_ini, dt_fim in TABELAS[registro]:\n"
        "        if dt_ini and dt_ini > data_fim:\n"
        "            continue\n"
        "        if dt_fim and dt_fim < data_inicio:\n"
        "            continue\n"
        "        vigentes.append((codigo, descricao, tipo))\n"
        "    return vigentes\n"
    )
    conteudo = "".join(partes)
    with open(saida, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xlsx")
    parser.add_argument("--leiaute", required=True)
    parser.add_argument("--abas", default=",".join(ABAS_PADRAO))
    parser.add_argument("--saida", required=True)
    args = parser.parse_args()
    total = gerar(args.xlsx, args.abas.split(","), args.leiaute, args.saida)
    print(  # noqa: T201 pylint: disable=print-used
        f"{args.saida}: {total} linhas geradas"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
