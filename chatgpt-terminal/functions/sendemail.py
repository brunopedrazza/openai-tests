from functions.functioncallingbase import FunctionCallingBase
from services.email_service import EmailService
import re

class SendEmail(FunctionCallingBase):
    def __init__(self):
        super().__init__()
        self.email_service = EmailService()

    def _get_function_definition(self):
        return {
            "name": "send_email",
            "description": "Send an email to a specified recipient",
            "operation_type": "write",  # This is a write operation as it modifies state (sends an email)
            "parameters": {
                "type": "object",
                "properties": {
                    "to_email": {
                        "type": "string",
                        "description": "The recipient's email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "The subject line of the email"
                    },
                    "body": {
                        "type": "string",
                        "description": "The content of the email. Can include HTML formatting if is_html is true."
                    },
                    "is_html": {
                        "type": "boolean",
                        "description": "Whether the body contains HTML formatting",
                        "default": False
                    }
                },
                "required": ["to_email", "subject", "body"],
                "additionalProperties": False
            }
        }

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def execute(self, **kwargs):
        to_email = kwargs.get("to_email")
        subject = kwargs.get("subject")
        body = kwargs.get("body")
        is_html = kwargs.get("is_html", False)

        # Validate email format
        if not self._validate_email(to_email):
            return {
                "success": False,
                "error": "Invalid email address format"
            }

        # Send the email
        success, error = self.email_service.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            is_html=is_html
        )

        if not success:
            return {
                "success": False,
                "error": error
            }

        return {
            "success": True,
            "message": f"Email sent successfully to {to_email}",
            "details": {
                "to": to_email,
                "subject": subject,
                "is_html": is_html
            }
        } 