"""
API REST de Tienda Online - Módulo Principal
=============================================

Este módulo implementa una API REST utilizando FastAPI para gestionar
una tienda online. Utiliza estructuras de datos personalizadas:
    - Árbol Binario de Búsqueda (BST): Para gestión eficiente de productos
    - Lista Enlazada: Para gestión de pedidos

Endpoints disponibles:

PRODUCTOS:
    - GET /productsbst/{product_id}: Busca un producto por ID usando BST
    - POST /products: Crea un nuevo producto

PEDIDOS:
    - GET /pedidos: Lista todos los pedidos
    - GET /pedidos/{pedido_id}: Obtiene un pedido específico
    - POST /pedidos: Crea un nuevo pedido
    - PUT /pedidos/{pedido_id}: Actualiza un pedido
    - DELETE /pedidos/{pedido_id}: Elimina un pedido

EXPORTACIÓN/IMPORTACIÓN:
    - GET /export_data: Exporta productos a JSON
    - POST /import_data: Importa productos desde JSON
    - GET /export_pedidos: Exporta pedidos a JSON
    - POST /import_pedidos: Importa pedidos desde JSON

Ejecución:
    uvicorn main:app --reload

Requisitos:
    - Variables de entorno en archivo .env:
        DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
"""

from dotenv import load_dotenv
# Cargar variables de entorno desde archivo .env
load_dotenv()

from fastapi import FastAPI, Request
from datetime import datetime
from fastapi.responses import JSONResponse
from configuration.connection import DatabaseConnection
import mysql.connector
import os
from bst import Producto, ArbolProductosBST, bst_to_list, serializar_arbol_productos
from lst import NodoPedido, ListaEnlazadaPedidos
import json


# ============================================================
# INICIALIZACIÓN DE LA APLICACIÓN Y ESTRUCTURAS DE DATOS
# ============================================================

# Instancia principal de FastAPI
app = FastAPI()

# Árbol Binario de Búsqueda para almacenar productos en memoria
# Permite búsquedas eficientes O(log n) por ID de producto
arbol_productos = ArbolProductosBST()

# Lista Enlazada para almacenar pedidos en memoria
# Mantiene el orden de inserción de los pedidos
lista_pedidos = ListaEnlazadaPedidos()


# ============================================================
# ENDPOINTS DE PRODUCTOS
# ============================================================

@app.get("/productsbst/{product_id}")
async def get_product_bst(product_id: int):
    """
    Busca un producto por su ID utilizando el Árbol Binario de Búsqueda.
    
    Este endpoint carga todos los productos de la base de datos en un BST
    y luego realiza una búsqueda eficiente O(log n) por el ID especificado.
    
    Args:
        product_id (int): ID único del producto a buscar
    
    Returns:
        JSONResponse: 
            - 200: Producto encontrado con todos sus datos
            - 404: Producto no encontrado en el BST
    
    Ejemplo de respuesta exitosa:
        {
            "product_id": 1,
            "nombre": "Laptop",
            "precio": 999.99,
            "descripcion": "Laptop gaming",
            "stock": 10
        }
    """
    db_connection = DatabaseConnection(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    mydb = await db_connection.get_connection()
    cursor = mydb.cursor(dictionary=True)
    query = "SELECT * FROM productos"
    cursor.execute(query)
    productos = cursor.fetchall()
    for prod in productos:
        producto = Producto(
            product_id=prod["producto_id"],
            nombre=prod["nombre"],
            precio=prod["precio"],
            descripcion=prod["descripcion"],
            stock=prod["stock"]
        )
        arbol_productos.insertar(producto)
    producto_buscado = arbol_productos.buscar(product_id)
    cursor.close()
    mydb.close()
    if producto_buscado is None:
        return JSONResponse(status_code=404, content={"message": "Producto no encontrado en BST"})
    return JSONResponse(content={
        "product_id": producto_buscado.product_id,
        "nombre": producto_buscado.nombre,
        "precio": float(producto_buscado.precio),
        "descripcion": producto_buscado.descripcion,
        "stock": producto_buscado.stock
    })


@app.post("/products")
async def create_product(request: Request):
    """
    Crea un nuevo producto y lo añade a la base de datos y al BST.
    
    Este endpoint recibe los datos del producto, lo inserta en la base de datos
    MySQL y también lo agrega al árbol BST en memoria para búsquedas rápidas.
    
    Args:
        request (Request): Objeto de solicitud con el cuerpo JSON
    
    Cuerpo de la solicitud (JSON):
        {
            "nombre": "string" (requerido),
            "precio": float (requerido),
            "descripcion": "string" (requerido),
            "stock": int (requerido)
        }
    
    Returns:
        JSONResponse:
            - 200: Producto creado exitosamente
            - 400: Faltan datos obligatorios
    """
    db_connection = DatabaseConnection(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    mydb = await db_connection.get_connection()
    body = await request.json()
    nombre = body["nombre"]
    precio = body["precio"]
    descripcion = body["descripcion"]
    stock = body["stock"]  

    if stock is None or not nombre or precio is None or not descripcion:
        return JSONResponse(status_code=400, content={"message": "Faltan datos obligatorios"})
   
    cursor = mydb.cursor()
    query = "INSERT INTO productos (nombre, precio, descripcion, stock) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (nombre, precio, descripcion, stock))
    mydb.commit()

    nuevo_producto = Producto(
        product_id=cursor.lastrowid,
        nombre=nombre,
        precio=precio,
        descripcion=descripcion,
        stock=stock
    )

    arbol_productos.insertar(nuevo_producto)

    cursor.close()
    mydb.close()
    return JSONResponse(content={"message": "Producto creado exitosamente"})


# ============================================================
# ENDPOINTS DE PEDIDOS
# ============================================================

@app.get("/pedidos/{pedido_id}")
async def get_pedido(pedido_id: int):
    """
    Obtiene un pedido específico por su ID.
    
    Este endpoint implementa una estrategia de búsqueda en dos niveles:
        1. Primero busca en la Lista Enlazada (caché en memoria)
        2. Si no lo encuentra, busca en la base de datos MySQL
    
    Cuando encuentra el pedido en la BD, lo agrega a la Lista Enlazada
    para acelerar futuras consultas del mismo pedido.
    
    Args:
        pedido_id (int): ID único del pedido a consultar
    
    Returns:
        JSONResponse:
            - 200: Pedido encontrado con sus productos y total calculado
            - 404: Pedido no encontrado en BD ni en Lista Enlazada
    
    Ejemplo de respuesta exitosa:
        {
            "pedido_id": 1,
            "cliente": "Juan Pérez",
            "fecha_pedido": "2025-12-08T14:00:00",
            "productos": [
                {
                    "producto_id": 1,
                    "nombre": "Laptop",
                    "precio": 999.99,
                    "cantidad": 2
                }
            ],
            "total": 1999.98
        }
    
    Proceso interno:
        1. Buscar en Lista Enlazada (memoria) - O(n)
        2. Si existe: convertir productos a objetos Producto si son dicts
        3. Si no existe: consultar BD MySQL
        4. Obtener productos asociados de tabla pedido_productos
        5. Crear objetos Producto con cantidad
        6. Guardar en Lista Enlazada para futuras consultas
        7. Retornar JSON con pedido, productos y total
    """

    # ============================================================
    # 1. BUSCAR EN LISTA ENLAZADA
    # ============================================================
    pedido_ll = lista_pedidos.buscar_pedido(pedido_id)

    if pedido_ll:
        # Asegurar objetos Producto
        productos = []
        for p in pedido_ll.productos:
            if isinstance(p, dict):
                prod = Producto(
                    product_id=p["producto_id"],
                    nombre=p["nombre"],
                    precio=float(p["precio"]),
                    descripcion="",
                    stock=0
                )
                prod.cantidad = p["cantidad"]
                productos.append(prod)
            else:
                productos.append(p)

        pedido_ll.productos = productos

        total = sum(p.precio * p.cantidad for p in productos)

        # Convertir fecha a string si es objeto datetime
        fecha_str = pedido_ll.fecha.isoformat() if hasattr(pedido_ll.fecha, 'isoformat') else str(pedido_ll.fecha)

        return JSONResponse(content={
            "pedido_id": pedido_ll.pedido_id,
            "cliente": pedido_ll.cliente,
            "fecha_pedido": fecha_str,
            "productos": [p.to_dict() for p in productos],
            "total": total
        })

    # ============================================================
    # 2. BUSCAR EN BASE DE DATOS
    # ============================================================
    db_connection = DatabaseConnection(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    mydb = await db_connection.get_connection()
    cursor = mydb.cursor(dictionary=True)

    cursor.execute("SELECT * FROM pedidos WHERE pedido_id = %s", (pedido_id,))
    pedido = cursor.fetchone()

    if not pedido:
        cursor.close()
        mydb.close()
        return JSONResponse(status_code=404, content={"message": "Pedido no encontrado"})

    # ============================================================
    # 3. OBTENER PRODUCTOS DEL PEDIDO DESDE MYSQL
    # ============================================================
    cursor.execute("""
        SELECT pp.producto_id, pp.cantidad, p.nombre, p.precio
        FROM pedido_productos pp
        JOIN productos p ON pp.producto_id = p.producto_id
        WHERE pp.pedido_id = %s
    """, (pedido_id,))

    productos_raw = cursor.fetchall()

    productos = []
    for row in productos_raw:
        prod = Producto(
            product_id=row["producto_id"],
            nombre=row["nombre"],
            precio=float(row["precio"]),
            descripcion="",
            stock=0
        )
        prod.cantidad = row["cantidad"]
        productos.append(prod)

    total = sum(p.precio * p.cantidad for p in productos)

    # ============================================================
    # 4. GUARDAR EN LISTA ENLAZADA COMO OBJETOS, NO DICTS
    # ============================================================
    # Convertir fecha a string si es objeto datetime
    fecha_str = pedido["fecha_pedido"].isoformat() if hasattr(pedido["fecha_pedido"], 'isoformat') else str(pedido["fecha_pedido"])
    
    lista_pedidos.agregar_pedido(
        pedido["pedido_id"],
        pedido["cliente"],
        fecha_str,
        productos  # OBJETOS Producto
    )

    cursor.close()
    mydb.close()

    return JSONResponse(content={
        "pedido_id": pedido["pedido_id"],
        "cliente": pedido["cliente"],
        "fecha_pedido": fecha_str,
        "productos": [p.to_dict() for p in productos],
        "total": total
    })


@app.post("/pedidos")
async def create_pedido(request: Request):
    """
    Crea un nuevo pedido y lo añade a la base de datos y a la Lista Enlazada.
    
    Este endpoint recibe los datos del pedido, lo inserta en las tablas
    'pedidos' y 'pedido_productos' de MySQL, y también lo agrega a la
    lista enlazada en memoria.
    
    Args:
        request (Request): Objeto de solicitud con el cuerpo JSON
    
    Cuerpo de la solicitud (JSON):
        {
            "cliente": "string" (requerido),
            "fecha_pedido": "string ISO" (requerido, ej: "2025-12-08T14:00:00"),
            "productos": [
                {"producto_id": int, "cantidad": int},
                ...
            ]
        }
    
    Returns:
        JSONResponse:
            - 200: Pedido creado con su ID asignado
            - 400: Faltan datos obligatorios o formato de fecha incorrecto
    """
    db_connection = DatabaseConnection(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    mydb = await db_connection.get_connection()
    body = await request.json()

    cliente = body.get("cliente")
    fecha_pedido = body.get("fecha_pedido")  # Espera string ISO, ej: "2025-12-08T14:00:00"
    productos = body.get("productos", [])    

    if cliente is None or fecha_pedido is None:
        return JSONResponse(status_code=400, content={"message": "Faltan datos obligatorios"})

    try:
        fecha_pedido_dt = datetime.fromisoformat(fecha_pedido)
    except ValueError:
        return JSONResponse(status_code=400, content={"message": "Formato de fecha incorrecto"})

    cursor = mydb.cursor()
    query = "INSERT INTO pedidos (cliente, fecha_pedido) VALUES (%s, %s)"
    cursor.execute(query, (cliente, fecha_pedido_dt))
    mydb.commit()
    pedido_id = cursor.lastrowid

    # Agregar productos a la tabla intermedia y a la LinkedList
    for p in productos:
        producto_id = p.get("producto_id")
        cantidad = p.get("cantidad", 1)
        if producto_id is None:
            continue
        cursor.execute(
            "INSERT INTO pedido_productos (pedido_id, producto_id, cantidad) VALUES (%s, %s, %s)",
            (pedido_id, producto_id, cantidad)
        )
    mydb.commit()

    # Agregar pedido a la LinkedList
    lista_pedidos.agregar_pedido(pedido_id, cliente, fecha_pedido_dt.isoformat(), productos)

    cursor.close()
    mydb.close()

    return JSONResponse(content={"message": "Pedido creado exitosamente", "pedido_id": pedido_id})


@app.put("/pedidos/{pedido_id}")
async def update_pedido(pedido_id: int, request: Request):
    """
    Actualiza un pedido existente.
    
    Este endpoint modifica los datos de un pedido tanto en la base de datos
    como en la lista enlazada en memoria. Los productos se reemplazan
    completamente (no se agregan a los existentes).
    
    Args:
        pedido_id (int): ID del pedido a actualizar
        request (Request): Objeto de solicitud con el cuerpo JSON
    
    Cuerpo de la solicitud (JSON):
        {
            "cliente": "string" (requerido),
            "fecha_pedido": "string ISO" (requerido),
            "productos": [
                {"producto_id": int, "cantidad": int},
                ...
            ]
        }
    
    Returns:
        JSONResponse:
            - 200: Pedido actualizado exitosamente
            - 400: Faltan datos o formato de fecha incorrecto
    """
    db_connection = DatabaseConnection(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    mydb = await db_connection.get_connection()
    body = await request.json()
    cliente = body.get("cliente")
    fecha_pedido = body.get("fecha_pedido")
    productos = body.get("productos", [])

    if not cliente or not fecha_pedido:
        return JSONResponse(status_code=400, content={"message": "Faltan datos obligatorios"})
    
    # Convertir fecha a datetime
    try:
        fecha_pedido_dt = datetime.fromisoformat(fecha_pedido)
    except ValueError:
        return JSONResponse(status_code=400, content={"message": "Formato de fecha incorrecto"})
    
    cursor = mydb.cursor()

    # Actualizar pedido en la DB
    query = "UPDATE pedidos SET cliente = %s, fecha_pedido = %s WHERE pedido_id = %s"
    cursor.execute(query, (cliente, fecha_pedido_dt, pedido_id))
    mydb.commit()

    # Actualizar productos en la DB
    if productos:
        cursor.execute("DELETE FROM pedido_productos WHERE pedido_id = %s", (pedido_id,))
        for p in productos:
            producto_id = p.get("producto_id")
            cantidad = p.get("cantidad", 1)
            if producto_id is None:
                continue
            cursor.execute(
                "INSERT INTO pedido_productos (pedido_id, producto_id, cantidad) VALUES (%s, %s, %s)",
                (pedido_id, producto_id, cantidad)
            )
        mydb.commit()

    # Construir lista de productos desde BST
    productos_lista = []
    for p in productos:
        producto_obj = arbol_productos.buscar(p.get("producto_id"))
        if producto_obj:
            productos_lista.append({
                "producto_id": p.get("producto_id"),
                "nombre": producto_obj.nombre,
                "precio": float(producto_obj.precio),
                "cantidad": p.get("cantidad", 1)
            })
    # Actualizar pedido en la LinkedList
    lista_pedidos.actualizar_pedido(pedido_id, cliente, fecha_pedido_dt.isoformat(), productos_lista)

    cursor.close()
    mydb.close()

    return JSONResponse(content={
        "message": "Pedido actualizado exitosamente",
    })


@app.delete("/pedidos/{pedido_id}")
async def delete_pedido(pedido_id: int):
    """
    Elimina un pedido de la base de datos y de la lista enlazada.
    
    Este endpoint elimina primero los registros de la tabla intermedia
    'pedido_productos' y luego el pedido de la tabla 'pedidos'.
    También lo elimina de la lista enlazada en memoria.
    
    Args:
        pedido_id (int): ID del pedido a eliminar
    
    Returns:
        JSONResponse: Mensaje de confirmación de eliminación
    """
    db_connection = DatabaseConnection(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    mydb = await db_connection.get_connection()
    cursor = mydb.cursor()
    # Eliminar pedido y sus productos
    cursor.execute("DELETE FROM pedido_productos WHERE pedido_id = %s", (pedido_id,))
    mydb.commit()
    query = "DELETE FROM pedidos WHERE pedido_id = %s"
    cursor.execute(query, (pedido_id,))
    mydb.commit()
    lista_pedidos.eliminar_pedido(pedido_id)
    cursor.close()
    mydb.close()
    return JSONResponse(content={"message": "Pedido eliminado exitosamente"})


@app.get("/pedidos")
async def list_pedidos():
    """
    Lista todos los pedidos de la tienda.
    
    Este endpoint carga todos los pedidos desde la base de datos,
    los almacena en la lista enlazada (reinicializándola) y devuelve
    la lista completa con todos los productos de cada pedido.
    
    Returns:
        JSONResponse: Lista de todos los pedidos con sus productos
    
    Ejemplo de respuesta:
        [
            {
                "pedido_id": 1,
                "cliente": "Juan",
                "fecha": "2025-12-08T14:00:00",
                "productos": [...]
            },
            ...
        ]
    """
    db_connection = DatabaseConnection(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    mydb = await db_connection.get_connection()
    cursor = mydb.cursor(dictionary=True)

    #Obtener todos los pedidos
    cursor.execute("SELECT * FROM pedidos")
    pedidos = cursor.fetchall()

    #Limpiar lista enlazada antes de volver a llenarla
    lista_pedidos.cabeza = None

    #Cargar pedidos uno por uno
    for ped in pedidos:
        pedido_id = ped["pedido_id"]

        #Obtener productos del pedido
        cursor.execute("""
            SELECT pp.producto_id, p.nombre, p.precio, pp.cantidad
            FROM pedido_productos pp
            JOIN productos p ON p.producto_id = pp.producto_id
            WHERE pp.pedido_id = %s
        """, (pedido_id,))
        productos = cursor.fetchall()

        #Convertir precios a float
        productos_lista = [
            {
                "producto_id": prod["producto_id"],
                "nombre": prod["nombre"],
                "precio": float(prod["precio"]),
                "cantidad": prod["cantidad"]
            }
            for prod in productos
        ]

        #Agregar a la lista enlazada
        lista_pedidos.agregar_pedido(
            pedido_id,
            ped["cliente"],
            ped["fecha_pedido"].isoformat(),
            productos_lista
        )

    #Devolver lista completa
    pedidos_listados = lista_pedidos.listar_pedidos()

    cursor.close()
    mydb.close()

    return JSONResponse(content=pedidos_listados)


# ============================================================
# ENDPOINTS DE EXPORTACIÓN E IMPORTACIÓN JSON
# ============================================================

@app.get("/export_data")
async def export_data():
    """
    Exporta todos los productos a un archivo JSON.
    
    Este endpoint carga los productos de la base de datos en el árbol BST,
    los serializa mediante recorrido in-order (ordenados por ID) y los
    guarda en el archivo 'productos.json'.
    
    El proceso:
        1. Consulta todos los productos de la BD
        2. Los inserta en el árbol BST
        3. Serializa el árbol a una lista ordenada
        4. Guarda en productos.json
    
    Returns:
        dict: Mensaje de confirmación de exportación
    
    Archivo generado: productos.json
    """

    # 1. Cargar productos de la BD al árbol
    db_connection = DatabaseConnection(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    mydb = await db_connection.get_connection()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productos")
    productos_bd = cursor.fetchall()
    cursor.close()
    mydb.close()

    arbol_productos.raiz = None  # limpiar árbol

    for p in productos_bd:
        arbol_productos.insertar(
            Producto(
                product_id=p["producto_id"],
                nombre=p["nombre"],
                precio=float(p["precio"]),
                descripcion=p["descripcion"],
                stock=p["stock"]
            )
        )

    # 2. Serializar BST
    productos_serializados = serializar_arbol_productos(arbol_productos.raiz)

    with open("productos.json", "w", encoding="utf-8") as f:
        json.dump(productos_serializados, f, ensure_ascii=False, indent=4)

    return {"message": "Datos exportados del árbol exitosamente"}


@app.post("/import_data")
async def import_data():
    """
    Importa productos desde un archivo JSON al árbol BST.
    
    Este endpoint lee el archivo 'productos.json', limpia el árbol BST
    actual y carga todos los productos del archivo en el árbol.
    
    Nota: Solo carga en memoria (BST), no modifica la base de datos.
    
    Returns:
        dict: Mensaje de confirmación y cantidad de productos importados
    
    Archivo requerido: productos.json
    """
    with open("productos.json", "r", encoding="utf-8") as f:
        productos_data = json.load(f)

    arbol_productos.raiz = None  # limpiamos el árbol antes de cargar

    for prod in productos_data:
        arbol_productos.insertar(
            Producto(
                product_id=prod["product_id"],
                nombre=prod["nombre"],
                precio=prod["precio"],
                descripcion=prod["descripcion"],
                stock=prod["stock"]
            )
        )

    return {"message": "Datos importados exitosamente", "cantidad": len(productos_data)}


@app.get("/export_pedidos")
async def export_pedidos():
    """
    Exporta todos los pedidos a un archivo JSON.
    
    Este endpoint consulta todos los pedidos de la base de datos
    junto con sus productos asociados y los guarda en 'pedidos.json'.
    
    Estructura del archivo exportado:
        [
            {
                "pedido_id": int,
                "cliente": str,
                "fecha": str (ISO),
                "productos": [...]
            },
            ...
        ]
    
    Returns:
        JSONResponse: Mensaje de confirmación
    
    Archivo generado: pedidos.json
    """
    db_connection = DatabaseConnection(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    mydb = await db_connection.get_connection()
    cursor = mydb.cursor(dictionary=True)

    # Obtener todos los pedidos
    cursor.execute("SELECT * FROM pedidos")
    pedidos_db = cursor.fetchall()

    pedidos_exportar = []

    for ped in pedidos_db:
        # Obtener productos asociados a este pedido
        cursor.execute("""
            SELECT pp.producto_id, pp.cantidad, p.nombre, p.precio
            FROM pedido_productos pp
            JOIN productos p ON p.producto_id = pp.producto_id
            WHERE pp.pedido_id = %s
        """, (ped["pedido_id"],))
        productos = cursor.fetchall()

        # Convertir a formato serializable
        productos_serializados = [
            {
                "producto_id": p["producto_id"],
                "nombre": p["nombre"],
                "precio": float(p["precio"]),
                "cantidad": p["cantidad"]
            }
            for p in productos
        ]

        pedidos_exportar.append({
            "pedido_id": ped["pedido_id"],
            "cliente": ped["cliente"],
            "fecha": ped["fecha_pedido"].isoformat(),
            "productos": productos_serializados
        })

    # Guardar en archivo JSON
    with open("pedidos.json", "w", encoding="utf-8") as f:
        json.dump(pedidos_exportar, f, ensure_ascii=False, indent=4)

    cursor.close()
    mydb.close()

    return JSONResponse(content={"message": "Pedidos exportados correctamente"})


@app.post("/import_pedidos")
async def import_pedidos():
    """
    Importa pedidos desde un archivo JSON a la lista enlazada.
    
    Este endpoint lee el archivo 'pedidos.json', limpia la lista
    enlazada actual y carga todos los pedidos del archivo.
    
    Nota: Solo carga en memoria (Lista Enlazada), no modifica la BD.
    
    Returns:
        JSONResponse: Mensaje de confirmación de importación
    
    Archivo requerido: pedidos.json
    """
    with open("pedidos.json", "r", encoding="utf-8") as f:
        pedidos_data = json.load(f)

    # Limpia la lista antes de importar (si así lo deseas)
    lista_pedidos.cabeza = None  

    for ped in pedidos_data:
        lista_pedidos.agregar_pedido(
            ped["pedido_id"],
            ped["cliente"],
            ped["fecha"],
            ped["productos"]
        )

    return JSONResponse(content={"message": "Pedidos importados exitosamente"})
