# Glossário

Vocabulário do domínio usado nas specs, nos casos e nas skills. Cada entrada
fixa o significado do termo e diz o que **evitar** usar como sinônimo, porque
é aí que revisor e autor se desencontram. Só na branch canônica.

## Estrutura

**Norma**: qualquer fonte que fixa um comportamento esperado: lei, nota
técnica, manual, leiaute, pronunciamento contábil, tabela oficial. Tem id
`N-<slug>` e trechos citáveis.
_Evitar_: "lei" para nota técnica ou manual; citar a norma inteira sem o trecho.

**Marco**: data em que algo passa a valer ou deixa de valer. Tem id
`M-<data>-<slug>` e aponta para as normas que o definem.
_Evitar_: "prazo" (é a visão de quem planeja) e "fase" (é um atributo do marco).

**Capacidade**: o que o ERP precisa saber fazer, independente de módulo
(`CAP-<DOM>-<slug>`).
_Evitar_: "feature" e "funcionalidade" como sinônimo de módulo.

**Requisito**: comportamento verificável de uma capacidade, com norma,
cenário, teste alvo e estado nesta série (`REQ-<slug>-NN`). Uma frase que um
revisor confere com sim ou não.
_Evitar_: requisito sem norma e sem `Tipo: qualidade`; "melhorar", "tratar
corretamente" e outros verbos que não se conferem.

**Spec**: documento que agrupa os requisitos de uma capacidade
(`SPEC-<DOM>-<slug>`), com seams e invariantes.
_Evitar_: spec por módulo (a unidade é a capacidade) e spec com plano de
entrega dentro.

**Seam**: fronteira pública onde o teste encosta (ação do usuário, método
público, cliente do webservice, arquivo importado).
_Evitar_: testar método privado; seam novo quando um existente alcança.

**Invariante**: o que nunca pode quebrar, qualquer que seja o requisito
implementado.
_Evitar_: confundir com requisito (invariante não tem estado).

**Estado**: situação de um requisito nesta série: `pronto`, `pr`, `parcial`,
`nada`, `nao-se-aplica`, `desconhecido`.
_Evitar_: "feito" ou "ok"; `pronto` sem teste nomeado e SHA.

**Evidência**: teste nomeado (`modulo/tests/arquivo.py::Classe::metodo`) ou
caso de QA ratificado, com o SHA em que foi visto passar (`Visto em`).
_Evitar_: link de PR como evidência (PR prova intenção, teste prova
comportamento); evidência de outro SHA.

**Caso de QA**: jornada verificável pela interface e por RPC
(`BR-<CAMADA>-<FAMILIA>-NNN`).
_Evitar_: "teste" para o caso de QA (teste é o unitário no módulo).

**Série**: versão do Odoo, igual ao nome da branch (14.0, 16.0, 18.0, 20.0).
_Evitar_: "versão" para a série (versão é a do módulo, no manifest).

**Branch canônica**: a série mais nova, onde moram normas, marcos, glossário e
skills.
_Evitar_: "master" ou "main" (a OCA não tem).

## Fiscal

**Documento fiscal**: NF-e, NFC-e, CT-e, MDF-e, NFS-e e congêneres, próprios
ou de terceiros.
_Evitar_: "nota" como termo genérico (CT-e e MDF-e não são notas).

**Evento**: ocorrência registrada junto ao fisco sobre um documento já
autorizado: cancelamento, carta de correção, manifestação do destinatário,
ciência, EPEC.
_Evitar_: "ocorrência" e "ajuste" como sinônimos; "evento" para mudança de
estado só local.

**Inutilização**: pedido ao fisco para inutilizar uma faixa de numeração não
usada. Tem protocolo próprio e não é evento.
_Evitar_: tratar inutilização como cancelamento ou como evento.

**Cancelamento**: evento que torna sem efeito um documento autorizado, dentro
do prazo da UF.
_Evitar_: "estornar" (é operação contábil) e "excluir".

**Carta de correção (CC-e)**: evento que corrige dados do documento que não
alteram valores, partes nem data de emissão; tem sequência (`nSeqEvento`).
_Evitar_: "retificação" (termo do SPED) e "nota complementar" (é outro documento).

**Chave de acesso**: identificador de 44 posições do documento fiscal
eletrônico; desde a NT Conjunta 2025.001, as posições 7 a 20 (CNPJ do
emitente) aceitam letras.
_Evitar_: "número da nota" (é só um dos campos da chave).

**CNPJ alfanumérico**: número de inscrição com letras e algarismos nas 12
primeiras posições e dois dígitos verificadores numéricos (módulo 11 sobre o
valor ASCII menos 48).
_Evitar_: "novo CNPJ" (os antigos continuam válidos) e "CNPJ com letras
vedadas" (a Receita não vedou letra alguma).

**Autorização**: resposta do fisco que dá validade ao documento (cStat 100).
_Evitar_: "aprovação" e "homologação" (homologação é o ambiente de teste).

**Homologação**: ambiente de teste do fisco (`tpAmb` 2), sem valor fiscal.
_Evitar_: usar "homologação" para a autorização em produção.

**Rejeição**: recusa do fisco a um documento ou evento, com código `cStat` e
motivo. É dado a registrar, não exceção a engolir.
_Evitar_: "erro" sem o código; tratar rejeição como falha de transporte.

**Apuração**: cálculo do tributo devido num período, com débitos, créditos,
ajustes e saldo.
_Evitar_: "fechamento" (é do período contábil) e "declaração" (é o arquivo
entregue).

**Obrigação acessória**: declaração ou arquivo entregue ao fisco (EFD ICMS/IPI,
EFD Contribuições, ECD, ECF, Reinf, DCTFWeb).
_Evitar_: "SPED" como sinônimo de uma obrigação específica.

## Processo

**Forward-port**: levar uma mudança de uma série mais antiga para uma mais
nova, com `oca-port`. A spec vai junto por passo explícito.
_Evitar_: reenviar à mão o mesmo PR por branch.

**Migração**: levar um módulo inteiro para uma série nova. A spec dele vem na
mesma leva.
_Evitar_: "porte" para migração de módulo (porte é de mudança pontual).

**Checkpoint**: entrega parcial com evidência; vira `parcial`, nunca `pronto`
por acumulação.
_Evitar_: contar checkpoints como completude da spec.
