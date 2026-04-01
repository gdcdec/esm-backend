from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from api.models import Notification, CustomUser, Post


def send_admin_notification(user, subject, message, notification_type='info', 
                            link=None, admin_user=None, action_type=None, 
                            object_repr=None):
    """
    Отправка уведомления пользователю о действиях администрации
    
    Args:
        user: пользователь, которому отправляется уведомление
        subject: тема уведомления
        message: сообщение
        notification_type: тип уведомления (info, success, warning, error)
        link: ссылка для перехода
        admin_user: администратор, совершивший действие
        action_type: тип действия (создание, изменение, удаление)
        object_repr: строковое представление объекта
    """
    if not user or not user.pk:
        return None
    
    # Добавляем информацию об администраторе в метаданные
    metadata = {
        'admin_username': admin_user.username if admin_user else 'System',
        'admin_id': admin_user.pk if admin_user else None,
        'action_type': action_type,
        'object_repr': object_repr,
        'timestamp': timezone.now().isoformat()
    }
    
    return Notification.create_notification(
        user=user,
        subject=subject,
        message=message,
        notification_type=notification_type,
        link=link,
        **metadata
    )


def notify_user_about_post_status_change(post, old_status, new_status, admin_user):
    """
    Уведомление пользователя об изменении статуса поста
    """
    status_names = {
        'draft': 'черновик',
        'check': 'на проверку',
        'published': 'опубликован',
        'archived': 'архивирован',
        'deleted': 'удален'
    }
    
    old_name = status_names.get(old_status, old_status)
    new_name = status_names.get(new_status, new_status)
    
    subject = f"Статус вашего поста \"{post.title}\" изменен"
    message = (
        f"Администратор {admin_user.get_full_name() or admin_user.username} "
        f"изменил статус вашего поста \"{post.title}\" "
        f"с \"{old_name}\" на \"{new_name}\"."
    )
    
    return send_admin_notification(
        user=post.author,
        subject=subject,
        message=message,
        notification_type='info' if new_status == 'published' else 'warning',
        link=f'/posts/{post.id}/',
        admin_user=admin_user,
        action_type='status_change',
        object_repr=post.title
    )


def notify_user_about_post_edit(post, admin_user, changed_fields):
    """
    Уведомление пользователя об изменении поста
    """
    fields_names = {
        'title': 'заголовок',
        'description': 'описание',
        'address': 'адрес',
        'rubric': 'рубрику',
        'latitude': 'широту',
        'longitude': 'долготу'
    }
    
    changed_fields_str = ', '.join(
        fields_names.get(field, field) for field in changed_fields
    )
    
    subject = f"Ваш пост \"{post.title}\" был изменен администрацией"
    message = (
        f"Администратор {admin_user.get_full_name() or admin_user.username} "
        f"внес изменения в ваш пост \"{post.title}\". "
        f"Были изменены: {changed_fields_str}."
    )
    
    return send_admin_notification(
        user=post.author,
        subject=subject,
        message=message,
        notification_type='info',
        link=f'/posts/{post.id}/',
        admin_user=admin_user,
        action_type='edit',
        object_repr=post.title
    )


def notify_user_about_post_deletion(post, admin_user):
    """
    Уведомление пользователя об удалении поста
    """
    subject = f"Ваш пост \"{post.title}\" был удален"
    message = (
        f"Администратор {admin_user.get_full_name() or admin_user.username} "
        f"удалил ваш пост \"{post.title}\"."
    )
    
    return send_admin_notification(
        user=post.author,
        subject=subject,
        message=message,
        notification_type='error',
        admin_user=admin_user,
        action_type='deletion',
        object_repr=post.title
    )


def notify_user_about_user_data_change(user, admin_user, changed_fields):
    """
    Уведомление пользователя об изменении его данных
    """
    fields_names = {
        'first_name': 'имя',
        'last_name': 'фамилию',
        'patronymic': 'отчество',
        'email': 'email',
        'phone_number': 'номер телефона',
        'city': 'город',
        'street': 'улицу',
        'house': 'дом',
        'apartment': 'квартиру'
    }
    
    changed_fields_str = ', '.join(
        fields_names.get(field, field) for field in changed_fields
    )
    
    subject = "Ваши персональные данные были изменены"
    message = (
        f"Администратор {admin_user.get_full_name() or admin_user.username} "
        f"изменил ваши персональные данные. "
        f"Были изменены: {changed_fields_str}.\n"
        f"Если вы не запрашивали эти изменения, пожалуйста, свяжитесь с администрацией."
    )
    
    return send_admin_notification(
        user=user,
        subject=subject,
        message=message,
        notification_type='warning',
        admin_user=admin_user,
        action_type='user_data_change',
        object_repr=user.get_full_name() or user.username
    )