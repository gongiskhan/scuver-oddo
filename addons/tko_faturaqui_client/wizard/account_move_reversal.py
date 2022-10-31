from odoo import api, fields, models, _
from odoo.exceptions import Warning

class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    # Removed 'refund' option
    filter_refund = fields.Selection([
        ('cancel', 'Cancel: create credit note and reconcile'),
        ('modify', 'Modify: create credit note, reconcile and create a new draft invoice')
    ], default='cancel', string='Refund Method', required=True, help='Refund base on this type. You can not Modify and Cancel if the invoice is already reconciled')

    def reverse_moves(self):
        move_obj = self.env['account.move']
        context = dict(self._context or {})

        for form in self:
            for move in move_obj.browse(context.get('active_ids')):
                if move.amount_residual > 0:
                    raise Warning("You can not create credit note for partially paid invoices.")
        return super(AccountMoveReversal, self).reverse_moves()


    @api.model
    def default_get(self, fields):
        res = super(AccountMoveReversal, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        for move in self.env['account.move'].browse(active_ids):
            res['reason'] = 'Valores Inválidos #%s' %move.name
        return res