from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
logger = logging.getLogger(__name__)

class MailTemplate(models.Model):
    _inherit = 'mail.template'

    def generate_email(self, res_ids, fields=None):
        # for references see addons: email_template_qweb, l10n_ch
        self.ensure_one()
        multi_mode = True
        # TODO: Imporatnt do not pass res_ids in parameters instead pass src_res_ids
        # if we modify res_ids, we have to set multi_mode = false
        # which can't be passed to super and  can't be passed to super
        # pass same res_ids to super as received in parameter
        src_res_ids = res_ids
        if isinstance(res_ids, int):
            res_ids = [res_ids]
        # Before super, not to generate Account invoice PDF if FaturAqui invoice
        account_tmpl = self.env.ref('account.email_template_edi_invoice')
        if self.id == account_tmpl.id:
            for res_id in res_ids:
                for record in self.env[account_tmpl.model].browse(res_id):
                    if record.server_reference:
                        raise UserError(_('Cannot use Account mail template for a FaturAqui invoice. '
                                          'Please select a different option in Use template.'))
        result = super(MailTemplate, self).generate_email(src_res_ids, fields=fields)
        # After super, to update the template values with attachment_ids
        faturaqui_tmpl = self.env.ref('tko_faturaqui_client.email_template_edi_invoice')
        if self.id == faturaqui_tmpl.id:
            for res_id in res_ids:
                for record in self.env[account_tmpl.model].browse(res_id):
                    if record.server_reference:
                        attachments = record.invoice_attachment_id
                        if attachments.exists():
                            result[res_id]['attachment_ids'] = [(6, 0, attachments.ids)]
                        else:
                            logger.error(_('Failed to load Invoice Attachment. Please select one.'))
                    else:
                        raise UserError(_('Cannot use FaturAqui mail template for a non-FaturAqui invoice. '
                                          'Please select a different option in Use template.'))
        return result
