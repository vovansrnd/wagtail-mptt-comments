// wagtail_mptt_comments/static/wagtail_mptt_comments/js/comment_handler.js
document.addEventListener('DOMContentLoaded', function () {
    const commentForm = document.querySelector('form[data-form-type="comment"]') ||
                        document.querySelector('form.compose-form') ||
                        document.querySelector('.comment-compose form');
    if (!commentForm) return;

    const parentInput = commentForm.querySelector('input[name="parent"]');

    // ── 1. Взаимное исключение чекбоксов (только ОДИН чекбокс цитирования активен!) ──
    document.addEventListener('change', function (e) {
        if (e.target.matches('.with-quote-checkbox, input[id^="quote_"], input[id^="with_quote_"]')) {
            if (e.target.checked) {
                document.querySelectorAll('.with-quote-checkbox, input[id^="quote_"], input[id^="with_quote_"]').forEach(cb => {
                    if (cb !== e.target) cb.checked = false;
                });
            }
        }
    });

    // ── 2. Распахиваем компактную форму (ZenWay / Nova) ──
    function revealComposeForm() {
        const trigger = document.getElementById('compose-trigger') || document.querySelector('.compose-trigger');
        const body = document.getElementById('compose-body') || document.querySelector('.compose-body');

        if (body) {
            body.hidden = false;
            body.style.display = 'block';
        }
        if (trigger) {
            trigger.hidden = true;
            trigger.style.display = 'none';
        }
    }

    // ── 3. Надежная вставка контента в ProseMirror ──
    function insertIntoEditor(htmlContent) {
        const editorDiv = commentForm.querySelector('.ProseMirror[contenteditable="true"]');
        if (!editorDiv) return;

        editorDiv.focus();

        // Способ через имитацию Paste (ProseMirror сам переводит HTML в свои узлы)
        try {
            const dt = new DataTransfer();
            dt.setData('text/html', htmlContent);
            dt.setData('text/plain', htmlContent.replace(/<[^>]+>/g, ''));
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
            }, 60);
        } catch (e) {
            editorDiv.innerHTML = htmlContent + '<p><br class="ProseMirror-trailingBreak"></p>';
        }
    }

    // ── 4. Обработчик клика «Ответить» ──
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.comment-reply-btn');
        if (!btn) return;

        e.preventDefault();
        e.stopPropagation();

        const commentId = btn.dataset.commentId;
        const author = btn.dataset.author || btn.dataset.commentAuthor || '';

        // Заполняем ID родительского комментария
        if (parentInput && commentId) {
            parentInput.value = commentId;
        }

        // Ищем чекбокс и блок текста комментария
        const quoteCb = document.getElementById('quote_' + commentId) ||
                        document.getElementById('with_quote_' + commentId);
        const textEl = document.getElementById('comment_text_' + commentId) ||
                       document.getElementById('comment-html-' + commentId);

        let html = '';
        if (quoteCb && quoteCb.checked && textEl) {
            const rawContent = textEl.innerHTML.trim();
            html = `<blockquote><p><strong>@${author}</strong></p><p>${rawContent}</p></blockquote><p></p>`;
            quoteCb.checked = false; // сбрасываем галочку
        } else if (author) {
            html = `<p><strong>@${author}</strong>,&nbsp;</p>`;
        }

        // 1. Распахиваем форму
        revealComposeForm();

        // 2. Скроллим к ней
        const anchor = document.getElementById('comment-form-anchor') || commentForm;
        if (anchor) {
            anchor.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        // 3. Вставляем цитату с паузой 220мс (гарантирует, что ProseMirror стал видимым и готов к приему)
        if (html) {
            setTimeout(() => {
                insertIntoEditor(html);
            }, 220);
        }
    });

    // ── 5. Клик на сам плейсхолдер «Написать комментарий…» ──
    const composeTrigger = document.getElementById('compose-trigger');
    if (composeTrigger) {
        composeTrigger.addEventListener('click', function () {
            revealComposeForm();
            setTimeout(() => {
                const ed = commentForm.querySelector('.ProseMirror');
                if (ed) ed.focus();
            }, 150);
        });
    }

    // ── 6. Кнопка «Отмена» ──
    const cancelBtn = document.getElementById('compose-cancel');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function () {
            const trigger = document.getElementById('compose-trigger');
            const body = document.getElementById('compose-body');
            if (body) {
                body.hidden = true;
                body.style.display = 'none';
            }
            if (trigger) {
                trigger.hidden = false;
                trigger.style.display = 'flex';
            }
            if (parentInput) parentInput.value = '';
        });
    }
});
