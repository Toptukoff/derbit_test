CREATE TABLE deribit (
    Id SERIAL PRIMARY KEY,
    ticker VARCHAR(10),
    index_price NUMERIC (10,2),
    timestamp BIGINT NOT NULL
)