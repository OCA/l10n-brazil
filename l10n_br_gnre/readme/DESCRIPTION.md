Emissão e transmissão da GNRE (Guia Nacional de Recolhimento de Tributos
Estaduais) a partir dos dados que o Odoo já tem, sem redigitação no portal.

O módulo cobre os dois modos que a operação exige: uma guia por documento, para
quem não tem inscrição estadual no destino e precisa que a guia paga acompanhe a
mercadoria, e a guia consolidada do período, para quem tem inscrição e apura.

A escolha entre os dois é dado, não código: fica no cadastro de regras por UF.

A guia é transmitida ao Portal GNRE pelo webservice do Manual de Integração do
Contribuinte (lote 2.00), com o certificado digital da empresa. O resultado do
lote traz o PDF da guia, a linha digitável, o código de barras e o Pix copia e
cola, que ficam gravados na guia.

As obrigações têm uma análise por UF, origem do valor (ICMS ST ou DIFAL), receita
e mês de vencimento, em tabela dinâmica e gráfico.
