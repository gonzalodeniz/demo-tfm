document.addEventListener('DOMContentLoaded', function() {
    const btnSave = document.getElementById('btn-save');
    const btnNew = document.getElementById('btn-new-student');
    const btnConfirmDelete = document.getElementById('btn-confirm-delete');
    
    // --- Lógica: Nuevo Alumno ---
    if (btnNew) {
        btnNew.addEventListener('click', function(e) {
            if (e) e.preventDefault();
            
            // 1. Quitar selección visual
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

            // 2. Limpiar formulario Y CABECERA
            const nameInput = document.getElementById('student-name');
            if (nameInput) nameInput.value = '';
            
            // --- NUEVO: Limpiar el nombre en la cabecera ---
            const headerName = document.getElementById('header-student-name');
            if (headerName) headerName.textContent = ''; 
            // -----------------------------------------------
            
            // Desmarcar checkboxes
            document.querySelectorAll('.app-checkbox').forEach(cb => cb.checked = false);
            document.querySelectorAll('.service-card').forEach(card => card.classList.remove('selected'));
            
            // Ocultar botón de borrar si está visible
            const btnDeleteTrigger = document.getElementById('btn-delete-modal-trigger');
            if (btnDeleteTrigger) btnDeleteTrigger.style.display = 'none';

            // 3. Obtener siguiente ID
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
                    
                    if (data.next_id) {
                        setTimeout(() => {
                             window.location.href = "/?id=" + data.next_id;
                        }, 500);
                    } else {
                        // Si NO quedan alumnos
                        const listGroup = document.querySelector('.list-group');
                        if (listGroup) listGroup.innerHTML = '';
                        
                        // Esto dispara el evento click de arriba, que ahora limpia la cabecera
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

            // Actualización visual inmediata (opcional, mejora UX)
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