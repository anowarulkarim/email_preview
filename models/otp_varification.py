from odoo import fields, models

class SubOtpVarification(models.Model):
    _name = "previewotp.varification"
    _description = "Otp for subdomain requester"

    email = fields.Char(string="Email", required=True)
    otp = fields.Char(string="OTP", required=True)
    expiry_time = fields.Datetime(string="Expiry Time", required=True)
    verified = fields.Boolean(string="Verified", default=False)