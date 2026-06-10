CREATE TABLE printers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    hourly_cost NUMERIC(10, 2) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE filament_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    temp_min INTEGER NOT NULL,
    temp_max INTEGER NOT NULL
);

CREATE TABLE spools (
    id SERIAL PRIMARY KEY,
    number INTEGER NOT NULL,
    type_id INTEGER NOT NULL REFERENCES filament_types(id),
    brand VARCHAR(100) NOT NULL,
    color VARCHAR(50) NOT NULL,
    total_weight_g NUMERIC(10, 2) NOT NULL,
    remaining_weight_g NUMERIC(10, 2) NOT NULL,
    cost_per_kg NUMERIC(10, 2) NOT NULL
);

CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL,
    cnpj VARCHAR(20) NOT NULL,
    address VARCHAR(255),
    mobile VARCHAR(20) NOT NULL,
    phone VARCHAR(20)
);

CREATE TABLE prints (
    id SERIAL PRIMARY KEY,
    part_name VARCHAR(150) NOT NULL,
    printer_id INTEGER NOT NULL REFERENCES printers(id),
    client_id INTEGER NOT NULL REFERENCES clients(id),
    weight_g NUMERIC(10, 2) NOT NULL,
    time_h NUMERIC(10, 2) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    date DATE NOT NULL,
    notes TEXT
);

CREATE TABLE print_spools (
    print_id INTEGER NOT NULL REFERENCES prints(id),
    spool_id INTEGER NOT NULL REFERENCES spools(id),
    PRIMARY KEY (print_id, spool_id)
);

CREATE TABLE quotes (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    discount NUMERIC(5, 2) NOT NULL DEFAULT 0,
    total NUMERIC(10, 2) NOT NULL,
    date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
);

CREATE TABLE quote_items (
    id SERIAL PRIMARY KEY,
    quote_id INTEGER NOT NULL REFERENCES quotes(id),
    part_name VARCHAR(150) NOT NULL,
    quantity INTEGER NOT NULL,
    weight_g NUMERIC(10, 2) NOT NULL,
    time_h NUMERIC(10, 2) NOT NULL,
    margin NUMERIC(5, 2) NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    total NUMERIC(10, 2) NOT NULL
);
