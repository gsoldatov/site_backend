config_schema = {
    "type": "object",
    "required": ["app", "cors_urls", "db"],
    "properties": {
        "app": {
            "type": "object",
            "required": ["host", "port", "default_user", "token_lifetime"],
            "properties":{
                "host": {
                    "type": "string",
                    "minLength": 1
                },

                "port": {
                    "type": "integer",
                    "minimum": 1025,
                    "maximum": 65535
                },

                "default_user": {
                    "type": "object",
                    "required": ["login", "password", "username"],
                    "properties": {
                        "login": {
                            "type": "string",
                            "minLength": 1
                        },
                        "password": {
                            "type": "string",
                            "minLength": 8,
                            "maxLength": 72     # Postgres password hashing algorithm limitation
                        },
                        "username": {
                            "type": "string",
                            "minLength": 1
                        }
                    }
                },

                "token_lifetime": {
                    "type": "integer",
                    "minimum": 1 * 1 * 1 * 60,      # 1 min
                    "maximum": 90 * 24 * 60 * 60    # 90 days
                }
            }
        },

        "cors_urls": {
            "type": "array",
            "minItems": 1,
            "items" : {
                "type": "string"
            }
        },

        "db": {
            "type": "object",
            "required": [
                "db_host", 
                "db_port", 
                "db_init_database", 
                "db_init_username", 
                "db_init_password", 
                "db_database", 
                "db_schema"
            ],
            "dependencies": {
                "db_username": ["db_password"]
            },
            "properties": {
                "db_host": {
                    "type": "string",
                    "minLength": 1
                },
                "db_port": {
                    "type": "integer",
                    "minimum": 1025,
                    "maximum": 65535
                },
                "db_init_database": {
                    "type": "string",
                    "minLength": 1
                },
                "db_init_username": {
                    "type": "string",
                    "minLength": 1
                },
                "db_init_password": {
                    "type": "string",
                    "minLength": 1
                },
                "db_database": {
                    "type": "string",
                    "minLength": 1
                },
                "db_schema": {
                    "type": "string",
                    "minLength": 1
                },
                "db_username": {
                    "type": "string",
                    "minLength": 1
                },
                "db_password": {
                    "type": "string",
                    "minLength": 1
                }
            }
        }
    }
}