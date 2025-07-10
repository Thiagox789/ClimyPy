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

                // Actualizar valores principales
                document.getElementById('temp').textContent = data.temperatura ?? '--';
                document.getElementById('hum').textContent = data.humedad ?? '--';
                document.getElementById('last-update-temp').textContent =
                    'Última actualización: ' + (data.fecha ?? '--');
                document.getElementById('last-update-hum').textContent =
                    'Última actualización: ' + (data.fecha ?? '--');

                // Nuevo: Actualizar la temperatura del chip
                const espTemp = data.temperatura_interna_esp;
                document.getElementById('esp-temp').textContent = (espTemp !== null && espTemp !== undefined) ? espTemp.toFixed(1) : '--';
                document.getElementById('last-update-esp').textContent = 'Última actualización: ' + (data.fecha ?? '--');

                // Actualizar estados visuales
                const tempStatusElement = document.getElementById('temp-status');
                const humStatusElement = document.getElementById('hum-status');
                const tempValueElement = document.getElementById('temp');
                const humValueElement = document.getElementById('hum');

                // Nuevo: Elementos de la tarjeta del chip
                const espStatusElement = document.getElementById('esp-status');
                const espValueElement = document.getElementById('esp-temp');

                if (sensorOnline) {
                    tempStatusElement.className = 'status status-online';
                    tempStatusElement.textContent = 'En línea';
                    humStatusElement.className = 'status status-online';
                    humStatusElement.textContent = 'En línea';
                    tempValueElement.classList.add('pulse'); // Añadir animación si está en línea
                    humValueElement.classList.add('pulse'); // Añadir animación si está en línea
                    // Nuevo: Estado para el chip
                    espStatusElement.className = 'status status-online';
                    espStatusElement.textContent = 'En línea';
                    espValueElement.classList.add('pulse');
                } else {
                    tempStatusElement.className = 'status status-offline';
                    tempStatusElement.textContent = 'Desconectado';
                    humStatusElement.className = 'status status-offline';
                    humStatusElement.textContent = 'Desconectado';
                    tempValueElement.classList.remove('pulse'); // Quitar animación si está desconectado
                    humValueElement.classList.remove('pulse'); // Quitar animación si está desconectado
                    document.getElementById('temp').textContent = '--'; // Mostrar -- si está desconectado
                    document.getElementById('hum').textContent = '--';     // Mostrar -- si está desconectado
                    // Nuevo: Estado para el chip
                    espStatusElement.className = 'status status-offline';
                    espStatusElement.textContent = 'Desconectado';
                    espValueElement.classList.remove('pulse');
                    document.getElementById('esp-temp').textContent = '--';
                }

            } catch (error) {
                console.error('Error al obtener datos:', error);
                // Si hay un error (ej. red, servidor no responde, o 401), se asume desconexión visualmente
                document.getElementById('temp-status').className = 'status status-offline';
                document.getElementById('temp-status').textContent = 'Desconectado';
                document.getElementById('hum-status').className = 'status status-offline';
                document.getElementById('hum-status').textContent = 'Desconectado';
                document.getElementById('temp').classList.remove('pulse');
                document.getElementById('hum').classList.remove('pulse');
                document.getElementById('temp').textContent = '--';
                document.getElementById('hum').textContent = '--';
                // Nuevo: Manejo de error para el chip
                document.getElementById('esp-status').className = 'status status-offline';
                document.getElementById('esp-status').textContent = 'Desconectado';
                document.getElementById('esp-temp').classList.remove('pulse');
                document.getElementById('esp-temp').textContent = '--';
            }
        }

        async function obtenerEstadisticas() {
            try {
                const response = await fetch('/status');
                if (!response.ok) {
                    if (response.status === 401) return; // No hacer nada si no está autenticado
                    throw new Error('Error en respuesta de estadísticas');
                }
                const data = await response.json();
                document.getElementById('total-records').textContent = data.total_records;
                document.getElementById('uptime').textContent = data.uptime;
                document.getElementById('avg-temp').textContent = data.average_temperature_last_24h + '°C';
                document.getElementById('avg-hum').textContent = data.average_humidity_last_24h + '%';
            } catch (error) {
                console.error('Error al obtener estadísticas:', error);
                document.getElementById('total-records').textContent = '--';
                document.getElementById('uptime').textContent = '--';
                document.getElementById('avg-temp').textContent = '--';
                document.getElementById('avg-hum').textContent = '--';
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

        // Inicializar
        actualizarDatos();
        obtenerEstadisticas();

        // Intervalos de actualización
        setInterval(actualizarDatos, 3000);
        setInterval(obtenerEstadisticas, 30000); // Estadísticas actualizadas cada 30 segundos