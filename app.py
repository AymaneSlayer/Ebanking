from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
from sqlalchemy import desc
import random

app = Flask(__name__)
app.secret_key = "supersecret"

# Connexion PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://Aymane:test1234@localhost:5432/banque_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Admin(db.Model):
    __tablename__ = 'Admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # non hashé si tu veux le laisser simple

# Modèle Client
class Client(db.Model):
    __tablename__ = 'Clients'

    id = db.Column("ID", db.String, primary_key=True)
    nom = db.Column("Nom", db.String(50), nullable=False)
    prenom = db.Column("Prenom", db.String(50), nullable=False)
    email = db.Column("Email", db.String(100), unique=True, nullable=False)

    comptes = db.relationship("Compte", backref="client", lazy=True)
    

    # ⚠️ Vérifie qu'il n'y a PAS de ligne comme :
    # etat_carte = db.Column(...) ❌


# Modèle Compte
class Operation(db.Model):
    __tablename__ = 'Operations'   

    id = db.Column(db.Integer, primary_key=True)
    compte = db.Column(db.String, nullable=False)
    montant = db.Column(db.Float, nullable=False)
    type = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, nullable=False)

class Compte(db.Model):
    __tablename__ = 'Compte'   
    client_id = db.Column("ClientID", db.String, db.ForeignKey("Clients.ID"))
    numero = db.Column("Numero", db.String(20), primary_key=True)
    solde = db.Column("Solde", db.Float, nullable=False)
    etat_carte = db.Column("etat_carte", db.String(20), nullable=False, default='actif')

@app.route('/create-admin-table')
def create_admin_table():
    try:
        db.create_all()
        return "✅ Table Admins créée avec succès !"
    except Exception as e:
        return f"❌ Erreur : {e}"
@app.route("/clients")
def liste_clients():
    if 'utilisateur' not in session:
        return redirect(url_for('login'))

    clients = Client.query.all()
    return render_template("Clients.html", clients=clients)

# ✨ Page de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        utilisateur = request.form['username']
        mot_de_passe = request.form['password']

        admin = Admin.query.filter_by(username=utilisateur, password=mot_de_passe).first()

        if admin:
            session['utilisateur'] = admin.username
            return redirect(url_for('dashboard'))
        else:
            flash('Identifiants incorrects', 'error')

    return render_template('login.html')

# ✨ Page de déconnexion
@app.route('/logout')
def logout():
    session.pop('utilisateur', None)
    return redirect(url_for('login'))
@app.route("/ajouter-compte", methods=["GET", "POST"])
def ajouter_compte():
    clients = Client.query.all()

    if request.method == "POST":
        client_id = request.form["client_id"]
        solde = float(request.form["solde"])
        numero = generate_account_number()

        nouveau_compte = Compte(client_id=client_id, numero=numero, solde=solde)
        db.session.add(nouveau_compte)
        db.session.commit()

        # Affiche la modal de succès
        return render_template("ajouter_compte.html", clients=clients, show_modal=True)

    return render_template("ajouter_compte.html", clients=clients)
@app.route("/supprimer-client", methods=["GET", "POST"])
def supprimer_client():
    if request.method == "POST":
        client_id = request.form.get("client_id")

        client = Client.query.filter_by(id=client_id).first()

        if not client:
            flash("❌ Client introuvable.", "error")
            return redirect(url_for("supprimer_client"))

        # Supprimer tous les comptes liés
        if client.comptes:
            for compte in client.comptes:
                db.session.delete(compte)

        # Supprimer le client
        db.session.delete(client)
        db.session.commit()

        flash("✅ Client et ses comptes supprimés avec succès.", "success")
        return redirect(url_for("home"))

    return render_template("supprimer_client.html")



# Générer un ID aléatoire
def generate_unique_id():
    while True:
        new_id = str(random.randint(100000, 999999))
        if not Client.query.filter_by(id=new_id).first():
            return new_id
def generate_account_number():
    return "BE" + str(random.randint(100000000000, 999999999999))  # Ex: BE123456789012


@app.route("/")
def home():
    return redirect(url_for("login"))


# Route Ajout
@app.route("/ajouter", methods=["GET", "POST"])
def ajouter_client():
    if request.method == "POST":
        nom = request.form["nom"]
        prenom = request.form["prenom"]
        email = request.form["email"]

        if Client.query.filter_by(email=email).first():
            flash("❌ Email déjà utilisé.", "error")
            return redirect(url_for("ajouter_client"))

        nouveau = Client(id=generate_unique_id(), nom=nom, prenom=prenom, email=email)
        db.session.add(nouveau)
        db.session.commit()

        # Affiche la popup
        return render_template("ajouter.html", show_modal=True)

    return render_template("ajouter.html")
from datetime import datetime
from sqlalchemy import text

@app.route("/operations", methods=["GET", "POST"])
def operations():
    comptes = Compte.query.all()
    compte_selectionne = request.args.get('compte_selectionne', default=None)

    if request.method == "POST":
        numero = request.form["numero"]
        try:
            montant = float(request.form["montant"])
        except ValueError:
            flash("Montant invalide.", "error")
            return redirect(url_for("operations", compte_selectionne=numero))

        type_op = request.form["type"]
        compte = Compte.query.filter_by(numero=numero).first()

        if not compte:
            flash("Compte introuvable.", "error")
            return redirect(url_for("operations"))

        if type_op == "Retrait":
            if compte.solde < montant:
                flash("Solde insuffisant pour le retrait.", "error")
                return redirect(url_for("operations", compte_selectionne=numero))
            compte.solde = round(compte.solde - montant, 2)
        elif type_op == "Dépôt":
            compte.solde = round(compte.solde + montant, 2)

        nouvelle_op = Operation(
            compte=numero,
            montant=montant,
            type=type_op,
            date=datetime.now()
        )

        db.session.add(nouvelle_op)
        db.session.add(compte)
        db.session.commit()

        comptes = Compte.query.all()

        return render_template("depots.html", comptes=comptes, show_modal=True, compte_selectionne=numero)

    return render_template("depots.html", comptes=comptes, compte_selectionne=compte_selectionne)



@app.route("/gerer-comptes", methods=["GET", "POST"])

def gerer_comptes():
    client = None

    if request.method == "POST":
        client_id = request.form.get("client_id")

        # Rechercher le client
        client = Client.query.filter_by(id=client_id).first()

        if client and "update" in request.form:
    # Mise à jour des données client uniquement
            client.nom = request.form["nom"]
            client.prenom = request.form["prenom"]
            client.email = request.form["email"]


        return render_template("gerer_comptes.html", client=client,was_posted=(request.method == "POST"))

    # ✅ Ce return s’exécutera pour les requêtes GET
    return render_template("gerer_comptes.html", client=None)


@app.route("/init-db")
def init_db():

    try:
        db.drop_all()
        db.create_all()
        return "✅ Base de données initialisée avec succès !"
    except Exception as e:
        return f"❌ Erreur lors de l'initialisation : {str(e)}"



# 🔧 AJOUTEZ CES ROUTES À VOTRE app.py

@app.route('/clients/<client_id>/update', methods=['PUT'])
def update_client(client_id):
    try:
        data = request.get_json()
        print(f"Données reçues pour mise à jour: {data}")  # Debug
        
        # Chercher le client par ID
        client = Client.query.filter_by(id=client_id).first()
        if not client:
            return jsonify({'success': False, 'message': 'Client non trouvé'}), 404
        
        # Validation des données
        if not data.get('nom') or not data.get('prenom') or not data.get('email'):
            return jsonify({'success': False, 'message': 'Tous les champs sont requis'}), 400
        
        # Vérifier si l'email n'est pas déjà utilisé par un autre client
        email_existe = Client.query.filter(
            Client.email == data['email'],
            Client.id != client_id
        ).first()
        
        if email_existe:
            return jsonify({'success': False, 'message': 'Cet email est déjà utilisé par un autre client'}), 400
        
        # Mettre à jour les données
        client.nom = data['nom'].strip()
        client.prenom = data['prenom'].strip()
        client.email = data['email'].strip()
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Client mis à jour avec succès',
            'client': {
                'id': client.id,
                'nom': client.nom,
                'prenom': client.prenom,
                'email': client.email
            }
        })
        
    except Exception as e:
        print(f"Erreur lors de la mise à jour: {e}")  # Debug
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur serveur: {str(e)}'}), 500

@app.route('/clients/<client_id>/delete', methods=['DELETE'])
def delete_client(client_id):
    try:
        print(f"Tentative de suppression du client: {client_id}")  # Debug
        
        # Chercher le client par ID
        client = Client.query.filter_by(id=client_id).first()
        if not client:
            return jsonify({'success': False, 'message': 'Client non trouvé'}), 404
        
        # Supprimer d'abord tous les comptes liés (pour éviter les erreurs de contrainte)
        comptes_lies = Compte.query.filter_by(client_id=client_id).all()
        for compte in comptes_lies:
            # Supprimer les opérations liées au compte
            operations_liees = Operation.query.filter_by(compte=compte.numero).all()
            for operation in operations_liees:
                db.session.delete(operation)
            
            # Supprimer le compte
            db.session.delete(compte)
        
        # Supprimer le client
        db.session.delete(client)
        db.session.commit()
        
        print(f"Client {client_id} supprimé avec succès")  # Debug
        
        return jsonify({
            'success': True, 
            'message': 'Client et ses comptes supprimés avec succès'
        })
        
    except Exception as e:
        print(f"Erreur lors de la suppression: {e}")  # Debug
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur serveur: {str(e)}'}), 500
# ➕ Nouvelle route : Dashboard
@app.route("/dashboard")
def dashboard():
    if 'utilisateur' not in session:
        return redirect(url_for('login'))

    try:
        nb_clients = Client.query.count()
        total_solde = db.session.query(db.func.sum(Compte.solde)).scalar() or 0
        nb_transactions = 1805  # ← tu peux le remplacer par Operation.query.count() si tu veux le vrai chiffre
        nb_comments = 54

        clients = Client.query.all()

        # 🔥 Récupérer les 10 dernières opérations
        recent_ops = Operation.query.order_by(desc(Operation.date)).limit(10).all()

        return render_template("index.html",
                               nb_clients=nb_clients,
                               total_solde=total_solde,
                               nb_transactions=nb_transactions,
                               nb_comments=nb_comments,
                               clients=clients,
                               recent_ops=recent_ops)
    except Exception as e:
        import traceback
        return f"<h2>Erreur Dashboard :</h2><pre>{traceback.format_exc()}</pre>"

@app.route('/details_client/<int:client_id>')
def details_client(client_id):
    # Convertir l'ID en string car la colonne Clients.ID est de type String
    client_id_str = str(client_id)

    # Récupérer le client, ou renvoyer une erreur 404 s'il n'existe pas
    client = Client.query.get_or_404(client_id_str)

    # Récupérer tous les comptes liés à ce client
    comptes = Compte.query.filter_by(client_id=client_id_str).all()

    # Récupérer toutes les opérations associées aux comptes du client
    operations = (
        db.session.query(Operation)
        .join(Compte, Operation.compte == Compte.numero)
        .filter(Compte.client_id == client_id_str)
        .order_by(Operation.date.desc())
        .all()
    )

    # Afficher la page avec toutes les infos
    return render_template(
        'details_client.html',
        client=client,
        comptes=comptes,
        operations=operations
    )


@app.route('/modifier_client/<id>', methods=['POST'])
def modifier_client(id):
    data = request.get_json()
    client = db.session.get(Client, id)

    if not client:
        return jsonify({'error': 'Client introuvable'}), 404

    client.nom = data.get('nom', client.nom)
    client.prenom = data.get('prenom', client.prenom)
    client.email = data.get('email', client.email)

    db.session.commit()
    return jsonify({'message': 'Client modifié avec succès'})
@app.route('/compte/<string:numero>')
def details_compte(numero):
    compte = Compte.query.filter_by(numero=numero).first_or_404()
    # Tu peux récupérer ici aussi les opérations liées si tu veux
    operations = Operation.query.filter_by(compte=numero).order_by(Operation.date.desc()).all()

    return render_template('details_compte.html', compte=compte, operations=operations)
@app.route("/historique")
def historique():
    operations = Operation.query.order_by(Operation.date.desc()).all()
    return render_template("historique.html", operations=operations)
@app.route("/supprimer-compte/<numero>")
def supprimer_compte(numero):
    compte = Compte.query.filter_by(numero=numero).first()
    if compte:
        db.session.delete(compte)
        db.session.commit()
        flash("Compte supprimé avec succès.", "success")
    else:
        flash("Compte introuvable.", "error")
    return redirect(request.referrer or url_for('dashboard'))

if __name__ == "__main__":
    app.run(debug=True)

