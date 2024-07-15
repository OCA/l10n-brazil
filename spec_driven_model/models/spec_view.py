# Copyright 2019-2020 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import logging

from lxml import etree
from lxml.builder import E
from odoo import models, api
from odoo.osv.orm import setup_modifiers

_logger = logging.getLogger(__name__)

TAB_NAME = "NFe"  # TODO dynamic
FIELD_PREFIX = "nfe40_"
CHOICE_PREFIX = "nfe40_choice"
# TODO use schema name as default root key unless a key is provided in the
#  class


# TODO use MetaModel._get_concrete

class SpecViewMixin(models.AbstractModel):
    _inherit = 'spec.mixin'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(SpecViewMixin, self.with_context(no_subcall=True)
                    ).fields_view_get(view_id, view_type, toolbar)
        # _logger.info("+++++++++++++++", self, type(self), self._context)
        if self._context.get('no_subcall'):
            return res
        # TODO collect class ancestors of StackedModel kind and
        # extract the different XSD schemas injected. Then add a tab/page
        # per schema unless context specify some specific schemas.

        # TODO override only if special dev or fiscal group or if spec_class in
        # context
        # TODO allow special XML placeholders to be replaced by proper fragment
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            fields = []
            if len(doc.xpath("//notebook")) > 0:
                arch, fields = self._build_spec_fragment()
                # arch.set("col", "4") TODO ex res.partner
                node = doc.xpath("//notebook")[0]
                page = E.page(string=TAB_NAME)
                page.append(arch)
                node.insert(1000, page)
            elif len(doc.xpath("//sheet")) > 0:
                arch, fields = self._build_spec_fragment()
                node = doc.xpath("//sheet")[0]
                arch.set("string", TAB_NAME)
                arch.set("col", "2")  # TODO ex fleet
                if res['name'] == 'default':
                    # we replace the default view by our own
                    # _logger.info("Defaulttttttt view:")
                    # _logger.info(etree.tostring(node, pretty_print=True).decode())
                    for c in node.getchildren():
                        node.remove(c)
                    arch = arch.getchildren()[0]
                    arch.set("col", "4")
                    node.insert(1000, arch)
                    # _logger.info("Specccccccccc View:")
                    # _logger.info(etree.tostring(node, pretty_print=True).decode())
                else:
                    node.insert(1000, arch)
            elif len(doc.xpath("//form")) > 0:  # ex invoice.line
                arch, fields = self._build_spec_fragment()
                node = doc.xpath("//form")[0]
                arch.set("string", TAB_NAME)
                arch.set("col", "2")
                node.insert(1000, arch)

            # print("VIEW IS NOW:")
            # print(etree.tostring(doc, pretty_print=True).decode())
            for field_name in fields:
                if not self.fields_get().get(field_name):
                    continue
                field = self.fields_get()[field_name]
#                print("----", field_name, field)
                res['fields'][field_name] = field
                # print("looking for", field_name)
                field_node = doc.xpath("//field[@name='%s']" %
                                       (field_name,))
                if field_node:
                    setup_modifiers(field_node[0], field)

            res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def _build_spec_fragment(self, container=None):
        if container is None:
            container = E.group()

            view_child = E.group()
            view_child.append(E.button(
                name='export_xml',
                type='object',
                string='Export',
            ))

        container.append(view_child)
        fields = []
        if hasattr(type(self), '_stacked') and type(self)._stacked:
            # we want the root of what is stacked to recreate the hierarchy
            lib_model = self.env[type(self)._stacked]
            self.build_arch(lib_model, container, fields, 0)
        else:
            if hasattr(self, 'fiscal_document_id'):
                lib_model = self.fiscal_document_id
            elif hasattr(self, 'fiscal_document_line_id'):
                lib_model = self.fiscal_document_line_id
            else:
                lib_model = self
            classes = [getattr(x, '_name', None)
                       for x in type(lib_model).mro()]
            # _logger.info("#####", lib_model, classes)
            for c in set(classes):
                if c is None:
                    continue
                if 'nfe.' not in c:  # make generic brittle
                    continue
                # the following filter to fields to show
                # when several XSD class are injected in the same object
                if self._context.get('spec_class') and \
                        c != self._context['spec_class']:
                    continue
                lib_model = self.env[c]
                short_desc = lib_model._description.splitlines()[0]
                sub_container = E.group(string=short_desc)
                self.build_arch(lib_model, sub_container, fields, 1)
                container.append(sub_container)
        # _logger.info(etree.tostring(container, pretty_print=True).decode())
        return container, fields

    # TODO cache!!
    # TODO pass schema arg (nfe_, nfse_)
    # TODO required only if visible
    @api.model
    def build_arch(self, lib_node, view_node, fields, depth=0):
        """Creates a view arch from an generateds lib model arch"""
        # _logger.info("BUILD ARCH", lib_node)
        choices = set()
        wrapper_group = None
        wrapper_notebook = None
        inside_notebook = False
        stacked_classes = [getattr(x, '_name', None) for x in type(self).mro()]

#        for spec in lib_node.member_data_items_:
        for field_name, field in lib_node._fields.items():
            # _logger.info("   field", field_name)
            # import pudb; pudb.set_trace()

            # skip automatic m2 fields, non xsd fields
            # and display choice selector only where it is used
            # (possibly later)
            if '_id' in field_name\
                    or FIELD_PREFIX not in field_name\
                    or CHOICE_PREFIX in field_name:
                continue

            # Odoo expects fields nested in 2 levels of group tags
            # but past 2 levels, extra nesting ruins the layout
            if depth == 0 and not wrapper_group:
                wrapper_group = E.group()

            # should we create a choice block?
            if hasattr(field, 'choice'):
                choice = getattr(field, 'choice')
                selector_name = "%s%s" % (CHOICE_PREFIX, choice,)
                if choice not in choices:
                    choices.add(choice)
                    fields.append(selector_name)
                    selector_field = E.field(name=selector_name)
                    if wrapper_group is not None:
                        view_node.append(wrapper_group)
                        wrapper_group.append(selector_field)
                    else:
                        view_node.append(selector_field)
            else:
                selector_name = None

            if hasattr(field, 'view_attrs'):
                attrs = getattr(field, 'view_attrs')
            else:
                if False:  # TODO getattr(field, 'xsd_required', None):
                    required = True
                    # TODO if inside optionaly visible group, required should
                    # be optional too
                else:  # assume dynamically required via attrs
                    required = False

                if selector_name is not None:
                    invisible = "[('%s','!=','%s')]" % (selector_name,
                                                        field_name)
                    attrs = {'invisible': invisible}
                else:
                    attrs = False

            # complex m2o stacked child
            if hasattr(type(self), '_stacked') and field.type == 'many2one' \
                    and field.comodel_name in stacked_classes:
                # TODO is is a suficient condition?
                # study what happen in res.partner with dest#nfe_enderDest
                # _logger.info('STACKED', field_name, field.comodel_name)
                wrapper_group = None
                if hasattr(field, 'original_comodel_name'):
                    lib_child = self.env[getattr(field,
                                                 'original_comodel_name')]
                else:
                    lib_child = self.env[field.comodel_name]

                child_string = field.string
#                if isinstance(child_string, str):
#                    child_string = child_string  # .decode('utf-8')
#                if hasattr(lib_child, '_stack_path'): # TODO
#                    child_string = lib_child._stack_path
                if depth == 0:
                    view_child = E.group(string=child_string)
                    if attrs:
                        view_child.set('attrs', "%s" % (attrs,))
                        setup_modifiers(view_child)
                    view_node.append(view_child)
                    self.build_arch(lib_child, view_child, fields, depth + 1)
                else:
                    page = E.page(string=child_string)
                    invisible = False
                    if attrs:
                        page.set('attrs', "%s" % (attrs,))
                        setup_modifiers(page)
                    if not inside_notebook:
                        # first page
                        # this makes a difference in invoice line forms:
                        wrapper_notebook = E.notebook(colspan="2")
                        view_node.set('colspan', '2')
                        view_node.append(wrapper_notebook)
                        inside_notebook = True
                        if invisible:
                            # in case the notebook has only one page,
                            # the visibility should be carried by the
                            # notebook itself
                            wrapper_notebook.set('attrs', "{'invisible':%s}" %
                                                 (invisible,))
                            setup_modifiers(wrapper_notebook)
                    else:
                        # cancel notebook dynamic visbility
                        wrapper_notebook.set('attrs', '')
                        wrapper_notebook.set('modifiers', '')
                    view_child = E.group()
                    page.append(view_child)
                    wrapper_notebook.append(page)  # TODO attrs / choice
                    # TODO inherit required
                    self.build_arch(lib_child, view_child, fields, 0)

            # simple type, o2m or m2o mapped to an Odoo object
            else:
                wrapper_notebook = None
                inside_notebook = False
                fields.append(field_name)

                if required and attrs:
                    dyn_required = "[('%s','=','%s')]" % (selector_name,
                                                          field_name)
                    attrs['required'] = dyn_required

                # TODO the _stack_path assignation doesn't work
                # if hasattr(field, '_stack_path'):  # and
                # field.args.get('_stack_path') is not None:
                #     path = getattr(field, '_stack_path')

                if hasattr(field, 'original_comodel_name'):
                    spec_class = getattr(field, 'original_comodel_name')
                    field_tag = E.field(name=field_name,
                                        context="{'spec_class': '%s'})" %
                                        (spec_class,))
                else:
                    field_tag = E.field(name=field_name)
                if attrs:
                    field_tag.set('attrs', "%s" % (attrs,))
                elif required:
                    field_tag.set('required', 'True')

                if field.type in ('one2many', 'many2many', 'text', 'html'):
                    field_tag.set('colspan', '4')
                    view_node.append(E.newline())
                    if wrapper_group is not None:
                        view_node.append(wrapper_group)
                        wrapper_group.append(field_tag)
                    else:
                        view_node.append(field_tag)
                        view_node.append(E.newline())
                else:
                    if wrapper_group is not None:
                        view_node.append(wrapper_group)
                        wrapper_group.append(field_tag)
                    else:
                        view_node.append(field_tag)

    @api.model
    def _get_default_tree_view(self):
        """ Generates a single-field tree view, based on _rec_name.
        :returns: a tree view as an lxml document
        :rtype: etree._Element
        """
        desc = self._description
        tree = E.tree(string=desc)
        c = 0
        required_fields_num = len([f[1] for f in self._fields.items()
                                   if f[1].required])
        for fname, field in self._fields.items():
            if field.automatic or fname == 'currency_id':
                continue
            if len(self._fields) > 7 and required_fields_num > 2\
                    and not field.required:
                continue
            else:
                tree.append(E.field(name=fname))
            if c > 12:
                break
            c += 1
        return tree
