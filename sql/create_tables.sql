-- Código para rodar apenas em PostgreSQL

----------
-- user --
----------

-- Criação da tabela users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criação de índices adicionais
CREATE INDEX idx_users_nome ON users(nome);
CREATE INDEX idx_users_email ON users(email);

-- Exemplo de inserção de dados (com senhas hasheadas)
-- Senha 'senha123' hasheada com bcrypt
INSERT INTO users (nome, email, hashed_password, role) VALUES 
    ('João Silva', 'joao@email.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBcPkKyJTzLlP6', 'user'),
    ('Maria Santos', 'maria@email.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBcPkKyJTzLlP6', 'admin'),
    ('Pedro Oliveira', 'pedro@email.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBcPkKyJTzLlP6', 'user');
