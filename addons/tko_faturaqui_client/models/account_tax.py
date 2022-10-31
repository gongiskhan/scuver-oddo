from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from .at_constants import AT_TAX_EXEMPTION_REASON_VALS, AT_TAX_TYPES_VALS, \
    AT_TAX_REGIONS_VALS, AT_TAX_CODES_VALS


class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    at_tax_type = fields.Selection(AT_TAX_TYPES_VALS, 'AT Type', default='IVA')
    at_tax_country_region = fields.Selection(AT_TAX_REGIONS_VALS, 'AT Country Region', default='PT')
    at_tax_code = fields.Selection(AT_TAX_CODES_VALS, 'AT Code')


class AccountTax(models.Model):
    _inherit = 'account.tax'

    at_tax_type = fields.Selection(AT_TAX_TYPES_VALS, 'AT Type', default='IVA')
    at_tax_country_region = fields.Selection(AT_TAX_REGIONS_VALS, 'AT Country Region', default='PT')
    at_tax_code = fields.Selection(AT_TAX_CODES_VALS, 'AT Code')

    @api.model
    def update_at_fields(self):
        for record in self.search([]):
            tax_template = self.env['account.tax.template'].search([('name', '=', record.name)])
            record.at_tax_type = tax_template.at_tax_type
            record.at_tax_country_region = tax_template.at_tax_country_region
            record.at_tax_code = tax_template.at_tax_code


class AccountTaxExemptionReason(models.Model):
    _name = 'account.tax.er'
    _description = 'Tax Exemption Reasons'

    name = fields.Char('Name', required=True, copy=False)
    at_tax0_reason = fields.Selection(AT_TAX_EXEMPTION_REASON_VALS, 'Exemption Reason', required=True)
    at_tax0_code = fields.Char('AT Code', compute='_compute_at_tax0_code', store=True)
    tax_id = fields.Many2one('account.tax', 'Tax', default=lambda self: self.env.ref('l10n_pt.iva0'))

    @api.depends('at_tax0_reason')
    def _compute_at_tax0_code(self):
        for record in self:
            record.at_tax0_code = '%s' % record.at_tax0_reason

    @api.onchange('at_tax0_reason')
    def _onchange_at_tax0_reason(self):
        if self.at_tax0_reason:
            self.name = dict(self._fields['at_tax0_reason'].selection)[self.at_tax0_reason]

    @api.constrains('name')
    def _check_name(self):
        if self.name not in dict(self._fields['at_tax0_reason'].selection).values():
            raise ValidationError(_('Please add the article paragraph in the exemption reason.'))
