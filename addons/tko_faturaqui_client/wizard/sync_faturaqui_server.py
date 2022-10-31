from odoo import models, fields, api
from datetime import date
import logging

_logger = logging.getLogger(__name__)


class SyncFaturaquiServer(models.TransientModel):
    _name = 'sync.faturaqui.server'
    _description = 'Sync Faturaqui Server between given date'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    def sync_server(self):
        context = self.env.context
        config = self.env['faturaqui'].browse(context.get('active_id'))
        result = config.sync_invoies(json_data={'start_date': date.strftime(self.start_date, '%Y-%m-%d'),
                                                'end_date': date.strftime(self.end_date, '%Y-%m-%d')})
        ## TODO: dict key result is changed to invoices_dict
        if result.get('result') and result.get('status_code') == 200:
            for key, invoice_dict in result.get('result').items():
                self.check_invoice_status(invoice_dict)
        return True

    def recreate_missing_invoices_from_server(self, invoice_dict):
        def get_journal(code):
            journal = self.env['account.journal'].sudo().search([('code', '=', code)])
            if not journal:
                journal = self.env['account.journal'].sudo().search([('refund_code', '=', code)])
            if not journal:
                _logger.error("No journal found for code %s " % code)
            return journal

        def get_product(product_id):
            product = self.env['product.product'].browse(product_id)
            return product

        journal = get_journal(invoice_dict.get('internal_code'))
        invoice_type = invoice_dict.get('invoice_type', 'FT')
        type = 'out_invoice' if invoice_type != 'NC' else 'out_refund'
        if journal:
            invoice_state = 'paid' if invoice_type == 'NC' else 'open'
            if invoice_dict.get('invoice_status') == 'A':
                invoice_state = 'cancel'
            if invoice_dict.get('credit_note'):
                invoice_state = 'paid'
            invoice = self.env['account.invoice'].sudo().create(
                {'partner_id': int(invoice_dict.get('customer_id')),
                 'number': invoice_dict.get('number'),
                 'server_reference': invoice_dict.get('server_reference'),
                 'print_url': invoice_dict.get('print_url'),
                 'invoice_date': invoice_dict.get('invoice_date'),
                 'journal_id': journal.id,
                 'at_invoice_type': invoice_dict.get('invoice_type'),
                 'type': type,
                 'multibanco_reference': invoice_dict.get('multibanco_reference'),
                 'multibanco_entity': invoice_dict.get('multibanco_entity'),
                 'origin': invoice_dict.get('origin'),
                 'state': 'draft',
                 'print_url': invoice_dict.get('print_url'),
                 'origin': 'Faturaqui Sync',
                 'no_contract': True,
                 }
            )
            if invoice_dict.get('multibanco_entity') and invoice_dict.get('multibanco_reference'):
                self.env['mb.references'].sudo().create({
                    'mb_entity': invoice_dict.get('multibanco_entity'),
                    'mb_reference': invoice_dict.get('multibanco_reference'),
                    'mb_amount': invoice_dict.get('gross_total', 0.0),
                    'invoice_id': invoice.id,
                })
            ### Usig SQL to update this state so we do not trigger emails
            self.env.cr.execute("update account_invoice set state='%s', number='%s' where id= %s" % (
                invoice_state, invoice_dict.get('number'), invoice.id))
            invoice.message_post(body="This invoice was missing and has been created by syncing Faturaqui Server",
                                 subtype='mt_comment')
            for line in invoice_dict.get('lines'):
                product = get_product(int(line.get('product_code')))
                if product:
                    self.env['account.invoice.line'].sudo().create({
                        'product_id': product.id,
                        'account_id': product.property_account_income_id.id,
                        'name': line.get('description'),
                        'quantity': line.get('quantity'),
                        'price_unit': line.get('unit_price'),
                        'discount': line.get('discount'),
                        'uom_id': self.env['uom.uom'].sudo().search([('name','=',line.get('unit_of_measure'))],limit=1).id or False,
                        'tax0_reason_id': self.env['account.tax.er'].sudo().search([('name','=',line.get('tax_exemption_reason'))],limit=1).id or False,
                        'invoice_line_tax_ids': [(6, 0,  self.env['account.tax'].search([('at_tax_code','=',line.get('tax_code'))]).ids )],
                        'invoice_id': invoice.id,
                    })
            return invoice

    def check_invoice_status(self, invoice_dict):
        created_invoices = []
        if invoice_dict.get('server_reference'):
            invoice = self.env['account.invoice'].sudo().search(
                [('server_reference', '=', invoice_dict.get('server_reference'))])
            if not invoice:
                _logger.error("Invoice doesn't exists on server with server reference : %s " % invoice_dict.get(
                    'server_reference'))
                invoice = self.recreate_missing_invoices_from_server(invoice_dict)
                if invoice:
                    created_invoices.append(invoice.id)
                    _logger.info("Created missing invoice  : %s" % invoice)
        return created_invoices
