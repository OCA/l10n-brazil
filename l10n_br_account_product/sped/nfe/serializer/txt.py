# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime
from unicodedata import normalize
import pytz
from openerp import SUPERUSER_ID
from openerp import pooler
from openerp.addons.l10n_br_base.tools.misc import punctuation_rm


def nfe_export(cr, uid, ids, nfe_environment='1',
               nfe_version='2.00', context=False):
    # StrFile = ''

    StrNF = 'NOTA FISCAL|%s|\n' % len(ids)
    StrFile = StrNF
    pool = pooler.get_pool(cr.dbname)

    nfes = []

    for inv in pool.get('account.invoice').browse(
            cr, uid, ids, context={'lang': 'pt_BR'}):
        # Endereço do company
        company_addr = pool.get('res.partner').address_get(
            cr, uid, [inv.company_id.partner_id.id], ['default'])
        company_addr_default = pool.get('res.partner').browse(
            cr, uid, [company_addr['default']], context={'lang': 'pt_BR'})[0]

        StrA = 'A|%s|%s|\n' % (nfe_version, '')

        StrFile += StrA

        StrRegB = {
            'cUF': company_addr_default.state_id.ibge_code,
            'cNF': '',
            'NatOp': (normalize('NFKD',
                                unicode(inv.cfop_ids[0].small_name or ''))
                      .encode('ASCII', 'ignore')),
            'indPag': inv.payment_term and inv.payment_term.indPag or '0',
            'mod': inv.fiscal_document_id.code,
            'serie': inv.document_serie_id.code,
            'nNF': inv.internal_number or '',
            'hSaiEnt': '',
            'tpNF': '',
            'cMunFG': ('%s%s') % (company_addr_default.state_id.ibge_code,
                                  (company_addr_default
                                   .l10n_br_city_id.ibge_code)),
            'TpImp': '1',
            'TpEmis': '1',
            'cDV': '',
            'tpAmb': nfe_environment,
            'finNFe': inv.nfe_purpose,
            'procEmi': '0',
            # 'VerProc': '2.2.26',
            'dhCont': '',
            'xJust': '',
        }

        if inv.cfop_ids[0].type in ("input"):
            StrRegB['tpNF'] = '0'
        else:
            StrRegB['tpNF'] = '1'

        if nfe_version == '3.10':

            # Capturar a timezone do usuario
            user_pool = inv.pool.get('res.users')
            user = user_pool.browse(cr, SUPERUSER_ID, uid)
            tz = pytz.timezone(user.partner_id.tz) or pytz.utc

            StrRegB['dhEmi'] = str(pytz.utc.localize(datetime.strptime(
                inv.date_hour_invoice, '%Y-%m-%d %H:%M:%S'))
                .astimezone(tz)).replace(' ', 'T') or ''

            StrRegB['dhSaiEnt'] = str(pytz.utc.localize(datetime.strptime(
                inv.date_in_out, '%Y-%m-%d %H:%M:%S'))
                .astimezone(tz)).replace(' ', 'T') or ''

            StrRegB['idDest'] = inv.fiscal_position.cfop_id.id_dest or ''
            StrRegB['indFinal'] = inv.ind_final or ''
            StrRegB['indPres'] = inv.ind_pres or ''
            StrRegB['VerProc'] = '3.10.18'

            # Modificado
            StrB = 'B|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\
            |%s|%s|%s|%s|%s|%s|\n' % (
                StrRegB['cUF'], StrRegB['cNF'], StrRegB[
                    'NatOp'], StrRegB['indPag'], StrRegB['mod'],
                StrRegB['serie'], StrRegB['nNF'], StrRegB[
                    'dhEmi'], StrRegB['dhSaiEnt'], StrRegB['hSaiEnt'],
                StrRegB['tpNF'], StrRegB['idDest'], StrRegB[
                    'cMunFG'], StrRegB['TpImp'], StrRegB['TpEmis'],
                StrRegB['cDV'], StrRegB['tpAmb'], StrRegB[
                    'finNFe'], StrRegB['indFinal'], StrRegB['indPres'],
                StrRegB['procEmi'], StrRegB['VerProc'], StrRegB['dhCont'],
                StrRegB['xJust'])

        else:
            StrRegB['dEmi'] = inv.date_invoice or ''
            StrRegB['dSaiEnt'] = str(datetime.strptime(
                inv.date_in_out, '%Y-%m-%d %H:%M:%S').date()) or ''
            StrRegB['VerProc'] = '2.2.26'

            StrB = 'B|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\
            |%s|%s|%s|\n' % (
                StrRegB['cUF'], StrRegB['cNF'], StrRegB[
                    'NatOp'], StrRegB['indPag'],
                StrRegB['mod'], StrRegB['serie'], StrRegB[
                    'nNF'], StrRegB['dEmi'], StrRegB['dSaiEnt'],
                StrRegB['hSaiEnt'], StrRegB['tpNF'], StrRegB[
                    'cMunFG'], StrRegB['TpImp'], StrRegB['TpEmis'],
                StrRegB['cDV'], StrRegB['tpAmb'], StrRegB[
                    'finNFe'], StrRegB['procEmi'], StrRegB['VerProc'],
                StrRegB['dhCont'], StrRegB['xJust'])

        StrFile += StrB

        for inv_related in inv.fiscal_document_related_ids:

            if inv_related.document_type == 'nf':
                StrRegB14 = {
                    'cUF': '%s' % inv_related.state_id and
                    inv_related.state_id.ibge_code or '',
                    'AAMM': datetime.strptime(
                        inv_related.date,
                        '%Y-%m-%d').strftime('%y%m') or '',
                    'CNPJ': punctuation_rm(
                        inv_related.cnpj_cpf),
                    'Mod': inv_related.fiscal_document_id and
                    inv_related.fiscal_document_id.code or '',
                    'serie': inv_related.serie or '',
                    'nNF': punctuation_rm(
                        inv_related.internal_number),
                }

                StrB14 = 'B14|%s|%s|%s|%s|%s|%s|\n' % (StrRegB14['cUF'],
                                                       StrRegB14['AAMM'],
                                                       StrRegB14['CNPJ'],
                                                       StrRegB14['CNPJ'],
                                                       StrRegB14['serie'],
                                                       StrRegB14['nNF'])

                StrFile += StrB14

            elif inv_related.document_type == 'nfrural':
                StrRegB20a = {
                    'cUF': '%s' % inv_related.state_id and
                    inv_related.state_id.ibge_code or '',
                    'AAMM': datetime.strptime(
                        inv_related.date,
                        '%Y-%m-%d').strftime('%y%m') or '',
                    'IE': punctuation_rm(
                        inv_related.inscr_est),
                    'mod': inv_related.fiscal_document_id and
                    inv_related.fiscal_document_id.code or '',
                    'serie': inv_related.serie or '',
                    'nNF': punctuation_rm(
                        inv_related.internal_number),
                }
                StrB20a = 'B20a|%s|%s|%s|%s|%s|%s|\n' % (StrRegB20a['cUF'],
                                                         StrRegB20a['AAMM'],
                                                         StrRegB20a['IE'],
                                                         StrRegB20a['mod'],
                                                         StrRegB20a['serie'],
                                                         StrRegB20a['nNF'])

                StrFile += StrB20a

                if inv_related.cpfcnpj_type == 'cnpj':
                    StrRegB20d = {
                        'CNPJ': punctuation_rm(inv_related.cnpj_cpf)
                    }
                    StrB20d = 'B20d|%s|\n' % StrRegB20d['CNPJ']
                    StrFile += StrB20d
                else:
                    StrRegB20e = {
                        'CPF': punctuation_rm(inv_related.cnpj_cpf)
                    }
                    StrB20e = 'B20e|%s|\n' % StrRegB20e['CPF']
                    StrFile += StrB20e
            elif inv_related.document_type == 'nfe':
                StrRegBA02 = {
                    'refNFe': inv_related.access_key or '',
                }
                StrBA02 = 'BA02|%s|\n' % StrRegBA02['refNFe']
                StrFile += StrBA02
            elif inv_related.document_type == 'cte':
                StrRegB20i = {
                    'refCTe': inv_related.access_key or '',
                }
                StrB20i = 'B20i|%s|\n' % StrRegB20i['refCTe']
                StrFile += StrB20i
            elif inv_related.document_type == 'cf':
                StrRegB20j = {
                    'mod': inv_related.fiscal_document_id and
                    inv_related.fiscal_document_id.code or '',
                    'nECF': inv_related.internal_number,
                    'nCOO': inv_related.serie,
                }
                StrB20j = 'B20j|%s|%s|%s|\n' % (StrRegB20j['mod'], StrRegB20j[
                                                'nECF'], StrRegB20j['nCOO'])
                StrFile += StrB20j

        StrRegC = {
            'XNome': normalize(
                'NFKD',
                unicode(inv.company_id.partner_id.legal_name or '')).encode(
                'ASCII', 'ignore'),
            'XFant': normalize(
                'NFKD',
                unicode(inv.company_id.partner_id.name or '')).encode(
                'ASCII', 'ignore'),
            'IE': punctuation_rm(inv.company_id.partner_id.inscr_est),
            'IEST': '',
            'IM': punctuation_rm(inv.company_id.partner_id.inscr_mun),
            'CNAE': punctuation_rm(inv.company_id.cnae_main_id.code),
            'CRT': inv.company_id.fiscal_type or '', }

        # TODO - Verificar, pois quando e informado do CNAE ele exige que a
        # inscricao municipal, parece um bug do emissor da NFE
        if not inv.company_id.partner_id.inscr_mun:
            StrRegC['CNAE'] = ''

        StrC = 'C|%s|%s|%s|%s|%s|%s|%s|\n' % (StrRegC['XNome'],
                                              StrRegC['XFant'],
                                              StrRegC['IE'],
                                              StrRegC['IEST'],
                                              StrRegC['IM'],
                                              StrRegC['CNAE'],
                                              StrRegC['CRT'])

        StrFile += StrC

        if inv.company_id.partner_id.is_company:
            StrC02 = 'C02|%s|\n' % (punctuation_rm(
                inv.company_id.partner_id.cnpj_cpf))
        else:
            StrC02 = 'C02a|%s|\n' % (punctuation_rm(
                inv.company_id.partner_id.cnpj_cpf))

        StrFile += StrC02

        address_company_bc_code = ''
        if company_addr_default.country_id.bc_code:
            address_company_bc_code = (company_addr_default
                                       .country_id.bc_code[1:])

        StrRegC05 = {
            'XLgr': normalize(
                'NFKD',
                unicode(
                    company_addr_default.street or '')).encode(
                'ASCII',
                'ignore'),
            'Nro': company_addr_default.number or '',
            'Cpl': normalize(
                'NFKD',
                unicode(
                    company_addr_default.street2 or '')).encode(
                'ASCII',
                'ignore'),
            'Bairro': normalize(
                'NFKD',
                unicode(
                    company_addr_default.district or 'Sem Bairro')).encode(
                'ASCII',
                'ignore'),
            'CMun': '%s%s' % (company_addr_default.state_id.ibge_code,
                              company_addr_default.l10n_br_city_id.ibge_code),
            'XMun': normalize(
                'NFKD',
                unicode(
                    company_addr_default.l10n_br_city_id.name or '')).encode(
                'ASCII',
                'ignore'),
            'UF': company_addr_default.state_id.code or '',
            'CEP': punctuation_rm(company_addr_default.zip),
            'cPais': address_company_bc_code or '',
            'xPais': normalize(
                'NFKD',
                unicode(
                    company_addr_default.country_id.name or '')).encode(
                'ASCII',
                'ignore'),
            'fone': punctuation_rm(
                company_addr_default.phone or '').replace(
                ' ',
                ''),
        }

        StrC05 = 'C05|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n' % (
            StrRegC05['XLgr'], StrRegC05['Nro'], StrRegC05[
                'Cpl'], StrRegC05['Bairro'],
            StrRegC05['CMun'], StrRegC05[
                'XMun'], StrRegC05['UF'], StrRegC05['CEP'],
            StrRegC05['cPais'], StrRegC05['xPais'], StrRegC05['fone'])

        StrFile += StrC05

        partner_bc_code = ''
        address_invoice_state_code = ''
        address_invoice_city = ''
        UFEmbarq = ''
        XLocEmbarq = ''
        partner_cep = ''
        if inv.partner_id.country_id.bc_code:
            partner_bc_code = inv.partner_id.country_id.bc_code[1:]

        if inv.partner_id.country_id.id != company_addr_default.country_id.id:
            address_invoice_state_code = 'EX'
            address_invoice_city = 'Exterior'
            address_invoice_city_code = '9999999'
            UFEmbarq = company_addr_default.state_id.code
            XLocEmbarq = company_addr_default.city
            partner_cep = ''
        else:
            address_invoice_state_code = inv.partner_id.state_id.code
            address_invoice_city = normalize(
                'NFKD', unicode(
                    inv.partner_id.l10n_br_city_id.name or '')).encode(
                'ASCII', 'ignore')
            address_invoice_city_code = ('%s%s') % (
                inv.partner_id.state_id.ibge_code,
                inv.partner_id.l10n_br_city_id.ibge_code)
            partner_cep = punctuation_rm(inv.partner_id.zip)

        # Se o ambiente for de teste deve ser escrito na razão do destinatário
        if nfe_environment == '2':
            xNome = 'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO'\
                    ' - SEM VALOR FISCAL'
        else:
            xNome = normalize('NFKD', unicode(
                inv.partner_id.legal_name or '')).encode('ASCII', 'ignore')

        StrRegE = {
            'xNome': xNome,
            'IE': punctuation_rm(inv.partner_id.inscr_est),
            'ISUF': '',
            'email': inv.partner_id.email or '',
        }

        # Adicionado
        if nfe_version == '3.10':
            StrRegE['indIEDest'] = inv.cfop_ids[0].id_dest
            StrRegE['IM'] = StrRegC['IM']

            StrE = 'E|%s|%s|%s|%s|%s|%s|\n' % (StrRegE['xNome'],
                                               StrRegE['indIEDest'],
                                               StrRegE['IE'],
                                               StrRegE['ISUF'],
                                               StrRegE['IM'],
                                               StrRegE['email'])
        else:
            StrE = 'E|%s|%s|%s|%s|\n' % (StrRegE['xNome'], StrRegE[
                'IE'], StrRegE['ISUF'], StrRegE['email'])

        StrFile += StrE

        if inv.partner_id.is_company:
            StrE0 = 'E02|%s|\n' % (punctuation_rm(inv.partner_id.cnpj_cpf))
        else:
            StrE0 = 'E03|%s|\n' % (punctuation_rm(inv.partner_id.cnpj_cpf))

        StrFile += StrE0

        StrRegE05 = {
            'xLgr': (normalize('NFKD', unicode(inv.partner_id.street or ''))
                     .encode('ASCII', 'ignore')),
            'nro': (normalize('NFKD', unicode(inv.partner_id.number or ''))
                    .encode('ASCII', 'ignore')),
            'xCpl': (punctuation_rm(normalize(
                'NFKD', unicode(inv.partner_id.street2 or ''))
                .encode('ASCII', 'ignore'))),
            'xBairro': (normalize(
                'NFKD', unicode(inv.partner_id.district or 'Sem Bairro'))
                .encode('ASCII', 'ignore')),
            'cMun': address_invoice_city_code,
            'xMun': address_invoice_city,
            'UF': address_invoice_state_code,
            'CEP': partner_cep,
            'cPais': partner_bc_code,
            'xPais': (normalize(
                'NFKD', unicode(inv.partner_id.country_id.name or ''))
                .encode('ASCII', 'ignore')),
            # 'fone': re.sub('[%s]' % re.escape(string.punctuation), '',
            #                str(inv.partner_id.phone or '').replace(' ', '')),
            'fone': (punctuation_rm(inv.partner_id.phone or '')
                     .replace(' ', '')),
        }

        StrE05 = 'E05|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n' % (
            StrRegE05['xLgr'], StrRegE05['nro'], StrRegE05[
                'xCpl'], StrRegE05['xBairro'],
            StrRegE05['cMun'], StrRegE05[
                'xMun'], StrRegE05['UF'], StrRegE05['CEP'],
            StrRegE05['cPais'], StrRegE05['xPais'], StrRegE05['fone'],)

        StrFile += StrE05

        if inv.partner_shipping_id:

            if inv.partner_id.id != inv.partner_shipping_id.id:

                StrRegG = {
                    'XLgr': (normalize(
                        'NFKD', unicode(inv.partner_shipping_id.street or ''))
                        .encode('ASCII', 'ignore')),
                    'Nro': (normalize(
                            'NFKD',
                            unicode(inv.partner_shipping_id.number or ''))
                            .encode('ASCII', 'ignore')),
                    'XCpl': (punctuation_rm(normalize(
                        'NFKD', unicode(inv.partner_shipping_id.street2 or ''))
                        .encode('ASCII', 'ignore'))),
                    'XBairro': punctuation_rm(normalize(
                        'NFKD', unicode(inv.partner_shipping_id.district or
                                        'Sem Bairro')).encode('ASCII',
                                                              'ignore')),
                    'CMun': ('%s%s') % (
                        inv.partner_shipping_id.state_id.ibge_code,
                        inv.partner_shipping_id.l10n_br_city_id.ibge_code),
                    'XMun': (normalize(
                             'NFKD',
                             unicode((inv.partner_shipping_id
                                      .l10n_br_city_id.name) or ''))
                             .encode('ASCII', 'ignore')),
                    'UF': inv.partner_shipping_id.state_id.code,
                }

                StrG = 'G|%s|%s|%s|%s|%s|%s|%s|\n' % (
                    StrRegG['XLgr'], StrRegG['Nro'], StrRegG[
                        'XCpl'], StrRegG['XBairro'], StrRegG['CMun'],
                    StrRegG['XMun'],
                    StrRegG['UF'])
                StrFile += StrG

                if inv.partner_id.is_company:
                    # StrG0 = 'G02|%s|\n' % (
                    # re.sub('[%s]' % re.escape(string.punctuation), '',
                    # inv.partner_id.cnpj_cpf or ''))
                    StrG0 = 'G02|%s|\n' % punctuation_rm(
                        inv.partner_id.cnpj_cpf)
                else:
                    # StrG0 = 'G02a|%s|\n' % (
                    # re.sub('[%s]' % re.escape(string.punctuation), '',
                    # inv.partner_id.cnpj_cpf or ''))
                    StrG0 = 'G02a|%s|\n' % punctuation_rm(
                        inv.partner_id.cnpj_cpf)

                StrFile += StrG0

        i = 0
        for inv_line in inv.invoice_line:
            i += 1

            # FIXME
            if inv_line.freight_value:
                freight_value = str("%.2f" % inv_line.freight_value)
            else:
                freight_value = ''

            if inv_line.insurance_value:
                insurance_value = str("%.2f" % inv_line.insurance_value)
            else:
                insurance_value = ''

            if inv_line.other_costs_value:
                other_costs_value = str("%.2f" % inv_line.other_costs_value)
            else:
                other_costs_value = ''

            if inv_line.discount_value:
                discount_value = str("%.2f" % inv_line.discount_value)
            else:
                discount_value = ''

            StrH = 'H|%s||\n' % (i)

            StrFile += StrH

            CProd = ''
            XProd = ''
            if inv_line.product_id.code:
                CProd = inv_line.product_id.code
                XProd = normalize('NFKD', unicode(
                    inv_line.product_id.name or '')).encode('ASCII', 'ignore')
            else:
                CProd = unicode(i).strip().rjust(4, u'0')
                XProd = normalize('NFKD', unicode(
                    inv_line.name or '')).encode('ASCII', 'ignore')

            StrRegI = {
                'CProd': CProd,
                'CEAN': inv_line.product_id.ean13 or '',
                'XProd': XProd,
                'EXTIPI': '',
                'CFOP': inv_line.cfop_id.code,
                'UCom': normalize(
                    'NFKD',
                    unicode(
                        inv_line.uos_id.name or '',
                    )).encode(
                    'ASCII',
                    'ignore'),
                'QCom': str(
                    "%.4f" %
                    inv_line.quantity),
                'VUnCom': str(
                    "%.7f" %
                    inv_line.price_unit),
                'VProd': str(
                    "%.2f" %
                    inv_line.price_gross),
                'CEANTrib': inv_line.product_id.ean13 or '',
                'UTrib': normalize(
                    'NFKD',
                    unicode(
                        inv_line.uos_id.name or '',
                    )).encode(
                    'ASCII',
                    'ignore'),
                'QTrib': str(
                    "%.4f" %
                    inv_line.quantity),
                'VUnTrib': str(
                    "%.7f" %
                    inv_line.price_unit),
                'VFrete': freight_value,
                'VSeg': insurance_value,
                'VDesc': discount_value,
                'vOutro': other_costs_value,
                'indTot': '1',
                'xPed': '',
                'nItemPed': '',
                'nFCI': inv_line.fci or '',
            }

            StrRegI['NCM'] = punctuation_rm(
                inv_line.fiscal_classification_id.name)

            if nfe_version == '3.10':

                StrRegI['NVE'] = ''
                StrRegI['nFCI'] = ''

                StrI = 'I|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s'\
                       '|%s|%s|%s|%s|%s|%s|%s|\n' % (
                           StrRegI['CProd'], StrRegI['CEAN'],
                           StrRegI['XProd'], StrRegI['NCM'],
                           StrRegI['NVE'], StrRegI['EXTIPI'],
                           StrRegI['CFOP'], StrRegI['UCom'],
                           StrRegI['QCom'], StrRegI['VUnCom'],
                           StrRegI['VProd'], StrRegI['CEANTrib'],
                           StrRegI['UTrib'], StrRegI['QTrib'],
                           StrRegI['VUnTrib'], StrRegI['VFrete'],
                           StrRegI['VSeg'], StrRegI['VDesc'],
                           StrRegI['vOutro'], StrRegI['indTot'],
                           StrRegI['xPed'], StrRegI['nItemPed'],
                           StrRegI['nFCI'])
            else:
                StrI = 'I|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s'\
                       '|%s|%s|%s|%s|%s|\n' % (
                           StrRegI['CProd'], StrRegI['CEAN'],
                           StrRegI['XProd'], StrRegI['NCM'],
                           StrRegI['EXTIPI'], StrRegI['CFOP'],
                           StrRegI['UCom'], StrRegI['QCom'],
                           StrRegI['VUnCom'], StrRegI['VProd'],
                           StrRegI['CEANTrib'], StrRegI['UTrib'],
                           StrRegI['QTrib'], StrRegI['VUnTrib'],
                           StrRegI['VFrete'], StrRegI['VSeg'],
                           StrRegI['VDesc'], StrRegI['vOutro'],
                           StrRegI['indTot'], StrRegI['xPed'],
                           StrRegI['nItemPed'], StrRegI['nFCI'])

            StrFile += StrI

            for inv_di in inv_line.import_declaration_ids:

                StrRegI18 = {
                    'NDI': inv_di.name,
                    'DDI': inv_di.date_registration or '',
                    'XLocDesemb': inv_di.location,
                    'UFDesemb': inv_di.state_id.code or '',
                    'DDesemb': inv_di.date_release or '',
                    'tpViaTransp': inv_di.type_transportation or '',
                    'vAFRMM': str("%.2f" % inv_di.afrmm_value),
                    'tpIntermedio': inv_di.type_import or '',
                    'CNPJ': inv_di.exporting_code or '',
                    'UFTerceiro': inv_di.thirdparty_state_id.code or '',
                    'CExportador': inv_di.exporting_code,
                }

                StrI18 = 'I18|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n' % (
                    StrRegI18['NDI'],
                    StrRegI18['DDI'],
                    StrRegI18['XLocDesemb'],
                    StrRegI18['UFDesemb'],
                    StrRegI18['DDesemb'],
                    StrRegI18['tpViaTransp'],
                    StrRegI18['vAFRMM'],
                    StrRegI18['tpIntermedio'],
                    StrRegI18['CNPJ'],
                    StrRegI18['UFTerceiro'],
                    StrRegI18['CExportador'],
                )

                StrFile += StrI18

                for inv_di_line in inv_di.line_ids:

                    StrRegI25 = {
                        'NAdicao': inv_di_line.name,
                        'NSeqAdic': inv_di_line.sequence,
                        'CFabricante': inv_di_line.manufacturer_code,
                        'VDescDI': str("%.2f" % inv_di_line.amount_discount),
                    }

                    if StrRegI25['VDescDI'] == '0.00':
                        StrRegI25['VDescDI'] = ''

                    StrI25 = 'I25|%s|%s|%s|%s|\n' % (
                        StrRegI25['NAdicao'],
                        StrRegI25['NSeqAdic'],
                        StrRegI25['CFabricante'],
                        StrRegI25['VDescDI'],
                    )

                    StrFile += StrI25

            icms_cst = inv_line.icms_cst_id and\
                inv_line.icms_cst_id.code or ''
            ipi_cst = inv_line.ipi_cst_id and\
                inv_line.ipi_cst_id.code or ''
            pis_cst = inv_line.pis_cst_id and inv_line.pis_cst_id.code or ''
            cofins_cst = inv_line.cofins_cst_id and\
                inv_line.cofins_cst_id.code or ''

            StrRegStrM = {
                'vTotTrib': str("%.2f" % inv_line.total_taxes),
            }

            StrM = 'M|%s|\n' % (StrRegStrM['vTotTrib'])

            StrFile += StrM

            StrN = 'N|\n'

            StrFile += StrN

            # TODO - Fazer alteração para cada tipo de cst ICMS
            if inv_line.product_type == 'product':
                if icms_cst in ('00',):
                    StrRegN02 = {
                        'Orig': inv_line.product_id.origin or '0',
                        'CST': icms_cst,
                        'ModBC': inv_line.icms_base_type,
                        'VBC': str("%.2f" % inv_line.icms_base),
                        'PICMS': str("%.2f" % inv_line.icms_percent),
                        'VICMS': str("%.2f" % inv_line.icms_value),
                    }

                    StrN02 = 'N02|%s|%s|%s|%s|%s|%s|\n' % (
                        StrRegN02['Orig'], StrRegN02['CST'], StrRegN02[
                            'ModBC'], StrRegN02['VBC'], StrRegN02['PICMS'],
                        StrRegN02['VICMS'])

                    StrFile += StrN02

                if icms_cst in ('10',):
                    StrRegN03 = {
                        'Orig': inv_line.product_id.origin or '0',
                        'CST': icms_cst,
                        'ModBC': inv_line.icms_base_type,
                        'VBC': str("%.2f" % inv_line.icms_base),
                        'PICMS': str("%.2f" % inv_line.icms_percent),
                        'VICMS': str("%.2f" % inv_line.icms_value),
                        'ModBCST': inv_line.icms_st_base_type,
                        'PMVAST': str("%.2f" % inv_line.icms_st_mva) or '',
                        'PRedBCST': '',
                        'VBCST': str("%.2f" % inv_line.icms_st_base),
                        'PICMSST': str("%.2f" % inv_line.icms_st_percent),
                        'VICMSST': str("%.2f" % inv_line.icms_st_value),
                    }

                    StrN03 = 'N03|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n' % (
                        StrRegN03['Orig'], StrRegN03[
                            'CST'], StrRegN03['ModBC'],
                        StrRegN03['VBC'], StrRegN03[
                            'PICMS'], StrRegN03['VICMS'],
                        StrRegN03['ModBCST'], StrRegN03['PMVAST'],
                        StrRegN03['PRedBCST'], StrRegN03['VBCST'],
                        StrRegN03['PICMSST'], StrRegN03['VICMSST'])

                    StrFile += StrN03

                if icms_cst in ('20',):
                    StrRegN04 = {
                        'Orig': inv_line.product_id.origin or '0',
                        'CST': icms_cst,
                        'ModBC': inv_line.icms_base_type,
                        'PRedBC': str(
                            "%.2f" %
                            inv_line.icms_percent_reduction),
                        'VBC': str(
                            "%.2f" %
                            inv_line.icms_base),
                        'PICMS': str(
                            "%.2f" %
                            inv_line.icms_percent),
                        'VICMS': str(
                            "%.2f" %
                            inv_line.icms_value),
                    }

                    StrN04 = 'N04|%s|%s|%s|%s|%s|%s|%s|\n' % (
                        StrRegN04['Orig'], StrRegN04[
                            'CST'], StrRegN04['ModBC'],
                        StrRegN04['PRedBC'], StrRegN04[
                            'VBC'], StrRegN04['PICMS'],
                        StrRegN04['VICMS'])

                    StrFile += StrN04

                if icms_cst in ('40', '50'):
                    StrRegN06 = {
                        'Orig': inv_line.product_id.origin or '0',
                        'CST': icms_cst,
                        'vICMS': str("%.2f" % inv_line.icms_value),
                        'motDesICMS': '9',  # FIXME
                    }
                    StrN06 = 'N06|%s|%s|%s|%s|\n' % (
                        StrRegN06['Orig'], StrRegN06[
                            'CST'], StrRegN06['vICMS'],
                        StrRegN06['motDesICMS'])
                    StrFile += StrN06

                if icms_cst in ('41',):
                    StrRegN06 = {
                        'Orig': inv_line.product_id.origin or '0',
                        'CST': icms_cst,
                        'vICMS': '',
                        'motDesICMS': '',
                    }
                    StrN06 = 'N06|%s|%s|%s|%s|\n' % (
                        StrRegN06['Orig'], StrRegN06[
                            'CST'], StrRegN06['vICMS'],
                        StrRegN06['motDesICMS'])
                    StrFile += StrN06

                if icms_cst in ('51',):
                    StrRegN07 = {
                        'Orig': inv_line.product_id.origin or '0',
                        'CST': icms_cst,
                        'ModBC': inv_line.icms_base_type,
                        'PRedBC': str(
                            "%.2f" %
                            inv_line.icms_percent_reduction),
                        'VBC': str(
                            "%.2f" %
                            inv_line.icms_base),
                        'PICMS': str(
                            "%.2f" %
                            inv_line.icms_percent),
                        'VICMS': str(
                            "%.2f" %
                            inv_line.icms_value),
                    }
                    StrN07 = 'N07|%s|%s|%s|%s|%s|%s|%s|\n' % (
                        StrRegN07['Orig'], StrRegN07[
                            'CST'], StrRegN07['ModBC'],
                        StrRegN07['PRedBC'], StrRegN07['VBC'],
                        StrRegN07['PICMS'], StrRegN07['VICMS'])
                    StrFile += StrN07

                if icms_cst in ('60',):
                    StrRegN08 = {
                        'Orig': inv_line.product_id.origin or '0',
                        'CST': icms_cst,
                        'VBCST': str("%.2f" % 0.00),
                        'VICMSST': str("%.2f" % 0.00),
                    }

                    StrN08 = 'N08|%s|%s|%s|%s|\n' % (StrRegN08['Orig'],
                                                     StrRegN08['CST'],
                                                     StrRegN08['VBCST'],
                                                     StrRegN08['VICMSST'])
                    StrFile += StrN08

                if icms_cst in ('70',):
                    StrRegN09 = {
                        'Orig': inv_line.product_id.origin or '0',
                        'CST': icms_cst,
                        'ModBC': inv_line.icms_base_type,
                        'PRedBC': str(
                            "%.2f" %
                            inv_line.icms_percent_reduction),
                        'VBC': str(
                            "%.2f" %
                            inv_line.icms_base),
                        'PICMS': str(
                            "%.2f" %
                            inv_line.icms_percent),
                        'VICMS': str(
                            "%.2f" %
                            inv_line.icms_value),
                        'ModBCST': inv_line.icms_st_base_type,
                        'PMVAST': str(
                            "%.2f" %
                            inv_line.icms_st_mva) or '',
                        'PRedBCST': '',
                        'VBCST': str(
                            "%.2f" %
                            inv_line.icms_st_base),
                        'PICMSST': str(
                            "%.2f" %
                            inv_line.icms_st_percent),
                        'VICMSST': str(
                            "%.2f" %
                            inv_line.icms_st_value),
                    }

                    StrN09 = 'N09|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s'\
                             '|%s|%s|%s|\n' % (
                                 StrRegN09['Orig'], StrRegN09['CST'],
                                 StrRegN09['ModBC'], StrRegN09['PRedBC'],
                                 StrRegN09['VBC'], StrRegN09['PICMS'],
                                 StrRegN09['VICMS'], StrRegN09['ModBCST'],
                                 StrRegN09['PMVAST'], StrRegN09['PRedBCST'],
                                 StrRegN09['VBCST'], StrRegN09['PICMSST'],
                                 StrRegN09['VICMSST'])
                    StrFile += StrN09

                if icms_cst in ('90',):
                    StrRegN10 = {
                        'Orig': inv_line.product_id.origin or '0',
                        'CST': icms_cst,
                        'ModBC': inv_line.icms_base_type,
                        'PRedBC': str(
                            "%.2f" %
                            inv_line.icms_percent_reduction),
                        'VBC': str(
                            "%.2f" %
                            inv_line.icms_base),
                        'PICMS': str(
                            "%.2f" %
                            inv_line.icms_percent),
                        'VICMS': str(
                            "%.2f" %
                            inv_line.icms_value),
                        'ModBCST': inv_line.icms_st_base_type,
                        'PMVAST': str(
                            "%.2f" %
                            inv_line.icms_st_mva) or '',
                        'PRedBCST': '',
                        'VBCST': str(
                            "%.2f" %
                            inv_line.icms_st_base),
                        'PICMSST': str(
                            "%.2f" %
                            inv_line.icms_st_percent),
                        'VICMSST': str(
                            "%.2f" %
                            inv_line.icms_st_value),
                    }

                    StrN10 = 'N10|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n' %\
                        (StrRegN10['Orig'], StrRegN10['CST'],
                         StrRegN10['ModBC'], StrRegN10['PRedBC'],
                         StrRegN10['VBC'], StrRegN10['PICMS'],
                         StrRegN10['VICMS'], StrRegN10['ModBCST'],
                         StrRegN10['PMVAST'], StrRegN10['PRedBCST'],
                         StrRegN10['VBCST'], StrRegN10['PICMSST'],
                         StrRegN10['VICMSST'])
                    StrFile += StrN10

                if icms_cst in ('101',):
                    StrRegN10c = {
                        'Orig': inv_line.product_id.origin or '0',
                        'CSOSN': icms_cst,
                        'pCredSN': str("%.2f" % inv_line.icms_percent),
                        'vCredICMSSN': str("%.2f" % inv_line.icms_value),
                    }

                    StrN10c = 'N10c|%s|%s|%s|%s|\n' %\
                        (StrRegN10c['Orig'], StrRegN10c['CSOSN'],
                         StrRegN10c['pCredSN'], StrRegN10c['vCredICMSSN'])
                    StrFile += StrN10c

                # Incluido CST 102,103 e 300 - Uso no Simples Nacional - Linha
                # original era para CST 400
                if icms_cst in ('102', '103', '300', '400'):
                    StrRegN10d = {
                        'Orig': inv_line.product_id.origin or '0',
                        'CSOSN': icms_cst
                    }

                    StrN10d = 'N10d|%s|%s|\n' % (
                        StrRegN10d['Orig'], StrRegN10d['CSOSN'])
                    StrFile += StrN10d

                if icms_cst in ('201',):
                    StrRegN10e = {
                        'Orig': inv_line.product_id.origin or '0',
                        'CSOSN': icms_cst,
                        'ModBCST': inv_line.icms_st_base_type,
                        'PMVAST': str("%.2f" % inv_line.icms_st_mva) or '',
                        'PRedBCST': '',
                        'VBCST': str("%.2f" % inv_line.icms_st_base),
                        'PICMSST': str("%.2f" % inv_line.icms_st_percent),
                        'VICMSST': str("%.2f" % inv_line.icms_st_value),
                        # TODO Obter aliquota ICMS Simples
                        'pCredSN': str("%.2f" % 0.00),
                        # TODO Calcular Crédito ICMS baseado aliquota anterior.
                        'vCredICMSSN': str("%.2f" % 0.00),
                    }

                    StrN10e = 'N10e|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n' %\
                        (StrRegN10e['Orig'], StrRegN10e['CSOSN'],
                         StrRegN10e['ModBCST'], StrRegN10e['PMVAST'],
                         StrRegN10e['PRedBCST'], StrRegN10e['VBCST'],
                         StrRegN10e['PICMSST'], StrRegN10e['VICMSST'],
                         StrRegN10e['pCredSN'], StrRegN10e['vCredICMSSN'])
                    StrFile += StrN10e

                if icms_cst in ('202', '203'):
                    StrRegN10f = {
                        'Orig': inv_line.product_id.origin or '0',
                        'CSOSN': icms_cst,
                        'ModBCST': inv_line.icms_st_base_type,
                        'PMVAST': str("%.2f" % inv_line.icms_st_mva) or '',
                        'PRedBCST': '',
                        'VBCST': str("%.2f" % inv_line.icms_st_base),
                        'PICMSST': str("%.2f" % inv_line.icms_st_percent),
                        'VICMSST': str("%.2f" % inv_line.icms_st_value),
                    }

                    StrN10f = 'N10f|%s|%s|%s|%s|%s|%s|%s|%s|\n' %\
                        (StrRegN10f['Orig'], StrRegN10f['CSOSN'],
                         StrRegN10f['ModBCST'], StrRegN10f['PMVAST'],
                         StrRegN10f['PRedBCST'], StrRegN10f['VBCST'],
                         StrRegN10f['PICMSST'], StrRegN10f['VICMSST'])
                    StrFile += StrN10f

                if icms_cst in ('500',):
                    StrRegN10g = {
                        'Orig': inv_line.product_id.origin or '0',
                        'CSOSN': icms_cst,
                        'vBCSTRet': '',  # TODO Variavel cf Faixa faturamento
                        'vICMSSTRet': ''  # TODO Variavel cf Faixa faturamento
                    }

                    StrN10g = 'N10g|%s|%s|%s|%s|\n' %\
                        (StrRegN10g['Orig'], StrRegN10g['CSOSN'],
                         StrRegN10g['vBCSTRet'], StrRegN10g['vICMSSTRet'])
                    StrFile += StrN10g

                if icms_cst in ('900',):
                    StrRegN10h = {
                        'Orig': inv_line.product_id.origin or '0',
                        'CSOSN': icms_cst,
                        'modBC': inv_line.icms_base_type,
                        'vBC': str("%.2f" % 0.00),
                        'pRedBC': '',
                        'pICMS': str("%.2f" % 0.00),
                        'vICMS': str("%.2f" % 0.00),
                        'modBCST': '',
                        'pMVAST': '',
                        'pRedBCST': '',
                        'vBCST': '',
                        'pICMSST': '',
                        'vICMSST': '',
                        'pCredSN': str("%.2f" % 0.00),
                        'vCredICMSSN': str("%.2f" % 0.00),
                    }

                    StrN10h = 'N10h|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s'\
                              '|%s|\n' % (StrRegN10h['Orig'],
                                          StrRegN10h['CSOSN'],
                                          StrRegN10h['modBC'],
                                          StrRegN10h['vBC'],
                                          StrRegN10h['pRedBC'],
                                          StrRegN10h['pICMS'],
                                          StrRegN10h['vICMS'],
                                          StrRegN10h['modBCST'],
                                          StrRegN10h['pMVAST'],
                                          StrRegN10h['pRedBCST'],
                                          StrRegN10h['vBCST'],
                                          StrRegN10h['pICMSST'],
                                          StrRegN10h['vICMSST'],
                                          StrRegN10h['pCredSN'],
                                          StrRegN10h['vCredICMSSN'])

                    StrFile += StrN10h

                StrRegO = {
                    'ClEnq': '',
                    'CNPJProd': '',
                    'CSelo': '',
                    'QSelo': '',
                    'CEnq': '999',
                }

                StrO = 'O|%s|%s|%s|%s|%s|\n' % (StrRegO['ClEnq'],
                                                StrRegO['CNPJProd'],
                                                StrRegO['CSelo'],
                                                StrRegO['QSelo'],
                                                StrRegO['CEnq'])

                StrFile += StrO

                if ipi_cst in ('50', '51', '52') and inv_line.ipi_percent > 0:
                    StrRegO07 = {
                        'CST': ipi_cst,
                        'VIPI': str("%.2f" % inv_line.ipi_value),
                    }

                    StrO07 = 'O07|%s|%s|\n' % (
                        StrRegO07['CST'], StrRegO07['VIPI'])

                    StrFile += StrO07

                    if inv_line.ipi_type == 'percent' or '':
                        StrRegO10 = {
                            'VBC': str("%.2f" % inv_line.ipi_base),
                            'PIPI': str("%.2f" % inv_line.ipi_percent),
                        }
                        StrO1 = 'O10|%s|%s|\n' % (
                            StrRegO10['VBC'], StrRegO10['PIPI'])

                    if inv_line.ipi_type == 'quantity':
                        pesol = 0
                        if inv_line.product_id:
                            pesol = inv_line.product_id.weight_net
                        StrRegO11 = {
                            'QUnid': str("%.4f" % (inv_line.quantity * pesol)),
                            'VUnid': str("%.4f" % inv_line.ipi_percent),
                        }
                        StrO1 = 'O11|%s|%s|\n' % (
                            StrRegO11['QUnid'], StrRegO11['VUnid'])

                    StrFile += StrO1

                if ipi_cst in ('99'):
                    StrRegO07 = {
                        'CST': ipi_cst,
                        'VIPI': str("%.2f" % inv_line.ipi_value),
                    }

                    StrO07 = ('O07|%s|%s|\n') % (
                        StrRegO07['CST'], StrRegO07['VIPI'])
                    StrFile += StrO07

                    StrRegO10 = {
                        'VBC': str("%.2f" % inv_line.ipi_base),
                        'PIPI': str("%.2f" % inv_line.ipi_percent),
                    }

                    StrO10 = ('O10|%s|%s|\n') % (
                        StrRegO10['VBC'], StrRegO10['PIPI'])
                    StrFile += StrO10

                if inv_line.ipi_percent == 0 and ipi_cst not in ('99'):
                    StrO1 = 'O08|%s|\n' % ipi_cst
                    StrFile += StrO1

                StrRegP = {
                    'VBC': str("%.2f" % inv_line.ii_base),
                    'VDespAdu': str("%.2f" % inv_line.ii_customhouse_charges),
                    'VII': str("%.2f" % inv_line.ii_value),
                    'VIOF': str("%.2f" % inv_line.ii_iof),
                }

                StrP = ('P|%s|%s|%s|%s|\n') % (StrRegP['VBC'], StrRegP[
                    'VDespAdu'], StrRegP['VII'], StrRegP['VIOF'])
                StrFile += StrP

            if inv_line.product_type == 'service':
                StrRegU = {
                    'VBC': str(
                        "%.2f" % inv_line.issqn_base),
                    'VAliq': str(
                        "%.2f" % inv_line.issqn_percent),
                    'VISSQN': str(
                        "%.2f" % inv_line.issqn_value),
                    'CMunFG': ('%s%s') % (inv.partner_id.state_id.ibge_code,
                                          (inv.partner_id
                                           .l10n_br_city_id.ibge_code)),
                    'CListServ': punctuation_rm(
                        inv_line.service_type_id.code),
                    'cSitTrib': inv_line.issqn_type}

                StrU = ('U|%s|%s|%s|%s|%s|%s|\n') % (
                    StrRegU['VBC'],
                    StrRegU['VAliq'],
                    StrRegU['VISSQN'],
                    StrRegU['CMunFG'],
                    StrRegU['CListServ'],
                    StrRegU['cSitTrib'])
                StrFile += StrU

            StrQ = 'Q|\n'
            StrFile += StrQ

            if pis_cst in ('01', '02') and inv_line.pis_percent > 0:
                StrRegQ02 = {
                    'CST': pis_cst,
                    'VBC': str("%.2f" % inv_line.pis_base),
                    'PPIS': str("%.2f" % inv_line.pis_percent),
                    'VPIS': str("%.2f" % inv_line.pis_value),
                }

                StrQ02 = ('Q02|%s|%s|%s|%s|\n') % (StrRegQ02['CST'],
                                                   StrRegQ02['VBC'],
                                                   StrRegQ02['PPIS'],
                                                   StrRegQ02['VPIS'])

                StrFile += StrQ02

            if pis_cst in ('99', '49'):
                StrRegQ05 = {
                    'CST': pis_cst,
                    'VPIS': str("%.2f" % inv_line.pis_value),
                }

                StrQ05 = ('Q05|%s|%s|\n') % (
                    StrRegQ05['CST'], StrRegQ05['VPIS'])
                StrFile += StrQ05

                StrRegQ07 = {
                    'VBC': str("%.2f" % inv_line.pis_base),
                    'PPIS': str("%.2f" % inv_line.pis_percent),
                }

                StrQ07 = ('Q07|%s|%s|\n') % (
                    StrRegQ07['VBC'], StrRegQ07['PPIS'])
                StrFile += StrQ07

            if inv_line.pis_percent == 0 and pis_cst not in ('99', '49'):
                StrQ02 = 'Q04|%s|\n' % pis_cst
                StrFile += StrQ02

            StrQ = 'S|\n'

            StrFile += StrQ

            if cofins_cst in ('01', '02') and inv_line.cofins_percent > 0:
                StrRegS02 = {
                    'CST': cofins_cst,
                    'VBC': str("%.2f" % inv_line.cofins_base),
                    'PCOFINS': str("%.2f" % inv_line.cofins_percent),
                    'VCOFINS': str("%.2f" % inv_line.cofins_value),
                }

                StrS02 = ('S02|%s|%s|%s|%s|\n') % (StrRegS02['CST'], StrRegS02[
                    'VBC'], StrRegS02['PCOFINS'], StrRegS02['VCOFINS'])
                StrFile += StrS02

            if cofins_cst in ('99', '49'):
                StrRegS05 = {
                    'CST': cofins_cst,
                    'VCOFINS': str("%.2f" % inv_line.cofins_value),
                }

                StrS05 = ('S05|%s|%s|\n') % (
                    StrRegS05['CST'], StrRegS05['VCOFINS'])
                StrFile += StrS05

                StrRegS07 = {
                    'VBC': str("%.2f" % inv_line.cofins_base),
                    'PCOFINS': str("%.2f" % inv_line.cofins_percent),
                }

                StrS07 = ('S07|%s|%s|\n') % (
                    StrRegS07['VBC'], StrRegS07['PCOFINS'])
                StrFile += StrS07

            if inv_line.cofins_percent == 0 and cofins_cst not in ('99', '49'):
                StrS04 = 'S04|%s|\n' % cofins_cst
                StrFile += StrS04

        StrW = 'W|\n'

        StrFile += StrW

        StrRegW02 = {
            'vBC': str("%.2f" % inv.icms_base),
            'vICMS': str("%.2f" % inv.icms_value),
            'vBCST': str("%.2f" % inv.icms_st_base),
            'vST': str("%.2f" % inv.icms_st_value),
            'vProd': str("%.2f" % inv.amount_gross),
            'vFrete': str("%.2f" % inv.amount_freight),
            'vSeg': str("%.2f" % inv.amount_insurance),
            'vDesc': str("%.2f" % inv.amount_discount),
            'vII': str("%.2f" % inv.ii_value),
            'vIPI': str("%.2f" % inv.ipi_value),
            'vPIS': str("%.2f" % inv.pis_value),
            'vCOFINS': str("%.2f" % inv.cofins_value),
            'vOutro': str("%.2f" % inv.amount_costs),
            'vNF': str("%.2f" % inv.amount_total),
            'vTotTrib': str("%.2f" % inv.amount_total_taxes),
        }

        StrW02 = 'W02|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n' % (
            StrRegW02['vBC'], StrRegW02['vICMS'], StrRegW02['vBCST'],
            StrRegW02['vST'], StrRegW02['vProd'], StrRegW02['vFrete'],
            StrRegW02['vSeg'], StrRegW02['vDesc'], StrRegW02['vII'],
            StrRegW02['vIPI'], StrRegW02['vPIS'], StrRegW02['vCOFINS'],
            StrRegW02['vOutro'], StrRegW02['vNF'], StrRegW02['vTotTrib'])

        StrFile += StrW02

        # Modo do Frete:
        # 0- Por conta do emitente;
        # 1- Por conta do destinatário/remetente;
        # 2- Por conta de terceiros; 9- Sem frete (v2.0)
        try:
            if not inv.incoterm:
                StrRegX0 = '9'
            else:
                StrRegX0 = inv.incoterm.freight_responsibility
        except AttributeError:
            StrRegX0 = '9'

        StrX = 'X|%s|\n' % (StrRegX0)

        StrFile += StrX

        StrRegX03 = {
            'XNome': '',
            'IE': '',
            'XEnder': '',
            'UF': '',
            'XMun': '',
        }

        StrX0 = ''

        try:

            StrRegX03['XNome'] = normalize('NFKD', unicode(
                inv.carrier_name or '')).encode('ASCII', 'ignore')

            if inv.carrier_id:

                # Endereço da transportadora
                carrier_addr = pool.get('res.partner').address_get(
                    cr, uid, [inv.carrier_id.partner_id.id], ['default'])
                carrier_addr_default = pool.get('res.partner').browse(
                    cr, uid, [carrier_addr['default']])[0]

                if inv.carrier_id.partner_id.legal_name:
                    StrRegX03['XNome'] = (normalize(
                        'NFKD',
                        unicode(inv.carrier_id.partner_id.legal_name or ''))
                        .encode('ASCII', 'ignore'))
                else:
                    StrRegX03['XNome'] = (normalize(
                        'NFKD',
                        unicode(inv.carrier_id.partner_id.name or ''))
                        .encode('ASCII', 'ignore'))

                StrRegX03['IE'] = inv.carrier_id.partner_id.inscr_est or ''
                StrRegX03['XEnder'] = normalize(
                    'NFKD', unicode(
                        carrier_addr_default.street or '')).encode(
                    'ASCII', 'ignore')
                StrRegX03['UF'] = carrier_addr_default.state_id.code or ''

                if carrier_addr_default.l10n_br_city_id:
                    StrRegX03['XMun'] = (normalize(
                        'NFKD', unicode(
                            carrier_addr_default.l10n_br_city_id.name or ''))
                        .encode('ASCII', 'ignore'))

                if inv.carrier_id.partner_id.is_company:
                    StrX0 = 'X04|%s|\n' % (punctuation_rm(
                        inv.carrier_id.partner_id.cnpj_cpf))
                else:
                    StrX0 = 'X05|%s|\n' % (punctuation_rm(
                        inv.carrier_id.partner_id.cnpj_cpf))
        except AttributeError:
            pass
        StrX03 = 'X03|%s|%s|%s|%s|%s|\n' % (
            StrRegX03['XNome'], StrRegX03['IE'], StrRegX03['XEnder'],
            StrRegX03['UF'], StrRegX03['XMun'])

        StrFile += StrX03
        StrFile += StrX0

        StrRegX18 = {
            'Placa': '',
            'UF': '',
            'RNTC': '',
        }

        if inv.vehicle_plate:
            try:
                StrRegX18['Placa'] = inv.vehicle_plate or ''
                StrRegX18['UF'] = inv.vehicle_state_id.code or ''
                if inv.vehicle_id:
                    StrRegX18['RNTC'] = inv.vehicle_id.rntc_code or ''
            except AttributeError:
                pass

            StrX18 = 'X18|%s|%s|%s|\n' % (StrRegX18['Placa'], StrRegX18[
                                          'UF'], StrRegX18['RNTC'])

            StrFile += StrX18

            StrRegX26 = {
                'QVol': '',
                'Esp': '',
                'Marca': '',
                'NVol': '',
                'PesoL': '',
                'PesoB': '',
            }

        if inv.number_of_packages:
            StrRegX26['QVol'] = inv.number_of_packages
            StrRegX26['Esp'] = inv.kind_of_packages or ''
            StrRegX26['Marca'] = inv.brand_of_packages or ''
            StrRegX26['NVol'] = inv.number_of_packages or ''
            StrRegX26['PesoL'] = str("%.3f" % inv.weight_net)
            StrRegX26['PesoB'] = str("%.3f" % inv.weight)

            StrX26 = 'X26|%s|%s|%s|%s|%s|%s|\n' % (
                StrRegX26['QVol'], StrRegX26['Esp'], StrRegX26[
                    'Marca'], StrRegX26['NVol'], StrRegX26['PesoL'],
                StrRegX26['PesoB'])

            StrFile += StrX26

        if inv.journal_id.revenue_expense:

            StrY = 'Y|\n'

            StrFile += StrY

            for line in inv.move_line_receivable_id:

                if inv.type in ('out_invoice', 'in_refund'):
                    value = line.debit
                else:
                    value = line.credit

                StrRegY07 = {
                    'NDup': line.name,
                    'DVenc': line.date_maturity or inv.date_due or
                    inv.date_invoice,
                    'VDup': str(
                        "%.2f" %
                        value),
                }

                StrY07 = 'Y07|%s|%s|%s|\n' % (StrRegY07['NDup'], StrRegY07[
                                              'DVenc'], StrRegY07['VDup'])

                StrFile += StrY07

        StrRegZ = {
            'InfAdFisco': normalize(
                'NFKD',
                unicode(
                    inv.fiscal_comment or '')).encode(
                'ASCII',
                'ignore'),
            'InfCpl': normalize(
                'NFKD',
                unicode(
                    inv.comment or '')).encode(
                'ASCII',
                'ignore'),
        }

        StrZ = 'Z|%s|%s|\n' % (StrRegZ['InfAdFisco'], StrRegZ['InfCpl'])

        StrFile += StrZ

        if UFEmbarq != '' or XLocEmbarq != '':
            StrRegZA = {
                'UFEmbarq': UFEmbarq,
                'XLocEmbarq': XLocEmbarq,
            }
            StrZA = 'ZA|%s|%s|\n' % (
                StrRegZA['UFEmbarq'], StrRegZA['XLocEmbarq'])
            StrFile += StrZA

        documents = inv.internal_number

        pool.get('account.invoice').write(
            cr, uid, [inv.id], {'nfe_export_date': datetime.now()})

    nfes.append({'key': documents, 'nfe': StrFile,
                 'message': ''})
    return nfes
    # return unicode(StrFile.encode('utf-8'), errors='replace')


def nfe_import(cr, ids, nfe_environment='1', context=False):
    pass
