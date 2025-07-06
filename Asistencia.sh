#!/bin/bash

# Este script gestiona el servicio systemd de ClimyPy

SERVICE_NAME="climypy.service"

show_menu() {
    clear
    echo "========================================"
    echo "      Gestión de Servicio ClimyPy       "
    echo "========================================"
    echo "1. Ver estado del servicio"
    echo "2. Iniciar el servicio"
    echo "3. Detener el servicio"
    echo "4. Salir"
    echo "----------------------------------------"
    echo -n "Elige una opción: "
}

main_loop() {
    while true; do
        show_menu
        read -r choice
        echo "" # Salto de línea para mejor legibilidad

        case $choice in
            1)
                echo "Mostrando estado de $SERVICE_NAME..."
                sudo systemctl status "$SERVICE_NAME"
                echo ""
                read -n 1 -s -r -p "Presiona cualquier tecla para continuar..."
                ;;
            2)
                echo "Iniciando $SERVICE_NAME..."
                sudo systemctl start "$SERVICE_NAME"
                if [ $? -eq 0 ]; then
                    echo "Servicio $SERVICE_NAME iniciado correctamente."
                else
                    echo "Error al iniciar el servicio $SERVICE_NAME. Revisa los logs."
                fi
                echo ""
                read -n 1 -s -r -p "Presiona cualquier tecla para continuar..."
                ;;
            3)
                echo "Deteniendo $SERVICE_NAME..."
                sudo systemctl stop "$SERVICE_NAME"
                if [ $? -eq 0 ]; then
                    echo "Servicio $SERVICE_NAME detenido correctamente."
                else
                    echo "Error al detener el servicio $SERVICE_NAME."
                fi
                echo ""
                read -n 1 -s -r -p "Presiona cualquier tecla para continuar..."
                ;;
            4)
                echo "Saliendo del script. ¡Adiós!"
                exit 0
                ;;
            *)
                echo "Opción inválida. Por favor, selecciona un número del 1 al 4."
                echo ""
                read -n 1 -s -r -p "Presiona cualquier tecla para continuar..."
                ;;
        esac
    done
}

# Ejecutar el bucle principal
main_loop