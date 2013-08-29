#!/bin/bash
# Install the nightly version of OpenERP
cd ..
sudo apt-get -ym install python-dateutil python-docutils python-feedparser python-gdata python-jinja2 python-ldap python-lxml python-mako python-mock python-openid python-psycopg2 python-psutil python-pybabel python-pychart python-pydot python-pyparsing python-reportlab python-simplejson python-tz python-unittest2 python-vatnumber python-vobject python-webdav python-werkzeug python-xlwt python-yaml python-zsi python-imaging bzr
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
bzr branch --stacked lp:openerp-fiscal-rules fiscal_rules
