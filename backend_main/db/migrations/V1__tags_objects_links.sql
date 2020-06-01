CREATE TABLE tags (
    tag_id INT PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    modified_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    tag_name VARCHAR(255) NOT NULL UNIQUE,
    tag_description TEXT
);

CREATE TABLE objects (
    object_id INT PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    modified_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    object_name VARCHAR(255) NOT NULL UNIQUE,
    object_description TEXT
);

CREATE TABLE objects_tags_link (
    tag_id INT NOT NULL REFERENCES tags(tag_id),
    object_id INT NOT NULL REFERENCES objects(object_id)
);

CREATE TABLE url_links (
    object_id INT NOT NULL REFERENCES objects(object_id),
    link TEXT NOT NULL
);

