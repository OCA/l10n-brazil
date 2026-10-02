**Na empresa**:

- **Certificado digital**: cadastre o certificado **A1** (ICP-Brasil) da empresa
  (módulo `l10n_br_fiscal_certificate`). Ele assina a DPS e os eventos e também
  autentica a conexão mTLS com o ADN. A chave privada é usada só em memória e em
  arquivo temporário com permissão restrita, e não é registrada em log.
- **Processador de documentos eletrônicos**: Odoo Community (`oca`).
- **Provedor de NFS-e**: Sefin Nacional (ADN) (`provedor_nfse = nacional`). Só as
  empresas com esse provedor emitem pelo ADN.
- **Ambiente da NFS-e**: Produção ou Homologação. No ADN a homologação se chama
  produção restrita e usa outro endereço. O documento copia o ambiente da
  empresa na criação, e você pode alterá-lo no próprio documento.
- **Cadastro da empresa**: CNPJ ou CPF, município (com código IBGE) e regime
  tributário (MEI, Simples Nacional ou regime normal), pois a DPS informa o
  município emissor e o regime do prestador.

**Série e numeração.** A série e o número do documento vêm do documento fiscal
(a série na linha de numeração da empresa). O número informado é o `nDPS`, e não
existe RPS: a numeração é livre e a chave da DPS, de 42 dígitos, é montada com
município, tipo de emissor, CNPJ/CPF, série e número.

**Município.** O município do prestador precisa estar conveniado ao padrão
nacional. Para testar, use o ambiente de homologação (produção restrita) com o
certificado da empresa.

**Dependências Python**: `nfelib`, `brazilfiscalreport`, `erpbrasil.assinatura`,
`requests` e `cryptography`.
