from odoo import api, fields, models, _
from . import at_constants
from .at_constants import AT_TAX_EXEMPTION_REASON_VALS, AT_TAX_TYPES_VALS, \
    AT_TAX_REGIONS_VALS, AT_TAX_CODES_VALS, AT_PRODUCT_TYPES_VALS

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    at_product_type = fields.Selection(AT_PRODUCT_TYPES_VALS, 'AT Product Type',
                                       help='Indicador de produto ou serviço')
    tax0_reason_id = fields.Many2one('account.tax.er', 'Tax Exemption Reason', copy=False)
    has_tax0 = fields.Boolean('Needs Tax Exemption Reason', compute='_compute_has_tax0')

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'consu':
            at_product_type = 'P'
        elif self.type == 'service':
            at_product_type = 'S'
        else:
            at_product_type = 'O'
        self.at_product_type = at_product_type

    @api.depends('taxes_id')
    def _compute_has_tax0(self):

        for record in self:
            self.has_tax0 = False
            if any(not tax_amount for tax_amount in record.taxes_id.mapped('amount') if record.taxes_id):
                record.has_tax0 = True
                record.tax0_reason_id = False


class ProductProduct(models.Model):
    _inherit = 'product.product'

    has_tax0 = fields.Boolean('Needs Tax Exemption Reason', compute='_compute_has_tax0')

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'consu':
            at_product_type = 'P'
        elif self.type == 'service':
            at_product_type = 'S'
        else:
            at_product_type = 'O'
        self.at_product_type = at_product_type

    @api.depends('taxes_id')
    def _compute_has_tax0(self):
        self.has_tax0 = False
        for record in self:
            if any(not tax_amount for tax_amount in record.taxes_id.mapped('amount') if record.taxes_id):
                record.has_tax0 = True
                record.tax0_reason_id = False
