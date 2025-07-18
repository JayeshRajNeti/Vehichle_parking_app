from flask import Flask

# importing blueprints from all controllers
from .auth_controller import auth_paths
from .user_controller import user_paths
from .admin_controller import admin_paths