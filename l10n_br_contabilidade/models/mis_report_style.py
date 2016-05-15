# -*- coding: utf-8 -*-
# © 2016 Therp BV (<http://therp.nl>)
# © 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models, _
from openerp.exceptions import UserError

from .accounting_none import AccountingNone


class PropertyDict(dict):

    def __getattr__(self, name):
        return self.get(name)

    def copy(self):
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


class MisReportKpiStyle(models.Model):

    _name = 'mis.report.style'

    @api.one
    @api.constrains('indent_level')
    def check_positive_val(self):
        if self.indent_level < 0:
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
    )
    background_color_inherit = fields.Boolean(default=True)
    background_color = fields.Char(
        help='Background color in valid RGB code (from #000000 to #FFFFFF)'
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
    def to_xlsx_style(self, props):
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
            ('indent', props.indent_level),
            ('num_format', num_format),
        ]
        return dict([a for a in xlsx_attributes
                     if a[1] is not None])

    @api.model
    def to_css_style(self, props):
        css_attributes = [
            ('font-style', props.font_style),
            ('font-weight', props.font_weight),
            ('font-size',  props.font_size),
            ('color', props.color),
            ('background-color', props.background_color),
            ('indent-level', props.indent_level)
        ]
        return '; '.join(['%s: %s' % a for a in css_attributes
                          if a[1] is not None]) or None
