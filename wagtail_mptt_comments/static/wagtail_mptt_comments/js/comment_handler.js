// wagtail_mptt_comments/static/wagtail_mptt_comments/js/comment_handler.js
document.addEventListener('DOMContentLoaded', function () {
    // Находим форму по любому из используемых селекторов
    const commentForm = document.querySelector('form[data-form-type="comment"]') ||
                        document.querySelector('form.compose-form') ||
                        document.querySelector('.comment-compose form');
    if (!commentForm) return;

    const parentInput = commentForm.querySelector('input[name="parent"]');

    // ── Распахиваем форму, если она свернута (для тем ZenWay / Nova) ──
    function revealComposeForm() {
        const trigger = document.getElementById('compose-trigger') || document.querySelector('.compose-trigger');
        const body = document.getElementById('compose-body') || document.querySelector('.compose-body');

        if (body) {
            body.hidden = false;
        }
        if (trigger) {
            trigger.hidden = true;
            trigger.setAttribute('aria-expanded', 'true');
        }

        // Вызываем кастомное событие (для совместимости)
        document.dispatchEvent(new CustomEvent('reply-requested'));
    }

    // ── Функция вставки контента в ProseMirror ──
    function insertIntoEditor(html) {
        const editorDiv = commentForm.querySelector('.ProseMirror');
        if (!editorDiv) {
            // Если форма только раскрылась, даем 100мс на инициализацию
            setTimeout(() => insertIntoEditor(html), 100);
            return;
        }
        editorDiv.focus();

        try {
            const dt = new DataTransfer();
            dt.setData('text/html', html);
            dt.setData('text/plain', html.replace(/<[^>]+>/g, ''));
            const ev = new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true });
            editorDiv.dispatchEvent(ev);
            editorDiv.dispatchEvent(new InputEvent('input', { bubbles: true }));

            // Ставим курсор в самый конец
            setTimeout(() => {
                const sel = window.getSelection();
                const range = document.createRange();
                range.selectNodeContents(editorDiv);
                range.collapse(false);
                sel.removeAllRanges();
                sel.addRange(range);
            }, 50);
        } catch (e) {
            editorDiv.innerHTML = editorDiv.innerHTML + html;
        }
    }

    // ── Обработчик клика «Ответить» ──
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.comment-reply-btn');
        if (!btn) return;

        e.preventDefault();
        e.stopPropagation();

        const commentId = btn.dataset.commentId;
        const author = btn.dataset.author || btn.dataset.commentAuthor || '';

        // 1. Заполняем ID родителя
        if (parentInput && commentId) {
            parentInput.value = commentId;
        }

        // 2. Ищем текст цитаты (поддерживаем оба варианта разметки ID)
        const quoteCb = document.getElementById('quote_' + commentId) || document.getElementById('with_quote_' + commentId);
        const textEl = document.getElementById('comment_text_' + commentId) || document.getElementById('comment-html-' + commentId);

        let html = '';
        if (quoteCb && quoteCb.checked && textEl) {
            const rawContent = textEl.innerHTML.trim();
            html = `<blockquote><p><strong>@${author}</strong></p><p>${rawContent}</p></blockquote><p><br class="ProseMirror-trailingBreak"></p>`;
            quoteCb.checked = false;
        } else if (author) {
            html = `<p><strong>@${author}</strong>,&nbsp;</p>`;
        }

        // 3. РАСПАХИВАЕМ ФОРМУ!
        revealComposeForm();

        // 4. Мягко скроллим к ней
        const anchor = document.getElementById('comment-form-anchor') || commentForm;
        if (anchor) {
            anchor.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        // 5. Вставляем текст цитаты
        if (html) {
            setTimeout(() => insertIntoEditor(html), 120);
        }
    });

    // ── Обработчик клика на сам плейсхолдер формы (если кликнули «Написать комментарий…») ──
    const composeTrigger = document.getElementById('compose-trigger');
    if (composeTrigger) {
        composeTrigger.addEventListener('click', function () {
            revealComposeForm();
            setTimeout(() => {
                const ed = commentForm.querySelector('.ProseMirror');
                if (ed) ed.focus();
            }, 100);
        });
    }

    const cancelBtn = document.getElementById('compose-cancel');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function () {
            const trigger = document.getElementById('compose-trigger');
            const body = document.getElementById('compose-body');
            if (body) body.hidden = true;
            if (trigger) {
                trigger.hidden = false;
                trigger.setAttribute('aria-expanded', 'false');
            }
            if (parentInput) parentInput.value = '';
        });
    }
});
