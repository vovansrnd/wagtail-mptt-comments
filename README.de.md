# wagtail-mptt-comments

**Bietet verschachtelte Seitenkommentare, Anti-Spam-Schutz für Gäste, optionale Moderation, Benachrichtigungen und Wagtail-Admin-Werkzeuge. Gedacht für Kommentare unter Artikeln/Seiten, nicht für Forenbereiche oder private Nachrichten.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## Wichtigste Funktionen

- Verschachtelte Antworten mit django-mptt.
- Honeypot, Zeit-Token und einfache Prüfung für Gastbeiträge.
- Optionale Moderation sowie Benachrichtigungen an Admins und Antwortautoren.
- Template-Tags für Kommentarbaum und Neueste-Kommentare-Widget mit Filterung auf die aktuelle Site.

## Voraussetzungen und Kompatibilität

- Deklarierte Abhängigkeiten: `Wagtail >= 6.0; django-mptt >= 0.16.0; django-prose-editor >= 0.26; nh3 >= 0.2.14`.
- Die Kompatibilität von Python, Django und Wagtail muss gemeinsam geprüft werden. Die minimale Paketabhängigkeit bestätigt keine Unterstützung jeder Version.

Die Paketmetadaten deklarieren Wagtail >= 6.0. Eine minimale Abhängigkeit ist jedoch kein Kompatibilitätstest. Dieses Quellarchiv enthält keine vollständige automatisierte Matrix für alle Django-/Wagtail-Kombinationen. Prüfen Sie vor einem Produktionsupgrade die konkreten Versionen, Datenbank, Speicher-Backend und Deployment-Einstellungen in einer Staging-Umgebung.

## Installation

Installieren Sie das Paket in derselben virtuellen Umgebung wie Ihr Wagtail-Projekt:

```bash
pip install wagtail-mptt-comments
```

Fügen Sie die Apps in der angegebenen Reihenfolge hinzu und behalten Sie die übrigen Projektabhängigkeiten bei:

```python
INSTALLED_APPS = [
    # Behalten Sie auch andere bereits benötigte Django-/Wagtail-Abhängigkeiten bei.
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

Führen Sie `python manage.py migrate wagtail_mptt_comments` aus.


## Erste Konfiguration

Minimales Einstiegsbeispiel. Passen Sie Modellnamen, API-Felder und URLs an Ihre Konfiguration an.

```django
{% load mptt_comment_tags %}
{% render_comments page %}
```

Neueste Kommentare lassen sich mit `{% get_latest_comments 5 as latest_comments %}` anzeigen. Verwenden Sie den Tag in einem Request-Kontext mit konfigurierter aktueller Wagtail Site.

Verwenden Sie den Tag statt Kommentarbaum, Formular und Anzahl erneut in `Page.get_context()` vorzubereiten. Die vollständige Einstellungstabelle, Moderationsabläufe und CSS-Variablen stehen in der englischen README.


## Wichtige Einstellungen und Verhalten

Die englische README in diesem Verzeichnis ist die maßgebliche Referenz und enthält vollständige Einstellungstabellen und ausführliche Beispiele. Diese Übersetzung erklärt die praktische Einrichtung und die wichtigsten Sicherheitshinweise; konsultieren Sie vor Änderungen an erweiterten Einstellungen die englische Referenz.

Die vollständige Einstellungsreferenz finden Sie in der [englischen README](README.md).

### Wichtige Hinweise

Verwenden Sie `{% render_comments page %}` im Template und bereiten Sie Formular/Baum nicht nochmals in `get_context()` vor. Neueste Kommentare müssen auf die aktuelle Wagtail-Site begrenzt sein; Proxy-Header bleiben ohne vertrauenswürdigen Proxy deaktiviert.

## Sicherheit und Betrieb

- Halten Sie Abhängigkeiten aktuell. Verwenden Sie für nutzererstelltes HTML den vorgesehenen Bereinigungs- und Ausgabepfad; geben Sie gespeicherte Kommentare oder Forenbeiträge nicht bedingungslos mit `|safe` aus.
- Prüfen Sie Migrationen und Berechtigungen mit normalen, eingeschränkten Benutzern, Moderatoren und Administratoren.
- Testen Sie bei mehreren Wagtail-Sites jede konfigurierte Domain sowie einen unbekannten Host. Wenn keine Site gefunden wird, darf eine Abfrage nicht auf Datensätze aller Sites erweitert werden.
- Behandeln Sie API-Tokens, SMTP-Zugangsdaten und private URLs als Geheimnisse. Committen Sie diese nicht in Git und veröffentlichen Sie sie nicht in Fehlerberichten.
- Sichern Sie Datenbank und Mediendateien vor Migrationen, Massenverschiebungen, Importen oder der ersten Massenveröffentlichung. Testen Sie diese Vorgänge zuerst in Staging.

## Empfohlene Kombinationen

- `wagtail-simple-forum` ergänzt Artikelkommentare um themenbasierte Diskussionen und private Nachrichten.
- Bildverzeichnisverwaltung und Bildauswahl sind optional.

## Checkliste zur Überprüfung

- [ ] Installieren Sie den Kandidaten in Staging und notieren Sie Python-, Django-, Wagtail- und Datenbankversionen.
- [ ] Führen Sie `python manage.py check` und die Paketmigrationen aus.
- [ ] Prüfen Sie den Hauptablauf mit einem normalen und einem eingeschränkten Benutzer.
- [ ] Prüfen Sie Logs, Zugriffskontrolle, Caching, Backups und Wiederherstellung.

Das Archiv besteht statische Syntax- und Packaging-Prüfungen; die vollständige Django-/Wagtail-Laufzeitintegration wurde in dieser Umgebung jedoch nicht getestet. Betrachten Sie die folgende Checkliste als Freigabekriterium und nicht als Behauptung, dass jede Versionskombination getestet wurde.

## Fehlerbehebung

Wenn der Ablauf nicht funktioniert, prüfen Sie App-Konfiguration, Migrationen, URL-Reihenfolge, Benutzerrechte und Django-Logs. Vergleichen Sie Paketversion und Beispiel mit der englischen README.

## Lizenz und Support

MIT. Quellcode: [https://github.com/vovansrnd/wagtail-mptt-comments](https://github.com/vovansrnd/wagtail-mptt-comments).

