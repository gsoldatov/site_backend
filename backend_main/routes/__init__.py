from backend_main.routes.tags import get_subapp as get_tags_subapp
from backend_main.routes.objects import get_subapp as get_objects_subapp


def setup_routes(app):
    for module_name in ("tags", "objects"):
        factory = globals()[f"get_{module_name}_subapp"]
        module = factory()
        app.add_subapp(f"/{module_name}/", module)
        module["engine"] = app["engine"]
        module["tables"] = app["tables"]
    
    return app
