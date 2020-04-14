from .tags import get_subapp as get_tags_subapp


def setup_routes(app):
    for module_name in ("tags", ):
        factory = globals()[f"get_{module_name}_subapp"]
        module = factory()
        app.add_subapp(f"/{module_name}/", module)
        module["engine"] = app["engine"]
        module["tables"] = app["tables"]
    
    return app
