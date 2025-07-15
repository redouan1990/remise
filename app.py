from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'
CORS(app)  # Enable CORS for all routes
DB_PATH = 'remise.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('index.html')

@app.route('/add', methods=['POST'])
def add_remise():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    data = request.form
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO remises (ref, prenom, nom, telephone, fonction, direction, affectation, type, etat, nom_materiel, numero_serie, categorie, date_remise, accessoires, projet, responsable_dsi) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (data['ref'], data['prenom'], data['nom'], data['telephone'], data['fonction'], data['direction'], data['affectation'], data['type'], data['etat'], data['nom_materiel'], data['numero_serie'], data['categorie'], data['date_remise'], data['accessoires'], data['projet'], data['responsable_dsi']))
        conn.commit()
        flash('Remise ajoutée avec succès!')
    except sqlite3.IntegrityError as e:
        flash('Erreur: doublon ou donnée invalide. {}'.format(str(e)), 'danger')
    finally:
        conn.close()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Déconnexion réussie.')
    return redirect(url_for('index'))

# API Endpoints for frontend integration
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role']
            }
        })
    else:
        return jsonify({'success': False, 'message': 'Nom d\'utilisateur ou mot de passe invalide.'}), 401

@app.route('/api/remises', methods=['GET'])
def api_get_remises():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 401
    
    conn = get_db_connection()
    remises = conn.execute('SELECT * FROM remises ORDER BY date_created DESC').fetchall()
    conn.close()
    
    remises_list = []
    for remise in remises:
        remises_list.append({
            'id': remise['id'],
            'ref': remise['ref'],
            'prenom': remise['prenom'],
            'nom': remise['nom'],
            'telephone': remise['telephone'],
            'fonction': remise['fonction'],
            'direction': remise['direction'],
            'affectation': remise['affectation'],
            'type': remise['type'],
            'etat': remise['etat'],
            'nom_materiel': remise['nom_materiel'],
            'numero_serie': remise['numero_serie'],
            'categorie': remise['categorie'],
            'date_remise': remise['date_remise'],
            'accessoires': remise['accessoires'],
            'projet': remise['projet'],
            'responsable_dsi': remise['responsable_dsi'],
            'date_created': remise['date_created']
        })
    
    return jsonify({'success': True, 'remises': remises_list})

@app.route('/api/remises', methods=['POST'])
def api_add_remise():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 401
    
    data = request.get_json()
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO remises (ref, prenom, nom, telephone, fonction, direction, affectation, type, etat, nom_materiel, numero_serie, categorie, date_remise, accessoires, projet, responsable_dsi) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (data['ref'], data['prenom'], data['nom'], data['telephone'], data['fonction'], data['direction'], data['affectation'], data['type'], data['etat'], data['nom_materiel'], data['numero_serie'], data['categorie'], data['date_remise'], data['accessoires'], data['projet'], data['responsable_dsi']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Remise ajoutée avec succès!'})
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Erreur: doublon ou donnée invalide. {str(e)}'}), 400

@app.route('/api/next-remise-number', methods=['GET'])
def api_get_next_remise_number():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 401
    
    try:
        conn = get_db_connection()
        current_year = datetime.now().year
        
        # Get the highest number for the current year
        result = conn.execute(
            'SELECT ref FROM remises WHERE ref LIKE ? ORDER BY ref DESC LIMIT 1',
            (f'REM-{current_year}-%',)
        ).fetchone()
        
        if result:
            # Extract the number from the reference (e.g., "REM-2024-00005" -> 5)
            ref_parts = result['ref'].split('-')
            if len(ref_parts) == 3:
                last_number = int(ref_parts[2])
                next_number = last_number + 1
            else:
                next_number = 1
        else:
            next_number = 1
        
        # Format the new reference number
        new_ref = f'REM-{current_year}-{next_number:05d}'
        
        conn.close()
        return jsonify({'success': True, 'ref': new_ref})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur lors de la génération du numéro: {str(e)}'}), 500

@app.route('/api/remises/<int:remise_id>', methods=['DELETE'])
def api_delete_remise(remise_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 401
    
    # Check if user is admin
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès refusé. Seuls les administrateurs peuvent supprimer des remises.'}), 403
    
    try:
        conn = get_db_connection()
        cursor = conn.execute('DELETE FROM remises WHERE id = ?', (remise_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            conn.close()
            return jsonify({'success': True, 'message': 'Remise supprimée avec succès!'})
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Remise non trouvée'}), 404
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Erreur lors de la suppression: {str(e)}'}), 500

@app.route('/api/users', methods=['GET'])
def api_get_users():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès refusé'}), 403
    
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, role FROM users').fetchall()
    conn.close()
    
    users_list = []
    for user in users:
        users_list.append({
            'id': user['id'],
            'username': user['username'],
            'role': user['role']
        })
    
    return jsonify({'success': True, 'users': users_list})

@app.route('/api/users', methods=['POST'])
def api_add_user():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès refusé'}), 403
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    
    if not username or not password or not role:
        return jsonify({'success': False, 'message': 'Tous les champs sont requis'}), 400
    
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                     (username, password, role))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Utilisateur ajouté avec succès!'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Ce nom d\'utilisateur existe déjà'}), 400

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def api_update_user(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès refusé'}), 403
    
    data = request.get_json()
    password = data.get('password')
    
    if not password:
        return jsonify({'success': False, 'message': 'Mot de passe requis'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.execute('UPDATE users SET password = ? WHERE id = ?', (password, user_id))
        conn.commit()
        
        if cursor.rowcount > 0:
            conn.close()
            return jsonify({'success': True, 'message': 'Mot de passe modifié avec succès!'})
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Utilisateur non trouvé'}), 404
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Erreur lors de la modification: {str(e)}'}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def api_delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès refusé'}), 403
    
    try:
        conn = get_db_connection()
        cursor = conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            conn.close()
            return jsonify({'success': True, 'message': 'Utilisateur supprimé avec succès!'})
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Utilisateur non trouvé'}), 404
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Erreur lors de la suppression: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Déconnexion réussie'})

@app.route('/api/session', methods=['GET'])
def api_get_session():
    if 'user_id' in session:
        return jsonify({
            'success': True,
            'user': {
                'id': session['user_id'],
                'username': session['username'],
                'role': session['role']
            }
        })
    else:
        return jsonify({'success': False, 'message': 'Non connecté'}), 401

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        conn.close()
    app.run(debug=True, host='0.0.0.0', port=5000)

