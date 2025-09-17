# -*- coding: utf-8 -*-
import re

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import random
import datetime
from odoo import http, fields, _
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.http import request
from math import ceil
from itertools import groupby as groupbyelem
import base64
import secrets
import string


class AppPreviewController(http.Controller):

    @http.route('/app/preview', type='http', auth='public', website=True, csrf=True)
    def preview_form(self, **kw):
        """Show email input form"""
        return request.render('email_preview.view_email_input_form_email')

    @http.route('/app/preview/create_user', type='http', auth='public', website=True, csrf=True)
    def create_preview_user(self, **post):
        """Create preview user with restricted access"""
        email = post.get('email')
        if not email:
            return "Please provide a valid email."

        # Character set: letters + digits
        characters = string.ascii_letters + string.digits

        # Generate secure random string of length 8
        password = ''.join(secrets.choice(characters) for _ in range(8))

        # Check if user already exists
        user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
        if not user:
            # Create user without admin rights
            installed_modules = request.env['ir.module.module'].sudo().search([('state', '=', 'installed')])
            groups = request.env['res.groups'].sudo().search([
                ('id', 'in', request.env['ir.model.data'].sudo().search([
                    ('module', 'in', installed_modules.mapped('name')),
                    ('model', '=', 'res.groups')
                ]).mapped('res_id'))
            ])
            excluded_groups = [
                request.env.ref('base.group_portal').id,
                request.env.ref('base.group_public').id,
                request.env.ref('base.group_erp_manager').id,
            ]
            # Ensure Internal User group (mandatory)
            base_internal = request.env.ref('base.group_user')

            valid_groups = (groups.ids + [base_internal.id])
            valid_groups = list(set(valid_groups) - set(excluded_groups))

            user = request.env['res.users'].sudo().create({
                'name': email.split('@')[0].capitalize(),
                'login': email,
                'email': email,
                'password': password,
                'groups_id': [(6, 0, valid_groups)]
            })

            # Remove groups using ORM (safer than raw SQL)
            group_ids_to_remove = [2, 4]
            user.write({
                'groups_id': [(3, gid) for gid in group_ids_to_remove]
            })
            template = request.env.ref('email_preview.user_credentials_email_preview')
            mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
            email_from = mail_server.smtp_user
            if template:
                try:
                    # Add context with force_send to ensure immediate email sending
                    email_values = {
                        'email_to': email,
                        'email_from': email_from,
                    }

                    ctx = {
                        'default_model': 'previewotp.verification',
                        'default_res_id': 1,
                        'default_email_to': email,  # Ensure the email field exists
                        'default_template_id': template.id,
                        'email': email,
                        'password': password,
                    }

                    s = template.with_context(**ctx).sudo().send_mail(user.id, email_values=email_values, force_send=True)

                except Exception as e:
                    pass


        # Redirect user to login page
        # return request.redirect('/web/login')
        return http.Response('{"status": "success", "message": "User Created successfully"}',
                             content_type='application/json')

    @http.route('/email_preview/create/otp', auth='public', website=True, methods=['POST'], csrf=False)
    def send_otp(self, **post):
        """Generate OTP and store email in session"""
        email = post.get('email')

        if not email:
            return http.Response('{"status": "error", "message": "Email is required"}', content_type='application/json')

        user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
        if user:
            return http.Response('{"status": "error", "message": "This email already in use. Use different email."}', content_type='application/json')
        # Generate OTP
        otp_code = str(random.randint(100000, 999999))
        expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
        # Remove previous OTPs
        request.env['previewotp.varification'].sudo().search([('email', '=', email)]).unlink()

        # Store OTP in database
        x = request.env['previewotp.varification'].sudo().create({
            'email': email,
            'otp': otp_code,
            'expiry_time': expiry_time,
            'verified': False
        })
        template = request.env.ref('email_preview.otp_verification_template_email')
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        email_from = mail_server.smtp_user

        if template:
            try:
                # Add context with force_send to ensure immediate email sending
                email_values = {
                    'email_to': email,
                    'email_from': email_from,
                }

                ctx = {
                    'default_model': 'previewotp.verification',
                    'default_res_id': 1,
                    'default_email_to': email,  # Ensure the email field exists
                    'default_template_id': template.id,
                    'otp_code': otp_code,
                }

                s = template.with_context(**ctx).sudo().send_mail(x, email_values=email_values, force_send=True)

            except Exception as e:
                pass
        # return request.render('email_preview.preview_otp_form')
        return http.Response('{"status": "success", "message": "OTP has been sent"}', content_type='application/json')

    @http.route('/email_preview/verify_otp', auth='public', website=True, methods=['POST'], csrf=False)
    def verify_otp(self, **post):
        """Verify OTP"""
        email = post.get('email')
        otp = post.get('otp')

        if not email or not otp:
            return http.Response('{"status": "error", "message": "Email and OTP are required"}',
                                 content_type='application/json')

        otp_record = request.env['previewotp.varification'].sudo().search([('email', '=', email), ('otp', '=', otp)],
                                                                      limit=1)

        if not otp_record or otp_record.expiry_time < datetime.datetime.now():
            return http.Response('{"status": "error", "message": "Invalid or expired OTP"}',
                                 content_type='application/json')
        # Mark OTP as verified
        otp_record.sudo().write({'verified': True})
        # return request.redirect('/app/preview/create_user')
        return http.Response('{"status": "success", "message": "OTP verified successfully"}',
                             content_type='application/json')