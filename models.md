LogEntry: Содержит записи логов с полями, такими как id, content_type, user, action_flag, action_time, change_message, object_id, и object_repr.
User: Представляет пользователей системы с полями, такими как id, date_joined, email, first_name, is_active, is_staff, is_superuser, last_login, password, и username.
AbstractUser: Абстрактный класс, от которого наследуются другие классы, такие как User.
Group: Группы пользователей с полями id и name.
Permission: Разрешения с полями id, content_type, codename, и name.
ContentType: Типы контента с полями id, app_label, и model.
PermissionsMixin: Миксин для добавления функциональности разрешений.
PDFFile: Файлы PDF с полями id, teacher, uploaded_by, custom_name, file, и uploaded_at.
Teacher: Преподаватели с полями id, subject, и name.
Subject: Предметы с полями id, discipline, и name.
Discipline: Дисциплины с полем id и name.
Session: Сессии с полями session_key, expire_date, и session_data.
AbstractBaseSession: Абстрактный класс для сессий.


## Связи между таблицами

User и LogEntry: Пользователи связаны с записями логов через поле user.
User и Group: Пользователи могут принадлежать к группам.
User и Permission: Пользователи могут иметь определенные разрешения.
Group и Permission: Группы могут иметь определенные разрешения.
ContentType и Permission: Разрешения связаны с типами контента.
Teacher и Subject: Преподаватели связаны с предметами, которые они преподают.
PDFFile и User: Файлы PDF загружаются пользователями.
PDFFile и Teacher: Файлы PDF связаны с преподавателями.
Session и User: Сессии связаны с пользователями.


## Наследование

User наследуется от AbstractUser и PermissionsMixin.
AbstractBaseSession используется для создания сессий.