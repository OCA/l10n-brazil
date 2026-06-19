Este módulo possui as seguintes dependências Python:

- ``nfelib`` — bindings xsdata para documentos fiscais brasileiros (NFS-e Nacional DPS v1.0)
- ``erpbrasil.assinatura`` — assinatura digital de documentos fiscais brasileiros
- ``requests`` — cliente HTTP para comunicação com a API REST da SEFIN
- ``cryptography`` — carregamento de certificados PKCS12 para autenticação mTLS
- ``brazilfiscalreport`` — geração local do DANFSE em PDF a partir do XML autorizado
- ``qrcode`` — geração de QR Code no DANFSE (dependência de ``brazilfiscalreport``)
