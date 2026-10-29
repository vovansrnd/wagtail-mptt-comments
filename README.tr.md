# wagtail-mptt-comments

**İç içe sayfa yorumları, misafirler için istenmeyen ileti koruması, isteğe bağlı moderasyon, bildirimler ve Wagtail yönetici araçları sunar. Forum bölümleri veya özel mesajlar için değil, makale yorumları için tasarlanmıştır.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## Temel özellikler

- django-mptt ile iç içe yanıtlar.
- Misafir gönderileri için honeypot, zaman belirteci ve basit doğrulama.
- İsteğe bağlı moderasyon ve yönetici/yanıt yazarı bildirimleri.
- Geçerli Site ile filtrelenen yorum ağacı ve son yorum widget’ı için şablon etiketleri.

## Gereksinimler ve uyumluluk

- Bildirilen bağımlılıklar: `Wagtail >= 6.0; django-mptt >= 0.16.0; django-prose-editor >= 0.26; nh3 >= 0.2.14`.
- Python, Django ve Wagtail uyumluluğu birlikte kontrol edilmelidir. Paketin asgari bağımlılığı tüm sürümlerin desteklendiğini kanıtlamaz.

Paket metaverisi Wagtail >= 6.0 belirtir; ancak asgari bağımlılık, tüm sürümlerle uyumluluğu kanıtlamaz. Bu arşiv tüm Django/Wagtail kombinasyonları için tam otomatik test matrisi içermez. Üretimi yükseltmeden önce tam sürümleri, veritabanını, depolama arka ucunu ve dağıtım ayarlarını staging ortamında sınayın.

## Kurulum

Paketi Wagtail projenizle aynı sanal ortama yükleyin:

```bash
pip install wagtail-mptt-comments
```

Diğer proje bağımlılıklarını koruyarak uygulamaları bu sırayla ekleyin:

```python
INSTALLED_APPS = [
    # Projenin zaten kullandığı diğer Django/Wagtail bağımlılıklarını da koruyun.
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

`python manage.py migrate wagtail_mptt_comments` komutunu çalıştırın.


## İlk yapılandırma

Başlangıç için en küçük örnek aşağıdadır. Model adlarını, API alanlarını ve URL’leri yapılandırmanıza uyarlayın.

```django
{% load mptt_comment_tags %}
{% render_comments page %}
```

Son yorumlar `{% get_latest_comments 5 as latest_comments %}` ile gösterilebilir. Etiketi, geçerli Wagtail Site tanımlı bir request bağlamında kullanın.

Aynı ağaç, form ve sayıyı `Page.get_context()` içinde yeniden hazırlamak yerine etiketi kullanın. Tam ayar tablosu, moderasyon akışı ve CSS değişkenleri İngilizce README’dedir.


## Önemli ayarlar ve davranış

Bu dizindeki İngilizce README, tüm seçenek tablolarını ve genişletilmiş örnekleri içeren temel başvuru belgesidir. Bu çeviri pratik kurulumu ve temel güvenlik uyarılarını kapsar; gelişmiş ayarları değiştirmeden önce İngilizce başvuruya bakın.

Tam ayar listesi için [İngilizce README](README.md) dosyasına bakın.

### Önemli notlar

Şablonda `{% render_comments page %}` kullanın ve form/ağaç verisini `get_context()` içinde tekrar hazırlamayın. Son yorumlar geçerli Site ile sınırlandırılmalı; güvenilir proxy yapılandırılmadıysa proxy başlıklarına güvenmeyin.

## Güvenlik ve işletim

- Bağımlılıkları güncel tutun. Kullanıcı HTML’si için belirlenen temizleme/görüntüleme yolunu kullanın; kaydedilmiş yorumları veya forum gönderilerini koşulsuz `|safe` ile göstermeyin.
- Geçişleri ve izinleri normal, kısıtlı, moderatör ve yönetici hesaplarıyla kontrol edin.
- Çoklu site kurulumlarında yapılandırılmış her alan adını ve bilinmeyen bir hostu sınayın. Site bulunamazsa sorgu tüm sitelerdeki kayıtları kapsayacak şekilde genişlememelidir.
- API tokenlarını, SMTP kimlik bilgilerini ve özel URL’leri gizli kabul edin. Bunları Git’e eklemeyin veya herkese açık hata raporlarında paylaşmayın.
- Geçişler, toplu taşıma, içe aktarma veya ilk toplu yayın öncesinde veritabanını ve medya dosyalarını yedekleyin. Önce staging ortamında deneyin.

## Önerilen kombinasyonlar

- `wagtail-simple-forum`, makale yorumlarını konu tartışmaları ve özel mesajlarla tamamlar.
- Görsel düzenleme ve seçici isteğe bağlıdır.

## Doğrulama kontrol listesi

- [ ] Aday sürümü staging ortamına kurun; Python, Django, Wagtail ve veritabanı sürümlerini kaydedin.
- [ ] `python manage.py check` ve paket geçişlerini çalıştırın.
- [ ] Ana akışı normal ve kısıtlı hesapla sınayın.
- [ ] Kayıtları, erişimi, önbelleği, yedeklemeyi ve geri yüklemeyi kontrol edin.

Arşiv statik sözdizimi ve paketleme kontrollerini geçer; ancak bu ortamda tam Django/Wagtail çalışma zamanı entegrasyonu test edilmedi. Aşağıdaki listeyi tüm sürümlerin test edildiğinin kanıtı değil, yayın öncesi zorunlu kontrol olarak görün.

## Sorun giderme

Akış çalışmıyorsa uygulama ayarlarını, geçişleri, URL sırasını, kullanıcı izinlerini ve Django kayıtlarını kontrol edin. Paket sürümünü ve örneği İngilizce README ile karşılaştırın.

## Lisans ve destek

MIT. Kaynak kod: [https://github.com/vovansrnd/wagtail-mptt-comments](https://github.com/vovansrnd/wagtail-mptt-comments).

