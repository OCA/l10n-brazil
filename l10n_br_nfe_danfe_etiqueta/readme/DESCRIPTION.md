This module prints the **DANFE Simplificado - Etiqueta** of an authorized
NF-e: the simplified DANFE in shipping label format (NT 2020.004; MOC 7.0
Anexo II, item 3.12), meant to be glued on the package handed to delivery
services such as Correios or JadLog.

The label carries the minimum fields required by the norm — the access key
with its CODE-128C barcode, the authorization protocol, number, series and
emission date, the issuer and the recipient with the delivery address — and
is rendered by the
[BrazilFiscalReport](https://github.com/Engenere/BrazilFiscalReport) library,
by default on the usual 100 x 150 mm thermal label paper.
