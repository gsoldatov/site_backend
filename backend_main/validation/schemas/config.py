_logging_mode_enum = ["file", "stdout", "off"]

config_schema = {
    "type": "object",
    "additionalProperties": False,
    "required": ["app", "cors_urls", "db", "auxillary", "logging"],
    "properties": {
        "app": {
            "type": "object",
            "additionalProperties": False,
            "required": ["host", "port", "use_forwarded", "debug", "default_user", "token_lifetime", "composite_hierarchy_max_depth"],
            "properties": {
                "host": {
                    "type": "string",
                    "minLength": 1
                },

                "port": {
                    "type": "integer",
                    "minimum": 1025,
                    "maximum": 65535
                },

                "use_forwarded": { "type": "boolean" },
                
                "debug": { "type": "boolean" },

                "default_user": {
                    "type": "object",
                    "additionalProperties": False,
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
                },

                "composite_hierarchy_max_depth": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10
                }
            }
        },

        "cors_urls": {
            "type": "array",
            "minItems": 1,
            "items" : {
                "type": "string",
                "minLength": 1
            }
        },

        "db": {
            "type": "object",
            "additionalProperties": False,
            "required": ["db_host", "db_port", 
                "db_init_database", "db_init_username",  "db_init_password", 
                "db_database", "db_password", "db_username"
            ],
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
                "db_username": {
                    "type": "string",
                    "minLength": 1
                },
                "db_password": {
                    "type": "string",
                    "minLength": 1
                }
            }
        },

        "auxillary": {
            "type": "object",
            "additionalProperties": False,
            "required": ["enable_searchables_updates"],
            "properties": {
                "enable_searchables_updates": {
                    "type": "boolean"
                }
            }
        },

        "logging": {
            "type": "object",
            "additionalProperties": False,
            "required": ["folder", "file_separator", "file_separator_replacement",
                "app_event_log_mode", "app_event_log_file_mode_interval", 
                "app_access_log_mode", "app_access_log_file_mode_interval", 
                "db_mode", 
                "scheduled_mode"],
            "properties": {
                "folder": { "type": "string" },

                "file_separator": { "type": "string" },
                
                "file_separator_replacement": { "type": "string" },

                "app_event_log_mode": {
                    "type": "string",
                    "enum": _logging_mode_enum
                },

                "app_event_log_file_mode_interval": {
                    "type": "integer",
                    "minimum": 1
                },

                "app_access_log_mode": {
                    "type": "string",
                    "enum": _logging_mode_enum
                },

                "app_access_log_file_mode_interval": {
                    "type": "integer",
                    "minimum": 1
                },

                "db_mode": {
                    "type": "string",
                    "enum": _logging_mode_enum
                },

                "scheduled_mode": {
                    "type": "string",
                    "enum": _logging_mode_enum
                }
            }
        }
    }
}
