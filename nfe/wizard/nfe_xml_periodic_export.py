# -*- coding: utf-8 -*-
# Copyright (C) 2014 Rodolfo Leme Bertozo - KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import os
import commands
import base64

from odoo import models, fields
from ..tools.misc import mount_path_nfe


class NfeXmlPeriodicExport(models.TransientModel):

    _name = 'nfe.xml.periodic.export'
    _description = 'Export NFes'

    name = fields.Char(
        'Nome', size=255
    )
    start_period_id = fields.Many2one(
        'account.period',
        u'Período Inicial'
    )
    stop_period_id = fields.Many2one(
        'account.period',
        u'Período Final'
    )
    zip_file = fields.Binary(
        'Zip Files',
        readonly=True
    )
    state = fields.Selection(
        [('init', 'init'),
         ('done', 'done')],
        'state',
        readonly=True,
        default='init',
    )
    export_type = fields.Selection(
        [('nfe', 'NF-e'),
         ('all', 'Tudo')],
        'Exportar',
        required=True,
        default='nfe',
    )

    def done(self, cr, uid, ids, context=False):
        return True

    def export(self, cr, uid, ids, context=False):
        a = self.pool.get('res.company')
        result = 0
        # Define a empresa correta se for multcompany
        company_id = a._company_default_get(cr, uid)
        obj_res_company = a.browse(cr, uid, company_id)
        export_dir = mount_path_nfe(obj_res_company, 'nfe')

        if export_dir == 'False':
            raise orm.except_orm(
                u'Erro!',
                u'Necessário configurar pasta de exportação da empresa.',)

        caminho = export_dir

        # completa o caminho com homologacao ou producao
        if obj_res_company.nfe_environment == '1':
            caminho = os.path.join(caminho, 'producao')
        elif obj_res_company.nfe_environment == '2':
            caminho = os.path.join(caminho, 'homologacao')

        try:
            # Diretorios de importacao, diretorios com formato do ano e mes
            dirs_date = os.listdir(caminho)
        except:
            raise orm.except_orm(
                u'Erro!',
                u'Necessário configurar pasta de exportação da empresa.',)

        for obj in self.browse(cr, uid, ids):
            data = False
            caminho_arquivos = ''
            date_start = obj.start_period_id.date_start
            date_stop = obj.stop_period_id.date_stop
            export_type = obj.export_type

            if date_start[:7] == date_stop[:7]:
                bkp_name = 'bkp_' + date_start[:7] + '.zip'
            else:
                bkp_name = 'bkp_' + \
                    date_start[:7] + '_' + date_stop[:7] + '.zip'

            for diretorio in dirs_date:
                # se houver arquivos fora do padrão (ano-mes, aaaa-mm) dentro
                #  da pasta de exportação
                try:
                    if (int(diretorio[:4]) >= int(date_start[:4]) and
                            int(diretorio[5:]) >= int(date_start[5:7])) and \
                            (int(diretorio[:4]) <= int(date_stop[:4]) and
                                int(diretorio[5:]) <= int(date_stop[5:7])):

                        caminho_aux = os.path.join(caminho, diretorio)
                        dirs_nfes = os.listdir(caminho_aux)

                        for diretorio_final in dirs_nfes:

                            caminho_final = os.path.join(caminho_aux,
                                                         diretorio_final) + '/'
                            comando_cce = 'ls ' + caminho_final + \
                                          '*-??-cce.xml'
                            comando_can = 'ls ' + caminho_final + \
                                          '*-??-can.xml'
                            comando_nfe = 'ls ' + caminho_final + \
                                          '*-nfe.xml| grep -E ' \
                                          '"[0-9]{44}-nfe.xml"'
                            comando_inv = 'ls ' + caminho_final + \
                                          '*-inu.xml| grep -E ' \
                                          '"[0-9]{41}-inu.xml"'

                            if os.system(comando_cce) == 0:
                                str_aux = commands.getoutput(comando_cce)
                                caminho_arquivos = caminho_arquivos + \
                                    str_aux + ' '

                            if os.system(comando_can) == 0:
                                str_aux = commands.getoutput(comando_can)
                                caminho_arquivos = caminho_arquivos + \
                                    str_aux + ' '

                            if os.system(comando_inv) == 0:
                                str_aux = commands.getoutput(comando_inv)
                                caminho_arquivos = caminho_arquivos + \
                                    str_aux + ' '

                            str_aux = commands.getoutput(comando_nfe)
                            if os.system(comando_nfe) == 0:
                                str_aux = commands.getoutput(comando_nfe)
                                caminho_arquivos = caminho_arquivos + \
                                    str_aux + ' '

                        # troca \n por espaços
                        caminho_arquivos = caminho_arquivos.replace('\n', ' ')

                        if export_type == 'nfe' and comando_nfe:
                            result = os.system("zip -r " +
                                               os.path.join(export_dir,
                                                            bkp_name) +
                                               ' ' + caminho_arquivos)
                        else:
                            result = os.system("zip -r " +
                                               os.path.join(export_dir,
                                                            bkp_name) +
                                               ' ' + caminho_arquivos)

                        if result:
                            raise orm.except_orm(
                                u'Erro!',
                                u'Não foi possível compactar os arquivos.',)

                        data = self.read(cr, uid, ids, [], context=context)[0]
                        orderFile = open(os.path.join(export_dir,
                                                      bkp_name), 'r')
                        itemFile = orderFile.read()

                        self.write(cr, uid, ids,
                                   {'state': 'done',
                                    'zip_file': base64.b64encode(itemFile),
                                    'name': bkp_name}, context=context)
                except:
                    pass

        if data:
            return {'type': 'ir.actions.act_window',
                    'res_model': self._name,
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_id': data['id'],
                    'target': 'new', }
        else:
            raise orm.except_orm(
                u'Atenção!',
                u'Não existem arquivos nesse período'
                u' ou período inválido.',)

        return False
