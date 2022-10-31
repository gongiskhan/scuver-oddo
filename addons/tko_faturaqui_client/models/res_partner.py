from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from . import at_constants


class Partner(models.Model):
    _inherit = 'res.partner'

    unknown = fields.Boolean('Desconhecido')

    @api.model
    def _default_at_self_billing_indicator(self):
        config = self.env.ref('tko_faturaqui_client.faturaqui_main', raise_if_not_found=False)
        return config.default_customer_at_self_billing_indicator

    street2 = fields.Char(size=10)
    at_self_billing_indicator = fields.Selection(at_constants.at_indicators,
                                                 string='Self-Billing Indicator',
                                                 company_dependent=True,
                                                 default=_default_at_self_billing_indicator,
                                                 help=_('Indicator of the existence of a self-billing agreement '
                                                        'between the customer and the supplier.\n'
                                                        'The field shall be filled in with \'Yes\' if there is '
                                                        'an agreement and with \'No\' if there is not one.'))

    @api.onchange('vat')
    def _onchange_vat(self):
        if self._origin.total_invoiced:
            if self._origin.vat and self._origin.vat != 'PT999999990':
                raise ValidationError(_('Cannot change VAT for already invoiced partner'))


    @api.onchange('unknown')
    def onchange_unknown(self):
        if self.unknown:
            if not self.street:
                self.street = 'Desconhecido'
            if not self.city:
                self.city = 'Desconhecido'
            if not self.zip:
                self.zip = 'Desconhecido'
            if not self.country_id:
                self.country_id = self.env['res.country'].search([('code','=','PT')], limit=1).id
            if not self.vat:
                self.vat = 'PT999999990'
