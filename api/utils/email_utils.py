# api/utils/email_utils.py
from django.core.mail import send_mail
from django.conf import settings

def send_password_reset_email(email, code):
    """Отправляет email с кодом сброса пароля"""
    subject = 'Восстановление пароля'
    message = f'''
    Здравствуйте!
    
    Вы запросили восстановление пароля на нашем сайте.
    
    Ваш код подтверждения: {code}
    
    Код действителен в течение 15 минут.
    
    Если вы не запрашивали восстановление пароля, просто проигнорируйте это письмо.
    
    С уважением,
    Команда сайта
    '''
    
    html_message = f'''
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #333;">Восстановление пароля</h2>
            <p>Здравствуйте!</p>
            <p>Вы запросили восстановление пароля на нашем сайте.</p>
            <div style="background-color: #f0f0f0; padding: 20px; text-align: center; margin: 20px 0;">
                <h1 style="color: #4CAF50; font-size: 36px; letter-spacing: 10px;">{code}</h1>
            </div>
            <p><strong>Код действителен в течение 15 минут.</strong></p>
            <p>Если вы не запрашивали восстановление пароля, просто проигнорируйте это письмо.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">С уважением, Команда сайта</p>
        </body>
    </html>
    '''
    
    try:
        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return True, "Email отправлен успешно"
    except Exception as e:
        return False, str(e)