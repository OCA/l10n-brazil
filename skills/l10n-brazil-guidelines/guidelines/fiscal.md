# Parametrização fiscal com lastro normativo

Toda regra que decide CFOP, CST, CEST, NCM, alíquota ou operação fiscal referencia uma
norma ou tabela oficial (por id em `docs/normas/` quando houver spec) e usa os campos
que espelham essas tabelas. Critério por tag livre, campo de observação ou nome de
produto é recusado.

## Por quê

O motor fiscal espelha tabelas oficiais; uma regra sem lastro vira "funciona no meu
cliente" e quebra no seguinte. Revisor que não acha a norma não consegue aprovar.

## Exceções

Campo de uso interno sem efeito fiscal (agrupamento gerencial, rótulo de tela).

# Rejeição do fisco é dado, não exceção

Resposta do fisco com `cStat` de rejeição grava código, motivo e XML de resposta no
registro, e o documento ou evento muda de estado pela máquina de estados. Não levante
`UserError` que faça rollback do que foi enviado.

```python
# bad
if resposta.cStat != "135":
    raise UserError(resposta.xMotivo)

# good
evento.write(
    {
        "state": "rejected",
        "status_code": resposta.cStat,
        "status_name": resposta.xMotivo,
    }
)
return evento._notificar_rejeicao()
```

## Por quê

O rollback apaga a prova de que o envio aconteceu e a mensagem de erro some com a
transação. Rejeição é informação fiscal (o que o fisco disse, quando), não falha do
programa.

## Exceções

Falha de transporte (timeout, certificado inválido, DNS) pode levantar erro: não há
resposta do fisco a guardar. Fluxo síncrono de botão pode, depois de gravar, mostrar
aviso ao usuário.

# Data e hora do fisco em UTC

`dhRecbto`, `dhRegEvento` e qualquer data de protocolo vêm do XML com o fuso do emitente
(`-03:00`). Converta para UTC antes de gravar num `Datetime`; nunca descarte o offset.

## Por quê

`Datetime` do Odoo é UTC sem fuso. Gravar o valor local como se fosse UTC atrasa ou
adianta o protocolo em três horas no DANFE, no DACCE e na comparação com prazos.

# CNPJ e chave de acesso são texto

CNPJ, CPF e chave de acesso são strings `[0-9A-Z]`. Nunca `int(cnpj)`, nunca `"%014d"`,
nunca `re.sub(r"[^0-9]", "", valor)`. Limpe com remoção de pontuação (ou `isalnum`),
normalize com `.upper()`, valide e formate pela `erpbrasil.base`.

## Por quê

Desde julho de 2026 o CNPJ aceita letras nas 12 primeiras posições e a chave de acesso
carrega essas letras nas posições 7 a 20. Conversão para inteiro quebra; limpeza só de
dígitos descarta letras em silêncio e manda CNPJ errado ao fisco.

## Exceções

NSU, número do documento, série, RNTRC e inscrição estadual continuam numéricos e podem
ser validados como dígitos.

# Produção e homologação sem comparação frouxa

A escolha de URL, serviço ou certificado pelo ambiente usa o valor normalizado
(`str(tp_amb) == "1"` ou enum), e o teste cobre produção e homologação separadamente.

## Por quê

O ambiente chega ora como inteiro, ora como string ("1", 1, "producao"). Comparação
`ambiente == 1` com string cai sempre em homologação, e o documento "autorizado" não
existe para o fisco.

# Sequência de evento pelo maior número registrado

`nSeqEvento` da carta de correção é `max` dos eventos já registrados (como inteiro) mais
um; evento rejeitado por duplicidade (573) consome o número.

## Por quê

`max` sobre strings ordena "10" antes de "9": a décima primeira carta sai com sequência
errada e o fisco rejeita. Como o fisco já guardou o número rejeitado, reutilizá-lo
repete a rejeição.
