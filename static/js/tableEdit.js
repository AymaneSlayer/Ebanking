document.addEventListener('DOMContentLoaded', () => {
    attachEditLogic();
});

function attachEditLogic() {
    document.querySelectorAll('.client-action-btn.edit').forEach(editBtn => {
        editBtn.addEventListener('click', (e) => {
            e.preventDefault();

            const row = editBtn.closest('tr');
            if (!row || row.classList.contains('editing')) return;

            row.classList.add('editing');

            const tds = row.querySelectorAll('td');
            const id = tds[0].innerText.replace('#', '').trim();

            const nom = tds[1].innerText.trim();
            const prenom = tds[2].innerText.trim();
            const email = tds[3].innerText.trim();

            tds[1].innerHTML = `<input type="text" value="${nom}" class="inline-input">`;
            tds[2].innerHTML = `<input type="text" value="${prenom}" class="inline-input">`;
            tds[3].innerHTML = `<input type="email" value="${email}" class="inline-input">`;

            const actionsCell = tds[4];
            const actionWrapper = actionsCell.querySelector('.client-actions') || actionsCell;

            actionWrapper.innerHTML = `
                <button class="client-action-btn save" title="Sauvegarder">✅</button>
                <button class="client-action-btn cancel" title="Annuler">❌</button>
            `;

            // Entrée déclenche sauvegarde
            [tds[1], tds[2], tds[3]].forEach(td => {
                td.querySelector('input').addEventListener('keydown', (event) => {
                    if (event.key === 'Enter') {
                        actionWrapper.querySelector('.save').click();
                    }
                });
            });

            // ✅ Sauvegarde
            actionWrapper.querySelector('.save').addEventListener('click', () => {
                const newNom = tds[1].querySelector('input').value.trim();
                const newPrenom = tds[2].querySelector('input').value.trim();
                const newEmail = tds[3].querySelector('input').value.trim();

                fetch(`/modifier_client/${id}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nom: newNom, prenom: newPrenom, email: newEmail })
                }).then(res => {
                    if (res.ok) {
                        tds[1].innerText = newNom;
                        tds[2].innerText = newPrenom;
                        tds[3].innerText = newEmail;

                        actionWrapper.innerHTML = `
                            <button class="client-action-btn edit" title="Éditer">✏️</button>
                            <button class="client-action-btn delete" title="Supprimer"
                                data-bs-toggle="modal"
                                data-bs-target="#confirmDeleteModal${id}">
                                🗑️
                            </button>
                        `;

                        row.classList.remove('editing');
                        attachEditLogic(); // Réattache les événements
                    } else {
                        alert("❌ Erreur lors de la mise à jour.");
                    }
                });
            });

            // ❌ Annulation
            actionWrapper.querySelector('.cancel').addEventListener('click', () => {
                tds[1].innerText = nom;
                tds[2].innerText = prenom;
                tds[3].innerText = email;

                actionWrapper.innerHTML = `
                    <button class="client-action-btn edit" title="Éditer">✏️</button>
                    <button class="client-action-btn delete" title="Supprimer"
                        data-bs-toggle="modal"
                        data-bs-target="#confirmDeleteModal${id}">
                        🗑️
                    </button>
                `;

                row.classList.remove('editing');
                attachEditLogic();
            });
        });
    });
}
