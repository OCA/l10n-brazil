O acesso se divide entre **Usuário DeRE** (trabalho diário) e **Gerente
DeRE** (menus de configuração e credenciais da Receita Integra). Conceda
o grupo de gerente só a quem configura o gateway.

No formulário da empresa, abra a aba **DeRE** e preencha:

1. Regime tributário principal (`regTribPrinc`) e regime secundário
   opcional
2. Natureza da tributação (`indNatTrib`) e atividades das tabelas
   oficiais 21, 31 ou 41
3. Plano referencial (`planoCtaRef`) e frequência de encerramento
   (`freqEncerr`)
4. Ambiente da Receita Integra. A produção restrita usa
   `https://api.receitafederal.gov.br/prr-dere` com
   `POST /v1/recepcao/lotes` e `GET /v1/consulta/lotes/{protocol}`.
   Sobrescreva a URL-base e os caminhos só quando a produção for
   publicada. Produção (`tpAmb` 1) fica bloqueada enquanto a URL
   apontar para esse host restrito. O token usa HTTP Basic
   (`client_id` / `client_secret`) e `grant_type=client_credentials`.
   Só gerentes leem esses segredos. O token de acesso é cacheado por
   empresa. Gerentes podem ligar **Permitir excluir registros DeRE
   aceitos** enquanto `tpAmb` for 2, para testes de implementação
   apagarem um mês ou um período de tabela. Isso não anula recibos na
   RFB e é ignorado em produção (`tpAmb` 1).
5. Versão da aplicação (`verAplic`) enviada em `ideEvento`.
6. Certificado A1 ICP-Brasil: é o campo **Certificado** da página
   **Certificados** da aba Fiscal (`l10n_br_fiscal_certificate`). Uma
   filial sem certificado próprio usa o da matriz. A geração do XML não
   precisa dele; o envio precisa.
7. Deixe habilitada a ação agendada **DeRE: consultar resultados dos
   lotes enviados** (a cada 2 minutos). Ela só consulta lotes cuja
   janela de backoff já venceu.
8. Se o contribuinte deve enviar D-1106, ligue **Sujeito ao D-1106**,
   mapeie ao menos uma conta do PGCC para um `codTrib` oficial de
   D-1106, marque as contas de investimento como **Investimento de
   reserva técnica DeRE** e cadastre cada `idAtivo`. A flag só registra
   a intenção: geração, encerramento e ordem de envio exigem esse
   mapeamento no PGCC (MS1135 / MS1147). Mantenha um ativo por conta
   para **Gerar D-1106** preencher valores a partir dos lançamentos.
   Opcionalmente defina **Conta de rendimento da reserva DeRE** na
   conta de investimento, para cupons que nunca passam nessa conta.
9. Se o contribuinte deve enviar D-1121, ligue **Sujeito ao D-1121** e
   marque **Dedutível na DeRE** nas operações fiscais cujos documentos
   entram no D-1121. A flag só vale para operações de entrada (compras,
   serviços tomados); uma operação de saída não aceita a marcação. Ela
   não tem relação com **Impostos dedutíveis**, da aba Conta da mesma
   operação, que trata o crédito do imposto na contabilização. A
   **Atividade da dedução DeRE** (`tpAtiv`) da operação sobrepõe o
   padrão do regime. Contas cujo `codTrib` está na lista oficial do
   D-1121 também exigem o evento.

Os menus de catálogo ficam em **Fiscal → Configuração → DeRE**:
Atividades, Códigos de Tributação e Ativos de Reserva Técnica.

Em **Fiscal → DeRE → Períodos de Tabela**, crie a vigência que cubra os
meses a declarar. D-1001, D-1011 e o snapshot do PGCC ficam ali e são
reutilizados por toda declaração mensal em vigor. Edite o snapshot só
no período de tabela, e só antes do D-1011 ser aceito. O formulário
mensal mostra as mesmas contas como contexto somente leitura do D-1101.

Em cada **grupo de contas** usado como nó sintético DeRE, preencha a
aba **DeRE** (`cCtaRef`, natureza) quando o código referencial oficial
diferir do prefixo. Os grupos ancestrais das contas analíticas
mapeadas são exportados automaticamente; no grupo, um `cCtaRef` vazio
usa o prefixo e a natureza do primeiro dígito. Nível e pai vêm da
hierarquia de prefixos.

Em cada **conta analítica** usada na declaração, preencha a aba
**DeRE**:

- código interno e quebra de 3 dígitos da conta mista (`cDbrMista`)
- código referencial, natureza e `codTrib` **obrigatório**. Natureza e
  código de natureza vazios herdam do grupo. O `cCtaRef` vazio herda
  só um `cCtaRef` preenchido explicitamente no grupo, nunca o prefixo:
  uma conta sem código próprio nem no grupo fica fora do PGCC. O
  many2one do `codTrib` mostra `código - nome`.
- grupo pai só quando o plano não for baseado em prefixo

Depois de remapear `codTrib` em uma conta que já pertence a um D-1011
aceito, use **Substituir** nessa linha do D-1011. A linha do snapshot
é atualizada e o código novo vai no próximo D-1011; as linhas mensais
que já apontam para ela são mantidas. O D-1001 permanece como está,
salvo se você substituir essa linha também.

Não reutilize o campo ECD/ECF `l10n_br_sped_referential_code` para o
DeRE.
