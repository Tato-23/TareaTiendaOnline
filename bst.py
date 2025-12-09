#Arbol binario de busqueda para gestionar productos en una tienda online

class Producto:
    def __init__(self, product_id, nombre, precio, descripcion, stock):
        self.product_id = product_id
        self.nombre = nombre
        self.precio = precio
        self.descripcion = descripcion
        self.stock = stock

class NodoBST:
    def __init__(self, producto: Producto):
        self.producto = producto
        self.izquierda = None
        self.derecha = None

def bst_to_list(nodo):
    if nodo is None:
        return []
    return bst_to_list(nodo.izquierda)+[{
        "product_id": nodo.producto.product_id,
        "nombre": nodo.producto.nombre,
        "precio": nodo.producto.precio,
        "descripcion": nodo.producto.descripcion,
        "stock": nodo.producto.stock
    }] + bst_to_list(nodo.derecha)

class ArbolProductosBST:
    def __init__(self):
        self.raiz = None

    def insertar(self, producto):
        if self.raiz is None:
            self.raiz = NodoBST(producto)
        else:
            self._insertar(self.raiz, producto)

    def _insertar(self, nodo: NodoBST, producto: Producto):
        if producto.product_id < nodo.producto.product_id:
            if nodo.izquierda is None:
                nodo.izquierda = NodoBST(producto)
            else:
                self._insertar(nodo.izquierda, producto)
        else:
            if nodo.derecha is None:
                nodo.derecha = NodoBST(producto)
            else:
                self._insertar(nodo.derecha, producto)

    def buscar(self, product_id):
        return self._buscar(self.raiz, product_id)

    def _buscar(self, nodo, product_id):
        if nodo is None:
            return None
        if product_id == nodo.producto.product_id:
            return nodo.producto
        elif product_id < nodo.producto.product_id:
            return self._buscar(nodo.izquierda, product_id)
        else:
            return self._buscar(nodo.derecha, product_id)
    
def serializar_arbol_productos(nodo):
    if nodo is None:
        return []

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
    
