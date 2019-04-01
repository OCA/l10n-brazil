## -*- coding: utf-8 -*-
<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
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

        <div class="act_as_table data_table">
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
                <div class="act_as_cell">${_('Journal Filter')}</div>
                <div class="act_as_cell">${_('Target Moves')}</div>
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
                    %if journals(data):
                        ${', '.join([journal.name for journal in journals(data)])}
                    %else:
                        ${_('All')}
                    %endif

                </div>
                <div class="act_as_cell">${ display_target_move(data) }</div>
            </div>
        </div>

        %for journal in objects:
        <%
        account_total_debit = 0.0
        account_total_credit = 0.0
        account_total_currency = 0.0
        %>

        <div class="account_title bg" style="width: 1080px; margin-top: 20px; font-size: 12px;">${journal.name}</div>

        <!-- we use div with css instead of table for tabular data because div do not cut rows at half at page breaks -->
        <div class="act_as_table list_table" style="margin-top: 5px;">
            <div class="act_as_thead">
                <div class="act_as_row labels">
                    ## date
                    <div class="act_as_cell first_column" style="width: 60px;">${_('Date')}</div>
                    ## move
                    <div class="act_as_cell" style="width: 100px;">${_('Entry')}</div>
                    ## account code
                    <div class="act_as_cell" style="width: 95px;">${_('Account')}</div>
                    ## label
                    <div class="act_as_cell" style="width: 550px;">${_('Label')}</div>
                    ## debit
                    <div class="act_as_cell amount" style="width: 125px;">${_('Debit')}</div>
                    ## credit
                    <div class="act_as_cell amount" style="width: 125px;">${_('Credit')}</div>
                    %if amount_currency(data):
                        ## currency balance
                        <div class="act_as_cell amount sep_left">${_('Curr. Balance')}</div>
                        ## curency code
                        <div class="act_as_cell amount" style="text-align: right;">${_('Curr.')}</div>
                    %endif
                </div>
            </div>
            %for move in moves[journal.id]:
            <%
            new_move = True
            %>

                %for line in move.line_id:
                <div class="act_as_tbody">
                    <%
                    account_total_debit += line.debit or 0.0
                    account_total_credit += line.credit or 0.0
                    %>
                    <div class="act_as_row lines">
                        ## date
                        <div class="act_as_cell first_column" style="width: 60px;">${formatLang(move.date, date=True) if new_move else ''}</div>
                        ## move
                        <div class="act_as_cell" style="width: 100px;">${move.name if new_move else ''}</div>
                        ## account code
                        <div class="act_as_cell" style="width: 95px;">${line.account_id.code}</div>
                        ## label
                        <div class="act_as_cell overflow_ellipsis" style="width: 550px;">${line.name}</div>
                        ## debit
                        <div class="act_as_cell amount" style="width: 125px;">${formatLang(line.debit) if line.debit else ''}</div>
                        ## credit
                        <div class="act_as_cell amount" style="width: 125px;">${formatLang(line.credit) if line.credit else ''}</div>
                        %if amount_currency(data):
                            ## currency balance
                            <div class="act_as_cell amount sep_left">${formatLang(line.amount_currency) if line.amount_currency else ''}</div>
                            ## curency code
                            <div class="act_as_cell amount" style="text-align: right;">${line.currency_id.symbol or ''}</div>
                        %endif
                    </div>
                    <%
                    new_move = False
                    %>
                </div>
                %endfor
            %endfor
            <div class="act_as_row lines labels">
                ## date
                <div class="act_as_cell first_column"></div>
                ## move
                <div class="act_as_cell"></div>
                ## account code
                <div class="act_as_cell"></div>
                ## date
                <div class="act_as_cell"></div>
                ## partner
                <div class="act_as_cell" style="width: 280px;"></div>
                ## label
                <div class="act_as_cell" style="width: 310px;"></div>
                ## debit
                <div class="act_as_cell amount">${formatLang(account_total_debit) | amount }</div>
                ## credit
                <div class="act_as_cell amount">${formatLang(account_total_credit) | amount }</div>
                %if amount_currency(data):
                  ## currency balance
                  <div class="act_as_cell amount sep_left"></div>
                  ## currency code
                  <div class="act_as_cell" style="text-align: right; right;"></div>
                %endif
            </div>
        </div>
        %endfor
    </body>
</html>
