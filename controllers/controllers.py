# -*- coding: utf-8 -*-
# from odoo import http


# class EmailPreview(http.Controller):
#     @http.route('/email_preview/email_preview', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/email_preview/email_preview/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('email_preview.listing', {
#             'root': '/email_preview/email_preview',
#             'objects': http.request.env['email_preview.email_preview'].search([]),
#         })

#     @http.route('/email_preview/email_preview/objects/<model("email_preview.email_preview"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('email_preview.object', {
#             'object': obj
#         })

