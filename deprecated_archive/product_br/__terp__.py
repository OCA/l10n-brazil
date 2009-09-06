# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name" : "Informações Fiscais de produtos no Brasil",
    "version" : "1.0",
    "author" : "Sidnei Brianti <web@asblogic.com.br",
    "category" : "Enterprise Specific Modules/Products of Brazil",
    "depends" : ["base", "account", "product", "stock"],
    "init_xml" : ["clfiscal.xml","cst.xml"],
    "demo_xml" : [],
    "description": "Este modulo adiciona os campos Situação Tributária e Classificação Fiscal na formulário de produtos",
    "update_xml" : ["product_br_view.xml"],
    "active": False,
    "installable": True
}


