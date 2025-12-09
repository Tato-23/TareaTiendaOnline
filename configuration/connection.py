"""
Módulo de Conexión a Base de Datos MySQL
=========================================

Este módulo proporciona una clase para gestionar conexiones a bases de datos
MySQL de forma eficiente. Implementa el patrón de conexión bajo demanda
(lazy connection) para optimizar recursos.

Características:
    - Conexión bajo demanda: La conexión se crea solo cuando se necesita
    - Reutilización de conexión: Una vez creada, la conexión se reutiliza
    - Compatible con async/await: Diseñado para usarse con FastAPI

Requisitos:
    - mysql-connector-python: Conector MySQL para Python

Ejemplo de uso:
    >>> from configuration.connection import DatabaseConnection
    >>> db = DatabaseConnection("localhost", "usuario", "contraseña", "mi_db")
    >>> conexion = await db.get_connection()
    >>> cursor = conexion.cursor()
"""

import mysql


class DatabaseConnection:
    """
    Envoltura compatible con async para gestionar conexiones MySQL.
    
    Esta clase implementa el patrón de conexión bajo demanda (lazy initialization),
    creando la conexión solo cuando se solicita por primera vez y reutilizándola
    en llamadas posteriores.
    
    Atributos:
        host (str): Dirección del servidor MySQL
        user (str): Nombre de usuario para la conexión
        password (str): Contraseña del usuario
        database (str): Nombre de la base de datos a usar
        mydb: Objeto de conexión MySQL, None hasta que se establezca
    
    Ejemplo:
        >>> import os
        >>> db = DatabaseConnection(
        ...     host=os.getenv("DB_HOST"),
        ...     user=os.getenv("DB_USER"),
        ...     password=os.getenv("DB_PASSWORD"),
        ...     database=os.getenv("DB_NAME")
        ... )
        >>> conexion = await db.get_connection()
    """

    def __init__(self, host: str, user: str, password: str, database: str):
        """
        Inicializa los parámetros de conexión sin establecer la conexión.
        
        La conexión real se creará cuando se llame a get_connection().
        Esto permite crear instancias de DatabaseConnection sin consumir
        recursos de conexión hasta que sea necesario.
        
        Args:
            host (str): Dirección del servidor MySQL (ej: "localhost", "127.0.0.1")
            user (str): Usuario de la base de datos
            password (str): Contraseña del usuario
            database (str): Nombre de la base de datos a conectar
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.mydb = None  # Conexión inicializada como None (lazy loading)

    async def get_connection(self):
        """
        Obtiene la conexión a la base de datos MySQL.
        
        Si la conexión no existe, la crea. Si ya existe, la reutiliza.
        Este método es async para ser compatible con FastAPI aunque
        la conexión subyacente sea síncrona.
        
        Returns:
            mysql.connector.connection.MySQLConnection: Objeto de conexión activa
        
        Raises:
            mysql.connector.Error: Si hay un error al conectar con MySQL
        
        Nota:
            Recuerda cerrar la conexión cuando ya no la necesites:
            >>> conexion = await db.get_connection()
            >>> # ... usar la conexión ...
            >>> conexion.close()
        """
        if self.mydb is None:
            # Crear nueva conexión solo si no existe
            self.mydb = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
        return self.mydb