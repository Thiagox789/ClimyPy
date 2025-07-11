const umbralDesconexionMs = 20 * 1000; // Umbral de desconexión: 20 segundos

        // Función para actualizar datos
        async function actualizarDatos() {
            try {
                const response = await fetch('/data');
                // Si la respuesta no es OK (ej. 401 Unauthorized por login_required), lo manejamos
                if (!response.ok) {
                    if (response.status === 401) {
                         // Si no está autenticado, no hacemos nada con los datos, solo actualizamos el estado
                         // console.log("Usuario no autenticado, no se obtienen datos.");
                         return; // Salimos de la función si no hay autenticación
                    }
                    throw new Error('Error en respuesta del servidor');
                }
                const data = await response.json();

                // Convertir la fecha del dato a un objeto Date para comparar
                const fechaUltimoDato = new Date(data.fecha);
                const ahora = new Date();
                const diferenciaMs = ahora.getTime() - fechaUltimoDato.getTime();

                // --- INICIO DEPURACIÓN (Mantener si aún tienes problemas de desconexión) ---
                console.log("Datos recibidos:", data);
                console.log("Fecha último dato (parseada):", fechaUltimoDato);
                console.log("Tiempo actual:", ahora);
                console.log("Diferencia en ms:", diferenciaMs);
                console.log("Umbral de desconexión:", umbralDesconexionMs);
                // --- FIN DEPURACIÓN ---

                // Determinar el estado del sensor
                let sensorOnline = true; // Variable local para el estado en este ciclo
                if (diferenciaMs < umbralDesconexionMs) {
                    sensorOnline = true;
                } else {
                    sensorOnline = false;
                }

                // Actualizar valores para cada sensor
                for (let i = 1; i <= 5; i++) {
                    const tempKey = `temperatura${i === 1 ? '' : i}`;
                    const humKey = `humedad${i === 1 ? '' : i}`;

                    const tempElement = document.getElementById(`temp${i === 1 ? '' : i}`);
                    const humElement = document.getElementById(`hum${i === 1 ? '' : i}`);
                    const lastUpdateTempElement = document.getElementById(`last-update-temp${i === 1 ? '' : i}`);
                    const lastUpdateHumElement = document.getElementById(`last-update-hum${i === 1 ? '' : i}`);
                    const tempStatusElement = document.getElementById(`temp${i === 1 ? '' : i}-status`);
                    const humStatusElement = document.getElementById(`hum${i === 1 ? '' : i}-status`);

                    if (tempElement) tempElement.textContent = data[tempKey] !== null ? data[tempKey].toFixed(1) : '--';
                    if (humElement) humElement.textContent = data[humKey] !== null ? data[humKey].toFixed(1) : '--';
                    if (lastUpdateTempElement) lastUpdateTempElement.textContent = 'Última actualización: ' + (data.fecha ?? '--');
                    if (lastUpdateHumElement) lastUpdateHumElement.textContent = 'Última actualización: ' + (data.fecha ?? '--');

                    if (sensorOnline) {
                        if (tempStatusElement) {
                            tempStatusElement.className = 'status status-online';
                            tempStatusElement.textContent = 'En línea';
                        }
                        if (humStatusElement) {
                            humStatusElement.className = 'status status-online';
                            humStatusElement.textContent = 'En línea';
                        }
                        if (tempElement) tempElement.classList.add('pulse');
                        if (humElement) humElement.classList.add('pulse');
                    } else {
                        if (tempStatusElement) {
                            tempStatusElement.className = 'status status-offline';
                            tempStatusElement.textContent = 'Desconectado';
                        }
                        if (humStatusElement) {
                            humStatusElement.className = 'status status-offline';
                            humStatusElement.textContent = 'Desconectado';
                        }
                        if (tempElement) tempElement.classList.remove('pulse');
                        if (humElement) humElement.classList.remove('pulse');
                        if (tempElement) tempElement.textContent = '--';
                        if (humElement) humElement.textContent = '--';
                    }
                }

                // Actualizar la temperatura del chip (siempre es solo uno)
                const espTemp = data.temperatura_interna_esp;
                const espTempElement = document.getElementById('esp-temp');
                const lastUpdateEspElement = document.getElementById('last-update-esp');
                const espStatusElement = document.getElementById('esp-status');

                if (espTempElement) espTempElement.textContent = (espTemp !== null && espTemp !== undefined) ? espTemp.toFixed(1) : '--';
                if (lastUpdateEspElement) lastUpdateEspElement.textContent = 'Última actualización: ' + (data.fecha ?? '--');

                if (sensorOnline) {
                    if (espStatusElement) {
                        espStatusElement.className = 'status status-online';
                        espStatusElement.textContent = 'En línea';
                    }
                    if (espTempElement) espTempElement.classList.add('pulse');
                } else {
                    if (espStatusElement) {
                        espStatusElement.className = 'status status-offline';
                        espStatusElement.textContent = 'Desconectado';
                    }
                    if (espTempElement) espTempElement.classList.remove('pulse');
                    if (espTempElement) espTempElement.textContent = '--';
                }

            } catch (error) {
                console.error('Error al obtener datos:', error);
                // Si hay un error, se asume desconexión visualmente para todos los sensores
                for (let i = 1; i <= 5; i++) {
                    const tempElement = document.getElementById(`temp${i === 1 ? '' : i}`);
                    const humElement = document.getElementById(`hum${i === 1 ? '' : i}`);
                    const tempStatusElement = document.getElementById(`temp${i === 1 ? '' : i}-status`);
                    const humStatusElement = document.getElementById(`hum${i === 1 ? '' : i}-status`);

                    if (tempStatusElement) {
                        tempStatusElement.className = 'status status-offline';
                        tempStatusElement.textContent = 'Desconectado';
                    }
                    if (humStatusElement) {
                        humStatusElement.className = 'status status-offline';
                        humStatusElement.textContent = 'Desconectado';
                    }
                    if (tempElement) tempElement.classList.remove('pulse');
                    if (humElement) humElement.classList.remove('pulse');
                    if (tempElement) tempElement.textContent = '--';
                    if (humElement) humElement.textContent = '--';
                }
                // Manejo de error para el chip
                const espTempElement = document.getElementById('esp-temp');
                const espStatusElement = document.getElementById('esp-status');
                if (espStatusElement) {
                    espStatusElement.className = 'status status-offline';
                    espStatusElement.textContent = 'Desconectado';
                }
                if (espTempElement) espTempElement.classList.remove('pulse');
                if (espTempElement) espTempElement.textContent = '--';
            }
        }

        // Menú móvil
        document.querySelector('.hamburger').addEventListener('click', function() {
            document.querySelector('.nav-menu').classList.toggle('active');
        });

        // Navegación suave
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            });
        });

        // Función para controlar la visibilidad de las tarjetas de sensores
        function updateSensorCardVisibility() {
            const selectedDisplaySensor = document.getElementById('sensor-display-select').value;
            const sensorCards = document.querySelectorAll('.sensor-card');
            const savedPreferences = JSON.parse(localStorage.getItem('sensorVisibilityPreferences')) || {};

            sensorCards.forEach(card => {
                const cardClasses = card.classList;
                let isConfiguredVisible = true; // Por defecto, si no hay preferencia guardada, es visible

                // Determinar si la tarjeta debería ser visible según la configuración guardada
                if (cardClasses.contains('sensor-1')) {
                    isConfiguredVisible = savedPreferences['toggle-sensor-1'] !== false;
                } else if (cardClasses.contains('sensor-2')) {
                    isConfiguredVisible = savedPreferences['toggle-sensor-2'] !== false;
                } else if (cardClasses.contains('sensor-3')) {
                    isConfiguredVisible = savedPreferences['toggle-sensor-3'] !== false;
                } else if (cardClasses.contains('sensor-4')) {
                    isConfiguredVisible = savedPreferences['toggle-sensor-4'] !== false;
                } else if (cardClasses.contains('sensor-5')) {
                    isConfiguredVisible = savedPreferences['toggle-sensor-5'] !== false;
                } else if (cardClasses.contains('esp-chip-card')) {
                    isConfiguredVisible = savedPreferences['toggle-esp-chip'] !== false;
                }

                // Aplicar la visibilidad basada en la configuración Y en el selector principal
                let isVisible = false;
                if (isConfiguredVisible) {
                    if (selectedDisplaySensor === 'all') {
                        isVisible = true;
                    } else if (cardClasses.contains(`sensor-${selectedDisplaySensor}`)) {
                        isVisible = true;
                    } else if (selectedDisplaySensor === 'esp-chip' && cardClasses.contains('esp-chip-card')) {
                        isVisible = true;
                    }
                }
                card.style.display = isVisible ? 'block' : 'none';
            });
        }

        // Lógica del Modal de Configuración
        const configModal = document.getElementById('config-modal');
        const openConfigBtn = document.getElementById('open-config-modal');
        const closeConfigBtn = document.querySelector('.close-button');
        const saveConfigBtn = document.getElementById('save-config');
        const sensorCheckboxes = document.querySelectorAll('.sensor-checkboxes input[type="checkbox"]');

        // Abrir modal
        if (openConfigBtn) {
            openConfigBtn.addEventListener('click', () => {
                configModal.style.display = 'flex';
                loadSensorVisibilityPreferences(); // Cargar preferencias al abrir el modal
            });
        }

        // Cerrar modal
        if (closeConfigBtn) {
            closeConfigBtn.addEventListener('click', () => {
                configModal.style.display = 'none';
            });
        }

        // Cerrar modal al hacer clic fuera
        window.addEventListener('click', (event) => {
            if (event.target === configModal) {
                configModal.style.display = 'none';
            }
        });

        // Guardar preferencias
        if (saveConfigBtn) {
            saveConfigBtn.addEventListener('click', () => {
                const preferences = {};
                sensorCheckboxes.forEach(checkbox => {
                    preferences[checkbox.id] = checkbox.checked;
                });
                localStorage.setItem('sensorVisibilityPreferences', JSON.stringify(preferences));
                configModal.style.display = 'none';
                updateSensorCardVisibility(); // Actualizar la visibilidad de las tarjetas
            });
        }

        // Cargar preferencias al inicio
        function loadSensorVisibilityPreferences() {
            const savedPreferences = JSON.parse(localStorage.getItem('sensorVisibilityPreferences'));
            if (savedPreferences) {
                sensorCheckboxes.forEach(checkbox => {
                    if (savedPreferences[checkbox.id] !== undefined) {
                        checkbox.checked = savedPreferences[checkbox.id];
                    }
                });
            }
        }

        // Inicializar
        actualizarDatos();
        loadSensorVisibilityPreferences(); // Cargar preferencias guardadas
        updateSensorCardVisibility(); // Aplicar visibilidad inicial

        // Intervalos de actualización
        setInterval(actualizarDatos, 3000);

        // Añadir listener para el cambio en el selector de visualización de sensores
        document.getElementById('sensor-display-select').addEventListener('change', updateSensorCardVisibility);
