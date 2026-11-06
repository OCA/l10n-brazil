Antes de apurar, configure no grupo de imposto (menu Contabilidade \>
Configuração \> Grupos de impostos), para cada empresa, a conta de
imposto a pagar e a conta de imposto a recuperar. Sem elas a apuração
não encerra.

1.  Vá em Contabilidade \> Lançamentos \> Apuração de Impostos e crie
    uma apuração informando grupo de imposto e período (o regime vem do
   grupo; contribuinte misto usa um grupo por regime).
2.  Clique em **Apurar**. As linhas de origem `Apurado das move lines`
    são montadas a partir dos lançamentos postados do período.
3.  Acrescente os ajustes manuais que não saem da contabilidade,
    informando o código da tabela 5.1.1 (`COD_AJ_APUR`) e a descrição. O
    quarto dígito do código classifica o ajuste, e o sistema recusa uma
    classificação que não bate com ele.
4.  Clique em **Encerrar**. O lançamento de encerramento transfere o
    saldo do período entre as contas do grupo de imposto.

A devolução é nota fiscal comum e segue o Guia Prático da EFD ICMS/IPI:
a devolução de compra (CFOP 5202/6202) soma ao débito do campo 02 do E110
e a devolução de venda (CFOP 1202/2202) soma ao crédito do campo 06. Cada
uma aparece na memória de cálculo em linha própria, marcada como
`Devolução`, ao lado da linha regular do mesmo imposto. Os campos 05 e 09
(estornos de crédito e de débito) são só a soma dos ajustes do E111, ou
seja, dos ajustes manuais com código da tabela 5.1.1.

Reapurar preserva os ajustes manuais e refaz apenas as linhas apuradas.

Período sem movimento também deve ser encerrado: é o que mantém a cadeia
de saldo credor sem buraco entre um período e o seguinte.
