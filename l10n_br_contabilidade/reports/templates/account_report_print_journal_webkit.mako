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

        <div class="act_as_table data_table" style="width: 100%;">
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

        <%
        account_total_debit = 0.0
        account_total_credit = 0.0
        account_total_currency = 0.0
        %>
        <% exibe_aprov_valid = data.get('datas').get('form').get('exibe_criador_aprovador') %>
        <!-- we use div with css instead of table for tabular data because div do not cut rows at half at page breaks -->
        <div class="act_as_table list_table" style="margin-top: 5px; width: 100%;">
            <div class="act_as_thead">
                <div class="act_as_row labels">
                    ## date
                    <div class="act_as_cell first_column" style="min-width: 10%; overflow: hidden;">${_('Date')}</div>
                    ## move
                    <div class="act_as_cell" style="min-width: 10%; overflow: hidden;">Sequência do Lançamento</div>
                    ## account code
                    <div class="act_as_cell" style="width: 12%;">${_('Account')}</div>
                    ## journal
                    <div class="act_as_cell" style="min-width: 10%; overflow: hidden;">${_('Journal')}</div>
                    %if exibe_aprov_valid:
                        ## Criado por
                        <div class="act_as_cell" style="min-width: 10%; overflow: hidden;">${_('Criado Por')}</div>
                        ## Aprovado Por
                        <div class="act_as_cell" style="min-width: 10%; overflow: hidden;">${_('Validado Por')}</div>
                    %endif
                    ## label
                    <div class="act_as_cell" style="width: 45%; overflow: hidden;">Histórico</div>
                    ## debit
                    <div class="act_as_cell amount" style="min-width: 10%; overflow: hidden;">${_('Debit')}</div>
                    ## credit
                    <div class="act_as_cell amount" style="min-width: 10%; overflow: hidden;">${_('Credit')}</div>
                </div>
            </div>
            <% depara_id = data.get('datas').get('form').get('account_depara_plano_id') %>

            %for move in moves:
                <div class="act_as_tbody">
                %for line in move.line_id:
                    <%
                    if depara_id:
                        depara_account_id = False
                        for depara_line in line.account_id.depara_ids:
                            if depara_line.account_depara_plano_id.id == depara_id:
                                depara_account_id = depara_line.conta_referencia_id
                                break
                    account_total_debit += line.debit or 0.0
                    account_total_credit += line.credit or 0.0

                    account_id = False
                    if depara_id:
                        account_id = depara_account_id
                    else:
                        account_id = line.account_id
                    %>
                    %if not depara_id or depara_id and account_id:
                        <div class="act_as_row lines">
                            ## date
                            <div class="act_as_cell first_column" style="min-width: 10%; overflow: hidden;">${formatLang(move.date, date=True)}</div>
                            ## move
                            <div class="act_as_cell" style="min-width: 10%; overflow: hidden;">${' ({})'.format(line.move_id.sequencia) if line.move_id.sequencia else ''}</div>
                            ## account code
                            <div class="act_as_cell" style="width: 12%;">${account_id.code}</div>
                            ## journal
                            <div class="act_as_cell" style="min-width: 10%; overflow: hidden;">${line.journal_id.name}</div>
                        %if exibe_aprov_valid:
                            ## Criado por
                            <div class="act_as_cell" style="min-width: 10%; overflow: hidden;">${move.criado_por.name or ' - '}</div>
                            ## Aprovado Por
                            <div class="act_as_cell" style="min-width: 10%; overflow: hidden;">${move.validado_por.name if move.validado_por.name else ' - '}</div>
                        %endif
                            ## label
                            <div class="act_as_cell" style="width: 45%; overflow: hidden;">${line.name}</div>
                            ## debit
                            <div class="act_as_cell amount" style="min-width: 10%; overflow: hidden;">${formatLang(line.debit) if line.debit else ''}</div>
                            ## credit
                            <div class="act_as_cell amount" style="min-width: 10%; overflow: hidden;">${formatLang(line.credit) if line.credit else ''}</div>
                        </div>
                    %endif
                %endfor
                </div>
            %endfor
            <div class="act_as_row lines labels">
                ## date
                <div class="act_as_cell first_column" style="min-width: 10%; overflow: hidden;"></div>
                ## move
                <div class="act_as_cell" style="min-width: 10%; overflow: hidden;"></div>
                ## account code
                <div class="act_as_cell" style="width: 12%;"></div>
                ## journal
                <div class="act_as_cell" style="min-width: 10%; overflow: hidden;"></div>
                %if exibe_aprov_valid:
                    ## Criado por
                    <div class="act_as_cell" style="min-width: 10%; overflow: hidden;"></div>
                    ## Aprovado Por
                    <div class="act_as_cell" style="min-width: 10%; overflow: hidden;"></div>
                %endif
                ## label
                <div class="act_as_cell" style="width: 45%; overflow: hidden;"></div>
                ## debit
                <div class="act_as_cell amount">${formatLang(account_total_debit) | amount }</div>
                ## credit
                <div class="act_as_cell amount">${formatLang(account_total_credit) | amount }</div>
            </div>
        </div>
    </body>
</html>
