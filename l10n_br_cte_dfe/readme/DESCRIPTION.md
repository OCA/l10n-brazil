# Monitor de CT-e (Distribuição de DF-e)

Este módulo monitora, baixa e processa os **Conhecimentos de Transporte Eletrônicos (CT-e, modelo 57)** emitidos contra o CNPJ da sua empresa (como tomadora, remetente, destinatária, expedidora ou recebedora), consultando o Web Service de Distribuição de DF-e do CT-e no Ambiente Nacional (`CTeDistribuicaoDFe`, NT 2015.002).

Ele estende o framework genérico `l10n_br_fiscal_dfe` com as particularidades do CT-e:

* **Sem resumo nem manifestação:** diferente da NF-e, o serviço do CT-e entrega o XML completo (`procCTe`) de imediato. Não existe `resCTe` nem Manifestação do Destinatário.
* **Busca só por NSU:** o serviço não aceita consulta por chave de acesso (`consChCTe` não existe).
* **Outros documentos do serviço:** CT-e OS (`procCTeOS`), GTV-e (`procGTVe`) e CT-e Simplificado (`procCTeSimp`) também são recebidos e guardados com seu XML. Só o CT-e modelo 57 pode ser importado como documento fiscal e impresso em DACTE.
* **Eventos:** cancelamento, carta de correção, comprovante de entrega, insucesso na entrega e prestação em desacordo são recebidos (`procEventoCTe`). O cancelamento marca o CT-e como cancelado.

## Principais Funcionalidades

* **Consulta automática (cron)** com os mesmos intervalos e controle de consumo indevido (cStat 656) do framework base.
* **Importação:** abre o assistente de importação de XML do `l10n_br_cte`, criando o `l10n_br_fiscal.document` de entrada.
* **DACTE:** gera o PDF a partir do XML com a biblioteca `brazilfiscalreport`.
* **Notificações** aos usuários inscritos quando novos CT-e de terceiros são encontrados.
