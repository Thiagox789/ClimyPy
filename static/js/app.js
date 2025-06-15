async function actualizarDatos() {
    try {
      const response = await fetch('/data');
      if (!response.ok) throw new Error('Error en respuesta');
      const data = await response.json();
  
      document.getElementById('temp').textContent = data.temperatura ?? '--';
      document.getElementById('hum').textContent = data.humedad ?? '--';
      document.getElementById('time').textContent = 'Actualizado: ' + (data.fecha ?? '--');
    } catch (error) {
      console.error('Error al obtener datos:', error);
    }
  }
  
  setInterval(actualizarDatos, 2000);
  actualizarDatos();
  