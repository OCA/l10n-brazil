  * [![Build Status](https://travis-ci.org/odoo-brazil/l10n-brazil.svg?branch=8.0)](https://travis-ci.org/odoo-brazil/l10n-brazil) 
 [![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/odoo-brazil/odoo-brazil?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=body_badge)


Localização Brasileira - Odoo - l10n-brazil
============================================

Este projeto contêm os principais módulos da localização brasileira do OpenERP, estes módulos são a base dos recursos:

* Fiscais
* Contábil
* Sped

Sobre
-----

Este projeto é open source sob licença AGPL v3 http://www.gnu.org/licenses/agpl-3.0.html

Instalação
----------

Instalar o Odoo para produção foge um pouco do escopo desse projeto, pois é algo complexo, em evolução, e que varia muito dependendo se você quer apenas testar, desenvolver, usar em produção ou ainda hospedar.

Vamos então dar aqui os procedimentos simples para testar apenas o core da localização brasileira do OpenERP numa máquina Ubuntu. Mas deixamos claro que essa forma de instalar certamente não é adequada para produção em termo de segurança, desempenho e mantenabilidade.

```
# pacotes debian:
sudo apt-get install postgresql-server
sudo apt-get install -qq graphviz
sudo apt-get -ym install python-dateutil python-docutils python-feedparser python-gdata python-jinja2 python-ldap python-lxml python-mako python-mock python-openid python-psycopg2 python-psutil python-pybabel python-pychart python-pydot python-pyparsing python-reportlab python-simplejson python-tz python-unittest2 python-vatnumber python-vobject python-webdav python-werkzeug python-xlwt python-yaml python-zsi python-imaging bzr

# OpenERP v7.0 nightly:
wget http://nightly.openerp.com/7.0/nightly/src/openerp-7.0-latest.tar.gz
mkdir -p src
tar -xf openerp-7.0-latest.tar.gz -C src

for f in ./src/*
do
    echo "$f" | grep -Eq '^\./abc.[0-9]+$' && continue
    echo "Something with $f here"
done

mv $f openerp
rm -rf ./src
cd openerp
python setup.py --quiet install
cd ..

# dependencias para as regras fiscais:
bzr branch --stacked lp:openerp-fiscal-rules fiscal_rules

# codigo do projeto l10n_br_core (esse projeto):
git clone https://github.com/openerpbrasil/l10n_br_core.git --depth=1 --branch=7.0


psql -c "CREATE USER openerp WITH PASSWORD 'admin';" -U postgres
psql -c 'create database l10n_br_test with owner openerp;' -U postgres


# serviço OpenERP:
cd openerp
./openerp-server --db_user=postgres --db_user=openerp --db_password=admin --db_host=localhost --stop-after-init --addons-path=../fiscal_rules,../l10n_br_core
```

Depois como usuário admin (senha admin), instalar os módulos l10n_br_**

É aconselhado instalar os módulos conforme a necessidade e capacidade de implementação, aos poucos, e não todos os módulos de uma só vez. Instalar com dados de demostração ajuda a melhor avaliar os módulos.

Contribuindo com o código
-----------------------

Você pode resolver umas das issues cadastradas no Github ou implementar melhorias em geral, nos enviando um pull request com as suas alterações.

lista de discussão: http://www.openerpbrasil.org/comunidade
