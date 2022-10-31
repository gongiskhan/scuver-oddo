from . import models
from . import wizard

from odoo import api, SUPERUSER_ID


def _clean_res_partner_default_values(cr, registry):
    """ There is no way to know what value is correct for existing customers, so it's better to empty it """
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['res.partner'].search([]).write({'at_self_billing_indicator': False})


def _archive_account_journals(cr, registry):
    """ Must use only new journals for FaturAqui """
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['account.journal'].search([
        ('type', '=', 'sale'),
        ('at_type_out_invoice', '=', False),
    ]).write({'active': False})


def _faturaqui_post_init_hook(cr, registry):
    _clean_res_partner_default_values(cr, registry)
    _archive_account_journals(cr, registry)

