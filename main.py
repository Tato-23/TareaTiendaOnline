from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from datetime import datetime
from fastapi.responses import JSONResponse
from configuration.connection import DatabaseConnection
import mysql.connector
import os
from bst import Producto, ArbolProductosBST, bst_to_list,serializar_arbol_productos
from lst import NodoPedido, ListaEnlazadaPedidos
import json


app = FastAPI()
arbol_productos = ArbolProductosBST()
lista_pedidos = ListaEnlazadaPedidos()

#Buscar producto por ID usando Arbol Binario de Busqueda
@app.get("/productsbst/{product_id}")
async def get_product_bst(product_id: int):
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

#Crear nuevo producto y añadirlo al BST
@app.post("/products")
async def create_product(request: Request):
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

    # Insert the new product into the BST
    arbol_productos.insertar(nuevo_producto)

    cursor.close()
    mydb.close()
    return JSONResponse(content={"message": "Producto creado exitosamente"})


#Gestión de pedidos usando lista enlazada
@app.get("/pedidos/{pedido_id}")
async def get_pedido(pedido_id: int):
    # Primero, intentar buscar en la LinkedList
    pedido_ll = lista_pedidos.buscar_pedido(pedido_id)
    if pedido_ll:
        # Acceder a atributos del objeto
        total = sum([p.precio * p.cantidad for p in pedido_ll.productos])
        productos = [
            {
                "producto_id": p.product_id,
                "nombre": p.nombre,
                "precio": float(p.precio),
                "cantidad": p.cantidad
            }
            for p in pedido_ll.productos
        ]
        return JSONResponse(content={
            "pedido_id": pedido_ll.pedido_id,
            "cliente": pedido_ll.cliente,
            "fecha_pedido": pedido_ll.fecha.isoformat() if hasattr(pedido_ll.fecha, 'isoformat') else pedido_ll.fecha,
            "productos": productos,
            "total": total
        })

    # Si no está en LinkedList, buscar en DB
    db_connection = DatabaseConnection(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    mydb = await db_connection.get_connection()
    cursor = mydb.cursor(dictionary=True)

    # Obtener datos del pedido
    cursor.execute("SELECT * FROM pedidos WHERE pedido_id = %s", (pedido_id,))
    pedido = cursor.fetchone()
    if not pedido:
        cursor.close()
        mydb.close()
        return JSONResponse(status_code=404, content={"message": "Pedido no encontrado"})

    # Obtener productos del pedido
    cursor.execute("""
        SELECT pp.producto_id, pp.cantidad, p.nombre, p.precio
        FROM pedido_productos pp
        JOIN productos p ON pp.producto_id = p.producto_id
        WHERE pp.pedido_id = %s
    """, (pedido_id,))
    productos = []
    for row in cursor.fetchall():
        productos.append({
            "producto_id": row["producto_id"],
            "nombre": row["nombre"],
            "precio": float(row["precio"]),
            "cantidad": row["cantidad"]
        })

    # Calcular total
    total = sum([p["precio"] * p["cantidad"] for p in productos])

    # Agregar a la LinkedList
    lista_pedidos.agregar_pedido(
        pedido["pedido_id"],
        pedido["cliente"],
        pedido["fecha_pedido"].isoformat() if hasattr(pedido["fecha_pedido"], 'isoformat') else pedido["fecha_pedido"],
        productos
    )

    cursor.close()
    mydb.close()

    return JSONResponse(content={
        "pedido_id": pedido["pedido_id"],
        "cliente": pedido["cliente"],
        "fecha_pedido": pedido["fecha_pedido"].isoformat() if hasattr(pedido["fecha_pedido"], 'isoformat') else pedido["fecha_pedido"],
        "productos": productos,
        "total": total
    })

#Crear nuevo pedido y añadirlo a la LinkedList
@app.post("/pedidos")
async def create_pedido(request: Request):
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


#Serializar y Deserializar Json los datos de productos y pedidos
@app.get("/export_data")
async def export_data():

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
