config_schema = {
    "type": "object",
    "required": ["app", "db"],
    "properties": {
        "app": {
            "type": "object",
            "required": ["host", "port"],
            "properties":{
                "host": {
                    "type": "string",
                    "minLength": 1
                },
                "port": {
                    "type": "integer",
                    "minimum": 1025,
                    "maximum": 65535
                }
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