## -*- coding: utf-8 -*-
<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta charset="UTF-8">
        <style type="text/css">
            .overflow_ellipsis {
                text-overflow: ellipsis;
                overflow: hidden;
                white-space: nowrap;
            }
            ${css}
        </style>
    </head>
    <body>
        <%!
        def amount(text):
            return text.replace('-', '&#8209;')  # replace by a non-breaking hyphen (it will not word-wrap between hyphen and numbers)
        %>

        <%setLang(user.lang)%>

        <%
        initial_balance_text = {'initial_balance': _('Computed'), 'opening_balance': _('Opening Entries'), False: _('No')}
        %>

        %if amount_currency(data):
        <div class="act_as_table data_table" style="width: 1205px;">
        %else:
        <div class="act_as_table data_table" style="width: 1100px;">
        %endif
            <div class="act_as_row labels">
                <div class="act_as_cell">${_('Chart of Account')}</div>
                <div class="act_as_cell">${_('Fiscal Year')}</div>
                <div class="act_as_cell">
                    %if filter_form(data) == 'filter_date':
                        ${_('Dates Filter')}
                    %else:
                        ${_('Periods Filter')}
                    %endif
                </div>
                <div class="act_as_cell">${_('Accounts Filter')}</div>
                <div class="act_as_cell">${_('Target Moves')}</div>
                <div class="act_as_cell">${_('Initial Balance')}</div>
            </div>
            <div class="act_as_row">
                <div class="act_as_cell">${ chart_account.name }</div>
                <div class="act_as_cell">${ fiscalyear.name if fiscalyear else '-' }</div>
                <div class="act_as_cell">
                    ${_('From:')}
                    %if filter_form(data) == 'filter_date':
                        ${formatLang(start_date, date=True) if start_date else u'' }
                    %else:
                        ${start_period.name if start_period else u''}
                    %endif
                    ${_('To:')}
                    %if filter_form(data) == 'filter_date':
                        ${ formatLang(stop_date, date=True) if stop_date else u'' }
                    %else:
                        ${stop_period.name if stop_period else u'' }
                    %endif
                </div>
                <div class="act_as_cell">
                    %if accounts(data):
                        ${', '.join([account.code for account in accounts(data)])}
                    %else:
                        ${_('All')}
                    %endif

                </div>
                <div class="act_as_cell">${ display_target_move(data) }</div>
                <div class="act_as_cell">${ initial_balance_text[initial_balance_mode] }</div>
            </div>
        </div>

        <!-- we use div with css instead of table for tabular data because div do not cut rows at half at page breaks -->
        %for account in objects:
        <%
          display_initial_balance = init_balance[account.id] and (init_balance[account.id].get('debit') != 0.0 or init_balance[account.id].get('credit', 0.0) != 0.0)
          display_ledger_lines = ledger_lines[account.id]
        %>
          %if display_account_raw(data) == 'all' or (display_ledger_lines or display_initial_balance):
              <%
              cumul_debit = 0.0
              cumul_credit = 0.0
              cumul_balance =  0.0
              cumul_balance_curr = 0.0
              %>
            <div class="act_as_table list_table" style="margin-top: 10px; margin-bottom: 10px;">

                <div class="act_as_caption account_title">
                    <div> Conta: ${account.code} </div> <div> Descrição: ${account.name} </div>
                </div>
                <div class="act_as_thead">
                    <div class="act_as_row labels">
                        ## date
                        <div class="act_as_cell first_column" style="width: 70px;">${_('Date')}</div>
                        ## Nº Lançamento (Sequencia)
                        <div class="act_as_cell" style="width: 70px;">Nº Lançamento</div>
                        ## counterpart
                        <div class="act_as_cell" style="width: 100px;">${_('Counter part')}</div>
                        ## Histórico
                        <div class="act_as_cell" style="text-align: center; width: 40%;">Histórico</div>
                        ## debit
                        <div class="act_as_cell amount" style="width: 7%;">${_('Debit')}</div>
                        ## credit
                        <div class="act_as_cell amount" style="width: 7%;">${_('Credit')}</div>
                        ## balance cumulated
                        <div class="act_as_cell amount" style="width: 7%;">Saldo</div>
                        %if amount_currency(data):
                            ## currency balance
                            <div class="act_as_cell amount sep_left" style="width: 75px;">${_('Curr. Balance')}</div>
                        %endif
                        ## identificação do saldo
                        <div class="act_as_cell amount" style="width:2%;"></div>
                    </div>
                </div>

                <div class="act_as_tbody">
                      %if display_initial_balance:
                        <%
                        cumul_debit = init_balance[account.id].get('debit') or 0.0
                        cumul_credit = init_balance[account.id].get('credit') or 0.0
                        cumul_balance = init_balance[account.id].get('init_balance') or 0.0
                        cumul_balance_curr = init_balance[account.id].get('init_balance_currency') or 0.0
                        %>
                        <div class="act_as_row initial_balance">
                          ## date
                          <div class="act_as_cell"></div>
                          ## Nº Lançamento (Sequencia)
                          <div class="act_as_cell"></div>
                          ## counterpart
                          <div class="act_as_cell"></div>
                          ## Histórico
                          <div class="act_as_cell" style="font-weight: bold; text-align: right; text-align: center; width:40%;">Anterior</div>
                          ## debit
                          <div class="act_as_cell amount">${formatLang(init_balance[account.id].get('debit')) | amount}</div>
                          ## credit
                          <div class="act_as_cell amount">${formatLang(init_balance[account.id].get('credit')) | amount}</div>
                          ## balance cumulated
                          <div class="act_as_cell amount" style="padding-right: 1px;">${formatLang(cumul_balance) | amount }</div>
                         %if amount_currency(data):
                              ## currency balance
                              <div class="act_as_cell amount sep_left">${formatLang(cumul_balance_curr) | amount }</div>
                         %endif
                          ## identificação do saldo
                          <div class="act_as_cell amount" style="width:2%;"></div>
                        </div>
                      %endif
                      %for line in ledger_lines[account.id]:
                        <%
                        cumul_debit += line.get('debit') or 0.0
                        cumul_credit += line.get('credit') or 0.0
                        cumul_balance_curr += line.get('amount_currency') or 0.0
                        cumul_balance += line.get('balance') or 0.0
                        label_elements = [line.get('lname') or '']
                        if line.get('invoice_number'):
                          label_elements.append("(%s)" % (line['invoice_number'],))
                        label = ' '.join(label_elements)
                        %>

                      <div class="act_as_row lines">
                          ## date
                          <div class="act_as_cell first_column">${formatLang(line.get('ldate') or '', date=True)}</div>
                          ## Nº Lançamento (Sequencia)
                          <div class="act_as_cell">${line.get('sequencia') or ''}</div>
                          ## counterpart
                          <div class="act_as_cell">${line.get('counterparts') or ''}</div>
                          ## Histórico
                          <div class="act_as_cell">${line.get('narration') or ''}</div>
                          ## debit
                          <div class="act_as_cell amount">${ formatLang(line.get('debit', 0.0)) | amount }</div>
                          ## credit
                          <div class="act_as_cell amount">${ formatLang(line.get('credit', 0.0)) | amount }</div>
                          ## balance cumulated
                          <div class="act_as_cell amount" style="padding-right: 1px;">${ formatLang(cumul_balance) | amount }</div>
                          %if amount_currency(data):
                              ## currency balance
                              <div class="act_as_cell amount sep_left">${formatLang(line.get('amount_currency') or 0.0)  | amount }</div>
                          %endif
                          ## identificação do saldo
                          %if cumul_balance > 0:
                              %if line.get('natureza') == 'C':
                                  <div class="act_as_cell amount" style="text-align: right; width:2%;">C</div>
                              %elif line.get('natureza') == 'D':
                                  <div class="act_as_cell amount" style="text-align: right; width:2%;">D</div>
                              %else:
                                  <div class="act_as_cell amount" style="text-align: right; width:2%;"></div>
                              %endif
                          %elif cumul_balance < 0:
                              %if line.get('natureza') == 'C':
                                  <div class="act_as_cell amount" style="text-align: right; width:2%;">D</div>
                              %elif line.get('natureza') == 'D':
                                  <div class="act_as_cell amount" style="text-align: right; width:2%;">C</div>
                              %else:
                                  <div class="act_as_cell amount" style="text-align: right; width:2%;"></div>
                              %endif
                          %elif cumul_balance == 0:
                            <div class="act_as_cell amount" style="text-align: right; width:2%;"></div>
                          %else:
                              <div class="act_as_cell amount" style="text-align: right; width:2%;"></div>
                          %endif
                      </div>
                      %endfor
                </div>
                <div class="act_as_table list_table" style="padding-top: 10px;">
                    <div class="act_as_row labels" style="font-weight: bold;">
                        ## date / Conta / Nº Lançamento (Sequencia)
                        <div class="act_as_cell first_column" style="width: 140px;">${account.code} - ${account.name}</div>
                        ## counterpart
                        <div class="act_as_cell" style="width: 100px;"></div>
                        ## Histórico
                        <div class="act_as_cell" style="font-weight: bold; text-align: center; width: 40%;">Total</div>
                        ## debit
                        <div class="act_as_cell amount" style="width: 7%;">${ formatLang(cumul_debit) | amount }</div>
                        ## credit
                        <div class="act_as_cell amount" style="width: 7%;">${ formatLang(cumul_credit) | amount }</div>
                        ## balance cumulated
                        <div class="act_as_cell amount" style="width: 7%;">${ formatLang(cumul_balance) | amount }</div>
                        %if amount_currency(data):
                            %if account.currency_id:
                                ## currency balance
                                <div class="act_as_cell amount sep_left">${formatLang(cumul_balance_curr) | amount }</div>
                                ## identificação do saldo
                                <div class="act_as_cell amount">-</div>
                            %else:
                                <div class="act_as_cell amount sep_left">-</div>
                                ## identificação do saldo
                                <div class="act_as_cell amount"></div>
                            %endif
                        %endif
                          ## identificação do saldo
                          <div class="act_as_cell amount" style="width:2%;"></div>
                    </div>
                </div>
            </div>
          %endif
        %endfor
    </body>
</html>
