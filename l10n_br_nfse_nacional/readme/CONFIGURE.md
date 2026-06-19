Após a instalação do módulo, configure a empresa nos seguintes pontos:

**1. Certificado Digital**

Cadastre o certificado digital da empresa (e-CNPJ ou A1) em:

Configurações → Empresas → \[Empresa\] → Certificados

O certificado é utilizado para autenticação mTLS em todas as chamadas à API SEFIN.

**2. Configurações da Empresa**

Acesse Configurações → Empresas → \[Empresa\] → NFS-e e defina:

- Provedor NFS-e: selecione ``NFS-e Nacional (SEFIN)``
- Ambiente NFS-e: ``Homologação`` para testes, ``Produção`` para uso real
- Verificação SSL: habilite em produção

**3. Códigos de Tributação**

Configure nos produtos ou linhas de serviço:

- NBS — Nomenclatura Brasileira de Serviços
- Código de Tributação Nacional ISS
- Código de Tributação Municipal
