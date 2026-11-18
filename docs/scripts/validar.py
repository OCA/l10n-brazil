"""Valida docs/: esquemas, vocabulários, ids, referências, módulos, links e texto.

Uso, de qualquer pasta:

    python docs/scripts/validar.py [--root DIR]

Sai com 0 quando não há erros e com 1 quando há. Cada erro é uma linha
`caminho/relativo: mensagem` no stderr, seguida do resumo. Depende só de
pyyaml e jsonschema (o hook docs-validar do pre-commit os instala); não usa
rede nem o Odoo. A leitura dos arquivos é a mesma do gerar_index.py, que
também gera o texto com que o docs/INDEX.md é conferido.
"""

import argparse
import difflib
import functools
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

import gerar_index
from gerar_index import (
    Acervo,
    Erro,
    Item,
    Requisito,
    Taxonomia,
    como_lista,
    como_texto,
)
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError

ESQUEMAS = ("adr", "capacidade", "caso", "marco", "norma", "requisito", "spec")

# Vocabulários de docs/taxonomia/vocabularios.yaml que as regras abaixo usam.
VOCABULARIOS_USADOS = (
    "status_norma",
    "confianca",
    "status_trecho",
    "status_data",
    "status_capacidade",
    "status_spec",
    "estado",
    "tipo_requisito",
    "camada_caso",
    "estado_caso",
    "nivel_caso",
    "status_adr",
)

# Campo (com "[]" para listas) -> vocabulário ou lista de códigos que o limita.
CAMPOS_COM_VOCABULARIO = {
    "norma": (
        ("tipo", "tipos_norma"),
        ("status", "status_norma"),
        ("confianca", "confianca"),
        ("versoes[].confianca", "confianca"),
        ("trechos[].status", "status_trecho"),
        ("dominios[]", "dominios"),
    ),
    "marco": (("status_data", "status_data"), ("dominios[]", "dominios")),
    "capacidade": (("status", "status_capacidade"), ("dominio", "dominios")),
    "spec": (("status", "status_spec"), ("dominios[]", "dominios")),
    "requisito": (("estado", "estado"), ("tipo", "tipo_requisito")),
    "caso": (
        ("camada", "camada_caso"),
        ("estado", "estado_caso"),
        ("nivel", "nivel_caso"),
    ),
    "adr": (("status", "status_adr"),),
}

# Campo -> tipo da entidade que ele referencia.
CAMPOS_COM_REFERENCIA = {
    "norma": (("supersede", "norma"),),
    "marco": (("normas", "norma"),),
    "capacidade": (
        ("normas", "norma"),
        ("marcos", "marco"),
        ("depende_de", "capacidade"),
    ),
    "spec": (
        ("normas", "norma"),
        ("marcos", "marco"),
        ("capacidade", "capacidade"),
        ("substitui", "spec"),
    ),
    "requisito": (("normas", "norma"), ("casos", "caso")),
    "caso": (("requisitos", "requisito"),),
    "adr": (
        ("specs_afetadas", "spec"),
        ("substitui", "adr"),
        ("substituido_por", "adr"),
    ),
}
ROTULOS_DE_REFERENCIA = {"adr": "ADR"}  # os demais usam o próprio nome do tipo
PREFIXOS_DE_REFERENCIA = {
    "norma": "N-",
    "marco": "M-",
    "capacidade": "CAP-",
    "spec": "SPEC-",
    "adr": "ADR-",
    "requisito": "REQ-",
    "caso": "BR-",
}
# Pasta em que cada tipo mora (chave de Acervo.ilegiveis).
PASTAS = {
    "norma": "normas",
    "marco": "marcos",
    "capacidade": "capacidades",
    "spec": "specs",
    "adr": "decisoes",
    "caso": "casos",
}
# Tipos que só existem na branch canônica (ADR-0001). Nas outras branches a
# pasta não existe e a referência é conferida pela matriz entre branches.
SO_NA_CANONICA = ("norma", "marco")
EXTENSAO_DO_ARQUIVO = {
    "norma": ".yaml",
    "marco": ".yaml",
    "capacidade": ".md",
    "spec": ".md",
    "adr": ".md",
}
ROTULOS_DE_CAMPO = {
    "evidencia": "Evidência",
    "visto_em": "Visto em",
}

# Caracteres tipográficos proibidos em docs/ (escritos por código para que este
# arquivo também seja só ASCII e acentos).
TIPOGRAFICOS = {
    0x2014: "travessão",
    0x2013: "meia-risca",
    0x201C: "aspas curvas de abertura",
    0x201D: "aspas curvas de fechamento",
    0x2018: "aspa simples curva de abertura",
    0x2019: "aspa simples curva de fechamento",
    0x2026: "reticências em um caractere só",
    0x2192: "seta",
    0x2264: "símbolo de menor ou igual",
    0x2265: "símbolo de maior ou igual",
    0x00D7: "sinal de multiplicação",
    0x2212: "sinal de menos matemático",
}
EXTENSOES_DE_TEXTO = {".md", ".yaml", ".yml", ".json", ".txt", ".csv", ".html", ".svg"}

_RE_TIPOGRAFICO = re.compile(
    "[" + "".join(re.escape(chr(codigo)) for codigo in TIPOGRAFICOS) + "]"
)
_RE_REFERENCIA_NORMA = re.compile(
    r"N-[A-Z0-9][A-Za-z0-9.-]*(?:#[A-Za-z0-9][A-Za-z0-9._-]*)?"
)
_RE_ID_SPEC = re.compile(r"SPEC-([A-Z]+)-([a-z0-9][a-z0-9-]*)")
_RE_ID_REQUISITO = re.compile(r"REQ-([a-z0-9][a-z0-9-]*)-[0-9]{2}")
_RE_ID_DOMINIO = re.compile(r"(?:CAP|SPEC)-([A-Z]+)-.+")
_RE_DATA_DO_MARCO = re.compile(r"M-([0-9]{4}-[0-9]{2}-[0-9]{2})-.+")
_RE_DATA = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_RE_URL = re.compile(r"https?://\S+")
_RE_OBRIGATORIO = re.compile(r"^'(.*)' is a required property$")
_RE_ESQUEMA_DE_URL = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_RE_CODIGO_NA_LINHA = re.compile(r"`[^`\n]*`")
_RE_LINK = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]*)\)")
_RE_CAMINHO_DE_DOCS = re.compile(
    r"(?<![A-Za-z0-9_])docs/[A-Za-z0-9_./-]+\.(?:md|yaml)(?![A-Za-z0-9_])"
)


# --------------------------------------------------------------------------
# Existência de arquivos
# --------------------------------------------------------------------------


@functools.cache
def _nomes_em(pasta: Path) -> frozenset[str]:
    try:
        return frozenset(unicodedata.normalize("NFC", n) for n in os.listdir(pasta))
    except OSError:
        return frozenset()


def existe(root: Path, caminho: Path) -> bool:
    """Existência com caixa exata: o macOS ignora a caixa e o CI em Linux não."""
    try:
        relativo = caminho.relative_to(root)
    except ValueError:
        return caminho.exists()
    atual = root
    for parte in relativo.parts:
        if unicodedata.normalize("NFC", parte) not in _nomes_em(atual):
            return False
        atual = atual / parte
    return True


def modulo_existe(root: Path, nome: str) -> bool:
    return existe(root, root / nome / "__manifest__.py")


# --------------------------------------------------------------------------
# Esquemas JSON
# --------------------------------------------------------------------------


def _eh_data(valor: object) -> bool:
    if not isinstance(valor, str):
        return True
    if not _RE_DATA.fullmatch(valor):
        return False
    try:
        date.fromisoformat(valor)
    except ValueError:
        return False
    return True


def _eh_url(valor: object) -> bool:
    return not isinstance(valor, str) or bool(_RE_URL.fullmatch(valor))


def _verificador_de_formatos() -> FormatChecker:
    """Só date e uri, definidos aqui: não dependem de extras do jsonschema."""
    verificador = FormatChecker(formats=[])
    verificador.checks("date")(_eh_data)
    verificador.checks("uri")(_eh_url)
    return verificador


def _carregar_esquemas(
    root: Path, erros: list[Erro]
) -> dict[str, Draft202012Validator]:
    verificador = _verificador_de_formatos()
    validadores = {}
    for nome in ESQUEMAS:
        caminho = root / "docs" / "schema" / f"{nome}.schema.json"
        arquivo = caminho.relative_to(root).as_posix()
        try:
            esquema = json.loads(caminho.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(esquema)
        except OSError:
            erros.append(Erro(arquivo, "esquema ausente"))
        except ValueError as exc:
            erros.append(Erro(arquivo, f"JSON inválido: {exc}"))
        except SchemaError as exc:
            erros.append(Erro(arquivo, f"esquema inválido: {exc.message}"))
        else:
            validadores[nome] = Draft202012Validator(
                esquema, format_checker=verificador
            )
    return validadores


def _formatar_caminho(partes: list) -> str:
    texto = ""
    for parte in partes:
        if isinstance(parte, int):
            texto += f"[{parte}]"
        else:
            texto += f".{parte}" if texto else str(parte)
    return texto


_TIPOS_JSON = {
    bool: "boolean",
    int: "integer",
    float: "number",
    str: "string",
    list: "array",
    dict: "object",
    type(None): "null",
}


def _msg_obrigatorio(problema: ValidationError) -> str:
    achado = _RE_OBRIGATORIO.match(problema.message)
    nome = achado.group(1) if achado else str(problema.validator_value)
    return f"campo obrigatório ausente: '{nome}'"


def _msg_adicional(problema: ValidationError) -> str:
    conhecidos = problema.schema.get("properties", {})
    extras = sorted(
        str(chave) for chave in problema.instance if chave not in conhecidos
    )
    return "campo desconhecido: " + ", ".join(f"'{extra}'" for extra in extras)


def _msg_tipo(problema: ValidationError) -> str:
    esperado = problema.validator_value
    esperado = " ou ".join(esperado) if isinstance(esperado, list) else str(esperado)
    tipo = type(problema.instance)
    recebido = _TIPOS_JSON.get(tipo, tipo.__name__)
    dica = ""
    if "string" in esperado and recebido in ("integer", "number", "boolean"):
        dica = " (coloque o valor entre aspas no YAML)"
    return f"tipo inválido: esperado {esperado}, recebido {recebido}{dica}"


def _msg_padrao(problema: ValidationError) -> str:
    return (
        f"valor {problema.instance!r} fora do formato esperado "
        f"({problema.validator_value})"
    )


def _msg_formato(problema: ValidationError) -> str:
    if problema.validator_value == "date":
        return f"data inválida {problema.instance!r}: use AAAA-MM-DD"
    if problema.validator_value == "uri":
        return f"URL inválida {problema.instance!r}: use http:// ou https://"
    return f"valor {problema.instance!r} fora do formato {problema.validator_value}"


def _msg_enum(problema: ValidationError) -> str:
    permitidos = ", ".join(str(valor) for valor in problema.validator_value)
    return f"valor {problema.instance!r} fora dos permitidos ({permitidos})"


def _msg_texto_curto(problema: ValidationError) -> str:
    minimo = problema.validator_value
    return "texto vazio" if minimo == 1 else f"texto com menos de {minimo} caracteres"


def _msg_lista_curta(problema: ValidationError) -> str:
    minimo = problema.validator_value
    if minimo == 1:
        return "lista vazia (mínimo 1 item)"
    return f"lista com menos de {minimo} itens"


def _msg_repetidos(_problema: ValidationError) -> str:
    return "itens repetidos na lista"


def _msg_minimo(problema: ValidationError) -> str:
    return f"valor menor que o mínimo permitido ({problema.validator_value})"


def _msg_generica(problema: ValidationError) -> str:
    return problema.message


TRADUTORES: dict[str, Callable[[ValidationError], str]] = {
    "required": _msg_obrigatorio,
    "additionalProperties": _msg_adicional,
    "type": _msg_tipo,
    "pattern": _msg_padrao,
    "format": _msg_formato,
    "enum": _msg_enum,
    "minLength": _msg_texto_curto,
    "minItems": _msg_lista_curta,
    "uniqueItems": _msg_repetidos,
    "minimum": _msg_minimo,
}


def _traduzir(problema: ValidationError, corte: int) -> str:
    caminho = _formatar_caminho(list(problema.absolute_path)[corte:])
    mensagem = TRADUTORES.get(problema.validator, _msg_generica)(problema)
    return f"{caminho}: {mensagem}" if caminho else mensagem


# --------------------------------------------------------------------------
# Objetos a validar
# --------------------------------------------------------------------------


@dataclass
class Alvo:
    """Um objeto lido de docs/ e o contexto para escrever seus erros."""

    entidade: str
    arquivo: str
    dados: dict
    linha: int | None = None
    rotulo: str = ""
    indice: int | None = None

    @property
    def id(self) -> str:
        valor = self.dados.get("id")
        return valor if isinstance(valor, str) else ""

    @property
    def local(self) -> str:
        if self.linha:
            return f"{self.arquivo}:{self.linha}"
        if self.indice is not None:
            return f"{self.arquivo} (item {self.indice + 1})"
        return self.arquivo

    def erro(self, mensagem: str) -> Erro:
        prefixo = f"{self.rotulo}: " if self.rotulo else ""
        return Erro(self.arquivo, prefixo + mensagem, self.linha)


def _rotulo_do_caso(caso: Item) -> str:
    if caso.id:
        return f"caso {caso.id}"
    return f"caso (item {(caso.indice or 0) + 1})"


def _alvos(acervo: Acervo) -> list[Alvo]:
    grupos = (
        ("norma", acervo.normas),
        ("marco", acervo.marcos),
        ("capacidade", acervo.capacidades),
        ("spec", acervo.specs),
        ("adr", acervo.adrs),
    )
    alvos = [Alvo(nome, i.arquivo, i.dados) for nome, itens in grupos for i in itens]
    alvos += [
        Alvo(
            "caso",
            caso.arquivo,
            caso.dados,
            rotulo=_rotulo_do_caso(caso),
            indice=caso.indice,
        )
        for caso in acervo.casos
    ]
    alvos += [
        Alvo("requisito", r.arquivo, r.dados, r.linha, rotulo=r.id)
        for r in acervo.requisitos
    ]
    return alvos


def _checar_esquemas(
    alvos: list[Alvo], validadores: dict[str, Draft202012Validator]
) -> list[Erro]:
    erros = []
    for alvo in alvos:
        validador = validadores.get(alvo.entidade)
        if validador is None:
            continue
        # O esquema do caso descreve a lista inteira do arquivo; cada caso é
        # validado numa lista de um item e o índice 0 sai do caminho do erro.
        instancia, corte = (
            ([alvo.dados], 1) if alvo.entidade == "caso" else (alvo.dados, 0)
        )
        erros += [
            alvo.erro(_traduzir(p, corte)) for p in validador.iter_errors(instancia)
        ]
    return erros


# --------------------------------------------------------------------------
# Taxonomia e vocabulários
# --------------------------------------------------------------------------


def _checar_taxonomia(acervo: Acervo) -> list[Erro]:
    vocabularios = acervo.taxonomia.vocabularios
    if vocabularios is None:
        return []
    return [
        Erro("docs/taxonomia/vocabularios.yaml", f"vocabulário '{nome}' ausente")
        for nome in VOCABULARIOS_USADOS
        if nome not in vocabularios
    ]


def _permitidos(taxonomia: Taxonomia) -> dict[str, tuple[list[str], str]]:
    """Nome do vocabulário -> (códigos aceitos, "do/de <origem>" para a mensagem)."""
    mapa = {
        nome: (codigos, f"do vocabulário {nome}")
        for nome, codigos in (taxonomia.vocabularios or {}).items()
    }
    if taxonomia.dominios is not None:
        mapa["dominios"] = (list(taxonomia.dominios), "de docs/taxonomia/dominios.yaml")
    if taxonomia.tipos_norma is not None:
        mapa["tipos_norma"] = (
            taxonomia.tipos_norma,
            "de docs/taxonomia/tipos-norma.yaml",
        )
    return mapa


def _percorrer(
    valor: object, partes: list[str], trilha: list
) -> Iterator[tuple[str, object]]:
    if not partes:
        yield _formatar_caminho(trilha), valor
        return
    chave = partes[0].removesuffix("[]")
    if not isinstance(valor, dict) or chave not in valor:
        return
    filho = valor[chave]
    if not partes[0].endswith("[]"):
        yield from _percorrer(filho, partes[1:], [*trilha, chave])
    elif isinstance(filho, list):
        for indice, item in enumerate(filho):
            yield from _percorrer(item, partes[1:], [*trilha, chave, indice])


def _checar_vocabularios(alvos: list[Alvo], taxonomia: Taxonomia) -> list[Erro]:
    permitidos = _permitidos(taxonomia)
    erros = []
    for alvo in alvos:
        for caminho, nome in CAMPOS_COM_VOCABULARIO.get(alvo.entidade, ()):
            if nome not in permitidos:
                continue
            codigos, origem = permitidos[nome]
            for local, valor in _percorrer(alvo.dados, caminho.split("."), []):
                if isinstance(valor, str) and valor not in codigos:
                    aceitos = ", ".join(codigos)
                    mensagem = (
                        f"{local}: valor '{valor}' fora {origem} "
                        f"(permitidos: {aceitos})"
                    )
                    erros.append(alvo.erro(mensagem))
    return erros


# --------------------------------------------------------------------------
# Ids, nomes de arquivo e datas
# --------------------------------------------------------------------------


def _checar_ids_unicos(alvos: list[Alvo]) -> list[Erro]:
    por_id: dict[str, list[Alvo]] = defaultdict(list)
    for alvo in alvos:
        if alvo.id:
            por_id[alvo.id].append(alvo)
    erros = []
    for identificador, grupo in sorted(por_id.items()):
        if len(grupo) < 2:
            continue
        for alvo in grupo:
            outros = ", ".join(outro.local for outro in grupo if outro is not alvo)
            mensagem = f"id duplicado '{identificador}': também definido em {outros}"
            erros.append(Erro(alvo.arquivo, mensagem, alvo.linha))
    return erros


def _erros_de_dominio(alvo: Alvo, taxonomia: Taxonomia) -> list[Erro]:
    """Pasta, campo `dominio` e taxonomia contra o domínio escrito no id."""
    achado = _RE_ID_DOMINIO.fullmatch(alvo.id)
    if not achado:
        return []
    dominio = achado.group(1)
    erros = []
    pasta = PurePosixPath(alvo.arquivo).parent.name
    if pasta != dominio:
        erros.append(
            alvo.erro(f"pasta '{pasta}' difere do domínio do id ('{dominio}')")
        )
    if taxonomia.dominios is not None and dominio not in taxonomia.dominios:
        erros.append(
            alvo.erro(f"domínio '{dominio}' do id não existe em dominios.yaml")
        )
    declarado = como_texto(alvo.dados.get("dominio"))
    if alvo.entidade == "capacidade" and declarado not in ("", dominio):
        erros.append(
            alvo.erro(f"dominio '{declarado}' difere do domínio do id ('{dominio}')")
        )
    return erros


def _checar_nomes_de_arquivo(alvos: list[Alvo], taxonomia: Taxonomia) -> list[Erro]:
    erros = []
    for alvo in alvos:
        extensao = EXTENSAO_DO_ARQUIVO.get(alvo.entidade)
        if not extensao or not alvo.id:
            continue
        nome = PurePosixPath(alvo.arquivo).name
        if nome != alvo.id + extensao:
            erros.append(
                alvo.erro(
                    f"nome do arquivo '{nome}' difere do id: "
                    f"esperado '{alvo.id}{extensao}'"
                )
            )
        if alvo.entidade in ("capacidade", "spec"):
            erros += _erros_de_dominio(alvo, taxonomia)
    return erros


def _checar_datas_dos_marcos(alvos: list[Alvo]) -> list[Erro]:
    erros = []
    for alvo in alvos:
        if alvo.entidade != "marco":
            continue
        achado = _RE_DATA_DO_MARCO.fullmatch(alvo.id)
        data = alvo.dados.get("data")
        if achado and isinstance(data, str) and data != achado.group(1):
            mensagem = f"data '{data}' difere da data do id ('{achado.group(1)}')"
            erros.append(alvo.erro(mensagem))
    return erros


# --------------------------------------------------------------------------
# Referências entre entidades
# --------------------------------------------------------------------------


def _refs_dos_trechos(dados: dict) -> set[str]:
    trechos = dados.get("trechos")
    if not isinstance(trechos, list):
        return set()
    return {
        t["ref"]
        for t in trechos
        if isinstance(t, dict) and isinstance(t.get("ref"), str)
    }


@dataclass
class Indices:
    """Ids existentes por tipo, mais os trechos de cada norma."""

    ids: dict[str, set[str]]
    trechos: dict[str, set[str]]
    ilegiveis: dict[str, set[str]]
    fora_da_branch: set[str]

    @classmethod
    def de(cls, acervo: Acervo) -> "Indices":
        ids = {
            "norma": {n.id for n in acervo.normas if n.id},
            "marco": {m.id for m in acervo.marcos if m.id},
            "capacidade": {c.id for c in acervo.capacidades if c.id},
            "spec": {s.id for s in acervo.specs if s.id},
            "adr": {a.id for a in acervo.adrs if a.id},
            "caso": {c.id for c in acervo.casos if c.id},
            "requisito": {r.id for r in acervo.requisitos if r.id},
        }
        trechos = {n.id: _refs_dos_trechos(n.dados) for n in acervo.normas if n.id}
        fora = {
            tipo
            for tipo in SO_NA_CANONICA
            if not (acervo.root / "docs" / PASTAS[tipo]).is_dir()
        }
        return cls(ids, trechos, acervo.ilegiveis, fora)

    def indeterminado(self, tipo: str, identificador: str) -> bool:
        """A referência pode apontar para um arquivo que não foi lido."""
        if tipo in self.fora_da_branch:
            return True
        if tipo == "requisito":
            return bool(self.ilegiveis.get("specs"))
        if tipo == "caso":
            return bool(self.ilegiveis.get("casos"))
        return identificador in self.ilegiveis.get(PASTAS[tipo], ())


def _sugestao(valor: str, existentes: set[str]) -> str:
    parecidos = difflib.get_close_matches(valor, sorted(existentes), n=1)
    return f" (parecido: {parecidos[0]})" if parecidos else ""


def _problema_de_referencia(tipo: str, valor: str, indices: Indices) -> str | None:
    identificador, _, trecho = valor.partition("#")
    if not identificador.startswith(PREFIXOS_DE_REFERENCIA[tipo]):
        return None  # formato errado: o esquema já acusa
    if indices.indeterminado(tipo, identificador):
        return None
    existentes = indices.ids[tipo]
    if identificador not in existentes:
        rotulo = ROTULOS_DE_REFERENCIA.get(tipo, tipo)
        sugestao = _sugestao(identificador, existentes)
        return f"{rotulo} inexistente '{valor}'{sugestao}"
    if (
        tipo == "norma"
        and trecho
        and trecho not in indices.trechos.get(identificador, ())
    ):
        trechos = ", ".join(sorted(indices.trechos[identificador])) or "nenhum"
        return (
            f"trecho '{trecho}' não existe na norma {identificador} "
            f"(trechos: {trechos})"
        )
    return None


def _valores_de_referencia(valor: object) -> list[str]:
    return [valor] if isinstance(valor, str) else como_lista(valor)


def _referencias_do_alvo(alvo: Alvo) -> Iterator[tuple[str, str, str]]:
    """(campo, tipo, valor) de cada referência que o alvo declara."""
    for campo, tipo in CAMPOS_COM_REFERENCIA.get(alvo.entidade, ()):
        for valor in _valores_de_referencia(alvo.dados.get(campo)):
            yield campo, tipo, valor
    if alvo.entidade == "caso":
        for valor in como_lista(alvo.dados.get("fonte")):
            if _RE_REFERENCIA_NORMA.fullmatch(valor):
                yield "fonte", "norma", valor


def _checar_referencias(alvos: list[Alvo], indices: Indices) -> list[Erro]:
    erros = []
    for alvo in alvos:
        for campo, tipo, valor in _referencias_do_alvo(alvo):
            problema = _problema_de_referencia(tipo, valor, indices)
            if problema:
                erros.append(alvo.erro(f"{campo}: {problema}"))
    return erros


# --------------------------------------------------------------------------
# Regras de specs, requisitos e casos
# --------------------------------------------------------------------------


def _regras_da_spec(spec: Item) -> list[Erro]:
    dados = spec.dados
    mensagens = []
    if not (
        como_lista(dados.get("modulos")) or como_lista(dados.get("modulos_planejados"))
    ):
        mensagens.append(
            "modulos e modulos_planejados vazios: informe ao menos um módulo"
        )
    if dados.get("status") != "rascunho":
        for campo in ("seams", "invariantes"):
            valor = dados.get(campo)
            if isinstance(valor, list) and not valor:
                mensagens.append(f"{campo}: não pode ser vazio fora do status rascunho")
    return [Erro(spec.arquivo, mensagem) for mensagem in mensagens]


def _faltas_do_estado_pronto(dados: dict) -> list[str]:
    if dados.get("estado") != "pronto":
        return []
    faltam = [c for c in ("evidencia", "visto_em") if not como_texto(dados.get(c))]
    if not faltam:
        return []
    nomes = ", ".join(ROTULOS_DE_CAMPO[campo] for campo in faltam)
    return [f"estado 'pronto' exige Evidência e Visto em (faltando: {nomes})"]


def _faltas_da_fonte_do_pronto(dados: dict, confiancas: dict[str, str]) -> list[str]:
    """Norma de confiança secundária não sustenta sozinha um estado pronto."""
    if dados.get("estado") != "pronto":
        return []
    normas = [valor.partition("#")[0] for valor in como_lista(dados.get("normas"))]
    conhecidas = [confiancas[norma] for norma in normas if norma in confiancas]
    if conhecidas and all(c == "secundaria" for c in conhecidas):
        mensagem = (
            "estado 'pronto' não pode se apoiar só em norma de confiança "
            "secundaria: cite uma fonte oficial"
        )
        return [mensagem]
    return []


def _faltas_do_slug(spec: Item, req: Requisito) -> list[str]:
    da_spec = _RE_ID_SPEC.fullmatch(spec.id)
    do_requisito = _RE_ID_REQUISITO.fullmatch(req.id)
    if not da_spec or not do_requisito or do_requisito.group(1) == da_spec.group(2):
        return []
    slug = da_spec.group(2)
    return [
        (
            f"o slug '{do_requisito.group(1)}' difere do slug da spec '{slug}' "
            f"(esperado REQ-{slug}-NN)"
        )
    ]


def _regras_do_requisito(
    spec: Item, req: Requisito, rascunho: bool, confiancas: dict[str, str]
) -> list[Erro]:
    dados = req.dados
    mensagens = []
    if not rascunho and not como_texto(dados.get("cenario")):
        mensagens.append("Cenário é obrigatório quando a spec não está em rascunho")
    if dados.get("estado") == "nao-se-aplica" and not como_texto(dados.get("nota")):
        mensagens.append("estado 'nao-se-aplica' exige Nota com o motivo")
    if dados.get("tipo", "normativo") == "normativo" and not como_lista(
        dados.get("normas")
    ):
        mensagens.append(
            "tipo normativo exige ao menos uma Norma (ou 'Tipo: qualidade')"
        )
    mensagens += _faltas_do_estado_pronto(dados)
    mensagens += _faltas_da_fonte_do_pronto(dados, confiancas)
    mensagens += _faltas_do_slug(spec, req)
    return [Erro(spec.arquivo, f"{req.id}: {m}", req.linha) for m in mensagens]


def _checar_specs(acervo: Acervo) -> list[Erro]:
    por_arquivo: dict[str, list[Requisito]] = defaultdict(list)
    for req in acervo.requisitos:
        por_arquivo[req.arquivo].append(req)
    # Vazio fora da branch canônica (sem docs/normas/): a regra não se aplica.
    confiancas = {
        norma.id: norma.dados.get("confianca")
        for norma in acervo.normas
        if norma.id and isinstance(norma.dados.get("confianca"), str)
    }
    erros = []
    for spec in acervo.specs:
        erros += _regras_da_spec(spec)
        rascunho = spec.dados.get("status") == "rascunho"
        for req in por_arquivo.get(spec.arquivo, []):
            erros += _regras_do_requisito(spec, req, rascunho, confiancas)
    return erros


def _checar_casos_cobertos(acervo: Acervo) -> list[Erro]:
    return [
        Erro(caso.arquivo, f"{_rotulo_do_caso(caso)}: estado 'coberto' exige visto_em")
        for caso in acervo.casos
        if caso.dados.get("estado") == "coberto"
        and not como_texto(caso.dados.get("visto_em"))
    ]


# --------------------------------------------------------------------------
# Módulos
# --------------------------------------------------------------------------


def _erros_de_modulos_da_spec_ou_capacidade(root: Path, item: Item) -> list[Erro]:
    erros = []
    for nome in como_lista(item.dados.get("modulos")):
        if not modulo_existe(root, nome):
            erros.append(
                Erro(
                    item.arquivo,
                    f"modulos: módulo '{nome}' não existe ({nome}/__manifest__.py "
                    "ausente); se ainda não foi mesclado, use modulos_planejados",
                )
            )
    for nome in como_lista(item.dados.get("modulos_planejados")):
        if modulo_existe(root, nome):
            erros.append(
                Erro(
                    item.arquivo,
                    f"modulos_planejados: módulo '{nome}' já existe; mova para modulos",
                )
            )
    return erros


def _checar_modulos(acervo: Acervo) -> list[Erro]:
    root = acervo.root
    erros = []
    planejados: set[str] = set()
    for item in [*acervo.specs, *acervo.capacidades]:
        erros += _erros_de_modulos_da_spec_ou_capacidade(root, item)
        planejados.update(como_lista(item.dados.get("modulos_planejados")))
    if acervo.ilegiveis.get("specs") or acervo.ilegiveis.get("capacidades"):
        return erros  # módulos planejados desconhecidos: não acusar os casos
    for caso in acervo.casos:
        nome = caso.dados.get("modulo")
        if (
            isinstance(nome, str)
            and nome not in planejados
            and not modulo_existe(root, nome)
        ):
            erros.append(
                Erro(
                    caso.arquivo,
                    f"{_rotulo_do_caso(caso)}: modulo '{nome}' não existe nem consta "
                    "em modulos_planejados de alguma spec ou capacidade",
                )
            )
    return erros


# --------------------------------------------------------------------------
# Arquivos de docs/: caracteres tipográficos e links
# --------------------------------------------------------------------------


def _arquivos_de_docs(root: Path) -> list[Path]:
    """Arquivos de docs/ fora de docs/scripts e dos ocultos."""
    base = root / "docs"
    achados = []
    for caminho in sorted(base.rglob("*")):
        partes = caminho.relative_to(base).parts
        oculto = any(parte.startswith(".") for parte in partes)
        if caminho.is_file() and partes[0] != "scripts" and not oculto:
            achados.append(caminho)
    return achados


def _erros_tipograficos(arquivo: str, conteudo: str) -> list[Erro]:
    erros = []
    for numero, linha in enumerate(conteudo.split("\n"), start=1):
        for achado in _RE_TIPOGRAFICO.finditer(linha):
            codigo = ord(achado.group(0))
            mensagem = (
                f"caractere tipográfico proibido U+{codigo:04X} "
                f"({TIPOGRAFICOS[codigo]}) na coluna {achado.start() + 1}; "
                "use pontuação ASCII"
            )
            erros.append(Erro(arquivo, mensagem, numero))
    return erros


def _alvo_do_link(conteudo: str) -> str:
    conteudo = conteudo.strip()
    if conteudo.startswith("<"):
        return conteudo[1:].split(">", 1)[0]
    return conteudo.split(maxsplit=1)[0] if conteudo else ""


def _problema_de_link(root: Path, arquivo: Path, alvo: str) -> str | None:
    if _RE_ESQUEMA_DE_URL.match(alvo) or alvo.startswith("//"):
        return None
    caminho = unquote(alvo.split("#", 1)[0].split("?", 1)[0])
    if not caminho:
        return None  # só âncora
    base = root if caminho.startswith("/") else arquivo.parent
    destino = Path(os.path.normpath(base / caminho.lstrip("/")))
    if existe(root, destino):
        return None
    return f"link relativo quebrado: '{alvo}' (arquivo não encontrado)"


def _erros_de_links(root: Path, caminho: Path, conteudo: str) -> list[Erro]:
    arquivo = caminho.relative_to(root).as_posix()
    erros = []
    for numero, linha in gerar_index.linhas_fora_de_cercas(conteudo):
        neutra = _RE_CODIGO_NA_LINHA.sub(lambda m: "x" * len(m.group(0)), linha)
        for achado in _RE_LINK.finditer(neutra):
            problema = _problema_de_link(root, caminho, _alvo_do_link(achado.group(1)))
            if problema:
                erros.append(Erro(arquivo, problema, numero))
    return erros


def _checar_arquivos_de_docs(root: Path, arquivos: list[Path]) -> list[Erro]:
    erros = []
    for caminho in arquivos:
        arquivo = caminho.relative_to(root).as_posix()
        try:
            conteudo = gerar_index.ler_arquivo(caminho)
        except gerar_index.ErroLeitura as exc:
            binario = isinstance(exc.__cause__, UnicodeDecodeError)
            if not binario or caminho.suffix.lower() in EXTENSOES_DE_TEXTO:
                erros.append(Erro(arquivo, exc.mensagem))
            continue
        erros += _erros_tipograficos(arquivo, conteudo)
        if caminho.suffix.lower() == ".md":
            erros += _erros_de_links(root, caminho, conteudo)
    return erros


# --------------------------------------------------------------------------
# DEVELOP.md dos módulos e INDEX.md
# --------------------------------------------------------------------------


def _arquivos_develop(root: Path) -> list[Path]:
    return sorted(root.glob("*/readme/DEVELOP.md"))


def _checar_develop(root: Path, arquivos: list[Path]) -> list[Erro]:
    erros = []
    for caminho in arquivos:
        arquivo = caminho.relative_to(root).as_posix()
        try:
            conteudo = gerar_index.ler_arquivo(caminho)
        except gerar_index.ErroLeitura as exc:
            erros.append(Erro(arquivo, exc.mensagem))
            continue
        for numero, linha in enumerate(conteudo.split("\n"), start=1):
            for achado in _RE_CAMINHO_DE_DOCS.finditer(linha):
                if not existe(root, root / achado.group(0)):
                    mensagem = f"caminho '{achado.group(0)}' não existe"
                    erros.append(Erro(arquivo, mensagem, numero))
    return erros


def _checar_index(root: Path) -> list[Erro]:
    destino = root / gerar_index.ARQUIVO_INDEX
    comando = "rode python docs/scripts/gerar_index.py"
    try:
        atual = destino.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [Erro(gerar_index.ARQUIVO_INDEX, f"INDEX.md ausente: {comando}")]
    except (OSError, UnicodeDecodeError):
        return [Erro(gerar_index.ARQUIVO_INDEX, f"INDEX.md ilegível: {comando}")]
    if atual != gerar_index.gerar(root):
        return [Erro(gerar_index.ARQUIVO_INDEX, f"INDEX.md desatualizado: {comando}")]
    return []


# --------------------------------------------------------------------------
# Orquestração
# --------------------------------------------------------------------------


def validar(root: Path) -> tuple[list[Erro], int]:
    """Roda todas as regras; devolve (erros ordenados, arquivos verificados)."""
    _nomes_em.cache_clear()
    acervo = gerar_index.carregar(root)
    erros = list(acervo.erros)
    validadores = _carregar_esquemas(root, erros)
    alvos = _alvos(acervo)
    erros += _checar_taxonomia(acervo)
    erros += _checar_esquemas(alvos, validadores)
    erros += _checar_vocabularios(alvos, acervo.taxonomia)
    erros += _checar_ids_unicos(alvos)
    erros += _checar_nomes_de_arquivo(alvos, acervo.taxonomia)
    erros += _checar_datas_dos_marcos(alvos)
    erros += _checar_referencias(alvos, Indices.de(acervo))
    erros += _checar_specs(acervo)
    erros += _checar_casos_cobertos(acervo)
    erros += _checar_modulos(acervo)
    arquivos = _arquivos_de_docs(root)
    develop = _arquivos_develop(root)
    erros += _checar_arquivos_de_docs(root, arquivos)
    erros += _checar_develop(root, develop)
    erros += _checar_index(root)
    ordenados = sorted(set(erros), key=lambda e: (e.arquivo, e.linha or 0, e.mensagem))
    return ordenados, len(arquivos) + len(develop)


def _plural(quantidade: int, singular: str, plural: str) -> str:
    return f"{quantidade} {singular if quantidade == 1 else plural}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Valida normas, marcos, capacidades, specs, casos e links de docs/."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=gerar_index.RAIZ_PADRAO,
        help="pasta que contém docs/ (padrão: a raiz deste repositório)",
    )
    root = parser.parse_args(argv).root.resolve()
    if not (root / "docs").is_dir():
        sys.stderr.write(f"{root}: pasta docs/ não encontrada\n")
        return 1
    erros, total = validar(root)
    if not erros:
        sys.stdout.write(
            f"ok: {_plural(total, 'arquivo validado', 'arquivos validados')}\n"
        )
        return 0
    for erro in erros:
        sys.stderr.write(f"{erro}\n")
    total_erros = _plural(len(erros), "erro", "erros")
    com_erro = _plural(len({e.arquivo for e in erros}), "arquivo", "arquivos")
    sys.stderr.write(f"{total_erros} em {com_erro}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
