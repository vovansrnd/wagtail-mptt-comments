# wagtail-mptt-comments

**提供页面树状评论、访客反垃圾控制、可选审核、通知以及 Wagtail 管理工具。该包用于文章/页面评论，而不是论坛版块或私信对话。**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## 主要功能

- 使用 django-mptt 的嵌套回复。
- 访客提交采用 honeypot、时间令牌和轻量验证。
- 可选审核以及管理员/回复作者通知。
- 提供评论树和最新评论组件模板标签，并按当前 Site 过滤。

## 依赖与兼容性

- 声明的依赖: `Wagtail >= 6.0; django-mptt >= 0.16.0; django-prose-editor >= 0.26; nh3 >= 0.2.14`.
- Python、Django 与 Wagtail 的兼容性必须一起验证。最低依赖版本并不代表所有版本均受支持。

包元数据声明 Wagtail >= 6.0，但最低依赖版本并不代表已验证所有版本的兼容性。本归档不包含覆盖所有 Django/Wagtail 组合的完整自动化测试矩阵。升级生产环境前，请在预发布环境验证具体版本、数据库、文件存储后端和部署配置。

## 安装

请在与 Wagtail 项目相同的虚拟环境中安装此包：

```bash
pip install wagtail-mptt-comments
```

按以下顺序添加应用，同时保留项目原有的其他依赖：

```python
INSTALLED_APPS = [
    # 同时保留项目需要的其他 Django/Wagtail 依赖。
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

运行 `python manage.py migrate wagtail_mptt_comments`。


## 初始配置

下面是最小起步示例。请根据项目调整模型名、API 字段和 URL。

```django
{% load mptt_comment_tags %}
{% render_comments page %}
```

可通过 `{% get_latest_comments 5 as latest_comments %}` 显示最新评论。请在已配置当前 Wagtail Site 的请求上下文中使用该标签。

请使用该标签，而不要在 `Page.get_context()` 中重复准备评论树、表单和计数。完整设置表、审核流程和 CSS 变量请参阅英文 README。


## 重要设置与行为

本目录中的英文 README 是规范参考文档，包含完整设置表和扩展示例。本译文覆盖实际安装步骤和关键安全注意事项；修改高级设置前请查阅英文文档。

完整设置说明请参阅[英文 README](README.md)。

### 重要注意事项

在模板中使用 `{% render_comments page %}`，不要在 `get_context()` 中重复准备表单/评论树。最新评论必须限制在当前 Site；未正确配置可信代理时不要信任代理头。

## 安全与运维建议

- 请保持依赖更新。用户编写的 HTML 应使用预期的清理和渲染路径；不要无条件对已存储的评论或论坛帖子使用 `|safe`。
- 请分别使用普通用户、受限用户、版主和管理员验证迁移与权限。
- 多站点部署时，请测试每个已配置域名以及一个未知主机。找不到 Site 时，查询不得扩大为读取所有站点的数据。
- API 令牌、SMTP 凭据和私有 URL 都应视为机密。不要提交到 Git，也不要放入公开的问题报告。
- 执行迁移、批量移动、导入或首次批量发布之前，请备份数据库和媒体文件，并先在预发布环境测试。

## 推荐组合

- `wagtail-simple-forum` 可在文章评论之外提供主题讨论和私信。
- 图片目录管理和图片选择器都是可选项。

## 验证清单

- [ ] 在预发布环境安装候选版本，并记录 Python、Django、Wagtail 和数据库版本。
- [ ] 运行 `python manage.py check` 和包迁移。
- [ ] 使用普通用户与受限用户测试主要流程。
- [ ] 检查日志、访问权限、缓存、备份和恢复。

本归档通过静态语法与打包检查，但当前环境未完成 Django/Wagtail 运行时集成测试。请将以下清单视为发布前的必检项目，而不是所有版本组合均已测试的声明。

## 故障排查

如果流程无法运行，请检查应用配置、迁移、URL 顺序、用户权限和 Django 日志，并将包版本与示例和英文 README 对照。

## 许可证与支持

MIT. 源代码: [https://github.com/vovansrnd/wagtail-mptt-comments](https://github.com/vovansrnd/wagtail-mptt-comments).

