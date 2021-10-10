from backend_main.routes.auth import get_subapp as get_auth_subapp
from backend_main.routes.settings import get_subapp as get_settings_subapp
from backend_main.routes.users import get_subapp as get_users_subapp
from backend_main.routes.tags import get_subapp as get_tags_subapp
from backend_main.routes.objects import get_subapp as get_objects_subapp


from backend_main.util.constants import AUTH_SUBAPP_PREFIX


def setup_routes(app):
    for module_name in ("tags", "objects", AUTH_SUBAPP_PREFIX, "users", "settings"):
        factory = globals()[f"get_{module_name}_subapp"]
        module = factory()
        app.add_subapp(f"/{module_name}/", module)
    
    return app
