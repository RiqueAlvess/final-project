"""Serializers for organizational hierarchy."""

from rest_framework import serializers

from .models import CSVImport, LeaderPermission, Registro, Setor, Unidade


class SetorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setor
        fields = ('id', 'name', 'unidade', 'created_at')
        read_only_fields = ('id', 'created_at')


class UnidadeSerializer(serializers.ModelSerializer):
    setores = SetorSerializer(many=True, read_only=True)

    class Meta:
        model = Unidade
        fields = ('id', 'name', 'setores', 'created_at')
        read_only_fields = ('id', 'created_at')


class UnidadeMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unidade
        fields = ('id', 'name')


class SetorMinimalSerializer(serializers.ModelSerializer):
    unidade = UnidadeMinimalSerializer(read_only=True)

    class Meta:
        model = Setor
        fields = ('id', 'name', 'unidade')


class RegistroSerializer(serializers.ModelSerializer):
    unidade_name = serializers.CharField(source='unidade.name', read_only=True)
    setor_name = serializers.CharField(source='setor.name', read_only=True)

    class Meta:
        model = Registro
        fields = ('id', 'email', 'unidade', 'unidade_name', 'setor', 'setor_name', 'created_at')
        read_only_fields = ('id', 'created_at')


class CSVImportSerializer(serializers.ModelSerializer):
    imported_by_email = serializers.EmailField(source='imported_by.email', read_only=True)

    class Meta:
        model = CSVImport
        fields = (
            'id', 'file_name', 'status', 'total_rows', 'successful_rows',
            'failed_rows', 'errors', 'imported_by_email', 'created_at',
        )
        read_only_fields = fields


class LeaderPermissionSerializer(serializers.ModelSerializer):
    unidade_name = serializers.CharField(source='unidade.name', read_only=True)
    setor_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaderPermission
        fields = ('id', 'user', 'unidade', 'unidade_name', 'setor', 'setor_name')
        read_only_fields = ('id',)

    def get_setor_name(self, obj: LeaderPermission) -> str | None:
        return obj.setor.name if obj.setor else None


class LeaderPermissionWriteSerializer(serializers.Serializer):
    """
    Accepts a list of {unidade, setor?} pairs and replaces all
    permissions for the given user.
    """
    permissions = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=True,
    )

    def validate_permissions(self, value: list) -> list:
        validated: list[dict] = []
        for item in value:
            unidade_id = item.get('unidade')
            setor_id = item.get('setor')

            if not unidade_id:
                raise serializers.ValidationError('Each permission must include an "unidade" id.')

            try:
                unidade = Unidade.objects.get(pk=unidade_id)
            except Unidade.DoesNotExist:
                raise serializers.ValidationError(f'Unidade {unidade_id} not found.')

            setor = None
            if setor_id:
                try:
                    setor = Setor.objects.get(pk=setor_id, unidade=unidade)
                except Setor.DoesNotExist:
                    raise serializers.ValidationError(
                        f'Setor {setor_id} not found in Unidade {unidade_id}.'
                    )

            validated.append({'unidade': unidade, 'setor': setor})
        return validated
