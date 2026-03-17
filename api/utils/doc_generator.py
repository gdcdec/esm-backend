from django.utils import timezone


def build_universal_letter(user, post) -> str:
    """
    Строит универсальный текст обращения на основе данных пользователя и поста.
    Текст можно скопировать и вставить в форму ведомства / письмо.
    """
    # ФИО
    fio_parts = [user.last_name or "", user.first_name or "", getattr(user, "patronymic", "") or ""]
    fio = " ".join(p.strip() for p in fio_parts if p).strip() or user.username

    # Адрес проживания пользователя
    user_address_parts = [
        getattr(user, "city", "") or "",
        getattr(user, "street", "") or "",
        getattr(user, "house", "") or "",
        getattr(user, "apartment", "") or "",
    ]
    user_address = ", ".join(p for p in user_address_parts if p) or "(адрес проживания не указан)"

    # Контакты
    phone = getattr(user, "phone_number", "") or "-"
    email = user.email or "-"

    # Рубрика как тип нарушения
    rubric_name = getattr(post.rubric, "name", None) if hasattr(post, "rubric") else None
    violation_scope = rubric_name or "указанной проблемы"

    # Адрес события
    event_address = post.address or "(адрес события не указан)"

    # Дата/время события — берём created_at, если есть
    created_at = getattr(post, "created_at", None)
    if created_at:
        created_at = timezone.localtime(created_at)
        created_str = created_at.strftime("%d.%m.%Y %H:%M")
    else:
        created_str = "(дата и время не указаны)"

    # Описание
    description = post.description or "(описание проблемы не указано)"

    # Фото
    photos_count = getattr(post, "photo_count", None)
    if photos_count is None and hasattr(post, "photos"):
        photos_count = post.photos.count()
    photos_count = photos_count or 0

    lines = []
    lines.append(f'Кому: В компетентный орган, осуществляющий контроль в сфере "{violation_scope}"')
    lines.append("")
    lines.append(f"От: {fio}")
    lines.append(f"Адрес проживания: {user_address}")
    lines.append(f"Контакты: телефон {phone}, email {email}")
    lines.append("")
    lines.append("Заявление о нарушении")
    lines.append("")
    lines.append("Я сообщаю о следующем инциденте:")
    lines.append(f"Адрес события: {event_address}")
    lines.append(f"Дата и время: {created_str}")
    lines.append("")
    lines.append("Описание проблемы:")
    lines.append(description)
    lines.append("")
    lines.append(
        "Прошу рассмотреть настоящее обращение, принять меры в рамках вашей компетенции "
        "и уведомить меня о результатах по указанным контактам."
    )
    lines.append("")
    lines.append(f"Приложения: фотофиксация ({photos_count} шт.)")

    return "\n".join(lines)

