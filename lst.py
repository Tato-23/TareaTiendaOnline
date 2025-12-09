"""
Módulo de Lista Enlazada para Gestión de Pedidos
=================================================

Este módulo implementa una Lista Enlazada Simple (Singly Linked List) para
gestionar los pedidos de una tienda online. Permite operaciones CRUD
(Crear, Leer, Actualizar, Eliminar) sobre los pedidos.

Estructuras de datos:
    - NodoPedido: Nodo que representa un pedido individual
    - ListaEnlazadaPedidos: Lista enlazada que contiene todos los pedidos

Características:
    - Inserción al final de la lista: O(n)
    - Búsqueda por ID: O(n)
    - Eliminación: O(n)
    - Recorrido completo: O(n)

Uso típico:
    >>> lista = ListaEnlazadaPedidos()
    >>> lista.agregar_pedido(1, "Juan", "2025-12-08", [{"producto_id": 1}])
    >>> pedido = lista.buscar_pedido(1)
"""


class NodoPedido:
    """
    Nodo que representa un pedido individual en la lista enlazada.
    
    Cada nodo contiene toda la información de un pedido y una referencia
    al siguiente nodo en la lista.
    
    Atributos:
        pedido_id (int): Identificador único del pedido
        cliente (str): Nombre del cliente que realizó el pedido
        fecha (str): Fecha del pedido en formato ISO (ej: "2025-12-08T14:00:00")
        productos (list): Lista de productos incluidos en el pedido.
            Cada producto es un diccionario con:
            - producto_id (int): ID del producto
            - nombre (str): Nombre del producto
            - precio (float): Precio unitario
            - cantidad (int): Cantidad solicitada
        siguiente (NodoPedido): Referencia al siguiente nodo, None si es el último
    
    Ejemplo:
        >>> productos = [{"producto_id": 1, "nombre": "Laptop", "precio": 999.99, "cantidad": 1}]
        >>> nodo = NodoPedido(1, "Juan Pérez", "2025-12-08", productos)
    """
    
    def __init__(self, pedido_id, cliente, fecha, productos):
        """
        Inicializa un nuevo nodo de pedido.
        
        Args:
            pedido_id (int): ID único del pedido
            cliente (str): Nombre del cliente
            fecha (str): Fecha del pedido en formato ISO
            productos (list): Lista de productos del pedido
        """
        self.pedido_id = pedido_id
        self.cliente = cliente
        self.fecha = fecha
        self.productos = productos  # Lista de productos en el pedido
        self.siguiente = None


class ListaEnlazadaPedidos:
    """
    Lista Enlazada Simple para gestionar pedidos de la tienda.
    
    Esta estructura de datos almacena los pedidos de forma secuencial,
    donde cada nodo apunta al siguiente. Permite operaciones CRUD
    completas sobre los pedidos.
    
    Atributos:
        cabeza (NodoPedido): Primer nodo de la lista, None si está vacía
    
    Métodos:
        agregar_pedido: Añade un nuevo pedido al final de la lista
        buscar_pedido: Busca un pedido por su ID
        eliminar_pedido: Elimina un pedido de la lista
        listar_pedidos: Obtiene todos los pedidos como lista de diccionarios
        actualizar_pedido: Modifica los datos de un pedido existente
    
    Ejemplo:
        >>> lista = ListaEnlazadaPedidos()
        >>> lista.agregar_pedido(1, "Juan", "2025-12-08", [])
        >>> lista.agregar_pedido(2, "María", "2025-12-09", [])
        >>> pedidos = lista.listar_pedidos()
        >>> len(pedidos)
        2
    """
    
    def __init__(self):
        """Inicializa una lista enlazada vacía sin cabeza."""
        self.cabeza = None

    def agregar_pedido(self, pedido_id, cliente, fecha, productos):
        """
        Agrega un nuevo pedido al final de la lista enlazada.
        
        Crea un nuevo nodo con los datos del pedido y lo inserta
        al final de la lista. Si la lista está vacía, el nuevo
        nodo se convierte en la cabeza.
        
        Args:
            pedido_id (int): ID único del pedido
            cliente (str): Nombre del cliente
            fecha (str): Fecha del pedido en formato ISO
            productos (list): Lista de productos del pedido
        
        Complejidad: O(n) donde n es el número de pedidos
        """
        nuevo_nodo = NodoPedido(pedido_id, cliente, fecha, productos)
        if not self.cabeza:
            # Lista vacía, el nuevo nodo es la cabeza
            self.cabeza = nuevo_nodo
        else:
            # Recorrer hasta el último nodo e insertar al final
            actual = self.cabeza
            while actual.siguiente:
                actual = actual.siguiente
            actual.siguiente = nuevo_nodo

    def buscar_pedido(self, pedido_id):
        """
        Busca un pedido en la lista por su ID.
        
        Recorre la lista desde la cabeza hasta encontrar el pedido
        con el ID especificado o hasta llegar al final.
        
        Args:
            pedido_id (int): ID del pedido a buscar
        
        Returns:
            NodoPedido: El nodo del pedido encontrado, o None si no existe
        
        Complejidad: O(n) en el peor caso
        """
        actual = self.cabeza
        while actual:
            if actual.pedido_id == pedido_id:
                return actual
            actual = actual.siguiente
        return None
    
    def eliminar_pedido(self, pedido_id):
        """
        Elimina un pedido de la lista por su ID.
        
        Busca el pedido y lo elimina ajustando las referencias
        de los nodos adyacentes. Maneja el caso especial cuando
        el pedido a eliminar es la cabeza de la lista.
        
        Args:
            pedido_id (int): ID del pedido a eliminar
        
        Returns:
            bool: True si se eliminó exitosamente, False si no se encontró
        
        Complejidad: O(n) en el peor caso
        """
        actual = self.cabeza
        previo = None
        while actual:
            if actual.pedido_id == pedido_id:
                if previo:
                    # El nodo a eliminar no es la cabeza
                    previo.siguiente = actual.siguiente
                else:
                    # El nodo a eliminar es la cabeza
                    self.cabeza = actual.siguiente
                return True
            previo = actual
            actual = actual.siguiente
        return False
    
    def listar_pedidos(self):
        """
        Obtiene todos los pedidos de la lista como diccionarios.
        
        Recorre toda la lista y convierte cada nodo a un diccionario
        con la información del pedido.
        
        Returns:
            list: Lista de diccionarios con la información de cada pedido.
                Cada diccionario contiene:
                - pedido_id (int): ID del pedido
                - cliente (str): Nombre del cliente
                - fecha (str): Fecha del pedido
                - productos (list): Productos del pedido
        
        Complejidad: O(n)
        """
        pedidos = []
        actual = self.cabeza
        while actual:
            pedidos.append({
                "pedido_id": actual.pedido_id,
                "cliente": actual.cliente,
                "fecha": actual.fecha,
                "productos": actual.productos
            })
            actual = actual.siguiente
        return pedidos
    
    def actualizar_pedido(self, pedido_id, cliente=None, fecha=None, productos=None):
        """
        Actualiza los datos de un pedido existente.
        
        Busca el pedido por su ID y actualiza solo los campos
        que se proporcionen (que no sean None).
        
        Args:
            pedido_id (int): ID del pedido a actualizar
            cliente (str, opcional): Nuevo nombre del cliente
            fecha (str, opcional): Nueva fecha del pedido
            productos (list, opcional): Nueva lista de productos
        
        Returns:
            bool: True si se actualizó exitosamente, False si no se encontró
        
        Ejemplo:
            >>> lista.actualizar_pedido(1, cliente="Nuevo Cliente")
            True
        
        Complejidad: O(n) en el peor caso
        """
        actual = self.cabeza
        while actual:
            if actual.pedido_id == pedido_id:
                # Actualizar solo los campos proporcionados
                if cliente:
                    actual.cliente = cliente
                if fecha:
                    actual.fecha = fecha
                if productos is not None:
                    actual.productos = productos
                return True
            actual = actual.siguiente
        return False
    