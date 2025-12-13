document.addEventListener('DOMContentLoaded', function() {
    const btnSave = document.getElementById('btn-save');
    const btnNew = document.getElementById('btn-new-student');
    
    // --- Lógica: Nuevo Alumno ---
    if (btnNew) {
        btnNew.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 1. Quitar selección visual de la lista
            document.querySelectorAll('.active-student-card').forEach(el => {
                el.classList.remove('active-student-card');
                el.classList.add('bg-light', 'border-0');
                // Ajustar iconos
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

            // 2. Limpiar formulario
            const nameInput = document.getElementById('student-name');
            if (nameInput) nameInput.value = '';
            
            // Desmarcar todos los checkboxes
            document.querySelectorAll('.app-checkbox').forEach(cb => cb.checked = false);
            
            // Quitar clase 'selected' de las tarjetas de servicio
            document.querySelectorAll('.service-card').forEach(card => card.classList.remove('selected'));

            // 3. Obtener siguiente ID del servidor
            fetch('/next_id')
                .then(res => res.json())
                .then(data => {
                    const idInput = document.getElementById('student-id');
                    if (idInput) idInput.value = data.next_id;
                })
                .catch(err => console.error("Error obteniendo ID:", err));
        });
    }

    // --- Lógica: Guardar (Crear o Actualizar) ---
    if (btnSave) {
        btnSave.addEventListener('click', function() {
            const studentId = document.getElementById('student-id').value;
            const studentName = document.getElementById('student-name').value;
            
            const checkedBoxes = document.querySelectorAll('.app-checkbox:checked');
            const selectedApps = Array.from(checkedBoxes).map(cb => cb.value);

            // Validar nombre vacío
            if (!studentName.trim()) {
                showToast('Error', 'El nombre del alumno no puede estar vacío.', false);
                return;
            }

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
                    // Opcional: Recargar para ver el nuevo alumno en la lista tras un breve delay
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showToast('Error', data.message, false);
                }
            })
            .catch(error => {
                showToast('Error', 'No se pudo conectar con el servidor.', false);
                console.error('Error:', error);
            });
        });
    }
    
    // Lógica visual para checkboxes (para colorear la tarjeta al hacer click)
    document.querySelectorAll('.app-checkbox').forEach(cb => {
        cb.addEventListener('change', function() {
            const card = this.closest('.service-card');
            if (this.checked) {
                card.classList.add('selected');
            } else {
                card.classList.remove('selected');
            }
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
        setTimeout(() => { toastEl.style.opacity = '1'; }, 10);
        
        setTimeout(() => {
            toastEl.style.opacity = '0';
            setTimeout(() => { toastEl.style.display = 'none'; }, 1000);
        }, 5000);
    }
});