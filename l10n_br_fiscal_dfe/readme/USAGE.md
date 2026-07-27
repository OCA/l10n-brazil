## Painel (Banner)

O menu **Faturamento > Consultas DF-e > NF-e de Terceiros** exibe a lista
de documentos recebidos. No topo da tela, um banner mostra:

- **Última Consulta**: data e status da última consulta à SEFAZ
- **Próxima Consulta**: próxima consulta agendada e status da busca
  automática (ativa/desativada)
- **NSU**: progresso de sincronização (último NSU / NSU máximo) com
  indicadores Sincronizado/Pendente
- **Documentos Hoje**: documentos de terceiros recebidos hoje
- **Importação Pendente**: NF-e completas ainda não importadas como
  documento fiscal

O banner também exibe alertas quando o ambiente está em Homologação ou
quando há inatividade superior a 30 dias (após 60 dias sem consulta, a
SEFAZ para de gerar NSUs para o CNPJ).

## Consulta manual

- **Pesquisar Todos**: busca todos os documentos a partir do último NSU.
  Respeita o cooldown — se houver consulta agendada no futuro, exibe
  notificação com o tempo restante.
- **Pesquisa Específica**: abre assistente para buscar por chave de acesso
  (com validação do dígito verificador) ou por NSU específico.

## Documentos recebidos

Cada documento na lista mostra: tipo (NF-e Completa / Resumo da NF-e /
Cancelada/Denegada), chave de acesso, emitente, CNPJ, valor, CFOPs e
status de manifestação. Ações disponíveis nos botões da lista e formulário:

- **XML**: download do XML da NF-e completa
- **DANFE**: gera e baixa o DANFE em PDF
- **Importar**: importa a NF-e como documento fiscal (`l10n_br_fiscal.document`)
- **Manifestar**: abre assistente de manifestação do destinatário
- **Vincular Parceiro**: recomputa o parceiro pelo CNPJ da chave de acesso

Filtros disponíveis: NF-e Completa, Resumo, Cancelada/Denegada, Sem
Parceiro, Data de Emissão. Agrupamento por Parceiro, Data de Emissão ou
Empresa.

## Download em lote

Na lista de documentos, selecione múltiplos registros e use
**Ação > Download XMLs (zip)** para baixar todos os XMLs completos em um
arquivo zip.

## Manifestação automática

Com a opção **Manifestação Automática do Destinatário (NF-e)** habilitada
na empresa, o módulo envia automaticamente uma ciência da operação para cada
resumo de NF-e recebido. O envio é feito via `queue_job` no canal
`root.dfe`.

## Log de Distribuição

Acessível pelo botão de link no card "Última Consulta" do banner, o log
registra cada interação com a SEFAZ incluindo o XML SOAP de requisição e
resposta completos, útil para depuração de problemas. Filtros disponíveis:
Sucesso, Informação, Aviso, Erro, Com Dados SOAP.
