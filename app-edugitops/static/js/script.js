document.addEventListener('DOMContentLoaded', function() {
    const btnSave = document.getElementById('btn-save');
    const btnNew = document.getElementById('btn-new-student');
    const btnConfirmDelete = document.getElementById('btn-confirm-delete');
    const searchInput = document.getElementById('search-input');

    // --- LÓGICA DE BÚSQUEDA Y PERSISTENCIA ---
    if (searchInput) {
        // 1. Restaurar búsqueda anterior si existe (Persistencia al navegar)
        const savedSearch = sessionStorage.getItem('edu_search_term');
        if (savedSearch) {
            searchInput.value = savedSearch;
        }

        // 2. Evento de filtrado
        searchInput.addEventListener('input', function() {
            const filterValue = this.value.toLowerCase();
            
            // Guardar en sesión para que no se pierda al recargar la página (navegar)
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

        // 3. Aplicar el filtro visualmente al cargar si se restauró texto
        if (savedSearch) {
            searchInput.dispatchEvent(new Event('input'));
        }
    }

    // Función auxiliar para resetear el buscador y limpiar la persistencia
    function resetSearch() {
        if (searchInput) {
            searchInput.value = '';
            // Esto limpiará también el sessionStorage gracias al evento 'input'
            searchInput.dispatchEvent(new Event('input'));
        }
    }

    // --- Lógica: Nuevo Alumno ---
    if (btnNew) {
        btnNew.addEventListener('click', function(e) {
            if (e) e.preventDefault();
            
            // Limpiar Buscador (Requisito: borrar al pulsar Nuevo)
            resetSearch();

            // Quitar selección visual
            document.querySelectorAll('.active-student-card').forEach(el => {
                el.classList.remove('active-student-card');
                el.classList.add('bg-light', 'border-0');
                const icon = el.querySelector('.avatar-placeholder');
                if (icon) {
                    icon.classList.remove('text-primary');
                    icon.classList.add('text-secondary');
                }
                const smallText = el.querySelector('small');
                if (smallText) {
                    smallText.classList.remove('text-dark');
                    smallText.classList.add('text-muted');
                }
            });

            // Limpiar formulario y cabecera
            const nameInput = document.getElementById('student-name');
            if (nameInput) nameInput.value = '';
            
            const headerName = document.getElementById('header-student-name');
            if (headerName) headerName.textContent = ''; 
            
            document.querySelectorAll('.app-checkbox').forEach(cb => cb.checked = false);
            document.querySelectorAll('.service-card').forEach(card => card.classList.remove('selected'));
            
            const btnDeleteTrigger = document.getElementById('btn-delete-modal-trigger');
            if (btnDeleteTrigger) btnDeleteTrigger.style.display = 'none';

            fetch('/next_id')
                .then(res => res.json())
                .then(data => {
                    const idInput = document.getElementById('student-id');
                    if (idInput) idInput.value = data.next_id;
                })
                .catch(err => console.error("Error obteniendo ID:", err));
            
            window.history.pushState({}, "", "/");
        });
    }

    // --- Lógica: Borrar Alumno ---
    if (btnConfirmDelete) {
        btnConfirmDelete.addEventListener('click', function() {
            const studentId = document.getElementById('student-id').value;
            
            const modalEl = document.getElementById('deleteModal');
            const modalInstance = bootstrap.Modal.getInstance(modalEl);
            modalInstance.hide();

            fetch('/delete_student', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: studentId })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast('Eliminado', data.message, true);
                    
                    // Limpiar buscador al borrar (Requisito)
                    resetSearch();

                    if (data.next_id) {
                        setTimeout(() => {
                             window.location.href = "/?id=" + data.next_id;
                        }, 500);
                    } else {
                        const listGroup = document.querySelector('.list-group');
                        if (listGroup) listGroup.innerHTML = '';
                        if (btnNew) btnNew.click();
                    }
                } else {
                    showToast('Error', data.message, false);
                }
            })
            .catch(err => showToast('Error', 'Error de conexión', false));
        });
    }

    // --- Lógica: Guardar ---
    if (btnSave) {
        btnSave.addEventListener('click', function() {
            const studentId = document.getElementById('student-id').value;
            const studentName = document.getElementById('student-name').value;
            
            const checkedBoxes = document.querySelectorAll('.app-checkbox:checked');
            const selectedApps = Array.from(checkedBoxes).map(cb => cb.value);

            if (!studentName.trim()) {
                showToast('Error', 'El nombre del alumno no puede estar vacío.', false);
                return;
            }

            const headerName = document.getElementById('header-student-name');
            if (headerName) headerName.textContent = studentName;

            fetch('/save_student', {
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
                    showToast('Éxito', data.message, true);
                    
                    // Limpiar buscador al guardar (Requisito)
                    resetSearch();

                    setTimeout(() => {
                        window.location.href = "/?id=" + studentId;
                    }, 1000);
                } else {
                    showToast('Error', data.message, false);
                }
            })
            .catch(error => {
                showToast('Error', 'No se pudo conectar con el servidor.', false);
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