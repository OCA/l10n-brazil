# -*- coding: utf-8 -*-
# © 2016 Therp BV (<http://therp.nl>)
# © 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from .accounting_none import AccountingNone
from .data_error import DataError


class PropertyDict(dict):

    def __getattr__(self, name):
        return self.get(name)

    def copy(self):  # pylint: disable=copy-wo-api-one,method-required-super
        return PropertyDict(self)


PROPS = [
    'color',
    'background_color',
    'font_style',
    'font_weight',
    'font_size',
    'indent_level',
    'prefix',
    'suffix',
    'dp',
    'divider',
]

TYPE_NUM = 'num'
TYPE_PCT = 'pct'
TYPE_STR = 'str'

CMP_DIFF = 'diff'
CMP_PCT = 'pct'
CMP_NONE = 'none'


class MisReportKpiStyle(models.Model):

    _name = 'mis.report.style'

    @api.constrains('indent_level')
    def check_positive_val(self):
        for record in self:
            if record.indent_level < 0:
                raise UserError(_('Indent level must be greater than '
                                  'or equal to 0'))

    _font_style_selection = [
        ('normal', 'Normal'),
        ('italic', 'Italic'),
    ]

    _font_weight_selection = [
        ('nornal', 'Normal'),
        ('bold', 'Bold'),
    ]

    _font_size_selection = [
        ('medium', 'medium'),
        ('xx-small', 'xx-small'),
        ('x-small', 'x-small'),
        ('small', 'small'),
        ('large', 'large'),
        ('x-large', 'x-large'),
        ('xx-large', 'xx-large'),
    ]

    _font_size_to_xlsx_size = {
        'medium': 11,
        'xx-small': 5,
        'x-small': 7,
        'small': 9,
        'large': 13,
        'x-large': 15,
        'xx-large': 17
    }

    # style name
    # TODO enforce uniqueness
    name = fields.Char(string='Style name', required=True)

    # color
    color_inherit = fields.Boolean(default=True)
    color = fields.Char(
        string='Text color',
        help='Text color in valid RGB code (from #000000 to #FFFFFF)',
        default='#000000',
    )
    background_color_inherit = fields.Boolean(default=True)
    background_color = fields.Char(
        help='Background color in valid RGB code (from #000000 to #FFFFFF)',
        default='#FFFFFF',
    )
    # font
    font_style_inherit = fields.Boolean(default=True)
    font_style = fields.Selection(
        selection=_font_style_selection,
    )
    font_weight_inherit = fields.Boolean(default=True)
    font_weight = fields.Selection(
        selection=_font_weight_selection
    )
    font_size_inherit = fields.Boolean(default=True)
    font_size = fields.Selection(
        selection=_font_size_selection
    )
    # indent
    indent_level_inherit = fields.Boolean(default=True)
    indent_level = fields.Integer()
    # number format
    prefix_inherit = fields.Boolean(default=True)
    prefix = fields.Char(size=16, string='Prefix')
    suffix_inherit = fields.Boolean(default=True)
    suffix = fields.Char(size=16, string='Suffix')
    dp_inherit = fields.Boolean(default=True)
    dp = fields.Integer(string='Rounding', default=0)
    divider_inherit = fields.Boolean(default=True)
    divider = fields.Selection([('1e-6', _('µ')),
                                ('1e-3', _('m')),
                                ('1', _('1')),
                                ('1e3', _('k')),
                                ('1e6', _('M'))],
                               string='Factor',
                               default='1')

    @api.model
    def merge(self, styles):
        """ Merge several styles, giving priority to the last.

        Returns a PropertyDict of style properties.
        """
        r = PropertyDict()
        for style in styles:
            if not style:
                continue
            if isinstance(style, dict):
                r.update(style)
            else:
                for prop in PROPS:
                    inherit = getattr(style, prop + '_inherit', None)
                    if inherit is None:
                        value = getattr(style, prop)
                        if value:
                            r[prop] = value
                    elif not inherit:
                        value = getattr(style, prop)
                        r[prop] = value
        return r

    @api.model
    def render(self, lang, style_props, type, value):
        if type == 'num':
            return self.render_num(lang, value, style_props.divider,
                                   style_props.dp,
                                   style_props.prefix, style_props.suffix)
        elif type == 'pct':
            return self.render_pct(lang, value, style_props.dp)
        else:
            return self.render_str(lang, value)

    @api.model
    def render_num(self, lang, value,
                   divider=1.0, dp=0, prefix=None, suffix=None, sign='-'):
        # format number following user language
        if value is None or value is AccountingNone:
            return u''
        value = round(value / float(divider or 1), dp or 0) or 0
        r = lang.format('%%%s.%df' % (sign, dp or 0), value, grouping=True)
        r = r.replace('-', u'\N{NON-BREAKING HYPHEN}')
        if prefix:
            r = prefix + u'\N{NO-BREAK SPACE}' + r
        if suffix:
            r = r + u'\N{NO-BREAK SPACE}' + suffix
        return r

    @api.model
    def render_pct(self, lang, value, dp=1, sign='-'):
        return self.render_num(lang, value, divider=0.01,
                               dp=dp, suffix='%', sign=sign)

    @api.model
    def render_str(self, lang, value):
        if value is None or value is AccountingNone:
            return u''
        return unicode(value)

    @api.model
    def compare_and_render(self, lang, style_props, type, compare_method,
                           value, base_value,
                           average_value=1, average_base_value=1):
        delta = AccountingNone
        style_r = style_props.copy()
        if isinstance(value, DataError) or isinstance(base_value, DataError):
            return AccountingNone, '', style_r
        if value is None:
            value = AccountingNone
        if base_value is None:
            base_value = AccountingNone
        if type == TYPE_PCT:
            delta = value - base_value
            if delta and round(delta, (style_props.dp or 0) + 2) != 0:
                style_r.update(dict(
                    divider=0.01, prefix='', suffix=_('pp')))
            else:
                delta = AccountingNone
        elif type == TYPE_NUM:
            if value and average_value:
                value = value / float(average_value)
            if base_value and average_base_value:
                base_value = base_value / float(average_base_value)
            if compare_method == CMP_DIFF:
                delta = value - base_value
                if delta and round(delta, style_props.dp or 0) != 0:
                    pass
                else:
                    delta = AccountingNone
            elif compare_method == CMP_PCT:
                if base_value and round(base_value, style_props.dp or 0) != 0:
                    delta = (value - base_value) / abs(base_value)
                    if delta and round(delta, 1) != 0:
                        style_r.update(dict(
                            divider=0.01, dp=1, prefix='', suffix='%'))
                    else:
                        delta = AccountingNone
        if delta is not AccountingNone:
            delta_r = self.render_num(
                lang, delta,
                style_r.divider, style_r.dp,
                style_r.prefix, style_r.suffix,
                sign='+')
            return delta, delta_r, style_r
        else:
            return AccountingNone, '', style_r

    @api.model
    def to_xlsx_style(self, props, no_indent=False):
        num_format = '0'
        if props.dp:
            num_format += '.'
            num_format += '0' * props.dp
        if props.prefix:
            num_format = u'"{} "{}'.format(props.prefix, num_format)
        if props.suffix:
            num_format = u'{}" {}"'.format(num_format, props.suffix)

        xlsx_attributes = [
            ('italic', props.font_style == 'italic'),
            ('bold', props.font_weight == 'bold'),
            ('size', self._font_size_to_xlsx_size.get(props.font_size, 11)),
            ('font_color', props.color),
            ('bg_color', props.background_color),
            ('num_format', num_format),
        ]
        if props.indent_level is not None and not no_indent:
            xlsx_attributes.append(
                ('indent', props.indent_level))
        return dict([a for a in xlsx_attributes
                     if a[1] is not None])

    @api.model
    def to_css_style(self, props, no_indent=False):
        css_attributes = [
            ('font-style', props.font_style),
            ('font-weight', props.font_weight),
            ('font-size',  props.font_size),
            ('color', props.color),
            ('background-color', props.background_color),
        ]
        if props.indent_level is not None and not no_indent:
            css_attributes.append(
                ('text-indent', '{}em'.format(props.indent_level)))
        return '; '.join(['%s: %s' % a for a in css_attributes
                          if a[1] is not None]) or None
