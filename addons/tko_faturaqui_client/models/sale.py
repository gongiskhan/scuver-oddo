from odoo import models, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        if res['product_id']:
            res['tax0_reason_id'] = self.env['product.product'].search([('id', '=', res['product_id'])],
                                                                       limit=1).tax0_reason_id.id
        return res
