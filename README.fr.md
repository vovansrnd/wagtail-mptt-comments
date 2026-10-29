# wagtail-mptt-comments

**Fournit des commentaires hiérarchiques sur les pages, une protection antispam pour les invités, une modération optionnelle, des notifications et des outils d’administration Wagtail. Il vise les commentaires d’articles, pas les sections de forum ni les messages privés.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## Fonctionnalités principales

- Réponses imbriquées avec django-mptt.
- Honeypot, jeton temporel et défi simple pour les envois invités.
- Modération optionnelle et notifications aux administrateurs/auteurs des réponses.
- Balises de template pour l’arbre et les derniers commentaires, filtrés par le Site courant.

## Prérequis et compatibilité

- Dépendances déclarées: `Wagtail >= 6.0; django-mptt >= 0.16.0; django-prose-editor >= 0.26; nh3 >= 0.2.14`.
- La compatibilité de Python, Django et Wagtail doit être vérifiée conjointement. La dépendance minimale du paquet ne confirme pas que toutes les versions sont prises en charge.

Les métadonnées déclarent Wagtail >= 6.0, mais une dépendance minimale ne prouve pas la compatibilité. Cette archive ne contient pas de matrice automatisée complète pour toutes les combinaisons Django/Wagtail. Avant une mise à jour en production, testez les versions exactes, la base de données, le stockage et la configuration de déploiement en préproduction.

## Installation

Installez le paquet dans le même environnement virtuel que votre projet Wagtail :

```bash
pip install wagtail-mptt-comments
```

Ajoutez les applications dans cet ordre en conservant les autres dépendances du projet :

```python
INSTALLED_APPS = [
    # Conservez également les autres dépendances Django/Wagtail déjà requises.
    "mptt",
    "django_prose_editor",
    "wagtail_mptt_comments",
]
```

```python
from django.urls import include, path
urlpatterns = [
    # ...
    path("comments/", include("wagtail_mptt_comments.urls")),
]
```

Exécutez `python manage.py migrate wagtail_mptt_comments`.


## Configuration initiale

Exemple minimal pour démarrer. Adaptez les noms de modèles, les champs API et les URL à votre configuration.

```django
{% load mptt_comment_tags %}
{% render_comments page %}
```

Les commentaires récents peuvent être affichés avec `{% get_latest_comments 5 as latest_comments %}`. Utilisez la balise dans un contexte de requête où le Wagtail Site courant est configuré.

Utilisez la balise au lieu de préparer à nouveau l’arbre, le formulaire et le compteur dans `Page.get_context()`. La table complète des paramètres, le flux de modération et les variables CSS figurent dans le README anglais.


## Paramètres et comportement importants

Le README anglais de ce répertoire est la référence canonique et contient les tableaux complets des options et les exemples détaillés. Cette traduction couvre la mise en place pratique et les avertissements de sécurité essentiels ; consultez la référence anglaise avant de modifier les options avancées.

Consultez le [README en anglais](README.md) pour la référence complète des paramètres.

### Points importants

Utilisez `{% render_comments page %}` dans le template et ne préparez pas de nouveau le formulaire/arbre dans `get_context()`. Les derniers commentaires doivent être limités au Site courant ; ne faites confiance aux en-têtes proxy qu’avec un proxy fiable configuré.

## Sécurité et exploitation

- Maintenez les dépendances à jour. Pour le HTML utilisateur, utilisez le chemin prévu de nettoyage et de rendu ; n’affichez pas les commentaires ou messages stockés avec un `|safe` inconditionnel.
- Vérifiez migrations et autorisations avec des utilisateurs normaux, restreints, modérateurs et administrateurs.
- En environnement multisite, testez chaque domaine configuré ainsi qu’un hôte inconnu. Si aucun Site n’est trouvé, une requête ne doit jamais s’élargir à tous les sites.
- Traitez les jetons API, identifiants SMTP et URL privées comme des secrets. Ne les committez pas dans Git et ne les publiez pas dans les rapports de bug.
- Sauvegardez la base de données et les fichiers médias avant les migrations, déplacements en masse, imports ou première publication en masse. Testez d’abord en préproduction.

## Combinaisons recommandées

- `wagtail-simple-forum` complète les commentaires d’articles avec des discussions thématiques et des messages privés.
- L’organisation des images et le sélecteur sont facultatifs.

## Liste de vérification

- [ ] Installez la version candidate en préproduction et notez les versions de Python, Django, Wagtail et de la base de données.
- [ ] Exécutez `python manage.py check` et les migrations du paquet.
- [ ] Testez le flux principal avec un utilisateur normal et un utilisateur restreint.
- [ ] Vérifiez journaux, accès, cache, sauvegardes et restauration.

L’archive passe les contrôles statiques de syntaxe et de packaging, mais l’intégration Django/Wagtail complète n’a pas été exécutée dans cet environnement. Considérez la liste ci-dessous comme une condition de publication, et non comme la preuve que toutes les combinaisons sont testées.

## Dépannage

Si le flux ne fonctionne pas, vérifiez la configuration de l’application, les migrations, l’ordre des URL, les autorisations et les journaux Django. Comparez la version et l’exemple avec le README anglais.

## Licence et assistance

MIT. Code source: [https://github.com/vovansrnd/wagtail-mptt-comments](https://github.com/vovansrnd/wagtail-mptt-comments).

