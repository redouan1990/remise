
-- Table for users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
);

-- Insert default admin user
INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin');

-- Table for remises (handovers)
CREATE TABLE IF NOT EXISTS remises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ref TEXT UNIQUE NOT NULL,
    prenom TEXT,
    nom TEXT,
    telephone TEXT,
    fonction TEXT,
    direction TEXT,
    affectation TEXT,
    type TEXT,
    etat TEXT,
    nom_materiel TEXT,
    numero_serie TEXT,
    categorie TEXT,
    date_remise TEXT,
    accessoires TEXT,
    projet TEXT,
    responsable_dsi TEXT,
    date_created TEXT DEFAULT CURRENT_TIMESTAMP
);
