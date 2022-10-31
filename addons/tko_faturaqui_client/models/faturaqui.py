import base64
import json
import urllib.request
from io import BytesIO
from datetime import datetime
import xlwt
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

from . import at_constants

COPIES = [
    ('2', _('Duplicated')),
    ('3', _('Triplicated')),
    ('4', _('Quadruplicated')),
]

ORIGINS = [
    ('system', _('System')),
    # 'manual': 'Manual',
    # 'recovery': 'Recovery',
    # 'other': 'Other',
]

months = [
    ('01', _('January')),
    ('02', _('February')),
    ('03', _('March')),
    ('04', _('April')),
    ('05', _('May')),
    ('06', _('June')),
    ('07', _('July')),
    ('08', _('August')),
    ('09', _('September')),
    ('10', _('October')),
    ('11', _('November')),
    ('12', _('December')),
]


class Faturaqui(models.Model):
    _name = 'faturaqui'
    _description = 'FaturAqui'

    name = fields.Char('Software Name', required=True, readonly=True)
    version = fields.Char('Software Version', required=True, readonly=True)
    software_certificate_number = fields.Char('Software Certificate Number', required=True, readonly=True)

    server_url = fields.Char('Server URL')  # To make required need to provide default
    client_token = fields.Char('Client Token')
    use_webservice = fields.Boolean('Use Webservice', default=False)

    default_customer_at_self_billing_indicator = fields.Selection(at_constants.at_indicators,
                                                                  string='Default Customer Self-Billing Indicator',
                                                                  help=_(
                                                                      'This value will be set on every new customer.'))
    default_invoice_at_self_billing_indicator = fields.Selection(at_constants.at_indicators,
                                                                 string='Default Invoice Self-Billing Indicator',
                                                                 help=_('If not set here, it will be set on '
                                                                        'every invoice from its customer\'s default.'))
    default_invoice_at_cash_vat_scheme_indicator = fields.Selection(at_constants.at_indicators,
                                                                    string='Default Invoice Cash VAT Scheme Indicator',
                                                                    help=_(
                                                                        'This value will be set on every new invoice.'))
    default_invoice_at_third_parties_billing_indicator = fields.Selection(at_constants.at_indicators,
                                                                          string='Default Invoice Third Parties Billing Indicator',
                                                                          help=_(
                                                                              'This value will be set on every new invoice.'))
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    @api.model
    def get_main(self):
        main = self.env.ref('tko_faturaqui_client.faturaqui_main')
        if not main.server_url:
            raise UserError(_(
                'Cannot find FaturAqui Server URL. Please update in Invoicing/Configuration/FaturAqui/Information.'))
        if not main.client_token:
            raise UserError(_(
                'Cannot find FaturAqui Client Token. Please update in Invoicing/Configuration/FaturAqui/Information.'))
        return main

    @api.model
    def emit(self, json_data, action, destination):
        main = self.get_main()
        json_data.update({'client_token': main.client_token})
        url = '%s/faturaqui/1.0/%s/%s' % (main.server_url, action.upper(), destination.upper())
        jsondataasbytes = json.dumps(json_data).encode('utf-8')  # needs to be bytes
        req = urllib.request.Request(url)
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        req.add_header('Content-Length', len(jsondataasbytes))
        response = urllib.request.urlopen(req, jsondataasbytes)
        string = response.read().decode('utf-8')
        result = json.loads(string)['result']
        return result

    def log(self, document_sudo, action):
        now = fields.Datetime.to_string(fields.Datetime.now())
        user = '%d-%s' % (self.env.user.id, self.env.user.login)
        server_message = json.loads(document_sudo.server_message) if document_sudo.server_message else {}
        server_message.update({
            action: {
                'date': now,
                'user': user,
            }
        })
        document_sudo.server_message = json.dumps(server_message)
        if action == 'original':
            msg = _('Confirmed having kept the invoice\'s original')
        elif action == 'print_original':
            msg = _('Asked for the invoice\'s original')
        document_sudo.message_post(body=msg, message_type='comment', subtype='mail.mt_note')
        return True

    def sync_invoies(self, json_data={}):
        json_data.update({'client_token': self.client_token})
        url = '%s/faturaqui/1.0/SyncInvoces' % (self.server_url)
        jsondataasbytes = json.dumps(json_data).encode('utf-8')  # needs to be bytes
        req = urllib.request.Request(url)
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        req.add_header('Content-Length', len(jsondataasbytes))
        response = urllib.request.urlopen(req, jsondataasbytes)
        string = response.read().decode('utf-8')
        result = json.loads(string)['result']
        return result


class FaturaquiSaft(models.Model):
    _name = 'faturaqui.saft'
    _description = 'FaturAqui SAF-T'

    @api.model
    def _default_month(self):
        month = '%02d' % fields.Date.from_string(fields.Date.context_today(self)).month
        return month

    @api.model
    def _default_year(self):
        return str(fields.Date.from_string(fields.Date.context_today(self)).year)

    name = fields.Char(string='Name', required=True, readonly=True, compute='compute_name')
    type = fields.Selection([('m', 'Monthly'),
                             ('a', 'Annual')], default='m', string='Type', required=True, readonly=True)
    month = fields.Selection(months, 'Month', default=_default_month)
    year = fields.Char('Year', default=_default_year)
    export_type = fields.Selection([('s', 'Saft'), ('e', 'Excel')], default='s', required=True, string='Export')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    file = fields.Binary('File (Saft)', readonly=True, copy=False)
    filename = fields.Char('Filename')
    file_xls = fields.Binary('File XLS', readonly=True, copy=False)

    @api.depends('type', 'month', 'year')
    def compute_name(self):
        type = 'SAFT-'
        if self.type == 'e':
            type = 'Listagem-'
        self.name = type + self.month + '-' + self.year

    def get_saft_data(self):
        saft_data = {
            'year': self.year,
        }
        if self.type == 'm':
            saft_data.update({'month': self.month})
        return saft_data

    def generate_file(self):
        data = self.get_saft_data()
        response = self.env['faturaqui'].emit(data, 'create', 'saft')
        if response.get('error'):
            raise AccessError(_('FaturAqui Server Error: %s' % response['error']['message']))
        if response.get('result'):
            result = response['result']
            self.file = result['file']
            self.filename = result['filename']
        return True

    def generate_xls(self):
        style_lightblue = xlwt.easyxf('pattern: pattern solid, fore_colour light_blue;'
                                      'font: colour white, ;')

        style_0x31 = xlwt.easyxf('pattern: pattern solid, fore_colour 0x31;'
                                 'font: colour 0x21, bold True; align: vert centre, horiz centre, wrap off',
                                 )
        style_blue_center = xlwt.easyxf('pattern: pattern solid, fore_colour light_blue;'
                                        'font: colour white, bold True; align: vert centre, horiz centre, wrap off',
                                        'borders: top double, bottom double, left double, right double;')
        style_pink_center = xlwt.easyxf('pattern: pattern solid, fore_colour pink;'
                                        'font: colour white, bold True; align: vert centre, horiz centre, wrap off',
                                        'borders: top double, bottom double, left double, right double;')

        heading = [u'Data da Fatura', u'Data de Vencimento', u'Documento Origem.', u'Número',
                   u'Total na moeda da Fatura', u'URL']

        def set_header_building(row, title='Facturas'):
            sheet.write_merge(row, row, 0, 5, title, style_pink_center)
            row += 2
            return row

        def set_header(row, title='Facturas'):
            sheet.write_merge(row, row, 0, 5, title, style_blue_center)
            row += 1
            for col in range(0, len(heading)):
                sheet.write(row, col, heading[col], style_lightblue)
                col += 1
            return row

        def write_invoie_row(invoices, row):
            col = 0
            for invoice in invoices:
                sheet.write(row, col, invoice.date_invoice and datetime.strftime(invoice.date_invoice, '%d-%m-%Y') or '')
                sheet.write(row, col + 1, invoice.date_due and datetime.strftime(invoice.date_due, '%d-%m-%Y') or '')
                sheet.write(row, col + 2, invoice.partner_id.name)
                sheet.write(row, col + 3, invoice.number or invoice.move_name)
                sheet.write(row, col + 4, invoice.amount_total)
                sheet.write(row, col + 5, invoice.print_url or '')
                row += 1
            total = sum(invoices.mapped('amount_total'))
            row += 2
            sheet.write(row, col + 4, total, style_0x31)
            return row + 1

        def insert_invoices(row, FT_invoices, NC_invoices, CN_invoices):
            # Invoices.
            row = set_header(row, title='Facturas')
            row = write_invoie_row(FT_invoices, row + 1)

            # Credit Notes
            row += 1
            row = set_header(row, 'Nota de Credito')
            row = write_invoie_row(NC_invoices, row + 1)

            # Cancelled Invoices
            row += 1
            row = set_header(row, 'Facturas Canceladas')
            row = write_invoie_row(CN_invoices, row + 1)
            return row + 1

        # Create a workbook and add a worksheet.
        workbook = xlwt.Workbook(encoding="UTF-8")
        sheet = workbook.add_sheet('Facturas', cell_overwrite_ok=True)

        start_date = self.start_date
        end_date = self.end_date

        domain = [('date_invoice', '>=', start_date),
                  ('date_invoice', '<=', end_date)]
        row = 1
        try:
            ## Invoices with buildings
            buildings = self.env['op.building'].search([])
            for building in buildings:
                FT_invoices = self.env['account.invoice'].sudo().search(
                    domain + [('state', 'in', ['open', 'paid', 'cr']), ('type', '=', 'out_invoice'),
                              ('building_id', '=', building.id)])
                NC_invoices = self.env['account.invoice'].sudo().search(
                    domain + [('state', 'in', ['open', 'paid', 'cr']), ('type', '=', 'out_refund'),
                              ('building_id', '=', building.id)])
                CN_invoices = self.env['account.invoice'].sudo().search(
                    domain + [('state', 'in', ['cancel']), ('type', '=', 'out_invoice'),
                              ('building_id', '=', building.id)])
                if FT_invoices or NC_invoices or CN_invoices:
                    row = set_header_building(row, title=building.name)

                    row = insert_invoices(row, FT_invoices, NC_invoices, CN_invoices)
            #### Invoices with undefined Building
            FT_invoices = self.env['account.invoice'].sudo().search(
                domain + [('state', 'in', ['open', 'paid', 'cr']), ('type', '=', 'out_invoice'),
                          ('building_id', '=', False)])
            NC_invoices = self.env['account.invoice'].sudo().search(
                domain + [('state', 'in', ['open', 'paid', 'cr']), ('type', '=', 'out_refund'),
                          ('building_id', '=', False)])
            CN_invoices = self.env['account.invoice'].sudo().search(
                domain + [('state', 'in', ['cancel']), ('type', '=', 'out_invoice'),
                          ('building_id', '=', False)])
            if FT_invoices or NC_invoices or CN_invoices:
                row = set_header_building(row, title='Undefined')
                row = insert_invoices(row, FT_invoices, NC_invoices, CN_invoices)

        except:
            ## Invoices without building object in database
            FT_invoices = self.env['account.invoice'].sudo().search(
                domain + [('state', 'in', ['open', 'paid', 'cr']), ('type', '=', 'out_invoice')])
            NC_invoices = self.env['account.invoice'].sudo().search(
                domain + [('state', 'in', ['open', 'paid', 'cr']), ('type', '=', 'out_refund')])
            CN_invoices = self.env['account.invoice'].sudo().search(
                domain + [('state', 'in', ['cancel']), ('type', '=', 'out_invoice')])
            row = insert_invoices(row, FT_invoices, NC_invoices, CN_invoices)

        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        self.file_xls = base64.encodebytes(data)

        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': '/web/content/faturaqui.saft/%s/%s/%s.xls?download=true' % (self.id, 'file_xls', self.month),

        }

    @api.constrains('year')
    def _check_year(self):
        if not self.year.isdigit():
            raise ValidationError(_('Cannot use this year.'))
