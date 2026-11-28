1. As obrigações nascem da nota fiscal (com o `l10n_br_account_gnre`, na
   postagem da fatura) e aparecem em Fiscal, Obrigações de GNRE.
2. Em Fiscal, Gerar Guias GNRE, escolha o período de vencimento e as UFs: o
   assistente agrupa as obrigações pendentes em guias, respeitando o limite de
   100 itens por guia.
3. Na guia, use Transmitir GNRE. Guias selecionadas juntas vão no mesmo lote, e
   o portal devolve um recibo.
4. Use Consultar Resultado, ou espere a ação agendada que consulta os lotes
   pendentes a cada 30 minutos. Guia processada recebe o PDF, a linha
   digitável, o código de barras e o Pix; guia rejeitada mostra os motivos e
   pode ser transmitida de novo depois da correção.
5. Em Fiscal, Análise de GNRE, acompanhe os valores por UF, origem (ICMS ST ou
   DIFAL), receita e mês.
