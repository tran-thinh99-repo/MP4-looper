# Make auth module functions easily importable
from .email_auth import authenticate_user, is_authenticated, logout, handle_authentication
from .auth_ui import show_auth_dialog

__all__ = ['authenticate_user', 'is_authenticated', 'logout', 'handle_authentication', 'show_auth_dialog']