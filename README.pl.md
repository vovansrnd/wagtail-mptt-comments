# wagtail-mptt-comments

**Zapewnia zagnieżdżone komentarze do stron, ochronę antyspamową gości, opcjonalną moderację, powiadomienia i narzędzia administracyjne Wagtail. Służy do komentarzy pod artykułami, a nie do działów forum czy prywatnych wiadomości.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## Najważniejsze funkcje

- Zagnieżdżone odpowiedzi z django-mptt.
- Honeypot, token czasowy i proste wyzwanie dla gości.
- Opcjonalna moderacja i powiadomienia dla administratorów/autorów odpowiedzi.
- Tagi szablonów drzewa i najnowszych komentarzy z filtrowaniem bieżącego Site.

## Wymagania i zgodność

- Zadeklarowane zależności: `Wagtail >= 6.0; django-mptt >= 0.16.0; django-prose-editor >= 0.26; nh3 >= 0.2.14`.
- Zgodność Pythona, Django i Wagtail należy sprawdzać łącznie. Minimalna zależność pakietu nie potwierdza obsługi każdej wersji.

Metadane deklarują Wagtail >= 6.0, ale minimalna zależność nie dowodzi zgodności. Archiwum nie zawiera pełnej automatycznej macierzy wszystkich kombinacji Django/Wagtail. Przed aktualizacją produkcji sprawdź dokładne wersje, bazę danych, backend plików i konfigurację wdrożenia na środowisku testowym.

## Instalacja

Zainstaluj pakiet w tym samym środowisku wirtualnym co projekt Wagtail:

```bash
pip install wagtail-mptt-comments
```

Dodaj aplikacje w tej kolejności, zachowując pozostałe zależności projektu:

```python
INSTALLED_APPS = [
    # Zachowaj również inne zależności Django/Wagtail wymagane przez projekt.
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

Uruchom `python manage.py migrate wagtail_mptt_comments`.


## Pierwsza konfiguracja

Minimalny przykład na początek. Dostosuj nazwy modeli, pola API i adresy URL do swojej konfiguracji.

```django
{% load mptt_comment_tags %}
{% render_comments page %}
```

Najnowsze komentarze można wyświetlić przez `{% get_latest_comments 5 as latest_comments %}`. Użyj tagu w kontekście żądania z ustawionym bieżącym Wagtail Site.

Użyj tagu zamiast ponownie przygotowywać drzewo, formularz i liczbę komentarzy w `Page.get_context()`. Pełna tabela ustawień, przebieg moderacji i zmienne CSS są w angielskim README.


## Ważne ustawienia i zachowanie

Angielski README w tym katalogu jest kanoniczną dokumentacją i zawiera pełne tabele opcji oraz rozszerzone przykłady. To tłumaczenie opisuje praktyczną konfigurację i najważniejsze ostrzeżenia bezpieczeństwa; przed zmianą zaawansowanych opcji sprawdź dokumentację angielską.

Pełną tabelę ustawień znajdziesz w [angielskim README](README.md).

### Ważne uwagi

Użyj `{% render_comments page %}` w szablonie i nie przygotowuj ponownie formularza/drzewa w `get_context()`. Najnowsze komentarze muszą być ograniczone do bieżącego Site; nie ufaj nagłówkom proxy bez zaufanego proxy.

## Bezpieczeństwo i eksploatacja

- Aktualizuj zależności. Dla HTML użytkowników stosuj przewidziany mechanizm oczyszczania i renderowania; nie wyświetlaj zapisanych komentarzy ani postów bezwarunkowo przez `|safe`.
- Sprawdź migracje i uprawnienia jako zwykły, ograniczony użytkownik, moderator i administrator.
- W instalacji wieloserwisowej przetestuj każdą skonfigurowaną domenę i nieznany host. Brak Site nie może rozszerzać zapytania na rekordy wszystkich witryn.
- Traktuj tokeny API, dane SMTP i prywatne adresy URL jako sekrety. Nie dodawaj ich do Git ani do publicznych zgłoszeń.
- Wykonaj kopię zapasową bazy i plików multimedialnych przed migracjami, masowym przenoszeniem, importem lub pierwszą masową publikacją. Najpierw przetestuj te operacje na stagingu.

## Zalecane połączenia

- `wagtail-simple-forum` uzupełnia komentarze artykułów o dyskusje tematyczne i wiadomości prywatne.
- Organizacja obrazów i selektor są opcjonalne.

## Lista kontrolna

- [ ] Zainstaluj wersję kandydującą na stagingu i zapisz wersje Pythona, Django, Wagtail oraz bazy.
- [ ] Uruchom `python manage.py check` i migracje pakietu.
- [ ] Przetestuj główny przepływ jako zwykły i ograniczony użytkownik.
- [ ] Sprawdź logi, dostęp, cache, kopie zapasowe i odtwarzanie.

Archiwum przechodzi statyczne kontrole składni i pakowania, ale w tym środowisku nie wykonano pełnych testów integracyjnych Django/Wagtail. Poniższą listę traktuj jako warunek wydania, a nie potwierdzenie przetestowania każdej kombinacji.

## Rozwiązywanie problemów

Jeśli przepływ nie działa, sprawdź konfigurację aplikacji, migracje, kolejność URL, uprawnienia i logi Django. Porównaj wersję pakietu i przykład z angielskim README.

## Licencja i pomoc

MIT. Kod źródłowy: [https://github.com/vovansrnd/wagtail-mptt-comments](https://github.com/vovansrnd/wagtail-mptt-comments).

