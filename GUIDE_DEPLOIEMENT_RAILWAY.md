# Guide de déploiement ADAS sur Railway.app
## Rendre l'application accessible à tous sur Internet

---

## Résumé
Railway.app est une plateforme gratuite qui héberge ton application Flask sur Internet.
Une fois déployée, n'importe qui dans le monde pourra accéder à ADAS via une URL du type :
**https://adas-division.up.railway.app**

---

## ÉTAPE 1 — Créer un compte GitHub (si pas encore fait)

1. Va sur **https://github.com**
2. Clique sur **Sign up**
3. Crée ton compte gratuitement
4. Vérifie ton email

---

## ÉTAPE 2 — Mettre le projet sur GitHub

### 2a. Installe Git sur ton ordinateur
- Va sur **https://git-scm.com/download/win**
- Télécharge et installe Git
- Redémarre ton terminal (cmd)

### 2b. Initialise Git dans ton projet
Dans ton terminal (dans le dossier statdiv) :

```
git init
git add .
git commit -m "Premier déploiement ADAS"
```

### 2c. Crée un dépôt GitHub
1. Va sur **https://github.com/new**
2. Nom du dépôt : **adas-division**
3. Laisse tout le reste par défaut
4. Clique **Create repository**

### 2d. Connecte et envoie ton code
Copie les commandes affichées par GitHub, elles ressemblent à :

```
git remote add origin https://github.com/TONNOM/adas-division.git
git branch -M main
git push -u origin main
```

---

## ÉTAPE 3 — Créer un compte Railway

1. Va sur **https://railway.app**
2. Clique **Start a New Project**
3. Connecte-toi avec ton compte **GitHub**
4. Autorise Railway à accéder à tes dépôts

---

## ÉTAPE 4 — Déployer sur Railway

1. Une fois connecté sur Railway, clique **New Project**
2. Choisis **Deploy from GitHub repo**
3. Sélectionne ton dépôt **adas-division**
4. Railway détecte automatiquement que c'est Python

---

## ÉTAPE 5 — Configurer les variables d'environnement

Dans Railway, va dans ton projet > **Variables** et ajoute :

| Variable | Valeur |
|---|---|
| SECRET_KEY | une-longue-phrase-secrete-ici-2024 |
| FLASK_ENV | production |

Pour générer une clé secrète solide, tape ceci dans ton terminal :
```
python -c "import secrets; print(secrets.token_hex(32))"
```
Copie le résultat et mets-le comme valeur de SECRET_KEY.

---

## ÉTAPE 6 — Obtenir ton URL public

1. Dans Railway, clique sur ton projet
2. Clique sur **Settings** > **Networking**
3. Clique **Generate Domain**
4. Tu obtiens une URL comme : **https://adas-division.up.railway.app**

**C'est cette URL que tu partageras avec tous les étudiants !**

---

## ÉTAPE 7 — Mettre à jour l'application après modifications

Chaque fois que tu modifies des fichiers, dans ton terminal :

```
git add .
git commit -m "Description de la modification"
git push
```

Railway redéploie automatiquement en quelques minutes.

---

## ÉTAPE 8 — Ajouter le logo ENSEA

1. Place ton fichier logo (PNG ou JPG) dans le dossier :
   **statdiv/static/images/**
2. Renomme-le exactement : **logo_ensea.png**
3. Fais `git add . && git commit -m "Ajout logo" && git push`

Le logo apparaîtra automatiquement dans l'en-tête du site.

---

## Informations importantes

### Plan gratuit Railway
- 500 heures/mois d'utilisation (largement suffisant)
- 1 GB de mémoire
- Base de données SQLite incluse
- HTTPS automatique (site sécurisé)

### Limite du plan gratuit
Les fichiers uploadés (photos, documents) sont **temporaires** sur Railway.
Pour les conserver définitivement, il faudra plus tard configurer un stockage externe (comme Cloudinary pour les images).
Pour l'instant, les données de la base restent bien sauvegardées.

### Si tu veux un vrai nom de domaine
Tu peux acheter un domaine comme **adas-ensea.com** (~10€/an) et le connecter à Railway dans Settings > Networking > Custom Domain.

---

## En cas de problème

- Les logs d'erreur sont visibles dans Railway > ton projet > **Deployments** > clic sur le déploiement > **View Logs**
- L'erreur la plus fréquente : une bibliothèque manquante dans requirements.txt

---

*Guide préparé pour ADAS — Division des Analystes Statisticiens, ENSEA Abidjan*
