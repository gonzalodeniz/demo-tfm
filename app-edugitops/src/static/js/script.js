document.addEventListener('DOMContentLoaded', function() {
    const btnSave = document.getElementById('btn-save');
    const btnNew = document.getElementById('btn-new-student');
    const btnConfirmDelete = document.getElementById('btn-confirm-delete');
    const btnPush = document.getElementById('btn-git-push');
    const searchInput = document.getElementById('search-input');

    // --- FUNCIÓN REUTILIZABLE DE GUARDADO ---
    // Retorna una Promesa para poder encadenar el Push después
    function performSave(showSuccessToast = true) {
        const studentId = document.getElementById('student-id').value;
        
        // CORRECCIÓN: Definimos 'nameInput' aquí para poder usarlo después
        const nameInput = document.getElementById('student-name'); 
        
        // Ahora obtenemos el valor usándolo (si existe)
        const studentName = nameInput ? nameInput.value : '';
        
        const checkedBoxes = document.querySelectorAll('.app-checkbox:checked');
        const selectedApps = Array.from(checkedBoxes).map(cb => cb.value);

        if (!studentName.trim()) {
            showToast('Error', 'El nombre del alumno no puede estar vacío.', false);
            return Promise.reject('Validation Error');
        }

        const headerName = document.getElementById('header-student-name');
        if (headerName) headerName.textContent = studentName;

        return fetch('/save_student', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: studentId,
                nombre: studentName,
                apps: selectedApps
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (showSuccessToast) showToast('Guardado', data.message, true);
                // Si se guarda bien, quitamos el color de fondo
                if (nameInput) nameInput.classList.remove('input-highlight');
                resetSearch(); // Limpiar buscador
                return data; // Resolvemos promesa con éxito
            } else {
                showToast('Error Guardado', data.message, false);
                throw new Error(data.message); // Rechazamos promesa
            }
        });
    }

    // --- BÚSQUEDA Y PERSISTENCIA ---
    if (searchInput) {
        const savedSearch = sessionStorage.getItem('edu_search_term');
        if (savedSearch) searchInput.value = savedSearch;

        searchInput.addEventListener('input', function() {
            const filterValue = this.value.toLowerCase();
            sessionStorage.setItem('edu_search_term', this.value);
            const studentItems = document.querySelectorAll('.student-item');

            studentItems.forEach(item => {
                const nameText = item.querySelector('.student-name').textContent.toLowerCase();
                const idText = item.querySelector('.student-id').textContent.toLowerCase();
                if (nameText.includes(filterValue) || idText.includes(filterValue)) {
                    item.classList.remove('d-none');
                    item.style.display = ''; 
                } else {
                    item.classList.add('d-none');
                }
            });
        });

        if (savedSearch) searchInput.dispatchEvent(new Event('input'));
    }

    function resetSearch() {
        if (searchInput) {
            searchInput.value = '';
            searchInput.dispatchEvent(new Event('input'));
        }
    }

    // --- EVENTO: NUEVO ALUMNO ---
    if (btnNew) {
        btnNew.addEventListener('click', function(e) {
            e.preventDefault();
            resetSearch();

            document.querySelectorAll('.active-student-card').forEach(el => {
                el.classList.remove('active-student-card');
                el.classList.add('bg-light', 'border-0');
                el.querySelector('.avatar-placeholder')?.classList.replace('text-primary', 'text-secondary');
                el.querySelector('small')?.classList.replace('text-dark', 'text-muted');
            });

            const nameInput = document.getElementById('student-name');
            if (nameInput) {
                nameInput.value = '';
                nameInput.classList.add('input-highlight'); // Añadimos color
                nameInput.focus(); // Ponemos el cursor dentro automáticamente
            }
            const headerName = document.getElementById('header-student-name');
            if (headerName) headerName.textContent = ''; 
            
            document.querySelectorAll('.app-checkbox').forEach(cb => cb.checked = false);
            document.querySelectorAll('.service-card').forEach(card => card.classList.remove('selected'));
            
            const btnDeleteTrigger = document.getElementById('btn-delete-modal-trigger');
            if (btnDeleteTrigger) btnDeleteTrigger.style.display = 'none';

            fetch('/next_id')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('student-id').value = data.next_id;
                })
                .catch(err => console.error("Error ID:", err));
            
            window.history.pushState({}, "", "/");
        });
    }

    // --- EVENTO: GUARDAR ---
    if (btnSave) {
        btnSave.addEventListener('click', function() {
            performSave(true).then(() => {
                // Solo redireccionamos si es un guardado normal (sin push inmediato)
                setTimeout(() => {
                    const id = document.getElementById('student-id').value;
                    window.location.href = "/?id=" + id;
                }, 1000);
            }).catch(err => console.error(err));
        });
    }

    // --- EVENTO: GUARDAR + PUSH ---
    if (btnPush) {
        btnPush.addEventListener('click', function() {
            const originalText = btnPush.innerHTML;
            btnPush.disabled = true;
            btnPush.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Guardando...';

            // 1. PRIMERO GUARDAMOS
            performSave(false) // false para no mostrar toast de guardado, solo el final
            .then(() => {
                // 2. SI EL GUARDADO FUE BIEN, HACEMOS PUSH
                btnPush.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Subiendo a Git...';
                
                return fetch('/git_push', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: "Update via Save+Push Button" })
                });
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast('Todo Listo', 'Guardado y subido a Gitea correctamente.', true);
                    // Opcional: Recargar para asegurar estado
                    setTimeout(() => {
                        const id = document.getElementById('student-id').value;
                        window.location.href = "/?id=" + id;
                    }, 1500);
                } else {
                    showToast('Error Git', 'Guardado OK, pero falló Push: ' + data.message, false);
                }
            })
            .catch(err => {
                // Si falló el guardado o la red
                console.error(err);
                if (err.message !== 'Validation Error') { // El error de validación ya mostró su toast
                     showToast('Error', 'Proceso interrumpido.', false);
                }
            })
            .finally(() => {
                btnPush.disabled = false;
                btnPush.innerHTML = originalText;
            });
        });
    }

    // --- EVENTO: BORRAR ---
    if (btnConfirmDelete) {
        btnConfirmDelete.addEventListener('click', function() {
            const studentId = document.getElementById('student-id').value;
            bootstrap.Modal.getInstance(document.getElementById('deleteModal')).hide();

            fetch('/delete_student', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: studentId })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast('Eliminado', data.message, true);
                    resetSearch();
                    if (data.next_id) {
                        setTimeout(() => window.location.href = "/?id=" + data.next_id, 500);
                    } else {
                        document.querySelector('.list-group').innerHTML = '';
                        if (btnNew) btnNew.click();
                    }
                } else {
                    showToast('Error', data.message, false);
                }
            });
        });
    }
    
    // Helpers visuales
    document.querySelectorAll('.app-checkbox').forEach(cb => {
        cb.addEventListener('change', function() {
            const card = this.closest('.service-card');
            if (this.checked) card.classList.add('selected');
            else card.classList.remove('selected');
        });
    });

    function showToast(title, message, isSuccess) {
        const toastEl = document.getElementById('toast-message');
        const toastTitle = document.getElementById('toast-title');
        const toastBody = document.getElementById('toast-body');
        const toastIcon = document.getElementById('toast-icon');
        if (!toastEl) return;

        toastTitle.textContent = title + ':';
        toastBody.textContent = message;
        if (isSuccess) {
            toastEl.style.backgroundColor = '#198754';
            toastIcon.className = 'bi bi-check-circle-fill fs-4 me-3';
        } else {
            toastEl.style.backgroundColor = '#dc3545';
            toastIcon.className = 'bi bi-exclamation-triangle-fill fs-4 me-3';
        }
        toastEl.style.display = 'flex';
        void toastEl.offsetWidth; 
        toastEl.style.opacity = '1';
        setTimeout(() => {
            toastEl.style.opacity = '0';
            setTimeout(() => { toastEl.style.display = 'none'; }, 1000);
        }, 5000);
    }
});