# wagtail-mptt-comments

**Fornisce commenti annidati alle pagine, protezione antispam per gli ospiti, moderazione opzionale, notifiche e strumenti admin Wagtail. È pensato per i commenti agli articoli, non per le sezioni di un forum o i messaggi privati.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## Funzionalità principali

- Risposte annidate tramite django-mptt.
- Honeypot, token temporale e verifica leggera per gli invii degli ospiti.
- Moderazione opzionale e notifiche ad amministratori/autori delle risposte.
- Tag template per albero e widget dei commenti recenti, filtrati per il Site corrente.

## Requisiti e compatibilità

- Dipendenze dichiarate: `Wagtail >= 6.0; django-mptt >= 0.16.0; django-prose-editor >= 0.26; nh3 >= 0.2.14`.
- La compatibilità di Python, Django e Wagtail va verificata congiuntamente. La dipendenza minima del pacchetto non conferma il supporto di tutte le versioni.

I metadati dichiarano Wagtail >= 6.0, ma una dipendenza minima non dimostra la compatibilità. Questo archivio non contiene una matrice automatizzata completa per tutte le combinazioni Django/Wagtail. Prima di aggiornare la produzione, verifica in staging le versioni effettive, il database, lo storage e le impostazioni di deployment.

## Installazione

Installa il pacchetto nello stesso ambiente virtuale del progetto Wagtail:

```bash
pip install wagtail-mptt-comments
```

Aggiungi le app nell’ordine indicato mantenendo le altre dipendenze del progetto:

```python
INSTALLED_APPS = [
    # Mantieni anche le altre dipendenze Django/Wagtail già necessarie.
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

Eseguire `python manage.py migrate wagtail_mptt_comments`.


## Configurazione iniziale

Esempio minimo per iniziare. Adatta nomi dei modelli, campi API e URL alla tua configurazione.

```django
{% load mptt_comment_tags %}
{% render_comments page %}
```

I commenti recenti si possono mostrare con `{% get_latest_comments 5 as latest_comments %}`. Usare il tag in un contesto di richiesta con il Wagtail Site corrente configurato.

Usare il tag invece di preparare nuovamente albero, modulo e conteggio in `Page.get_context()`. La tabella completa delle impostazioni, il flusso di moderazione e le variabili CSS sono nel README inglese.


## Impostazioni e comportamento importanti

Il README inglese in questa directory è il riferimento canonico e contiene le tabelle complete delle opzioni e gli esempi estesi. Questa traduzione copre la configurazione pratica e gli avvisi di sicurezza essenziali; consulta il riferimento inglese prima di modificare le opzioni avanzate.

Consulta il [README inglese](README.md) per la tabella completa delle impostazioni.

### Note importanti

Usa `{% render_comments page %}` nel template e non preparare di nuovo modulo/albero in `get_context()`. I commenti recenti devono essere limitati al Site corrente; non fidarti degli header proxy senza un proxy attendibile configurato.

## Sicurezza e operatività

- Mantieni aggiornate le dipendenze. Per l’HTML degli utenti usa il percorso previsto di sanificazione e rendering; non mostrare commenti o post salvati con `|safe` incondizionato.
- Verifica migrazioni e permessi con utenti normali, limitati, moderatori e amministratori.
- Nei progetti multi-sito, verifica ogni dominio configurato e un host sconosciuto. Se non viene trovato un Site, la query non deve estendersi ai record di tutti i siti.
- Tratta token API, credenziali SMTP e URL privati come segreti. Non inserirli in Git né in segnalazioni pubbliche.
- Esegui il backup del database e dei file multimediali prima di migrazioni, spostamenti in blocco, importazioni o pubblicazioni massive iniziali. Prova prima in staging.

## Combinazioni consigliate

- `wagtail-simple-forum` completa i commenti agli articoli con discussioni tematiche e messaggi privati.
- L’organizzazione delle immagini e il selettore sono opzionali.

## Lista di verifica

- [ ] Installa la versione candidata in staging e annota le versioni di Python, Django, Wagtail e database.
- [ ] Esegui `python manage.py check` e le migrazioni del pacchetto.
- [ ] Prova il flusso principale con un utente normale e uno limitato.
- [ ] Controlla log, accessi, cache, backup e ripristino.

L’archivio supera i controlli statici di sintassi e packaging, ma in questo ambiente non è stato eseguito un test completo d’integrazione Django/Wagtail. Considera la lista seguente un requisito per il rilascio, non la prova che ogni combinazione sia stata testata.

## Risoluzione dei problemi

Se il flusso non funziona, controlla configurazione dell’app, migrazioni, ordine URL, permessi e log Django. Confronta versione ed esempio con il README inglese.

## Licenza e supporto

MIT. Codice sorgente: [https://github.com/vovansrnd/wagtail-mptt-comments](https://github.com/vovansrnd/wagtail-mptt-comments).

