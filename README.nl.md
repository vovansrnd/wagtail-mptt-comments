# wagtail-mptt-comments

**Biedt geneste paginacommentaren, anti-spam voor gasten, optionele moderatie, meldingen en Wagtail-beheerfuncties. Bedoeld voor reacties onder artikelen/pagina’s, niet voor forumsecties of privéberichten.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## Belangrijkste functies

- Geneste antwoorden met django-mptt.
- Honeypot, tijdtoken en eenvoudige uitdaging voor gastberichten.
- Optionele moderatie en meldingen aan beheerders/auteurs van antwoorden.
- Template-tags voor commentaarboom en recente-reacties-widget, gefilterd op de huidige Site.

## Vereisten en compatibiliteit

- Gedeclareerde afhankelijkheden: `Wagtail >= 6.0; django-mptt >= 0.16.0; django-prose-editor >= 0.26; nh3 >= 0.2.14`.
- Controleer de compatibiliteit van Python, Django en Wagtail gezamenlijk. De minimale pakketafhankelijkheid bewijst niet dat alle versies worden ondersteund.

De pakketmetadata vermeldt Wagtail >= 6.0, maar een minimale afhankelijkheid bewijst geen compatibiliteit. Dit archief bevat geen volledige geautomatiseerde matrix voor alle Django/Wagtail-combinaties. Test vóór een productie-upgrade de exacte versies, database, opslagbackend en deploymentinstellingen in staging.

## Installatie

Installeer het pakket in dezelfde virtuele omgeving als je Wagtail-project:

```bash
pip install wagtail-mptt-comments
```

Voeg de apps in deze volgorde toe en behoud de overige projectafhankelijkheden:

```python
INSTALLED_APPS = [
    # Behoud ook de overige Django/Wagtail-afhankelijkheden die het project nodig heeft.
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

Voer `python manage.py migrate wagtail_mptt_comments` uit.


## Eerste configuratie

Minimaal startvoorbeeld. Pas modelnamen, API-velden en URL’s aan je configuratie aan.

```django
{% load mptt_comment_tags %}
{% render_comments page %}
```

Recente reacties kunnen worden getoond met `{% get_latest_comments 5 as latest_comments %}`. Gebruik de tag in een requestcontext met de geconfigureerde huidige Wagtail Site.

Gebruik de tag in plaats van de boom, het formulier en de telling opnieuw in `Page.get_context()` voor te bereiden. De volledige instellingentabel, moderatieflow en CSS-variabelen staan in de Engelse README.


## Belangrijke instellingen en gedrag

De Engelse README in deze map is de canonieke referentie met volledige instellingstabellen en uitgebreide voorbeelden. Deze vertaling behandelt de praktische installatie en de belangrijkste veiligheidswaarschuwingen; raadpleeg de Engelse referentie voordat je geavanceerde instellingen wijzigt.

Raadpleeg de [Engelse README](README.md) voor het volledige instellingenoverzicht.

### Belangrijke aandachtspunten

Gebruik `{% render_comments page %}` in de template en bereid formulier/boom niet opnieuw voor in `get_context()`. Recente reacties moeten tot de huidige Site beperkt blijven; vertrouw proxyheaders alleen met een correct ingestelde vertrouwde proxy.

## Beveiliging en beheer

- Houd afhankelijkheden bijgewerkt. Gebruik voor door gebruikers geschreven HTML het bedoelde opschonings- en renderpad; geef opgeslagen reacties of forumberichten niet onvoorwaardelijk weer met `|safe`.
- Controleer migraties en rechten met gewone, beperkte gebruikers, moderators en beheerders.
- Test bij meerdere sites elk ingesteld domein en een onbekende host. Als geen Site wordt gevonden, mag een query niet worden verbreed naar records van alle sites.
- Behandel API-tokens, SMTP-inloggegevens en privé-URL’s als geheimen. Commit ze niet naar Git en vermeld ze niet in openbare bugrapporten.
- Maak een back-up van database en mediabestanden vóór migraties, bulkverplaatsingen, imports of de eerste bulkpublicatie. Test zulke handelingen eerst in staging.

## Aanbevolen combinaties

- `wagtail-simple-forum` vult artikelreacties aan met discussies per onderwerp en privéberichten.
- Afbeeldingsorganisatie en -kiezer zijn optioneel.

## Controlelijst

- [ ] Installeer de kandidaat in staging en noteer de Python-, Django-, Wagtail- en databaseversies.
- [ ] Voer `python manage.py check` en de pakketmigraties uit.
- [ ] Test de hoofdworkflow met een gewone en beperkte gebruiker.
- [ ] Controleer logs, toegang, caching, back-ups en herstel.

Het archief slaagt voor statische syntax- en packagingcontroles, maar volledige Django/Wagtail-runtime-integratie is hier niet uitgevoerd. Beschouw de lijst hieronder als vrijgavevoorwaarde, niet als bewijs dat elke combinatie is getest.

## Probleemoplossing

Als de workflow niet werkt, controleer appconfiguratie, migraties, URL-volgorde, gebruikersrechten en Django-logs. Vergelijk pakketversie en voorbeeld met de Engelse README.

## Licentie en ondersteuning

MIT. Broncode: [https://github.com/vovansrnd/wagtail-mptt-comments](https://github.com/vovansrnd/wagtail-mptt-comments).

