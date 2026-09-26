// wagtail_mptt_comments/static/wagtail_mptt_comments/js/admin_comments.js
// ЗАЩИТА ОТ ДВОЙНОГО ВЫПОЛНЕНИЯ
if (!window.adminCommentsInitialized) {
    window.adminCommentsInitialized = true;

    document.addEventListener('DOMContentLoaded', () => {
        // Контейнер с переводами из data-атрибутов
        const appContainer = document.querySelector('.comments-app') || document.body;

        // Получаем переведенные сообщения или используем английские фолбэки
        const msgs = {
            msgSelect: appContainer.dataset.msgSelect || 'Please select comments first.',
            msgError: appContainer.dataset.msgError || 'An error occurred.',
            msgNetError: appContainer.dataset.msgNetError || 'Network error while performing action.',
            msgConfirmDel: appContainer.dataset.msgConfirmDel || 'Are you sure you want to delete this comment?',
            msgConfirmBulk: appContainer.dataset.msgConfirmBulk || 'Are you sure you want to delete the selected comments?'
        };

        // Функция для получения CSRF-токена из cookie
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        const csrftoken = getCookie('csrftoken');

        async function performCommentAction(action, ids) {
            if (ids.length === 0) {
                document.dispatchEvent(new CustomEvent("w-messages:add", { detail: { type: 'warning', text: msgs.msgSelect }}));
                return;
            }

            const formData = new FormData();
            formData.append('action', action);
            ids.forEach(id => formData.append('ids[]', id));

            try {
                const response = await fetch('/admin/comments/action/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrftoken, 'X-Requested-With': 'XMLHttpRequest' },
                    body: formData,
                });
                const data = await response.json();
                if (data.success) {
                    document.dispatchEvent(new CustomEvent("w-messages:add", { detail: { type: 'success', text: data.message }}));
                    setTimeout(() => window.location.reload(), 800);
                } else {
                    document.dispatchEvent(new CustomEvent("w-messages:add", { detail: { type: 'error', text: data.error || msgs.msgError }}));
                }
            } catch (error) {
                document.dispatchEvent(new CustomEvent("w-messages:add", { detail: { type: 'error', text: msgs.msgNetError }}));
            }
        }

        document.querySelectorAll('.approve-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                performCommentAction('approve', [e.currentTarget.dataset.id]);
            });
        });

        document.querySelectorAll('.delete-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                if (confirm(msgs.msgConfirmDel)) {
                    performCommentAction('delete', [e.currentTarget.dataset.id]);
                }
            });
        });

        function getSelectedCommentIds() {
            return Array.from(document.querySelectorAll('.select-comment:checked')).map(cb => cb.value);
        }

        const bulkApproveBtn = document.getElementById('bulk-approve');
        if(bulkApproveBtn) {
            bulkApproveBtn.addEventListener('click', (e) => {
                e.preventDefault();
                performCommentAction('approve', getSelectedCommentIds());
            });
        }

        const bulkDeleteBtn = document.getElementById('bulk-delete');
        if(bulkDeleteBtn) {
            bulkDeleteBtn.addEventListener('click', (e) => {
                e.preventDefault();
                if (confirm(msgs.msgConfirmBulk)) {
                    performCommentAction('delete', getSelectedCommentIds());
                }
            });
        }

        const selectAllCheckbox = document.getElementById('select-all');
        if(selectAllCheckbox) {
            selectAllCheckbox.addEventListener('click', (e) => {
                document.querySelectorAll('.select-comment').forEach(checkbox => {
                    checkbox.checked = e.target.checked;
                });
            });
        }

        const selectAllToggle = document.getElementById('select-all-toggle');
        if (selectAllToggle) {
            selectAllToggle.addEventListener('click', () => {
                const boxes = document.querySelectorAll('.select-comment');
                const shouldCheck = ![...boxes].every(cb => cb.checked);
                boxes.forEach(cb => cb.checked = shouldCheck);
            });
        }
    });
}
