Em _Configurações > Empresas_, abra a empresa e use a aba **Apuração
Assistida**:

- **Sujeito à DeRE**: ative para contribuintes obrigados à Declaração de
  Regimes Específicos. A apuração passa a ser apresentada até o dia 20, e não
  até o dia 15 do mês seguinte.
- **Calendário da Apuração**: calendário com os feriados nacionais,
  estaduais e municipais do domicílio da matriz, usado para achar o último
  dia útil do prazo. Sem calendário, só os fins de semana são pulados. Os
  feriados podem ser carregados com o assistente do `l10n_br_resource`.
- **Responsável pela Apuração**: usuário que recebe a atividade de prazo.
  Sem responsável, a atividade vai para quem criou o período.
- **Tolerância da Conciliação**: diferença absoluta abaixo da qual a linha é
  considerada conciliada. O padrão é um centavo.

Feriados incluídos no calendário depois que a apuração já existe não
recalculam o prazo. Salve a apuração de novo para atualizá-lo.
