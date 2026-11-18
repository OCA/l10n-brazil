# Erro esperado dentro de mute_logger

Teste que provoca rejeição, exceção ou aviso envolve a chamada em
`mute_logger("odoo.addons.<modulo>...")` (ou o logger que emite), para que nenhum
WARNING ou ERROR esperado chegue ao log do CI.

## Por quê

O CI da OCA roda o checklog: um WARNING no log reprova o job mesmo com "0 failed". O CI
fica vermelho sem teste falhando, e a causa só aparece lendo o log.

# Assertiva compara com valor conhecido de fora

Toda assertiva compara com um valor literal esperado, vindo de norma, exemplo oficial ou
caso real anonimizado, escrito no teste. Helper que devolve lista vazia, assertiva que
compara o resultado com ele mesmo ou vetor gerado pelo código testado não contam como
cobertura.

```python
# bad
self.assertEqual(doc.document_key, doc._generate_key())

# good
self.assertEqual(doc.document_key, "35260112ABC34501DE35550010000001231837291450")
```

## Por quê

Teste tautológico passa com qualquer bug. Abrir o helper antes de creditar cobertura é
parte da revisão.

# Resposta do fisco gravada, não inventada

Mock de webservice devolve uma resposta real gravada (XML de autorização, rejeição ou
evento, com `cStat` e `xMotivo` verdadeiros), nunca um objeto que devolve o que o teste
quer. Rejeição também tem fixture.

## Por quê

A regra de negócio está em como o módulo lê a resposta do fisco; um mock que inventa o
retorno testa o mock. Fixture real também documenta o protocolo para quem vem depois.

## Exceções

Teste de transporte (timeout, certificado) pode simular a falha sem XML.

# Testar com o usuário que vai usar

Ação de usuário, job da fila e endpoint de API são testados com
`with_user(<usuario do perfil>)`, não como superusuário.

## Por quê

Como superusuário o teste esconde falta de ACL, de regra de registro e de e-mail do
remetente (`message_post` sem autor), que só explodem em produção.

# Dado demo conferido no fim

Teste de módulo com dado demo ou `post_init_hook` confere por ORM ou SQL o estado final
esperado (documento autorizado, fatura postada, picking validado), não só que a
instalação terminou.

## Por quê

Um WARNING no carregamento do demo descarta o arquivo inteiro e a instalação termina com
exit 0. Demo deve reproduzir o ciclo de vida completo, não só rascunhos.

# Teste externo só vê comportamento observável

Teste por RPC ou E2E chama só métodos públicos e confere estado observável (campos,
registros, mensagens). Método com underscore não é alcançável por RPC e não vira seam.

## Por quê

O ORM externo recusa método privado; teste que depende dele não roda fora do processo.
Comportamento que só se vê por método privado precisa virar jornada pública ou teste
unitário.
