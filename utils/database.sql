CREATE TABLE protocol (
  protocol_id SERIAL PRIMARY KEY,
  protocol VARCHAR (6) UNIQUE NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

INSERT INTO protocol (protocol)
VALUES ('http'), ('https');

CREATE TABLE links (
    id SERIAL PRIMARY KEY,
    link VARCHAR (32) UNIQUE NOT NULL,
    destination_proto INTEGER NOT NULL,
    destination_addr VARCHAR(50) NOT NULL,
    redirect char,
    creator_ip INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_dest_proto FOREIGN KEY (destination_proto) REFERENCES protocol(protocol_id)
);

CREATE FUNCTION insert_link(redir_link varchar, destination_proto varchar, destination_addr varchar, redirect int, creator_ip integer) RETURNS varchar AS
    $$
    DECLARE
        ret VARCHAR := null;
    BEGIN
    INSERT INTO links(link, destination_proto, redirect, destination_addr, creator_ip) VALUES
        (redir_link, (SELECT protocol.protocol_id FROM protocol where protocol.protocol = destination_proto), (redirect - 300), destination_addr, creator_ip)
        ON CONFLICT (link) DO NOTHING RETURNING links.link INTO ret;
    return ret;
    END;
    $$
    LANGUAGE 'plpgsql';

CREATE VIEW addresses AS
    SELECT CONCAT(protocol.protocol, '://', links.destination_addr) as url, (CAST(links.redirect AS INTEGER) + 300) as redirect, links.link as link FROM links INNER JOIN protocol ON protocol.protocol_id = links.destination_proto;

CREATE FUNCTION get_address(req_link varchar) RETURNS TABLE (url text, redirect integer) AS
    $$
    BEGIN
        RETURN QUERY
            SELECT addresses.url, addresses.redirect FROM addresses where addresses.link = req_link;
        END;
    $$
    LANGUAGE 'plpgsql';