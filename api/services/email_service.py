"""Transactional email service using Resend with local logging fallback."""
import logging
import resend

from api.config import (
    RESEND_API_KEY,
    RESEND_FROM_EMAIL,
    FRONTEND_URL,
)

logger = logging.getLogger(__name__)

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


class EmailService:
    """Manages sending transactional emails for verification and password reset."""

    @staticmethod
    def send_verification_email(to_email: str, token: str) -> bool:
        """Sends an email-verification link to the user."""
        verify_url = f"{FRONTEND_URL}/#/verify-email?token={token}"
        subject = "Verify your BuildBuddy account"
        html_content = f"""
        <div style="font-family: sans-serif; padding: 20px; line-height: 1.6; color: #333;">
            <h2>Welcome to BuildBuddy!</h2>
            <p>Please click the button below to verify your email address:</p>
            <p style="margin: 24px 0;">
                <a href="{verify_url}" style="background: #2563eb; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Verify Email</a>
            </p>
            <p style="font-size: 13px; color: #666;">Or copy and paste this link into your browser: <br><a href="{verify_url}">{verify_url}</a></p>
        </div>
        """
        logger.info(f"[EMAIL DISPATCH] Verification link for {to_email}: {verify_url}")

        if not RESEND_API_KEY:
            logger.info("RESEND_API_KEY not configured; email link logged locally above.")
            return True

        try:
            resend.api_key = RESEND_API_KEY
            res = resend.Emails.send({
                "from": RESEND_FROM_EMAIL,
                "to": to_email,
                "subject": subject,
                "html": html_content,
            })
            logger.info(f"Resend verification email dispatched to {to_email}: {res}")
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email via Resend to {to_email}: {e}")
            return False

    @staticmethod
    def send_password_reset_email(to_email: str, token: str) -> bool:
        """Sends a password-reset link to the user."""
        reset_url = f"{FRONTEND_URL}/#/reset-password?token={token}"
        subject = "Reset your BuildBuddy password"
        html_content = f"""
        <div style="font-family: sans-serif; padding: 20px; line-height: 1.6; color: #333;">
            <h2>Reset Your Password</h2>
            <p>You recently requested to reset your password for your BuildBuddy account. Click the button below to proceed:</p>
            <p style="margin: 24px 0;">
                <a href="{reset_url}" style="background: #dc2626; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Reset Password</a>
            </p>
            <p style="font-size: 13px; color: #666;">Or copy and paste this link into your browser: <br><a href="{reset_url}">{reset_url}</a></p>
            <p style="font-size: 12px; color: #888;">If you did not request this, you can safely ignore this email.</p>
        </div>
        """
        logger.info(f"[EMAIL DISPATCH] Password reset link for {to_email}: {reset_url}")

        if not RESEND_API_KEY:
            logger.info("RESEND_API_KEY not configured; reset link logged locally above.")
            return True

        try:
            resend.api_key = RESEND_API_KEY
            res = resend.Emails.send({
                "from": RESEND_FROM_EMAIL,
                "to": to_email,
                "subject": subject,
                "html": html_content,
            })
            logger.info(f"Resend email dispatched successfully to {to_email}: {res}")
            return True
        except Exception as e:
            logger.error(f"Failed to send password reset email via Resend to {to_email}: {e}")
            return False


email_service = EmailService()
