"""
Módulo BST (Árbol Binario de Búsqueda) para Gestión de Productos
================================================================

Este módulo implementa un Árbol Binario de Búsqueda (BST) para gestionar
productos en una tienda online. Permite operaciones eficientes de búsqueda,
inserción y serialización de productos.

Estructuras de datos:
    - Producto: Clase que representa un producto de la tienda
    - NodoBST: Nodo del árbol que contiene un producto
    - ArbolProductosBST: Árbol binario de búsqueda principal

Funciones auxiliares:
    - serializar_arbol_productos: Convierte el árbol a lista ordenada
    - bst_to_list: Recorrido in-order del árbol

Complejidad temporal:
    - Búsqueda: O(log n) en promedio, O(n) en el peor caso
    - Inserción: O(log n) en promedio, O(n) en el peor caso
"""


class Producto:
    """
    Clase que representa un producto de la tienda online.
    
    Esta clase almacena toda la información relevante de un producto
    que se vende en la tienda.
    
    Atributos:
        product_id (int): Identificador único del producto
        nombre (str): Nombre del producto
        precio (float): Precio unitario del producto
        descripcion (str): Descripción detallada del producto
        stock (int): Cantidad disponible en inventario
    
    Ejemplo:
        >>> producto = Producto(1, "Laptop", 999.99, "Laptop gaming", 10)
        >>> print(producto.nombre)
        'Laptop'
    """
    
    def __init__(self, product_id, nombre, precio, descripcion, stock):
        """
        Inicializa un nuevo producto con sus atributos.
        
        Args:
            product_id (int): ID único del producto
            nombre (str): Nombre del producto
            precio (float): Precio del producto
            descripcion (str): Descripción del producto
            stock (int): Cantidad en inventario
        """
        self.product_id = product_id
        self.nombre = nombre
        self.precio = precio
        self.descripcion = descripcion
        self.stock = stock
        self.cantidad = 0  # Cantidad en un pedido (usado en contexto de pedidos)

    def to_dict(self):
        """
        Convierte el producto a un diccionario serializable.
        
        Este método es útil para convertir el objeto Producto a un formato
        que pueda ser devuelto en respuestas JSON de la API.
        
        Returns:
            dict: Diccionario con los datos del producto
        """
        return {
            "producto_id": self.product_id,
            "nombre": self.nombre,
            "precio": float(self.precio),
            "cantidad": getattr(self, 'cantidad', 1)
        }


class NodoBST:
    """
    Nodo del Árbol Binario de Búsqueda que contiene un producto.
    
    Cada nodo almacena un producto y referencias a sus nodos hijos
    (izquierdo y derecho) siguiendo la estructura de un BST.
    
    Atributos:
        producto (Producto): El producto almacenado en este nodo
        izquierda (NodoBST): Referencia al hijo izquierdo (productos con ID menor)
        derecha (NodoBST): Referencia al hijo derecho (productos con ID mayor)
    """
    
    def __init__(self, producto: Producto):
        """
        Inicializa un nuevo nodo del árbol.
        
        Args:
            producto (Producto): El producto a almacenar en el nodo
        """
        self.producto = producto
        self.izquierda = None
        self.derecha = None


def serializar_arbol_productos(nodo):
    """
    Serializa el árbol de productos a una lista ordenada de diccionarios.
    
    Realiza un recorrido in-order (izquierda, raíz, derecha) del árbol
    para obtener los productos ordenados por su ID de menor a mayor.
    
    Args:
        nodo (NodoBST): Nodo raíz desde donde iniciar la serialización
    
    Returns:
        list: Lista de diccionarios con la información de cada producto
              ordenados por product_id de forma ascendente
    
    Ejemplo:
        >>> productos = serializar_arbol_productos(arbol.raiz)
        >>> print(productos)
        [{'product_id': 1, 'nombre': 'A', ...}, {'product_id': 2, ...}]
    """
    if nodo is None:
        return []

    # Recorrido in-order: izquierda -> actual -> derecha
    izq = serializar_arbol_productos(nodo.izquierda)
    der = serializar_arbol_productos(nodo.derecha)

    actual = [{
        "product_id": nodo.producto.product_id,
        "nombre": nodo.producto.nombre,
        "precio": nodo.producto.precio,
        "descripcion": nodo.producto.descripcion,
        "stock": nodo.producto.stock
    }]

    return izq + actual + der


def bst_to_list(nodo):
    """
    Convierte el árbol BST a una lista de diccionarios mediante recorrido in-order.
    
    Similar a serializar_arbol_productos, pero en una sola línea recursiva.
    Útil para obtener todos los productos ordenados por ID.
    
    Args:
        nodo (NodoBST): Nodo raíz desde donde iniciar el recorrido
    
    Returns:
        list: Lista de diccionarios con los productos ordenados por ID
    """
    if nodo is None:
        return []
    return bst_to_list(nodo.izquierda) + [{
        "product_id": nodo.producto.product_id,
        "nombre": nodo.producto.nombre,
        "precio": nodo.producto.precio,
        "descripcion": nodo.producto.descripcion,
        "stock": nodo.producto.stock
    }] + bst_to_list(nodo.derecha)


class ArbolProductosBST:
    """
    Árbol Binario de Búsqueda para gestionar productos de la tienda.
    
    Esta estructura de datos permite búsquedas eficientes de productos
    utilizando el ID del producto como clave de ordenamiento.
    Los productos con ID menor van al subárbol izquierdo y los de
    ID mayor van al subárbol derecho.
    
    Atributos:
        raiz (NodoBST): Nodo raíz del árbol, None si está vacío
    
    Métodos públicos:
        insertar(producto): Agrega un nuevo producto al árbol
        buscar(product_id): Busca un producto por su ID
    
    Ejemplo:
        >>> arbol = ArbolProductosBST()
        >>> arbol.insertar(Producto(1, "Laptop", 999.99, "Gaming", 10))
        >>> producto = arbol.buscar(1)
        >>> print(producto.nombre)
        'Laptop'
    """
    
    def __init__(self):
        """Inicializa un árbol vacío sin nodo raíz."""
        self.raiz = None

    def insertar(self, producto):
        """
        Inserta un nuevo producto en el árbol BST.
        
        Si el árbol está vacío, el producto se convierte en la raíz.
        Si no, se busca la posición correcta según el ID del producto.
        
        Args:
            producto (Producto): El producto a insertar en el árbol
        """
        if self.raiz is None:
            self.raiz = NodoBST(producto)
        else:
            self._insertar(self.raiz, producto)

    def _insertar(self, nodo: NodoBST, producto: Producto):
        """
        Método privado recursivo para insertar un producto.
        
        Compara el ID del producto con el nodo actual y decide
        si ir al subárbol izquierdo (ID menor) o derecho (ID mayor).
        
        Args:
            nodo (NodoBST): Nodo actual en la recursión
            producto (Producto): Producto a insertar
        """
        if producto.product_id < nodo.producto.product_id:
            # El producto va al subárbol izquierdo (ID menor)
            if nodo.izquierda is None:
                nodo.izquierda = NodoBST(producto)
            else:
                self._insertar(nodo.izquierda, producto)
        else:
            # El producto va al subárbol derecho (ID mayor o igual)
            if nodo.derecha is None:
                nodo.derecha = NodoBST(producto)
            else:
                self._insertar(nodo.derecha, producto)

    def buscar(self, product_id):
        """
        Busca un producto en el árbol por su ID.
        
        Args:
            product_id (int): ID del producto a buscar
        
        Returns:
            Producto: El producto encontrado, o None si no existe
        """
        return self._buscar(self.raiz, product_id)

    def _buscar(self, nodo, product_id):
        """
        Método privado recursivo para buscar un producto.
        
        Compara el ID buscado con el nodo actual y decide
        si buscar en el subárbol izquierdo, derecho, o si ya lo encontró.
        
        Args:
            nodo (NodoBST): Nodo actual en la recursión
            product_id (int): ID del producto a buscar
        
        Returns:
            Producto: El producto si se encuentra, None en caso contrario
        """
        if nodo is None:
            return None
        if product_id == nodo.producto.product_id:
            return nodo.producto
        elif product_id < nodo.producto.product_id:
            # Buscar en el subárbol izquierdo
            return self._buscar(nodo.izquierda, product_id)
        else:
            # Buscar en el subárbol derecho
            return self._buscar(nodo.derecha, product_id)
    

    
