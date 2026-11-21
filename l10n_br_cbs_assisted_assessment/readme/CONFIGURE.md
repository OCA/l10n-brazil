Em _Configurações > Empresas_, abra a empresa e use a aba **Apuração
Assistida**, grupo **Transporte CBS**:

- **Ambiente**: produção restrita (`apuracao-cbs-prr/v2`) ou produção
  (`apuracao-cbs/v2`).
- **Client Id** e **Client Secret**: credenciais Receita Integra da matriz.
  Elas são pedidas por serviço, então não são necessariamente as mesmas da
  DeRE. O manual para gerá-las está em
  <https://arquivos.receitafederal.gov.br> em _Documentos > Técnicos >
  Receita Integra_.
- **URL de Callback**: gerada ao salvar a empresa (e na instalação, para as
  que já existiam) e exibida para copiar. Ela embute um segredo e é a URL
  informada como `urlRetorno`. Gire o token se a URL vazou; o giro invalida
  as solicitações ainda em processamento.

Dois requisitos vêm do gateway e não são impostos pelo addon:

- a URL de callback precisa ser alcançável na internet em **HTTPS**, com
  certificado válido. Uma instância atrás de proxy reverso precisa de
  `web.base.url` apontando para o endereço público; uma URL HTTP só gera um
  aviso no log, para a homologação poder ser exercitada numa instância de
  desenvolvimento;
- o endpoint de abertura aceita **4 chamadas por dia** por serviço e responde
  HTTP 429 acima disso. O addon conta as chamadas e recusa ultrapassar a
  cota.

Há duas ações agendadas. _Consultar e baixar solicitações pendentes_ roda a
cada 15 minutos e vem habilitada; _Abrir as solicitações diárias_ vem
desabilitada e abre as solicitações de débitos e créditos do período corrente
para cada empresa que tiver credenciais.
