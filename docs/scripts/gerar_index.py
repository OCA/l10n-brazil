"""Gera docs/INDEX.md e lê o acervo de docs/ para o validador.

Uso, de qualquer pasta:

    python docs/scripts/gerar_index.py [--root DIR]

O índice é determinístico: o mesmo conteúdo de docs/ produz sempre o mesmo
texto. O validar.py reaproveita carregar() para ler o acervo e gerar() para
conferir se o docs/INDEX.md está atualizado.
"""

import argparse
import datetime
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

import yaml

RAIZ_PADRAO = Path(__file__).resolve().parents[2]
ARQUIVO_INDEX = "docs/INDEX.md"
CABECALHO = (
    "<!-- GERADO por docs/scripts/gerar_index.py a partir de docs/; "
    "nao editar a mao -->"
)
LIMITE_RESUMO = 120

# Campos de um requisito, escritos como "- Campo: valor" no corpo da spec.
# Chave: nome sem acento e em minúsculas. Valor: (campo, separadores de lista).
CAMPOS_REQUISITO = {
    "norma": ("normas", ";"),
    "tipo": ("tipo", None),
    "comportamento": ("comportamento", None),
    "cenario": ("cenario", None),
    "teste alvo": ("teste_alvo", None),
    "casos": ("casos", ",;"),
    "estado": ("estado", None),
    "evidencia": ("evidencia", None),
    "visto em": ("visto_em", None),
    "pr": ("pr", None),
    "obsoleto desde": ("obsoleto_desde", None),
    "nota": ("nota", None),
}
NOMES_CAMPOS = (
    "Norma, Tipo, Comportamento, Cenário, Teste alvo, Casos, Estado, "
    "Evidência, Visto em, PR, Obsoleto desde, Nota"
)

# Erros de YAML que os autores mais cometem, com a correção em português.
DICAS_YAML = {
    "mapping values are not allowed here": (
        "texto com dois-pontos seguido de espaço precisa estar entre aspas"
    ),
}

_TAG_MERGE = "tag:yaml.org,2002:merge"
_RE_CERCA = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_RE_TITULO = re.compile(r"^(#{1,6})\s+(\S.*?)\s*$")
_RE_REQUISITO = re.compile(r"^(REQ-[^\s:]+)\s*:\s*(\S.*)$")
_RE_CAMPO = re.compile(r"^[-*+]\s+([^:]+?)\s*:\s*(.*?)\s*$")


@dataclass(frozen=True)
class Erro:
    """Problema encontrado: arquivo (relativo à raiz), mensagem e linha opcional."""

    arquivo: str
    mensagem: str
    linha: int | None = None

    def __str__(self) -> str:
        onde = f"linha {self.linha}: " if self.linha else ""
        return f"{self.arquivo}: {onde}{self.mensagem}"


class ErroLeitura(Exception):
    """Falha ao ler um arquivo; leva a mensagem e a linha do problema."""

    def __init__(self, mensagem: str, linha: int | None = None) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.linha = linha


@dataclass
class Item:
    """Um objeto lido de docs/: norma, marco, capacidade, spec, caso ou ADR."""

    arquivo: str
    dados: dict
    corpo: str = ""
    linha_corpo: int = 1
    indice: int | None = None

    @property
    def id(self) -> str:
        valor = self.dados.get("id")
        return valor if isinstance(valor, str) else ""


@dataclass
class Requisito:
    """Requisito extraído do corpo de uma spec."""

    arquivo: str
    spec: str
    linha: int
    dados: dict

    @property
    def id(self) -> str:
        valor = self.dados.get("id")
        return valor if isinstance(valor, str) else ""


@dataclass
class Taxonomia:
    """Códigos de docs/taxonomia; None quando o arquivo não pôde ser lido."""

    dominios: dict[str, str] | None = None
    tipos_norma: list[str] | None = None
    vocabularios: dict[str, list[str]] | None = None


@dataclass
class Acervo:
    """Tudo o que foi lido de docs/ e os problemas achados na leitura."""

    root: Path
    normas: list[Item] = field(default_factory=list)
    marcos: list[Item] = field(default_factory=list)
    capacidades: list[Item] = field(default_factory=list)
    specs: list[Item] = field(default_factory=list)
    adrs: list[Item] = field(default_factory=list)
    casos: list[Item] = field(default_factory=list)
    requisitos: list[Requisito] = field(default_factory=list)
    taxonomia: Taxonomia = field(default_factory=Taxonomia)
    erros: list[Erro] = field(default_factory=list)
    # Por tipo de entidade, os nomes de arquivo que não puderam ser lidos.
    ilegiveis: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))

    def rel(self, caminho: Path) -> str:
        return caminho.relative_to(self.root).as_posix()

    def falha(self, caminho: Path, exc: ErroLeitura, tipo: str | None = None) -> None:
        self.erros.append(Erro(self.rel(caminho), exc.mensagem, exc.linha))
        if tipo:
            self.ilegiveis[tipo].add(caminho.stem)


# --------------------------------------------------------------------------
# Leitura de arquivos
# --------------------------------------------------------------------------


class _Carregador(yaml.SafeLoader):
    """SafeLoader que recusa chave repetida no mesmo mapeamento."""

    def construct_mapping(self, node, deep=False):
        vistas = set()
        for no_chave, _no_valor in node.value:
            if no_chave.tag == _TAG_MERGE or not isinstance(no_chave, yaml.ScalarNode):
                continue
            if no_chave.value in vistas:
                raise yaml.constructor.ConstructorError(
                    None,
                    None,
                    f"chave repetida: {no_chave.value!r}",
                    no_chave.start_mark,
                )
            vistas.add(no_chave.value)
        return super().construct_mapping(node, deep=deep)


def normalizar(valor: object) -> object:
    """Troca datas do YAML por texto ISO e percorre listas e mapas."""
    if isinstance(valor, datetime.date):
        return valor.isoformat()
    if isinstance(valor, dict):
        return {chave: normalizar(item) for chave, item in valor.items()}
    if isinstance(valor, list):
        return [normalizar(item) for item in valor]
    return valor


def _descrever_erro_yaml(exc: yaml.MarkedYAMLError) -> str:
    problema = str(exc.problem or exc)
    dica = DICAS_YAML.get(problema)
    return f"YAML inválido: {problema}" + (f" ({dica})" if dica else "")


def ler_yaml(conteudo: str, deslocamento: int = 0) -> object:
    """Lê YAML seguro; `deslocamento` soma linhas quando o YAML não começa na 1."""
    try:
        bruto = yaml.load(conteudo, Loader=_Carregador)
    except yaml.MarkedYAMLError as exc:
        marca = exc.problem_mark
        linha = marca.line + 1 + deslocamento if marca else None
        raise ErroLeitura(_descrever_erro_yaml(exc), linha) from exc
    except (yaml.YAMLError, ValueError) as exc:
        raise ErroLeitura(f"YAML inválido: {exc}") from exc
    return normalizar(bruto)


def ler_arquivo(caminho: Path) -> str:
    try:
        return caminho.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ErroLeitura(f"o arquivo não está em UTF-8 ({exc.reason})") from exc
    except OSError as exc:
        raise ErroLeitura(f"não foi possível ler o arquivo ({exc.strerror})") from exc


def _ler_mapa_yaml(caminho: Path) -> dict:
    dados = ler_yaml(ler_arquivo(caminho))
    if dados is None:
        raise ErroLeitura("arquivo vazio")
    if not isinstance(dados, dict):
        raise ErroLeitura("o conteúdo deve ser um objeto YAML (chave: valor)")
    return dados


def _ler_lista_yaml(caminho: Path) -> list:
    dados = ler_yaml(ler_arquivo(caminho))
    if dados is None:
        raise ErroLeitura("arquivo vazio")
    if not isinstance(dados, list):
        raise ErroLeitura("o conteúdo deve ser uma lista de casos")
    return dados


def dividir_frontmatter(conteudo: str) -> tuple[str, str, int]:
    """Separa (yaml, corpo, linha onde o corpo começa) de um Markdown."""
    linhas = conteudo.split("\n")
    if linhas[0].rstrip() != "---":
        raise ErroLeitura("frontmatter ausente: o arquivo deve começar com '---'", 1)
    for posicao in range(1, len(linhas)):
        if linhas[posicao].rstrip() == "---":
            bruto = "\n".join(linhas[1:posicao])
            corpo = "\n".join(linhas[posicao + 1 :])
            return bruto, corpo, posicao + 2
    raise ErroLeitura("frontmatter sem fechamento: falta a segunda linha '---'", 1)


def _ler_frontmatter(caminho: Path) -> tuple[dict, str, int]:
    bruto, corpo, linha_corpo = dividir_frontmatter(ler_arquivo(caminho))
    dados = ler_yaml(bruto, deslocamento=1)
    if not isinstance(dados, dict):
        raise ErroLeitura("o frontmatter deve ser um objeto YAML (chave: valor)", 2)
    return dados, corpo, linha_corpo


def _marca_de_cerca(linha: str) -> tuple[str, str] | None:
    """(marca, resto) se a linha abre ou fecha um bloco cercado, senão None."""
    achado = _RE_CERCA.match(linha)
    if not achado:
        return None
    marca, resto = achado.groups()
    if marca[0] == "`" and "`" in resto:
        return None  # trecho de código na própria linha, não um bloco
    return marca, resto


def _fecha_cerca(achado: tuple[str, str] | None, cerca: str) -> bool:
    if achado is None:
        return False
    marca, resto = achado
    return not resto.strip() and marca[0] == cerca[0] and len(marca) >= len(cerca)


def linhas_fora_de_cercas(
    conteudo: str, linha_inicial: int = 1
) -> Iterator[tuple[int, str]]:
    """Gera (número, texto) das linhas fora de blocos de código (``` ou ~~~)."""
    cerca = ""
    for numero, linha in enumerate(conteudo.split("\n"), start=linha_inicial):
        linha = linha.rstrip("\r")
        achado = _marca_de_cerca(linha)
        if cerca:
            if _fecha_cerca(achado, cerca):
                cerca = ""
        elif achado:
            cerca = achado[0]
        else:
            yield numero, linha


# --------------------------------------------------------------------------
# Taxonomia
# --------------------------------------------------------------------------


def _ler_taxonomia(acervo: Acervo, nome: str) -> object | None:
    caminho = acervo.root / "docs" / "taxonomia" / nome
    if not caminho.is_file():
        acervo.erros.append(Erro(acervo.rel(caminho), "arquivo ausente"))
        return None
    try:
        return ler_yaml(ler_arquivo(caminho))
    except ErroLeitura as exc:
        acervo.falha(caminho, exc)
        return None


def _itens_com_codigo(acervo: Acervo, nome: str, chave: str) -> list[dict] | None:
    dados = _ler_taxonomia(acervo, nome)
    if dados is None:
        return None
    arquivo = f"docs/taxonomia/{nome}"
    itens = dados.get(chave) if isinstance(dados, dict) else None
    if not isinstance(itens, list) or not all(
        isinstance(item, dict) and isinstance(item.get("codigo"), str) for item in itens
    ):
        acervo.erros.append(
            Erro(arquivo, f"esperado '{chave}' como lista de itens com 'codigo'")
        )
        return None
    repetidos = [c for c, n in Counter(i["codigo"] for i in itens).items() if n > 1]
    if repetidos:
        acervo.erros.append(Erro(arquivo, f"códigos repetidos: {', '.join(repetidos)}"))
    return itens


def _ler_vocabularios(acervo: Acervo) -> dict[str, list[str]] | None:
    dados = _ler_taxonomia(acervo, "vocabularios.yaml")
    if dados is None:
        return None
    if not isinstance(dados, dict) or not all(
        isinstance(valores, dict) for valores in dados.values()
    ):
        acervo.erros.append(
            Erro(
                "docs/taxonomia/vocabularios.yaml",
                "esperado um mapa de vocabulários, cada um com 'código: descrição'",
            )
        )
        return None
    return {str(nome): [str(c) for c in valores] for nome, valores in dados.items()}


def _carregar_taxonomia(acervo: Acervo) -> None:
    dominios = _itens_com_codigo(acervo, "dominios.yaml", "dominios")
    if dominios is not None:
        acervo.taxonomia.dominios = {
            item["codigo"]: str(item.get("nome", "")) for item in dominios
        }
    tipos = _itens_com_codigo(acervo, "tipos-norma.yaml", "tipos_norma")
    if tipos is not None:
        acervo.taxonomia.tipos_norma = [item["codigo"] for item in tipos]
    acervo.taxonomia.vocabularios = _ler_vocabularios(acervo)


# --------------------------------------------------------------------------
# Entidades
# --------------------------------------------------------------------------


def _arquivos(root: Path, *padroes: str) -> list[Path]:
    achados = {c for p in padroes for c in (root / "docs").glob(p) if c.is_file()}
    return sorted(c for c in achados if c.name.lower() != "readme.md")


def _carregar_yamls(acervo: Acervo, pasta: str) -> list[Item]:
    itens = []
    for caminho in _arquivos(acervo.root, f"{pasta}/*.yaml", f"{pasta}/*.yml"):
        try:
            itens.append(Item(acervo.rel(caminho), _ler_mapa_yaml(caminho)))
        except ErroLeitura as exc:
            acervo.falha(caminho, exc, pasta)
    return itens


def _carregar_markdowns(acervo: Acervo, tipo: str, padrao: str) -> list[Item]:
    itens = []
    for caminho in _arquivos(acervo.root, padrao):
        try:
            dados, corpo, linha_corpo = _ler_frontmatter(caminho)
        except ErroLeitura as exc:
            acervo.falha(caminho, exc, tipo)
            continue
        itens.append(Item(acervo.rel(caminho), dados, corpo, linha_corpo))
    return itens


def _carregar_casos(acervo: Acervo) -> None:
    for caminho in _arquivos(acervo.root, "casos/*.yaml", "casos/*.yml"):
        arquivo = acervo.rel(caminho)
        try:
            itens = _ler_lista_yaml(caminho)
        except ErroLeitura as exc:
            acervo.falha(caminho, exc, "casos")
            continue
        for indice, dados in enumerate(itens):
            if isinstance(dados, dict):
                acervo.casos.append(Item(arquivo, dados, indice=indice))
                continue
            acervo.erros.append(Erro(arquivo, f"item {indice + 1} não é um objeto"))
            acervo.ilegiveis["casos"].add(caminho.stem)


def carregar(root: Path) -> Acervo:
    """Lê todo o acervo de root/docs; problemas de leitura ficam em acervo.erros."""
    acervo = Acervo(root=root)
    _carregar_taxonomia(acervo)
    acervo.normas = _carregar_yamls(acervo, "normas")
    acervo.marcos = _carregar_yamls(acervo, "marcos")
    acervo.capacidades = _carregar_markdowns(
        acervo, "capacidades", "capacidades/*/*.md"
    )
    acervo.specs = _carregar_markdowns(acervo, "specs", "specs/*/*.md")
    acervo.adrs = _carregar_markdowns(acervo, "decisoes", "decisoes/*.md")
    _carregar_casos(acervo)
    for spec in acervo.specs:
        acervo.requisitos.extend(extrair_requisitos(acervo, spec))
    return acervo


# --------------------------------------------------------------------------
# Requisitos no corpo da spec
# --------------------------------------------------------------------------


@dataclass
class _Entrada:
    linha: int
    nome: str
    valor: str


@dataclass
class _Secao:
    id: str
    titulo: str
    linha: int
    entradas: list[_Entrada] = field(default_factory=list)


def _normalizar_nome(nome: str) -> str:
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", nome) if not unicodedata.combining(c)
    )
    return " ".join(sem_acento.casefold().split())


def _abrir_secao(
    acervo: Acervo, spec: Item, cabecalho: re.Match, linha: int
) -> _Secao | None:
    nivel, titulo = len(cabecalho.group(1)), cabecalho.group(2)
    if nivel != 3 or not titulo.startswith("REQ-"):
        return None
    achado = _RE_REQUISITO.match(titulo)
    if not achado:
        mensagem = (
            "cabeçalho de requisito malformado: use '### REQ-<slug>-NN: <título>'"
        )
        acervo.erros.append(Erro(spec.arquivo, mensagem, linha))
        return None
    return _Secao(achado.group(1), achado.group(2), linha)


def _ler_entrada(
    secao: _Secao, ultima: _Entrada | None, conteudo: str, linha: int
) -> _Entrada | None:
    """Campo '- Nome: valor', ou continuação recuada do campo anterior."""
    campo = _RE_CAMPO.match(conteudo)
    if campo:
        entrada = _Entrada(linha, campo.group(1), campo.group(2))
        secao.entradas.append(entrada)
        return entrada
    if ultima is not None and conteudo[:1] in (" ", "\t") and conteudo.strip():
        ultima.valor = f"{ultima.valor} {conteudo.strip()}".strip()
        return ultima
    return None


def _dividir_secoes(acervo: Acervo, spec: Item) -> list[_Secao]:
    secoes: list[_Secao] = []
    atual: _Secao | None = None
    ultima: _Entrada | None = None
    for linha, conteudo in linhas_fora_de_cercas(spec.corpo, spec.linha_corpo):
        cabecalho = _RE_TITULO.match(conteudo)
        if cabecalho and len(cabecalho.group(1)) <= 3:
            atual = _abrir_secao(acervo, spec, cabecalho, linha)
            ultima = None
            if atual:
                secoes.append(atual)
        elif atual is not None:
            ultima = _ler_entrada(atual, ultima, conteudo, linha)
    return secoes


def _converter_valor(valor: str, separadores: str | None) -> object:
    if separadores is None:
        return valor
    partes = re.split(f"[{re.escape(separadores)}]", valor)
    return [parte.strip() for parte in partes if parte.strip()]


def _montar_requisito(acervo: Acervo, spec: Item, secao: _Secao) -> Requisito:
    dados: dict = {"id": secao.id, "titulo": secao.titulo}
    for entrada in secao.entradas:
        definicao = CAMPOS_REQUISITO.get(_normalizar_nome(entrada.nome))
        if definicao is None:
            mensagem = (
                f"{secao.id}: campo desconhecido '{entrada.nome}' "
                f"(aceitos: {NOMES_CAMPOS})"
            )
            acervo.erros.append(Erro(spec.arquivo, mensagem, entrada.linha))
            continue
        campo, separadores = definicao
        if campo in dados:
            mensagem = f"{secao.id}: campo '{entrada.nome}' repetido"
            acervo.erros.append(Erro(spec.arquivo, mensagem, entrada.linha))
            continue
        dados[campo] = _converter_valor(entrada.valor, separadores)
    return Requisito(spec.arquivo, spec.id, secao.linha, dados)


def extrair_requisitos(acervo: Acervo, spec: Item) -> list[Requisito]:
    """Lê as seções '### REQ-<slug>-NN: <título>' do corpo da spec."""
    return [
        _montar_requisito(acervo, spec, secao)
        for secao in _dividir_secoes(acervo, spec)
    ]


# --------------------------------------------------------------------------
# Geração do índice
# --------------------------------------------------------------------------


def como_texto(valor: object) -> str:
    """Valor escalar como texto de uma linha só (vazio quando None)."""
    return "" if valor is None else " ".join(str(valor).split())


def como_lista(valor: object) -> list[str]:
    """Itens de texto de uma lista; qualquer outro valor vira lista vazia."""
    if not isinstance(valor, list):
        return []
    return [item for item in valor if isinstance(item, str)]


def _contar(valor: object) -> int:
    return len(valor) if isinstance(valor, list) else 0


def _celula(valor: object) -> str:
    return como_texto(valor).replace("|", "\\|")


def _resumo(valor: object, limite: int = LIMITE_RESUMO) -> str:
    conteudo = como_texto(valor)
    if len(conteudo) <= limite:
        return conteudo
    return conteudo[:limite].rstrip() + "..."


def _link(item: Item) -> str:
    destino = quote(item.arquivo.removeprefix("docs/"), safe="/")
    return f"[{item.id}]({destino})"


def _com_id(itens: Iterable[Item]) -> list[Item]:
    return sorted((i for i in itens if i.id), key=lambda item: item.id)


def _tabela(cabecalho: list[str], linhas: list[list[str]]) -> list[str]:
    if not linhas:
        return ["Nenhum registro."]
    saida = [
        "| " + " | ".join(cabecalho) + " |",
        "| " + " | ".join("---" for _ in cabecalho) + " |",
    ]
    saida.extend("| " + " | ".join(linha) + " |" for linha in linhas)
    return saida


def _citacoes(itens: list[Item]) -> dict[str, list[tuple[Item, bool]]]:
    """Módulo -> itens que o citam, com a marca de que vem de modulos_planejados."""
    mapa: dict[str, list[tuple[Item, bool]]] = defaultdict(list)
    for item in _com_id(itens):
        existentes = como_lista(item.dados.get("modulos"))
        for nome in existentes:
            mapa[nome].append((item, False))
        for nome in como_lista(item.dados.get("modulos_planejados")):
            if nome not in existentes:
                mapa[nome].append((item, True))
    return mapa


def _celula_citacoes(citacoes: list[tuple[Item, bool]]) -> str:
    return ", ".join(
        _link(item) + (" (planejado)" if planejado else "")
        for item, planejado in citacoes
    )


def _secao_modulos(acervo: Acervo) -> list[str]:
    por_spec = _citacoes(acervo.specs)
    por_capacidade = _citacoes(acervo.capacidades)
    linhas = [
        [
            f"`{nome}`",
            _celula_citacoes(por_spec.get(nome, [])),
            _celula_citacoes(por_capacidade.get(nome, [])),
        ]
        for nome in sorted(set(por_spec) | set(por_capacidade))
    ]
    return ["## Módulos", "", *_tabela(["Módulo", "Specs", "Capacidades"], linhas)]


def _contagem_por_estado(requisitos: list[Requisito], ordem: list[str]) -> str:
    contagem = Counter(como_texto(req.dados.get("estado")) for req in requisitos)
    chaves = [estado for estado in ordem if estado in contagem]
    chaves += sorted(set(contagem) - set(ordem))
    return ", ".join(f"{chave or '?'}: {contagem[chave]}" for chave in chaves) or "-"


def _secao_specs(acervo: Acervo) -> list[str]:
    ordem = list((acervo.taxonomia.vocabularios or {}).get("estado", []))
    capacidades = {cap.id: cap for cap in _com_id(acervo.capacidades)}
    linhas = []
    for spec in _com_id(acervo.specs):
        requisitos = [r for r in acervo.requisitos if r.arquivo == spec.arquivo]
        id_cap = como_texto(spec.dados.get("capacidade"))
        cap = capacidades.get(id_cap)
        linhas.append(
            [
                _link(spec),
                _celula(spec.dados.get("titulo")),
                _celula(spec.dados.get("status")),
                _link(cap) if cap else _celula(id_cap),
                _contagem_por_estado(requisitos, ordem),
            ]
        )
    cabecalho = ["Spec", "Título", "Status", "Capacidade", "Requisitos por estado"]
    return ["## Specs", "", *_tabela(cabecalho, linhas)]


def _dominio_da_capacidade(cap: Item) -> str:
    achado = re.match(r"^CAP-([A-Z]+)-", cap.id)
    return como_texto(cap.dados.get("dominio")) or (achado.group(1) if achado else "")


def _ordem_dominios(acervo: Acervo, presentes: Iterable[str]) -> list[str]:
    conhecidos = list(acervo.taxonomia.dominios or {})
    usados = set(presentes)
    return [c for c in conhecidos if c in usados] + sorted(usados - set(conhecidos))


def _tabela_capacidades(caps: list[Item], specs: dict[str, list[Item]]) -> list[str]:
    linhas = [
        [
            _link(cap),
            _celula(cap.dados.get("titulo")),
            _celula(cap.dados.get("status")),
            ", ".join(_link(spec) for spec in specs.get(cap.id, [])),
        ]
        for cap in caps
    ]
    return _tabela(["Capacidade", "Título", "Status", "Specs"], linhas)


def _secao_capacidades(acervo: Acervo) -> list[str]:
    grupos: dict[str, list[Item]] = defaultdict(list)
    for cap in _com_id(acervo.capacidades):
        grupos[_dominio_da_capacidade(cap)].append(cap)
    if not grupos:
        return ["## Capacidades", "", "Nenhum registro."]
    specs: dict[str, list[Item]] = defaultdict(list)
    for spec in _com_id(acervo.specs):
        specs[como_texto(spec.dados.get("capacidade"))].append(spec)
    nomes = acervo.taxonomia.dominios or {}
    saida = ["## Capacidades"]
    for dominio in _ordem_dominios(acervo, grupos):
        titulo = f"{dominio} - {nomes[dominio]}" if nomes.get(dominio) else dominio
        saida += ["", f"### {titulo}", ""]
        saida += _tabela_capacidades(grupos[dominio], specs)
    return saida


def _secao_normas(acervo: Acervo) -> list[str]:
    linhas = [
        [
            _link(norma),
            _celula(norma.dados.get("titulo")),
            _celula(norma.dados.get("tipo")),
            _celula(norma.dados.get("status")),
            _celula(norma.dados.get("confianca")),
            str(_contar(norma.dados.get("trechos"))),
            str(_contar(norma.dados.get("artefatos"))),
        ]
        for norma in _com_id(acervo.normas)
    ]
    cabecalho = [
        "Norma",
        "Título",
        "Tipo",
        "Status",
        "Confiança",
        "Trechos",
        "Artefatos",
    ]
    return ["## Normas", "", *_tabela(cabecalho, linhas)]


def _secao_marcos(acervo: Acervo) -> list[str]:
    marcos = sorted(
        _com_id(acervo.marcos),
        key=lambda marco: (como_texto(marco.dados.get("data")), marco.id),
    )
    linhas = [
        [
            _celula(marco.dados.get("data")),
            _link(marco),
            _celula(_resumo(marco.dados.get("o_que_muda"))),
            _celula(marco.dados.get("status_data")),
        ]
        for marco in marcos
    ]
    cabecalho = ["Data", "Marco", "O que muda", "Status da data"]
    return ["## Marcos", "", *_tabela(cabecalho, linhas)]


def _secao_casos(acervo: Acervo) -> list[str]:
    linhas = [
        [
            _celula(caso.id),
            _celula(caso.dados.get("titulo")),
            f"`{como_texto(caso.dados.get('modulo'))}`",
            _celula(caso.dados.get("estado")),
            _celula(", ".join(como_lista(caso.dados.get("requisitos")))),
        ]
        for caso in _com_id(acervo.casos)
    ]
    cabecalho = ["Caso", "Título", "Módulo", "Estado", "Requisitos"]
    return ["## Casos de QA", "", *_tabela(cabecalho, linhas)]


def _secao_decisoes(acervo: Acervo) -> list[str]:
    linhas = [
        [
            _link(adr),
            _celula(adr.dados.get("titulo")),
            _celula(adr.dados.get("data")),
            _celula(adr.dados.get("status")),
        ]
        for adr in _com_id(acervo.adrs)
    ]
    cabecalho = ["Decisão", "Título", "Data", "Status"]
    return ["## Decisões", "", *_tabela(cabecalho, linhas)]


def renderizar(acervo: Acervo) -> str:
    """Monta o texto do INDEX.md a partir de um acervo já lido."""
    introducao = [
        "# Índice das especificações",
        "",
        (
            "Gerado a partir de `docs/`. Para atualizar: "
            "`python docs/scripts/gerar_index.py`."
        ),
    ]
    blocos = [
        [CABECALHO],
        introducao,
        _secao_modulos(acervo),
        _secao_specs(acervo),
        _secao_capacidades(acervo),
        _secao_normas(acervo),
        _secao_marcos(acervo),
        _secao_casos(acervo),
        _secao_decisoes(acervo),
    ]
    return "\n\n".join("\n".join(bloco) for bloco in blocos) + "\n"


def gerar(root: Path) -> str:
    """Texto do docs/INDEX.md para o acervo que está em root/docs."""
    return renderizar(carregar(root))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gera docs/INDEX.md a partir de docs/."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=RAIZ_PADRAO,
        help="pasta que contém docs/ (padrão: a raiz deste repositório)",
    )
    root = parser.parse_args(argv).root.resolve()
    if not (root / "docs").is_dir():
        sys.stderr.write(f"{root}: pasta docs/ não encontrada\n")
        return 1
    destino = root / ARQUIVO_INDEX
    destino.write_text(gerar(root), encoding="utf-8", newline="\n")
    sys.stdout.write(f"{destino}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
