# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Danimar Ribeiro 26/06/2013                              #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################
{
    "name": "Envio de NFe",
    "version": "1.0",    
    "author": "Danimar Ribeiro",
    'category': 'Localisation Brasil',
    'license': 'AGPL-3',
    'website': 'http://www.openerpbrasil.org',
    "description": """
      Este módulo é complementar para enviar para a receita a nfe, inutilização e cancelamento de notas.
      Dependencias: pysped, geraldo, pyxmlsec
      Instalando pyxmlsec 
        sudo pip install pyxmlsec
        Dependencias ->
        sudo apt-get install libxmlsec1-dev
        sudo apt-get install libxml2-dev
      Instalando geraldo
        sudo pip install geraldo
    """,
    'depends': [
        'base',
        'l10n_br_account',        
    ],
    "init_xml": [],
    'update_xml': ['l10n_br_nfe.xml'],
    'demo_xml': [],
    'installable': True,
    'active': False,
}