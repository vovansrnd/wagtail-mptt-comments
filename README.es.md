# wagtail-mptt-comments

**Proporciona comentarios anidados para páginas, protección antispam para invitados, moderación opcional, notificaciones y herramientas del administrador de Wagtail. Está pensado para comentarios de artículos, no para secciones de foro ni mensajes privados.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## Funciones principales

- Respuestas anidadas con django-mptt.
- Honeypot, token temporal y desafío sencillo para envíos de invitados.
- Moderación opcional y avisos a administradores/autores de respuestas.
- Etiquetas de plantilla para el árbol y el widget de comentarios recientes, filtrados por el Site actual.

## Requisitos y compatibilidad

- Dependencias declaradas: `Wagtail >= 6.0; django-mptt >= 0.16.0; django-prose-editor >= 0.26; nh3 >= 0.2.14`.
- La compatibilidad de Python, Django y Wagtail debe verificarse en conjunto. La dependencia mínima del paquete no confirma que todas las versiones estén soportadas.

Los metadatos declaran Wagtail >= 6.0, pero una dependencia mínima no demuestra compatibilidad. Este archivo no incluye una matriz automatizada completa para todas las combinaciones de Django/Wagtail. Antes de actualizar producción, prueba las versiones exactas, la base de datos, el almacenamiento y la configuración de despliegue en un entorno de pruebas.

## Instalación

Instala el paquete en el mismo entorno virtual que tu proyecto Wagtail:

```bash
pip install wagtail-mptt-comments
```

Añade las aplicaciones en el orden indicado y conserva las demás dependencias del proyecto:

```python
INSTALLED_APPS = [
    # Conserva también las demás dependencias Django/Wagtail que necesita el proyecto.
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

Ejecute `python manage.py migrate wagtail_mptt_comments`.


## Configuración inicial

Ejemplo mínimo para empezar. Adapta los nombres de modelos, campos API y URL a tu configuración.

```django
{% load mptt_comment_tags %}
{% render_comments page %}
```

Los comentarios recientes se pueden mostrar con `{% get_latest_comments 5 as latest_comments %}`. Use la etiqueta en un contexto de solicitud con el Wagtail Site actual configurado.

Use la etiqueta en lugar de preparar de nuevo el árbol, formulario y contador en `Page.get_context()`. La tabla completa de ajustes, el flujo de moderación y las variables CSS están en el README en inglés.


## Ajustes y comportamiento importantes

El README en inglés de este directorio es la referencia canónica y contiene las tablas completas de opciones y ejemplos ampliados. Esta traducción cubre la configuración práctica y las advertencias de seguridad esenciales; consulta la referencia inglesa antes de cambiar opciones avanzadas.

Consulta la [versión inglesa del README](README.md) para ver la referencia completa de ajustes.

### Notas importantes

Usa `{% render_comments page %}` en la plantilla y no prepares otra vez el formulario/árbol en `get_context()`. Los comentarios recientes deben limitarse al Site actual; no confíes en cabeceras de proxy sin un proxy de confianza configurado.

## Seguridad y operación

- Mantén las dependencias actualizadas. Para HTML escrito por usuarios, utiliza la limpieza y representación previstas; no muestres comentarios o publicaciones almacenadas con `|safe` incondicional.
- Comprueba migraciones y permisos con usuarios normales, restringidos, moderadores y administradores.
- En instalaciones multisitio, prueba cada dominio configurado y un host desconocido. Si no se encuentra un Site, la consulta nunca debe ampliarse a todos los sitios.
- Trata los tokens de API, las credenciales SMTP y las URL privadas como secretos. No los guardes en Git ni los incluyas en informes públicos.
- Haz copias de seguridad de la base de datos y de los medios antes de migraciones, movimientos masivos, importaciones o la primera publicación masiva. Prueba primero en staging.

## Combinaciones recomendadas

- `wagtail-simple-forum` complementa los comentarios con debates temáticos y mensajes privados.
- La organización de imágenes y el selector son opcionales.

## Lista de verificación

- [ ] Instala la versión candidata en staging y anota las versiones de Python, Django, Wagtail y la base de datos.
- [ ] Ejecuta `python manage.py check` y las migraciones del paquete.
- [ ] Prueba el flujo principal con un usuario normal y otro restringido.
- [ ] Revisa registros, acceso, caché, copias de seguridad y recuperación.

El archivo supera comprobaciones estáticas de sintaxis y empaquetado, pero no se ha ejecutado aquí una prueba completa de integración Django/Wagtail. Trata la lista siguiente como un requisito previo a la publicación, no como una afirmación de que se han probado todas las combinaciones.

## Solución de problemas

Si el flujo no funciona, revisa la configuración de la app, las migraciones, el orden de URL, los permisos y los registros de Django. Compara la versión y el ejemplo con el README inglés.

## Licencia y soporte

MIT. Código fuente: [https://github.com/vovansrnd/wagtail-mptt-comments](https://github.com/vovansrnd/wagtail-mptt-comments).

