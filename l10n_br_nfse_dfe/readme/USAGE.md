## Caixa de entrada

Acesse **Faturamento > Fiscal > Consultas DF-e > Third-party NFS-e**.

A listagem mostra as NFS-e em que a empresa é tomadora. O último NSU, a próxima consulta e o ambiente ficam na empresa, na aba **Fiscal > NFS-e DF-e**.

Em cada documento:

1. **XML**: baixa o arquivo nacional recebido do ADN.
2. **Importar**: abre o assistente de importação com o XML completo. O assistente cria um `l10n_br_fiscal.document` do tipo `SE` (entrada), com o prestador como emitente e uma linha de serviço. Se o prestador ainda não existe, ele é criado na confirmação a partir do `prest` da DPS (o `emit` só completa dados quando o CNPJ é o mesmo). O produto e a operação fiscal podem ser ajustados antes de confirmar. Se `l10n_br_account` estiver instalado, a confirmação existente do assistente gera a fatura de fornecedor.

A pesquisa específica aceita a chave de acesso de 50 dígitos ou um NSU. A nota é consultada na Sefin Nacional e os eventos no ADN. Não há manifestação do destinatário neste fluxo: a NFS-e nacional já chega com o XML da nota.
