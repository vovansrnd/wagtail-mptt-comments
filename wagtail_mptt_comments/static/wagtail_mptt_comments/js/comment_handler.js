// wagtail_mptt_comments/static/wagtail_mptt_comments/js/comment_handler.js
document.addEventListener('DOMContentLoaded', function () {
    const commentForm = document.querySelector('form[data-form-type="comment"]');
    if (!commentForm) return;

    const parentInput = commentForm.querySelector('input[name="parent"]');
    const editorDiv = commentForm.querySelector('.ProseMirror');

    // ── Вспомогательная функция: перенос курсора в самый конец ──
    function moveCursorToEnd(element) {
        element.focus();
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(element);
        range.collapse(false); // false = переместить курсор в конец содержимого
        selection.removeAllRanges();
        selection.addRange(range);
    }

    // ── Вставка HTML в ProseMirror с правильным курсором ──
    function insertIntoEditor(html) {
        if (!editorDiv) return;
        editorDiv.focus();

        try {
            const dt = new DataTransfer();
            dt.setData('text/html', html);
            dt.setData('text/plain', html.replace(/<[^>]+>/g, ''));
            const ev = new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true });
            editorDiv.dispatchEvent(ev);
            editorDiv.dispatchEvent(new Event('input', { bubbles: true }));

            // С небольшой задержкой ставим курсор в конец (под цитату или после запятой с пробелом)
            setTimeout(() => {
                moveCursorToEnd(editorDiv);
            }, 50);
        } catch (e) {
            editorDiv.innerHTML = editorDiv.innerHTML + html;
            moveCursorToEnd(editorDiv);
        }
    }

    // ── Клик по кнопке «Ответить» ──
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.comment-reply-btn');
        if (!btn) return;

        e.preventDefault();
        const commentId = btn.dataset.commentId;
        const author = btn.dataset.author || '';

        if (parentInput) parentInput.value = commentId;

        const quoteCb = document.getElementById('quote_' + commentId);
        const textEl = document.getElementById('comment_text_' + commentId);

        let html = '';

        // 1. Если выбрано с цитированием:
        // Ник идет в заголовке цитаты, сам текст в отдельном параграфе внутри цитаты,
        // а под цитатой создается пустой параграф для ввода ответа!
        if (quoteCb && quoteCb.checked && textEl) {
            const rawContent = textEl.innerHTML.trim();
            html = `<blockquote><p><strong>@${author}</strong></p><p>${rawContent}</p></blockquote><p><br class="ProseMirror-trailingBreak"></p>`;
            quoteCb.checked = false;
        }
        // 2. Если обычный ответ:
        // После запятой стоит жесткий неразрывный пробел (&nbsp;), чтобы курсор не лип к запятой!
        else if (author) {
            html = `<p><strong>@${author}</strong>,&nbsp;</p>`;
        }

        const anchor = document.getElementById('comment-form-anchor');
        if (anchor) anchor.scrollIntoView({ behavior: 'smooth', block: 'center' });

        if (html) {
            setTimeout(() => insertIntoEditor(html), 150);
        }
    });
});
