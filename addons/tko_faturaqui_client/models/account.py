from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from .faturaqui import ORIGINS
from datetime import datetime

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    at_type_out_invoice = fields.Selection([
        ('FT', 'Invoice'),
        ('FS', 'Simplified Invoice'),
    ], 'AT Invoice Type')
    at_origin = fields.Selection(ORIGINS, 'AT Invoice Origin', default='system')
    code = fields.Char(string='Short Code', size=25, required=True,
                       help='The journal entries of this journal will be named using this code.')
    refund_code = fields.Char(string='Refund Code', size=25,
                              help='The refund entries of this journal will be named using this code.')
    series = fields.Char(string='Series', compute='_compute_series', store=False)
    sequence_id = fields.Many2one('ir.sequence','Sequence')
    refund_sequence_id = fields.Many2one('ir.sequence','Refund Sequence')

    def _get_code_series(self, prefix):
        split_by = ' ' if ' ' in prefix else '/'
        split = prefix.split(split_by, 1)
        code = split[0]
        series = split[1].strip('/')
        return code, series

    @api.depends('sequence_id')
    def _compute_series(self):
        self.series = False
        for record in self.filtered(lambda x: x.type == 'sale' and x.at_type_out_invoice):
            if record.sequence_id:
                ## HERE
                if record.sequence_id.use_date_range:
                    date_range = self.env['ir.sequence.date_range'].search(
                        [('sequence_id', '=', record.sequence_id.id), ('date_to', '>=', datetime.today().date()) ,
                         ('date_from', '<=', datetime.today().date())],
                        order='date_from desc', limit=1)
                    if not date_range:
                        raise ValidationError("Date range not found for sequence %s. \n"
                                      "Please contact Administrator"%record.sequence_id.name)
                    prefix, _ = record.sequence_id.with_context(ir_sequence_date_range=date_range.date_from,
                                                                ir_sequence_date=date_range.date_from)._get_prefix_suffix()
                else:
                    prefix, _ = record.sequence_id._get_prefix_suffix()
                code, series = self._get_code_series(prefix)
                record.series = series

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'sale':
            self.refund_sequence = True

    @api.constrains('refund_sequence')
    def _check_refund_sequence(self):
        for record in self.filtered(lambda x: x.type == 'sale'):
            if not record.refund_sequence:
                raise ValidationError(_('Invoice Series must have a Dedicated Credit Note Sequence.'))

    @api.model
    def _get_sequence_prefix(self, code, refund=False):
        prefix = code
        if refund:
            prefix = 'R' + code
        return prefix + ' %(range_year)s/'

