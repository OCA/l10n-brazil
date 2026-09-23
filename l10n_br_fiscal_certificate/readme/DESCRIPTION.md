Gerencia os certificados digitais A1 (e-CNPJ e e-NF-e) usados para assinar e
transmitir os documentos fiscais eletrônicos brasileiros.

O módulo não define um modelo próprio de certificado: ele estende o módulo
nativo `certificate` do Odoo (modelo `certificate.certificate`),
reaproveitando o armazenamento do arquivo PKCS#12 (`.pfx`/`.p12`), a extração
do certificado e da chave em PEM, o cálculo de validade e as telas do core, e
acrescenta o que é específico do Brasil:

- o escopo `l10n_br` ("Brazilian Fiscal"), que identifica os certificados
  fiscais brasileiros e filtra os certificados oferecidos nos campos de
  certificado do sistema;
- os campos calculados `owner_cnpj_cpf` (CNPJ/CPF do titular, lido do subject),
  `issuer_name` (emissor) e `name` (titular e validade);
- o campo `certificate_id` na empresa, exibido na página "Certificados" da aba
  Fiscal, que substitui os antigos `certificate_nfe_id` e
  `certificate_ecnpj_id`: agora cada empresa tem um único certificado;
- a herança de certificado entre empresas: uma filial sem certificado próprio
  usa o da matriz (campo calculado `certificate`), o que é aceito pela SEFAZ
  por terem a mesma raiz de CNPJ;
- os métodos `_get_br_certificate()` e `_get_br_ecertificate()`, ponto único
  de acesso ao certificado para assinatura e transmissão, com validação de
  vigência (e do CNPJ, quando a operação exige um e-CNPJ).

Esse ponto único de acesso é usado pelos módulos fiscais:

- `l10n_br_nfe`: assinatura e transmissão de NF-e e NFC-e, eventos de
  manifestação do destinatário (MDE) e inutilização de numeração;
- `l10n_br_mdfe`: assinatura e transmissão de MDF-e;
- `l10n_br_cte`: assinatura e transmissão de CT-e;
- `l10n_br_nfe_dfe`: distribuição de DF-e (consulta dos documentos por NSU);
- `l10n_br_nfse`: assinatura e transmissão de NFS-e;
- `l10n_br_ie_search`: consulta de inscrição estadual na SEFAZ.

A migração 18.0.2.0.0 converte automaticamente os certificados cadastrados no
modelo antigo (`l10n_br_fiscal.certificate`) para o modelo nativo, preservando
o arquivo, a senha e a empresa que os utilizava.
