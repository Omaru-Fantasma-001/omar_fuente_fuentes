"""
Proyecto Integrador de Python – Sistema de Inventario y Ventas
Autores:  <tu nombre o equipo>
Descripción:
  - Inventario (agregar / actualizar / listar / bajo stock)
  - Ventas con ticket (fecha‑hora, total)
  - Inicio de sesión con log
Requisitos: Python 3.x – sin librerías externas
"""

import datetime
import os
import json
import csv
from colorama import init, Fore, Style
init(autoreset=True)
import sys

# --- Tecla rápida multiplataforma ---
try:
    import msvcrt
    def leer_tecla():
        return msvcrt.getch().decode("utf-8")
except ImportError:
    import tty, termios
    def leer_tecla():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

# --- Rutas absolutas ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INVENTARIO_FILE = os.path.join(BASE_DIR, "inventario.json")
VENTAS_FILE = os.path.join(BASE_DIR, "registro_ventas.txt")
USUARIOS_FILE = os.path.join(BASE_DIR, "usuarios.json")
CAJA_FILE = os.path.join(BASE_DIR, "caja.json")
VENTAS_CSV = os.path.join(BASE_DIR, "ventas.csv")
LOG_FILE = os.path.join(BASE_DIR, "bitacora_sesiones.txt")
CLIENTES_FILE = os.path.join(BASE_DIR, "clientes.json")

# ---------------- utilidades y presentación ---------------- #

def limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")

def encabezado_principal():
    limpiar_pantalla()
    print(Fore.CYAN + "="*50)
    print(Fore.CYAN + "💵  SISTEMA DE CAJA E INVENTARIO  💵".center(50))
    print(Fore.CYAN + "="*50)
    print(Fore.CYAN + "Ingrese el número de la opción deseada. Para salir, elija 'Salir'.")

def bienvenida():
    print(Fore.CYAN + "\n¡Bienvenido al sistema de caja!")

def despedida():
    print(Fore.CYAN + "\nGracias por usar el sistema. ¡Hasta luego!")

def mostrar_manual():
    limpiar_pantalla()
    print(Fore.CYAN + "="*50)
    print(Fore.CYAN + "📖  MANUAL DE USUARIO  📖".center(50))
    print(Fore.CYAN + "="*50)
    print("""
Bienvenido al Sistema de Caja e Inventario.

Navegación:
- Usa los números del menú para seleccionar una opción.
- Puedes usar las teclas rápidas (por ejemplo, presiona '1' para agregar producto).
- Sigue las instrucciones en pantalla para cada operación.

Opciones principales:
1. Agregar producto: Añade un nuevo producto al inventario.
2. Listar productos: Muestra todos los productos registrados.
3. Actualizar stock: Cambia la cantidad disponible de un producto.
4. Modificar producto: Cambia el nombre o precio de un producto.
5. Productos con stock bajo: Muestra productos con poco stock.
6. Registrar venta: Realiza una venta y descuenta del inventario.
7. Reporte de ventas: Accede a reportes y estadísticas.
8. Eliminar producto (solo admin): Borra un producto del inventario.
9. Registrar usuario (solo admin): Crea nuevos usuarios.
0. Salir: Cierra el sistema.

Consejos:
- Los cambios quedan guardados automáticamente.
- Si tienes dudas, consulta este manual desde el menú principal.
""")
    input(Fore.YELLOW + "\nPresiona Enter para volver al menú principal...")

def timestamp():
    """Devuelve fecha y hora actual en string ISO (YYYY‑MM‑DD HH:MM:SS)."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def escribir_log(linea, ruta):
    """Agrega la línea al archivo indicado (creándolo si no existe)."""
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(linea + "\n")

def escribir_log_evento(evento, detalle=""):
    """Registra un evento con fecha y hora en el archivo de bitácora."""
    momento = timestamp()
    linea = f"{momento} | {evento}"
    if detalle:
        linea += f" | {detalle}"
    escribir_log(linea, LOG_FILE)

def exportar_ventas_csv(ventas):
    with open(VENTAS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Fecha", "Producto", "Cantidad", "Subtotal"])
        for venta in ventas:
            for item in venta["items"]:
                writer.writerow([venta["fecha"], item["nombre"], item["cantidad"], f"{item['subtotal']:.2f}"])

# ---------------- datos en memoria y persistencia ---------------- #

inventario = []        # cada item: {"id": int, "nombre": str, "precio": float, "stock": int}
siguiente_id = 1
ventas = []           # cada venta: {"fecha": str, "items": [{"nombre": str, "cantidad": int, "subtotal": float}], "total": float}
usuarios = []         # cada usuario: {"nombre": str, "password": str, "rol": str}
clientes = []         # cada cliente: {"nombre": str, "proxima_visita": str}

def guardar_inventario():
    with open(INVENTARIO_FILE, "w", encoding="utf-8") as f:
        json.dump({"inventario": inventario, "siguiente_id": siguiente_id}, f, ensure_ascii=False, indent=2)

def cargar_inventario():
    global inventario, siguiente_id
    if os.path.exists(INVENTARIO_FILE):
        try:
            with open(INVENTARIO_FILE, "r", encoding="utf-8") as f:
                datos = json.load(f)
                inventario = datos.get("inventario", [])
                siguiente_id = datos.get("siguiente_id", 1)
        except Exception as e:
            print("Error al cargar el inventario. Se iniciará vacío.")
            inventario = []
            siguiente_id = 1

def guardar_ventas():
    with open(VENTAS_FILE, "w", encoding="utf-8") as f:
        json.dump(ventas, f, ensure_ascii=False, indent=2)

def cargar_ventas():
    global ventas
    if os.path.exists(VENTAS_FILE):
        try:
            with open(VENTAS_FILE, "r", encoding="utf-8") as f:
                ventas = json.load(f)
        except Exception:
            ventas = []

def guardar_usuarios():
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=2)

def cargar_usuarios():
    global usuarios
    if os.path.exists(USUARIOS_FILE):
        try:
            with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
                usuarios = json.load(f)
        except Exception:
            usuarios = []
    else:
        usuarios = [{"nombre": "admin", "password": "admin", "rol": "admin"}]
        guardar_usuarios()

def guardar_clientes():
    with open(CLIENTES_FILE, "w", encoding="utf-8") as f:
        json.dump(clientes, f, ensure_ascii=False, indent=2)

def cargar_clientes():
    global clientes
    if os.path.exists(CLIENTES_FILE):
        with open(CLIENTES_FILE, "r", encoding="utf-8") as f:
            clientes = json.load(f)

# ---------------- funciones de clientes ---------------- #

def registrar_cliente():
    nombre = input("Nombre del cliente: ").strip()
    if not nombre:
        print("Nombre no válido.")
        return
    proxima_visita = input("¿Cuándo volverá a comprar? (YYYY-MM-DD): ").strip()
    clientes.append({"nombre": nombre, "proxima_visita": proxima_visita})
    guardar_clientes()
    print(Fore.GREEN + "Cliente registrado correctamente.")

def proximas_visitas():
    cargar_clientes()
    if not clientes:
        print("No hay clientes registrados.")
        return
    print("\n--- Próximas visitas de clientes ---")
    for c in clientes:
        print(f"{c['nombre']} volverá el {c['proxima_visita']}")

# ---------------- gestión de usuarios ---------------- #

def registrar_usuario():
    print("\n--- Registrar nuevo usuario ---")
    nombre = input("Nombre de usuario: ").strip()
    if not nombre or any(u["nombre"] == nombre for u in usuarios):
        print("Nombre inválido o ya existe.")
        return
    password = input("Contraseña: ").strip()
    rol = input("Rol (admin/cajero): ").strip().lower()
    if rol not in ("admin", "cajero"):
        print("Rol inválido.")
        return
    usuarios.append({"nombre": nombre, "password": password, "rol": rol})
    guardar_usuarios()
    print("Usuario registrado correctamente.")

def autenticar_usuario():
    print("="*40)
    print("      SISTEMA DE INVENTARIO Y VENTAS      ")
    print("="*40)
    for _ in range(3):
        nombre = input("Nombre de usuario: ").strip()
        password = input("Contraseña: ").strip()
        usuario = next((u for u in usuarios if u["nombre"] == nombre and u["password"] == password), None)
        if usuario:
            escribir_log_evento("Login", f"Usuario: {nombre} | Rol: {usuario['rol']}")
            print(f"\n¡Bienvenido, {nombre}! Sesión iniciada a las {timestamp()} (Rol: {usuario['rol']})\n")
            return usuario
        print("Usuario o contraseña incorrectos.")
    print("Demasiados intentos fallidos. Saliendo.")
    exit()

def cerrar_sesion(usuario):
    escribir_log_evento("Logout", f"Usuario: {usuario['nombre']} | Rol: {usuario['rol']}")
    print(f"Sesión cerrada para {usuario['nombre']} a las {timestamp()}.")

# ---------------- funciones de inventario ---------------- #

def agregar_producto():
    global siguiente_id
    nombre = input("Nombre del producto: ").strip()
    if not nombre:
        print("Operación cancelada.")
        return
    while True:
        try:
            precio = float(input("Precio unitario: $"))
            if precio < 0:
                print("El precio debe ser positivo.")
                continue
            break
        except ValueError:
            print("Ingrese un número válido para el precio.")
    while True:
        try:
            stock = int(input("Cantidad inicial: "))
            if stock < 0:
                print("El stock debe ser positivo.")
                continue
            break
        except ValueError:
            print("Ingrese un número válido para el stock.")
    inventario.append({"id": siguiente_id, "nombre": nombre, "precio": precio, "stock": stock})
    escribir_log_evento("Alta producto", f"{nombre} | Precio: ${precio:.2f} | Stock: {stock}")
    siguiente_id += 1
    print(Fore.GREEN + "✔ Producto agregado correctamente.")
    guardar_inventario()

def listar_productos():
    if not inventario:
        print(Fore.YELLOW + "Inventario vacío.")
        return
    print(Style.BRIGHT + f"+{'-'*4}+{'-'*18}+{'-'*10}+{'-'*8}+")
    print(f"| {'ID':^2} | {'Nombre':^15} | {'Precio':^7} | {'Stock':^5} |")
    print(f"+{'-'*4}+{'-'*18}+{'-'*10}+{'-'*8}+")
    for p in inventario:
        print(f"| {p['id']:^2} | {p['nombre']:<15} | ${p['precio']:<7.2f} | {p['stock']:^5} |")
    print(f"+{'-'*4}+{'-'*18}+{'-'*10}+{'-'*8}+" )

def actualizar_stock():
    listar_productos()
    if not inventario:
        return
    while True:
        pid_str = input("\nID del producto a modificar (Enter para cancelar): ").strip()
        if pid_str == "":
            print("Operación cancelada.")
            return
        if not pid_str.isdigit():
            print("Ingrese un ID válido (número).")
            continue
        pid = int(pid_str)
        producto = next((p for p in inventario if p["id"] == pid), None)
        if not producto:
            print("ID no encontrado.")
            continue
        while True:
            nuevo_str = input("Nuevo stock (Enter para cancelar): ").strip()
            if nuevo_str == "":
                print("Operación cancelada.")
                return
            if not nuevo_str.isdigit():
                print("Ingrese un número válido para el stock.")
                continue
            nuevo = int(nuevo_str)
            if nuevo < 0:
                print("El stock debe ser positivo.")
                continue
            confirm = input(f"¿Seguro que desea cambiar el stock de {producto['nombre']} de {producto['stock']} a {nuevo}? (s/n): ").strip().lower()
            if confirm != "s":
                print("Operación cancelada.")
                return
            escribir_log_evento("Actualización stock", f"{producto['nombre']} | Antes: {producto['stock']} | Ahora: {nuevo}")
            producto["stock"] = nuevo
            print("Stock actualizado.")
            guardar_inventario()
            return

def modificar_producto():
    listar_productos()
    if not inventario:
        return
    pid_str = input("\nID del producto a modificar (Enter para cancelar): ").strip()
    if pid_str == "":
        print("Operación cancelada.")
        return
    if not pid_str.isdigit():
        print("Ingrese un ID válido (número).")
        return
    pid = int(pid_str)
    producto = next((p for p in inventario if p["id"] == pid), None)
    if not producto:
        print("ID no encontrado.")
        return
    print(f"Modificando '{producto['nombre']}' (Precio: ${producto['precio']:.2f})")
    nuevo_nombre = input("Nuevo nombre (Enter para mantener): ").strip()
    if nuevo_nombre:
        confirm = input(f"¿Seguro que desea cambiar el nombre a '{nuevo_nombre}'? (s/n): ").strip().lower()
        if confirm == "s":
            escribir_log_evento("Cambio nombre", f"{producto['nombre']} -> {nuevo_nombre}")
            producto["nombre"] = nuevo_nombre
    while True:
        nuevo_precio = input("Nuevo precio (Enter para mantener): ").strip()
        if nuevo_precio == "":
            break
        try:
            precio = float(nuevo_precio)
            if precio < 0:
                print("El precio debe ser positivo.")
                continue
            confirm = input(f"¿Seguro que desea cambiar el precio a ${precio:.2f}? (s/n): ").strip().lower()
            if confirm == "s":
                escribir_log_evento("Cambio precio", f"{producto['nombre']} | Antes: ${producto['precio']:.2f} | Ahora: ${precio:.2f}")
                producto["precio"] = precio
            break
        except ValueError:
            print("Ingrese un número válido para el precio.")
    guardar_inventario()
    print("Producto modificado.")

def eliminar_producto():
    listar_productos()
    if not inventario:
        return
    pid_str = input("\nID del producto a eliminar (Enter para cancelar): ").strip()
    if pid_str == "":
        print("Operación cancelada.")
        return
    if not pid_str.isdigit():
        print("Ingrese un ID válido (número).")
        return
    pid = int(pid_str)
    producto = next((p for p in inventario if p["id"] == pid), None)
    if not producto:
        print("ID no encontrado.")
        return
    confirm = input(f"¿Seguro que desea eliminar '{producto['nombre']}'? (s/n): ").strip().lower()
    if confirm == "s":
        inventario.remove(producto)
        escribir_log_evento("Eliminación producto", f"{producto['nombre']} (ID: {producto['id']})")
        guardar_inventario()
        print("Producto eliminado.")
    else:
        print("Operación cancelada.")

def productos_bajos():
    while True:
        limite_str = input("Mostrar productos con stock menor a: ").strip()
        if limite_str == "":
            print("Operación cancelada.")
            return
        if not limite_str.isdigit():
            print("Ingrese un número válido para el límite.")
            continue
        limite = int(limite_str)
        if limite < 0:
            print("El límite debe ser positivo.")
            continue
        break
    bajos = [p for p in inventario if p["stock"] < limite]
    if bajos:
        print("\nProductos con stock bajo:")
        for p in bajos:
            print(f"- {p['nombre']} (stock: {p['stock']})")
    else:
        print("Ningún producto bajo ese límite.")

def productos_nunca_vendidos():
    vendidos = set()
    for venta in ventas:
        for item in venta["items"]:
            vendidos.add(item["nombre"])
    nunca_vendidos = [p["nombre"] for p in inventario if p["nombre"] not in vendidos]
    print("\n--- Productos nunca vendidos ---")
    if nunca_vendidos:
        for nombre in nunca_vendidos:
            print(f"- {nombre}")
    else:
        print("Todos los productos han sido vendidos al menos una vez.")

# ---------------- funciones de ventas ---------------- #

def registrar_venta():
    if not inventario:
        print("Inventario vacío. No se puede vender.")
        return
    cargar_clientes()
    print("¿La venta es para un cliente registrado? (s/n): ", end="")
    es_cliente = input().strip().lower()
    cliente_nombre = ""
    proxima_visita = ""
    if es_cliente == "s":
        if not clientes:
            print("No hay clientes registrados.")
        else:
            print("Clientes registrados:")
            for idx, c in enumerate(clientes, 1):
                print(f"{idx}. {c['nombre']} (Próxima visita: {c['proxima_visita']})")
            idx = input("Seleccione el número del cliente (Enter para cancelar): ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(clientes):
                cliente = clientes[int(idx)-1]
                cliente_nombre = cliente["nombre"]
                proxima_visita = cliente["proxima_visita"]
            else:
                print("Operación cancelada.")
                return
    else:
        cliente_nombre = input("Nombre del cliente: ").strip()
        proxima_visita = input("¿Cuándo volverá a comprar? (YYYY-MM-DD): ").strip()
        clientes.append({"nombre": cliente_nombre, "proxima_visita": proxima_visita})
        guardar_clientes()

    carrito = []
    total = 0.0
    while True:
        listar_productos()
        pid = input("\nID del producto a vender (Enter para terminar): ").strip()
        if pid == "":
            break
        if not pid.isdigit():
            print("Por favor, ingrese un ID válido (número).")
            continue
        pid = int(pid)
        producto = next((p for p in inventario if p["id"] == pid), None)
        if not producto:
            print("ID no válido.")
            continue
        while True:
            cant_str = input("Cantidad (Enter para cancelar): ").strip()
            if cant_str == "":
                print("Operación cancelada.")
                break
            if not cant_str.isdigit():
                print("Por favor, ingrese una cantidad válida (número entero).")
                continue
            cant = int(cant_str)
            if cant <= 0:
                print("La cantidad debe ser mayor a cero.")
                continue
            if cant > producto["stock"]:
                print(Fore.RED + "✖ Error: Stock insuficiente.")
                break
            producto["stock"] -= cant
            subtotal = producto["precio"] * cant
            carrito.append({"nombre": producto["nombre"], "cantidad": cant, "subtotal": subtotal})
            total += subtotal
            print(f"{cant} x {producto['nombre']} agregado/s al carrito.")
            # Alerta de bajo stock
            if producto["stock"] < 5:
                print(Fore.YELLOW + "¡Atención! Stock bajo para este producto.")
            break

    if carrito:
        momento = timestamp()
        ticket = f"\n--- Ticket {momento} ---"
        detalle_venta = []
        for item in carrito:
            ticket += f"\n{item['cantidad']} x {item['nombre']} = ${item['subtotal']:.2f}"
            detalle_venta.append(f"{item['cantidad']} x {item['nombre']} (${item['subtotal']:.2f})")
        ticket += f"\nTOTAL: ${total:.2f}\n"
        print(ticket)
        escribir_log_evento("Venta", f"{' | '.join(detalle_venta)} | Total: ${total:.2f}")
        ventas.append({
            "fecha": momento,
            "items": carrito,
            "total": total,
            "cliente": cliente_nombre,
            "proxima_visita": proxima_visita
        })
        guardar_inventario()
        guardar_ventas()
    else:
        print("No se registró ninguna venta.")

def imprimir_ticket(carrito, total, momento):
    print(Fore.WHITE + Style.BRIGHT + "\n" + "="*32)
    print("        TICKET DE VENTA")
    print("="*32)
    print(f"Fecha: {momento}")
    print("-"*32)
    for item in carrito:
        print(f"{item['cantidad']:>2} x {item['nombre']:<15} ${item['subtotal']:>8.2f}")
    print("-"*32)
    print(f"TOTAL: ${total:.2f}".rjust(32))

# ---------------- reportes ---------------- #

def reporte_ventas():
    if not ventas:
        print("No hay ventas registradas.")
        return
    monto_inicial = obtener_monto_inicial()
    print(f"Monto inicial de caja: ${monto_inicial:.2f}")
    total_ventas = 0
    productos_vendidos = {}
    for venta in ventas:
        total_ventas += venta["total"]
        for item in venta["items"]:
            productos_vendidos[item["nombre"]] = productos_vendidos.get(item["nombre"], 0) + item["cantidad"]
    print(f"Total de ingresos: ${total_ventas:.2f}")
    if productos_vendidos:
        mas_vendido = max(productos_vendidos, key=productos_vendidos.get)
        print(f"Producto más vendido: {mas_vendido} ({productos_vendidos[mas_vendido]} unidades)")
    else:
        print("No hay productos vendidos.")
    print("¿Desea exportar las ventas a CSV? (s/n): ", end="")
    if input().strip().lower() == "s":
        exportar_ventas_csv(ventas)
        print(f"Ventas exportadas a {VENTAS_CSV}")

def reporte_ventas_por_fecha():
    if not ventas:
        print("No hay ventas registradas.")
        return
    print("\n--- Reporte de Ventas por Fecha ---")
    fechas_disponibles = sorted(set(venta["fecha"][:10] for venta in ventas))
    print(f"Fechas disponibles: {', '.join(fechas_disponibles)}")
    while True:
        fecha_inicio = input("Fecha inicio (YYYY-MM-DD): ").strip()
        fecha_fin = input("Fecha fin (YYYY-MM-DD): ").strip()
        try:
            datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
            datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
        except ValueError:
            print("Formato de fecha incorrecto. Use YYYY-MM-DD.")
            continue
        if fecha_inicio > fecha_fin:
            print("La fecha de inicio no puede ser mayor que la fecha de fin.")
            continue
        break
    total = 0
    encontrados = False
    for venta in ventas:
        fecha_venta = venta["fecha"][:10]
        if fecha_inicio <= fecha_venta <= fecha_fin:
            print(f"{venta['fecha']} | Total: ${venta['total']:.2f}")
            total += venta["total"]
            encontrados = True
    if encontrados:
        print(f"Total de ingresos en el periodo: ${total:.2f}")
    else:
        print("No hay ventas en ese periodo.")

def historial_ventas_producto():
    if not ventas:
        print("No hay ventas registradas.")
        return
    nombre = input("Nombre del producto: ").strip()
    total_cant = 0
    total_ingreso = 0
    print(f"\n--- Historial de ventas para '{nombre}' ---")
    for venta in ventas:
        for item in venta["items"]:
            if item["nombre"].lower() == nombre.lower():
                print(f"{venta['fecha']} | {item['cantidad']} x ${item['subtotal']:.2f}")
                total_cant += item["cantidad"]
                total_ingreso += item["subtotal"]
    print(f"Total vendido: {total_cant} unidades | Ingresos: ${total_ingreso:.2f}")

def ventas_por_periodo(periodo="dia"):
    if not ventas:
        print("No hay ventas registradas.")
        return
    from collections import defaultdict
    resumen = defaultdict(float)
    for venta in ventas:
        fecha = venta["fecha"][:10]
        dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
        if periodo == "dia":
            clave = fecha
        elif periodo == "semana":
            clave = f"{dt.year}-W{dt.isocalendar()[1]}"
        elif periodo == "mes":
            clave = f"{dt.year}-{dt.month:02d}"
        resumen[clave] += venta["total"]
    print(f"\n--- Ventas por {periodo} ---")
    for clave, total in sorted(resumen.items()):
        print(f"{clave}: ${total:.2f}")

def menu_reportes():
    while True:
        print("\n--- Menú de Reportes ---")
        print("1. Resumen general")
        print("2. Ventas por fecha")
        print("3. Historial por producto")
        print("4. Productos nunca vendidos")
        print("5. Ventas por periodo")
        print("6. Ventas por día")
        print("7. Ventas por semana")
        print("8. Ventas por mes")
        print("9. Volver al menú principal")
        opcion = input("Seleccione una opción: ").strip()
        if opcion == "1":
            reporte_ventas()
        elif opcion == "2":
            reporte_ventas_por_fecha()
        elif opcion == "3":
            historial_ventas_producto()
        elif opcion == "4":
            productos_nunca_vendidos()
        elif opcion == "5":
            periodo = input("Seleccione el periodo (dia/semana/mes): ").strip().lower()
            if periodo in ("dia", "semana", "mes"):
                ventas_por_periodo(periodo)
            else:
                print("Periodo no válido.")
        elif opcion == "6":
            ventas_por_periodo("dia")
        elif opcion == "7":
            ventas_por_periodo("semana")
        elif opcion == "8":
            ventas_por_periodo("mes")
        elif opcion == "9":
            break
        else:
            print("Opción no válida.")

# ---------------- funciones de caja ---------------- #

def registrar_monto_inicial():
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(CAJA_FILE):
        with open(CAJA_FILE, "r", encoding="utf-8") as f:
            datos = json.load(f)
        if datos.get("fecha") == hoy:
            return datos["monto_inicial"]
    while True:
        monto_str = input("Ingrese el monto inicial de caja para hoy: $").strip()
        try:
            monto = float(monto_str)
            break
        except ValueError:
            print("Ingrese un monto válido.")
    with open(CAJA_FILE, "w", encoding="utf-8") as f:
        json.dump({"fecha": hoy, "monto_inicial": monto}, f)
    return monto

def obtener_monto_inicial():
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(CAJA_FILE):
        with open(CAJA_FILE, "r", encoding="utf-8") as f:
            datos = json.load(f)
        if datos.get("fecha") == hoy:
            return datos["monto_inicial"]
    return 0.0

def resumen_caja():
    monto_inicial = obtener_monto_inicial()
    total_ventas = sum(v["total"] for v in ventas)
    monto_final = monto_inicial + total_ventas
    print(Fore.MAGENTA + "\n" + "="*40)
    print("RESUMEN DE CAJA".center(40))
    print("="*40)
    print(f"Monto inicial: ${monto_inicial:.2f}")
    print(f"Total ventas:  ${total_ventas:.2f}")
    print(f"Monto final:   ${monto_final:.2f}")
    print("="*40)

# ---------------- menú principal ---------------- #

def menu_principal():
    encabezado_principal()
    cargar_inventario()
    cargar_ventas()
    cargar_usuarios()
    cargar_clientes()
    usuario = autenticar_usuario()
    monto_inicial = registrar_monto_inicial()
    bienvenida()
    while True:
        print(Style.BRIGHT + "\n--- Menú Principal ---")
        print("1. ➕ Agregar producto")
        print("2. 📦 Listar productos")
        print("3. 🔄 Actualizar stock")
        print("4. ✏️  Modificar producto")
        print("5. ⚠️  Productos con stock bajo")
        print("6. 🛒 Registrar venta")
        print("7. 📊 Reporte de ventas")
        print("M. 📖 Manual de usuario")
        print("C. 👥 Registrar cliente")
        print("V. 📅 Próximas visitas de clientes")
        if usuario["rol"] == "admin":
            print("8. ❌ Eliminar producto")
            print("9. 👤 Registrar usuario")
            print("0. 🚪 Salir")
        else:
            print("0. 🚪 Salir")

        print(Fore.CYAN + "Seleccione una opción (tecla rápida): ", end="", flush=True)
        opcion = leer_tecla()
        print(opcion)  # Muestra la tecla presionada

        if opcion == "1":
            agregar_producto()
        elif opcion == "2":
            listar_productos()
        elif opcion == "3":
            actualizar_stock()
        elif opcion == "4":
            modificar_producto()
        elif opcion == "5":
            productos_bajos()
        elif opcion == "6":
            registrar_venta()
        elif opcion == "7":
            menu_reportes()
        elif opcion.lower() == "m":
            mostrar_manual()
        elif opcion == "8" and usuario["rol"] == "admin":
            eliminar_producto()
        elif opcion == "9" and usuario["rol"] == "admin":
            registrar_usuario()
        elif opcion.lower() == "c":
            registrar_cliente()
        elif opcion.lower() == "v":
            proximas_visitas()
        elif opcion == "0":
            cerrar_sesion(usuario)
            print("Saliendo… ¡Hasta luego!")
            break
        else:
            print("Opción no válida.")

# ---------------- ejecutar ---------------- #

if __name__ == "__main__":
    try:
        cargar_inventario()
        cargar_ventas()
        cargar_usuarios()
        cargar_clientes()
        monto_inicial = registrar_monto_inicial()
        menu_principal()
    except Exception as e:
        print(Fore.RED + f"\nOcurrió un error inesperado: {e}")
        input("Presione Enter para salir...")
