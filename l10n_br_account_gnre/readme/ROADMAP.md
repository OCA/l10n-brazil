O gatilho lê as linhas fiscais, e não as linhas de imposto contábeis. Isso é
deliberado: o DIFAL não gera `account.move.line` com `tax_line_id` próprio, e um
gatilho sobre as linhas de imposto simplesmente não o veria. O DIFAL vem do
`icms_destination_value` e o FCP de destino do `icmsfcp_value`, os mesmos campos
que a NF-e leva em `vICMSUFDest` e `vFCPUFDest`.

A conciliação da baixa depende do parceiro, porque o plano de contas tem uma
única conta de ICMS ST a recolher, sem segregação por UF. Quem precisar separar
por estado pode usar a conta a pagar da regra por UF.
