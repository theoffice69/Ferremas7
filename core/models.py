from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.shortcuts import render


API_URL = "http://127.0.0.1:5000"
# Model for Marca
class Marca(models.Model):
    cod_marca = models.CharField(max_length=100, primary_key=True, unique=True)
    nombre_marca = models.CharField(max_length=60, unique=True)

    def __str__(self):
        return self.nombre_marca

class Producto(models.Model):
    id_producto = models.CharField(max_length=20, primary_key=True, unique=True, default=1)
    nombre = models.CharField(max_length=100, null=False)
    cod_marca = models.ForeignKey(Marca, on_delete=models.CASCADE, db_column='cod_marca', default=1)
    precio = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    stock = models.IntegerField(null=False)
    imagen_url = models.URLField(max_length=1000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    def vender(self, cantidad):
        if cantidad <= self.stock:
            self.stock -= cantidad
            self.save()
        else:
            raise ValueError("No hay suficiente stock disponible")

# Carro de Compras Models
class CarroItem(models.Model):
    producto_id_api = models.CharField(max_length=100)  # Cambiado el campo para almacenar el ID del producto de la API
    cantidad = models.PositiveIntegerField(default=1)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def subtotal(self):
        # Puedes obtener el precio del producto haciendo una solicitud a la API
        # Aquí asumo que la API devuelve el precio del producto junto con otros datos
        response = requests.get(f"{API_URL}/productos/{self.producto_id_api}")
        if response.status_code == 200:
            producto_data = response.json()
            precio = producto_data.get('precio')
            if precio is not None:
                return precio * self.cantidad
        # En caso de que no se pueda obtener el precio del producto, retorna 0
        return 0

class Compra(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Agregado el campo total
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Compra realizada por {self.usuario.username}'

class CompraItem(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE)
    carro_item = models.ForeignKey(CarroItem, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def subtotal(self):
        return self.carro_item.producto.precio * self.carro_item.cantidad

class CarroCompras(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(CarroItem)
    compra = models.ForeignKey(Compra, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total(self):
        total = 0
        for item in self.items.all():
            total += item.subtotal()
        return total

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'Pedido {self.id} - {self.usuario.username}'

class Pago(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='pendiente')
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'Pago {self.id} - {self.usuario.username}'

class Entrega(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    entregado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entregas_realizadas')
    recibido_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entregas_recibidas')

    def __str__(self):
        return f'Entrega {self.id} - Pedido {self.pedido.id}'

# Default Groups
class Cliente(Group):
    pass

class Vendedor(Group):
    pass

@receiver(post_save, sender=User)
def assign_user_to_group(sender, instance, created, **kwargs):
    if created:
        group = Group.objects.get(name='usuario')
        instance.groups.add(group)

@receiver(post_migrate)
def create_default_groups_and_superuser(sender, **kwargs):
    default_groups = ['administrador', 'vendedor', 'usuario', 'bodeguero', 'contador']
    for group_name in default_groups:
        Group.objects.get_or_create(name=group_name)

    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(username='admin', email='admin@example.com', password='admin')

class Orden(models.Model):
    bodeguero = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField()

    def __str__(self):
        return f"Orden para {self.bodeguero.username} - {self.fecha_creacion}"

class OrdenB(models.Model):
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Orden {self.id} - Vendedor: {self.vendedor.username}'  


class Checkdata(models.Model):
    REGIONS = [
        ('0', 'Región'),
        ('1', 'Región de Arica y Parinacota'),
        ('2', 'Región de Tarapacá'),
        ('3', 'Región de Antofagasta'),
        ('4', 'Región de Atacama'),
        ('5', 'Región de Coquimbo'),
        ('6', 'Región de Valparaiso'),
        ('7', 'Región de Metropolitana'),
        ('8', 'Región de O\'Higgins'),
        ('9', 'Región de Maule'),
        ('10', 'Región de Ñuble'),
        ('11', 'Región de Biobio'),
        ('12', 'Región de La Araucania'),
        ('13', 'Región de Los Rios'),
        ('14', 'Región de Los Lagos'),
        ('15', 'Región de Aysen'),
        ('16', 'Región de Magallanes'),
    ]
    
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name = models.CharField(max_length=100, verbose_name="Apellido")
    address1 = models.CharField(max_length=255, verbose_name="Dirección 1")
    region = models.CharField(max_length=2, choices=REGIONS, verbose_name="Región")
    zip_code = models.CharField(max_length=20, verbose_name="Código Postal")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"