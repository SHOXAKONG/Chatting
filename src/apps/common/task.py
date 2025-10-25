from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from src.apps.common.utils import code_generate
from src.apps.user.models import Code, User


@shared_task
def send_html_email_task(to, user_id):
    try:
        user = User.objects.get(id=user_id)
        code = code_generate()
        Code.objects.create(code=code, user=user)

        reset_link = f''
        subject = "Verify Your Email"
        from_email = "bekmurodovshohruh0224@gmail.com"
        recipient_list = [to]
        text_content = "Verify your email to activate your account"

        html_content = f"""
        <main>
            <h1>Hello, {user.email}!</h1>
            <h2>Your Verification Code: {code}</h2>
            <p>Click the button below to verify your email:</p>
            <a href="{reset_link}" style="display: inline-block; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px;">Verify Email</a>
            <p>If you didn't register, just ignore this email.</p>
        </main>
        """

        email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
        email.attach_alternative(html_content, "text/html")
        email.send()
        print("Verification email sent!")
    except Exception as e:
        print(f"Error sending verification email: {e}")
