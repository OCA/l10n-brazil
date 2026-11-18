---
id: SPEC-CAD-cnpj-alfanumerico
capacidade: CAP-CAD-identificacao-cnpj
titulo: CNPJ alfanumérico no cadastro, na validação e na chave de acesso
status: em-revisao
normas:
  - N-IN-RFB-2229-2024#formato
  - N-RFB-PR-CNPJ-ALFANUMERICO#q1
  - N-RFB-PR-CNPJ-ALFANUMERICO#q2
  - N-RFB-PR-CNPJ-ALFANUMERICO#q14
  - N-NT-CONJUNTA-2025.001#item-5
  - N-NT-CONJUNTA-2025.001#campos-cnpj
  - N-NT-2026.004#schema
marcos:
  - M-2026-07-01-cnpj-alfanumerico
dominios: [CAD]
modulos: []
modulos_planejados:
  - l10n_br_base
  - l10n_br_fiscal
  - l10n_br_nfe
  - l10n_br_fiscal_dfe
bibliotecas:
  - erpbrasil.base
  - nfelib
seams:
  - Criação e escrita de parceiro e de empresa pela interface e por RPC, pelo campo do CNPJ e pelos derivados formatado e sem máscara
  - Funções públicas de validação e formatação de CNPJ da biblioteca erpbrasil.base, e a classe de chave de acesso
  - Geração e validação da chave de acesso do documento fiscal, na confirmação do documento e na importação de XML
  - Consultas e eventos enviados ao fisco que carregam o CNPJ da empresa (distribuição de DF-e, manifestação, consulta de cadastro)
invariantes:
  - Todo CNPJ numérico válido hoje continua válido, com a mesma máscara e o mesmo dígito verificador
  - O valor sem máscara é sempre maiúsculo e só contém [0-9A-Z]; a comparação de duplicidade usa esse valor
  - Nenhuma rotina converte CNPJ em inteiro nem limpa o valor com uma expressão que remove letras
questoes_abertas:
  - texto: Os leiautes do SPED (EFD ICMS/IPI, ECD) e os layouts CNAB dos bancos já aceitam letras no campo de inscrição?
    dono: TODO(mantenedor)
  - texto: A nfelib das versões usadas por CT-e e MDF-e já traz o padrão alfanumérico do CNPJ e da chave?
    dono: TODO(mantenedor)
---

# CNPJ alfanumérico no cadastro, na validação e na chave de acesso

## Resumo

Desde julho de 2026 a Receita inscreve CNPJs com letras nas 12 primeiras
posições. A localização precisa aceitar e validar esse número no cadastro,
gravá-lo normalizado, detectar duplicidade sem depender da máscara, e levá-lo
intacto à chave de acesso e às consultas ao fisco. O dígito verificador segue o
módulo 11 com o valor ASCII menos 48 de cada caractere, o que mantém válido
todo CNPJ numérico existente.

## Escopo e fora de escopo

Entra: parceiro e empresa, biblioteca de validação, chave de acesso dos
documentos fiscais, consultas e eventos com CNPJ da empresa. Fora: CPF,
inscrição estadual, consulta de cadastro na Receita (capacidades próprias),
layouts CNAB e leiautes do SPED (questão aberta até os órgãos publicarem).

## Requisitos

### REQ-cnpj-alfanumerico-01: o cadastro aceita CNPJ alfanumérico válido

- Norma: N-IN-RFB-2229-2024#formato; N-RFB-PR-CNPJ-ALFANUMERICO#q2; N-RFB-PR-CNPJ-ALFANUMERICO#q14
- Comportamento: parceiro ou empresa com CNPJ cujas 12 primeiras posições estão em [0-9A-Z] e cujos dois dígitos verificadores batem com o módulo 11 (ASCII menos 48) é gravado, com máscara AA.AAA.AAA/AAAA-DV no campo formatado e só caracteres alfanuméricos no campo sem máscara.
- Cenário: dado um parceiro pessoa jurídica, quando gravo o CNPJ "99.XYZ.888/0001-50", então o campo formatado fica "99.XYZ.888/0001-50" e o campo sem máscara fica "99XYZ888000150"; o mesmo vale para "12ABC34501DE35" (exemplo da nota técnica) e para o CNPJ numérico "44.556.677/0001-86".
- Teste alvo: l10n_br_base/tests/test_cnpj_alfanumerico.py::CNPJAlfanumericoTest::test_partner_valid_alphanumeric_cnpj
- Casos: BR-BASE-CNPJALFA-001
- Estado: pr
- PR: #5246
- Nota: o teste já existe na migração do módulo para esta série; o estado vira pronto quando o PR for mesclado e o teste for visto passando nesta branch.

### REQ-cnpj-alfanumerico-02: CNPJ alfanumérico com dígito verificador errado é recusado

- Norma: N-RFB-PR-CNPJ-ALFANUMERICO#q14
- Comportamento: gravar um CNPJ cujo dígito verificador não bate com o módulo 11 (ASCII menos 48) levanta erro de validação com mensagem para o usuário; nada é gravado.
- Cenário: dado um parceiro pessoa jurídica, quando gravo "99.XYZ.888/0001-51", então recebo erro de CNPJ inválido e o parceiro não é criado.
- Teste alvo: l10n_br_base/tests/test_cnpj_alfanumerico.py::CNPJAlfanumericoTest::test_company_invalid_alphanumeric_cnpj
- Casos: BR-BASE-CNPJALFA-002
- Estado: pr
- PR: #5246

### REQ-cnpj-alfanumerico-03: qualquer letra de A a Z é aceita nas 12 primeiras posições

- Norma: N-RFB-PR-CNPJ-ALFANUMERICO#q1
- Comportamento: a validação não veda nenhuma letra; um CNPJ com I, O, U, Q ou F nas 12 primeiras posições e dígito verificador correto é válido.
- Cenário: dado um CNPJ com a letra I na raiz e dígito verificador correto pelo módulo 11, quando valido, então o resultado é válido.
- Teste alvo: erpbrasil.base: tests/test_tools_fiscal.py (letras antes vedadas)
- Estado: pr
- PR: erpbrasil/erpbrasil.base#67
- Nota: a versão 2.4.2 da biblioteca recusa I, O, U, Q e F, restrição que a Receita não adotou. Quando a correção for publicada, o módulo passa a exigir essa versão mínima em requirements.

### REQ-cnpj-alfanumerico-04: o valor gravado sem máscara é maiúsculo

- Norma: N-RFB-PR-CNPJ-ALFANUMERICO#q2; N-NT-CONJUNTA-2025.001#campos-cnpj
- Comportamento: letras digitadas em minúsculas no CNPJ são convertidas para maiúsculas ao gravar, no campo principal, no campo sem máscara e na chave Pix do tipo CNPJ; o XML e as consultas ao fisco só recebem [0-9A-Z].
- Cenário: dado um parceiro pessoa jurídica, quando gravo "99.xyz.888/0001-50", então o campo sem máscara fica "99XYZ888000150" e o formatado "99.XYZ.888/0001-50".
- Teste alvo: l10n_br_base/tests/test_cnpj_alfanumerico.py::CNPJAlfanumericoTest::test_partner_lowercase_cnpj_is_uppercased
- Estado: nada
- Nota: a normalização atual remove a pontuação e preserva a caixa; a validação aceita minúsculas, mas o valor minúsculo não casa com a chave de acesso nem passa no padrão dos leiautes.

### REQ-cnpj-alfanumerico-05: duplicidade é detectada sem depender da máscara nem da caixa

- Tipo: qualidade
- Comportamento: dois parceiros com o mesmo CNPJ, escritos com máscara diferente ou caixa diferente, são tratados como duplicados pela regra de unicidade; CNPJs distintos continuam permitidos.
- Cenário: dado um parceiro com "99.XYZ.888/0001-50", quando tento criar outro com "99xyz888000150", então recebo o erro de CNPJ duplicado.
- Teste alvo: l10n_br_base/tests/test_duplicate_cnpj.py::TestDuplicateCnpj::test_dup_different_format
- Estado: pr
- PR: #5246
- Nota: o teste existente cobre máscara diferente com CNPJ numérico; o caso de caixa diferente depende do REQ-cnpj-alfanumerico-04.

### REQ-cnpj-alfanumerico-06: a chave de acesso aceita as letras do CNPJ do emitente

- Norma: N-NT-CONJUNTA-2025.001#item-5; N-NT-2026.004#schema
- Comportamento: a geração e a validação da chave de acesso de 44 posições aceitam [0-9]{6}[A-Z0-9]{12}[0-9]{26}, com dígito verificador por módulo 11 sobre o valor ASCII menos 48; a importação de XML lê a chave inteira do identificador do documento, letras incluídas.
- Cenário: dado um emitente com CNPJ "12ABC34501DE35", quando gero a chave de acesso de uma NF-e, então as posições 7 a 20 trazem "12ABC34501DE35", o dígito verificador confere, e a importação do XML dessa nota devolve a mesma chave de 44 posições.
- Teste alvo: erpbrasil.base: tests/test_chave_edoc.py (chave alfanumérica)
- Estado: pr
- PR: erpbrasil/erpbrasil.base#67
- Nota: além da biblioteca, a importação de XML nos módulos de NF-e, CT-e e MDF-e extrai a chave do identificador com uma expressão só de dígitos e trunca a chave alfanumérica; é a próxima correção nesta spec, com teste alvo no módulo de NF-e.

### REQ-cnpj-alfanumerico-07: consultas e eventos ao fisco levam o CNPJ sem máscara e com as letras

- Norma: N-NT-CONJUNTA-2025.001#campos-cnpj
- Comportamento: distribuição de DF-e, manifestação do destinatário e consulta de cadastro usam o CNPJ da empresa sem pontuação e sem remover letras; a verificação de documento próprio compara o CNPJ da empresa com as posições 7 a 20 da chave.
- Cenário: dada uma empresa com CNPJ "12ABC34501DE35", quando consulto a distribuição de DF-e, então a consulta sai com "12ABC34501DE35"; e uma NF-e emitida por ela é reconhecida como documento próprio.
- Teste alvo: l10n_br_fiscal_dfe/tests/test_dfe_alphanumeric_cnpj.py (a criar)
- Estado: nada
- Nota: hoje essas rotinas limpam o CNPJ com uma expressão que remove tudo que não é dígito, o que descarta as letras.

## Divergências em relação a outras séries

- 16.0 e 18.0: REQ-01, REQ-02 e REQ-05 estão prontos (o teste de CNPJ alfanumérico está mesclado); REQ-03, REQ-04, REQ-06 e REQ-07 no mesmo estado desta série.
- 14.0: não verificado.

## Questões abertas

Ver o frontmatter. Enquanto SPED e CNAB não publicarem leiaute, os campos de
inscrição desses arquivos ficam fora desta spec.

## Histórico

- 2026-10-04: primeira versão, a partir da varredura do código feita em
  2026-09-30 e das normas listadas. Serve de exemplo da estrutura de specs.
