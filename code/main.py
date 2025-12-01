from sistema_transporte import SistemaTransporte
from cliente import Cliente

if __name__ == "__main__":
    # Instanciar el Sistema
    sistema = SistemaTransporte()

    # Crear Clientes
    admin = Cliente("admin@metro.com", "ID01", True)
    usuario = Cliente("usuario@gmail.com", "ID02", False)

    # Suscribir
    sistema.suscribir_usuario(usuario, "Mantenimiento")
    sistema.suscribir_usuario(admin, "Mantenimiento")

    # Cargar y ejecutar
    sistema.carga_datos("datos.csv")
    sistema.detectar_y_notificar()

    # Ver gráficas (cerrar la ventana de la gráfica para que el programa termine)
    sistema.ver_estadisticas(admin)
