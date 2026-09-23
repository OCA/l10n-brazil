On the company:

- set the city: companies in a city served by NotaControl (see
  `erpbrasil.edoc.provedores.notacontrol.MUNICIPIOS`) get **NFS-e via
  NotaControl** checked automatically;
- configure the ICP-Brasil A1 certificate and the municipal registration (IM),
  both required by the webservice;
- choose the **NotaControl Signature** algorithm: the official batch sample
  uses RSA-SHA1; switch to RSA-SHA256 if the webservice rejects the signature;
- **Simulate NotaControl** is for rehearsals only: the DPS is signed and packed
  as it would be sent, nothing is transmitted and the document is flagged
  SIMULADO.
