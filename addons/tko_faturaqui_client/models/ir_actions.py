from odoo import api, fields, models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def unlink_action_account_reports(self):
        for report in ['account.account_invoices', 'account.account_invoices_without_payment']:
            self.env.ref(report).unlink_action()
        return True


class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'

    @api.model
    def unlink_action_account_share(self):
        for report in ['account.model_account_invoice_action_share']:
            self.env.ref(report).unlink_action()
        return True
