from .tokens import EmailVerificationTokenGenerator

SUPPORT_TEXT = "If you didn't request this, please ignore this email."
ACTIVATION_EMAIL_TEMPLATE = 'email/activation.html'
EMAIL_VERIFICATION_TOKEN = EmailVerificationTokenGenerator()

class CompanyType:
    STARTUP = "startup"
    INVESTOR = "investor"