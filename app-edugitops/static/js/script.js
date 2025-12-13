document.addEventListener('DOMContentLoaded', function() {
    const btnSave = document.getElementById('btn-save');
    const toastEl = document.getElementById('toast-message');
    
    if (btnSave) {
        btnSave.addEventListener('click', function() {
            // 1. Recoger datos
            const studentIdInput = document.getElementById('student-id');
            const studentNameInput = document.getElementById('student-name');
            
            // Protección por si no hay alumno cargado
            if (!studentIdInput || !studentNameInput) return;

            const studentId = studentIdInput.value;
            const studentName = studentNameInput.value;
            
            const checkedBoxes = document.querySelectorAll('.app-checkbox:checked');
            const selectedApps = Array.from(checkedBoxes).map(cb => cb.value);

            // 2. Validación Frontend
            if (!studentName.trim()) {
                showToast('Error', 'El nombre del alumno no puede estar vacío.', false);
                return;
            }

            // 3. Enviar datos al servidor
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
                    showToast('Guardado', data.message, true);
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

    function showToast(title, message, isSuccess) {
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
        // Hack para permitir transición CSS
        setTimeout(() => { toastEl.style.opacity = '1'; }, 10);
        
        // Temporizador para desaparecer
        setTimeout(() => {
            toastEl.style.opacity = '0';
            setTimeout(() => { toastEl.style.display = 'none'; }, 1000);
        }, 5000);
    }
});