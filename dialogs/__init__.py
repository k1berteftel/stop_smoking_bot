from dialogs.user_dialog.dialog import user_dialog
from dialogs.admin_dialog.dialog import admin_dialog
from dialogs.language_dialog.dialog import language_dialog


def get_dialogs():
    return [user_dialog, admin_dialog, language_dialog]