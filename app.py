from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
import random

app = Flask(__name__)
app.secret_key = "supersecret"

# Connexion PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://Aymane:test1234@localhost:5432/banque_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modèle Client
class Client(db.Model):
    __tablename__ = 'Clients'

    id = db.Column("ID", db.String, primary_key=True)
    nom = db.Column("Nom", db.String(50), nullable=False)
    prenom = db.Column("Prenom", db.String(50), nullable=False)
    email = db.Column("Email", db.String(100), unique=True, nullable=False)

    # ⚠️ Clé étrangère définie côté Compte
    comptes = db.relationship("Compte", backref="client", lazy=True)

# Modèle Compte
class Compte(db.Model):
    __tablename__ = 'Compte'   
    client_id = db.Column("ClientID", db.String, db.ForeignKey("Clients.ID"))
    numero = db.Column("Numero", db.String(20), primary_key=True)
    solde = db.Column("Solde", db.Float, nullable=False)
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

        # Vérifier si le client existe
        client = Client.query.filter_by(id=client_id).first()

        if not client:
            flash("❌ Client introuvable.", "error")
            return redirect(url_for("supprimer_client"))

        # Supprimer le compte d'abord (si existe)
        if client.compte:
            db.session.delete(client.compte)

        # Supprimer le client ensuite
        db.session.delete(client)
        db.session.commit()

        flash("✅ Client et compte supprimés avec succès.", "success")
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


# Route Accueil
@app.route("/")
def home():
    try:
        clients = Client.query.all()
        return render_template("index.html", clients=clients)
    except Exception as e:
        import traceback
        return f"<h2>Erreur :</h2><pre>{traceback.format_exc()}</pre>"

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


@app.route("/client/<int:id>")
def client_details(id):
    client = Client.query.get_or_404(str(id))
    return render_template("client_details.html", client=client)
@app.route("/gerer-comptes", methods=["GET", "POST"])

def gerer_comptes():
    client = None

    if request.method == "POST":
        client_id = request.form.get("client_id")

        # Rechercher le client
        client = Client.query.filter_by(id=client_id).first()

        if client and "update" in request.form:
            # Mise à jour des données client
            client.nom = request.form["nom"]
            client.prenom = request.form["prenom"]
            client.email = request.form["email"]

            if client.comptes:
                try:
                    nouveau_solde = float(request.form["solde"])
                    client.comptes[0].solde = round(nouveau_solde, 2)
                except (ValueError, KeyError):
                    flash("❌ Solde invalide ou manquant.", "error")
                    return redirect(url_for("gerer_comptes"))

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




# ➕ Nouvelle route : Dashboard
@app.route("/dashboard")
def dashboard():
    try:
        nb_clients = Client.query.count()
        # Simule des données fictives pour stats (si tu veux aller plus loin, tu peux les calculer en base)
        total_solde = db.session.query(db.func.sum(Compte.solde)).scalar() or 0
        nb_transactions = 1805  # valeur fictive pour le visuel
        nb_comments = 54        # idem

        return render_template("dashboard.html",
                               nb_clients=nb_clients,
                               total_solde=total_solde,
                               nb_transactions=nb_transactions,
                               nb_comments=nb_comments)
    except Exception as e:
        import traceback
        return f"<h2>Erreur Dashboard :</h2><pre>{traceback.format_exc()}</pre>"
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



if __name__ == "__main__":
    app.run(debug=True)