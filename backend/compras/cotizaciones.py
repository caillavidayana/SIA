from decimal import Decimal
from rest_framework import serializers
from .models import CotizacionCompra


class CotizacionCompraSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()
    documento_url = serializers.SerializerMethodField()
    class Meta:
        model = CotizacionCompra
        fields = ['id', 'proveedor', 'empresa', 'proveedor_identificador', 'descripcion', 'cantidad', 'precio_unitario', 'total', 'documento', 'documento_url', 'seleccionada', 'creado_en']
        read_only_fields = ['id', 'seleccionada', 'creado_en']
        extra_kwargs = {'documento': {'write_only': True}}
    def get_documento_url(self, obj):
        return f'/api/compras/solicitudes/{obj.solicitud_id}/cotizaciones/{obj.pk}/archivo/'
    def get_total(self, obj):
        return str(obj.precio_unitario * obj.cantidad) if obj.precio_unitario is not None else None
    def validate_precio_unitario(self, valor):
        if valor is None:
            return valor
        if not valor.is_finite() or valor <= Decimal('0'):
            raise serializers.ValidationError('Ingrese un precio positivo.')
        return valor
    def validate_cantidad(self, valor):
        if valor < 1:
            raise serializers.ValidationError('Ingrese una cantidad positiva.')
        return valor
    def validate_documento(self, archivo):
        if archivo.size > 10 * 1024 * 1024:
            raise serializers.ValidationError('El documento supera 10 MB.')
        if archivo.content_type not in {'application/pdf', 'image/jpeg', 'image/png', 'image/webp'}:
            raise serializers.ValidationError('Adjunte PDF, JPG, PNG o WEBP.')
        return archivo
