Na linha de um documento fiscal (e também nas linhas de fatura, pedido de
venda e de compra), cada aba de imposto (ICMS, ISSQN, IPI etc.) passa a ter
o grupo "Manual", com os campos "Base" e "Value". O grupo só aparece quando o
imposto está presente na linha.

- Com os campos vazios, o cálculo automático continua igual.
- Com a base manual preenchida, o valor do imposto é calculado sobre ela.
- Com o valor manual preenchido, ele substitui o valor calculado.
- Os valores manuais acompanham a linha quando ela gera outro documento
  (ex.: pedido de venda → fatura).
- Para não poluir a tela, os grupos "Manual" só aparecem quando a opção
  "Allow Manual Tax Override" estiver marcada na operação fiscal
  (linha de operação) usada pela linha do documento. Os campos continuam
  funcionando normalmente mesmo com a opção desmarcada (ela só controla a
  visibilidade na tela).
- Uma retenção informada manualmente não é zerada pela regra de dispensa
  por valor mínimo (`withholding_min_value`): o valor informado é mantido
  mesmo quando for igual ou inferior ao mínimo configurado no imposto.
