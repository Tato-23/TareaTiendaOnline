# Lista enlazada para gestionar pedidos en una tienda online

class NodoPedido:
    def __init__(self, pedido_id,cliente,fecha,productos):
        self.pedido_id = pedido_id
        self.cliente = cliente
        self.fecha = fecha
        self.productos = productos  # Lista de productos en el pedido
        self.siguiente = None

class ListaEnlazadaPedidos:
    def __init__(self):
        self.cabeza = None

    def agregar_pedido(self, pedido_id, cliente, fecha, productos):
        nuevo_nodo = NodoPedido(pedido_id, cliente, fecha, productos)
        if not self.cabeza:
            self.cabeza = nuevo_nodo
        else:
            actual = self.cabeza
            while actual.siguiente:
                actual = actual.siguiente
            actual.siguiente = nuevo_nodo

    def buscar_pedido(self, pedido_id):
        actual = self.cabeza
        while actual:
            if actual.pedido_id == pedido_id:
                return actual
            actual = actual.siguiente
        return None
    
    def eliminar_pedido(self, pedido_id):
        actual = self.cabeza
        previo = None
        while actual:
            if actual.pedido_id == pedido_id:
                if previo:
                    previo.siguiente = actual.siguiente
                else:
                    self.cabeza = actual.siguiente
                return True
            previo = actual
            actual = actual.siguiente
        return False
    
    def listar_pedidos(self):
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
        actual = self.cabeza
        while actual:
            if actual.pedido_id == pedido_id:
                if cliente:
                    actual.cliente = cliente
                if fecha:
                    actual.fecha = fecha
                if productos is not None:
                    actual.productos = productos
                return True
            actual = actual.siguiente
        return False
    