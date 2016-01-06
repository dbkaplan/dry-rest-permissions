from django.db import models
from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework.request import Request
from rest_framework import serializers
from rest_framework import viewsets
from dry_rest_permissions.generics import DRYPermissions, DRYObjectPermissions, DRYGlobalPermissions, DRYPermissionsField, DRYPermissionFiltersBase


class DummyModel(models.Model):
    test_field = models.TextField()


class BaseGlobalMixin(object):
    base_global_allowed = True

    @classmethod
    def has_read_permission(cls, request):
        return cls.base_global_allowed

    @classmethod
    def has_write_permission(cls, request):
        return cls.base_global_allowed


class BaseObjectMixin(object):
    base_object_allowed = True

    def has_object_read_permission(self, request):
        return self.base_object_allowed

    def has_object_write_permission(self, request):
        return self.base_object_allowed


class SpecificGlobalMixin(object):
    specific_global_allowed = True

    @classmethod
    def has_list_permission(cls, request):
        return cls.specific_global_allowed

    @classmethod
    def has_create_permission(cls, request):
        return cls.specific_global_allowed

    @classmethod
    def has_destroy_permission(cls, request):
        return cls.specific_global_allowed

    @classmethod
    def has_retrieve_permission(cls, request):
        return cls.specific_global_allowed

    @classmethod
    def has_update_permission(cls, request):
        return cls.specific_global_allowed

    @classmethod
    def has_custom_action1_permission(cls, request):
        return cls.specific_global_allowed

    @classmethod
    def has_custom_action2_permission(cls, request):
        return cls.specific_global_allowed


class SpecificObjectMixin(object):
    specific_object_allowed = True

    #Ignore this method. It is here to make tests easier to construct, but list requests will never occur for single objects
    def has_object_list_permission(self, request):
        return self.specific_object_allowed

    #Ignore this method. It is here to make tests easier to construct, but create requests will never occur for single objects
    def has_object_create_permission(self, request):
        return self.specific_object_allowed

    def has_object_destroy_permission(self, request):
        return self.specific_object_allowed

    def has_object_retrieve_permission(self, request):
        return self.specific_object_allowed

    def has_object_update_permission(self, request):
        return self.specific_object_allowed

    def has_object_custom_action1_permission(self, request):
        return self.specific_object_allowed

    def has_object_custom_action2_permission(self, request):
        return self.specific_object_allowed


class DummySerializer(serializers.ModelSerializer):
    permissions = DRYPermissionsField(additional_actions=['custom_action1', 'custom_action2'])

    class Meta:
        model = DummyModel
        fields = ('test_field', 'permissions')


class DummyViewSet(viewsets.ModelViewSet):
    permission_classes = (DRYPermissions,)
    queryset = DummyModel.objects.all()
    serializer_class = DummySerializer

    def dummy_check_permission(self, request, obj):
        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                return False

        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                return False

        return True


class DRYRestPermissionsTests(TestCase):

    def setUp(self):
        self.action_set = ['retrieve', 'list', 'create', 'destroy', 'update', 'partial_update', 'custom_action1', 'custom_action2']

        self.factory = RequestFactory()
        self.request_retrieve = Request(self.factory.get('/dummy/1'))
        self.request_list = Request(self.factory.get('/dummy'))
        self.request_create = Request(self.factory.post('/dummy'), {})
        self.request_destroy = Request(self.factory.delete('/dummy/1'))
        self.request_update = Request(self.factory.put('/dummy/1', {}))
        self.request_partial_update = Request(self.factory.patch('/dummy/1', {}))
        self.request_custom_action1 = Request(self.factory.get('/dummy/custom_action1'))
        self.request_custom_action2 = Request(self.factory.post('/dummy/custom_action2', {}))

    def _run_permission_checks(self, view, obj, assert_value):
        for action in self.action_set:
            view.action = action
            request_name = "request_{action}".format(action=action)
            result = view.dummy_check_permission(getattr(self, request_name), obj)
            self.assertEqual(result, assert_value)

    def _run_dry_permission_field_checks(self, view, obj, assert_specific, assert_base):
        serializer = view.get_serializer_class()()
        # dummy request
        serializer.context['request'] = self.request_retrieve
        representation = serializer.to_representation(obj)

        for action in [action for action in self.action_set if action not in ['partial_update', 'list']]:
            has_permission = representation['permissions'].get(action, None)
            self.assertEqual(has_permission, assert_specific, "Action '%s' %s != %s" % (action, has_permission, assert_specific))

        for action in ['read', 'write']:
            has_permission = representation['permissions'].get(action, None)
            self.assertEqual(has_permission, assert_base, "Action '%s' %s != %s" % (action, has_permission, assert_base))

    def test_true_base_permissions(self):
        class TestModel(DummyModel, BaseObjectMixin, BaseGlobalMixin):
            pass

        class TestSerializer(DummySerializer):
            class Meta:
                model = TestModel

        class TestViewSet(DummyViewSet):
            serializer_class = TestSerializer

        view = TestViewSet()

        self._run_permission_checks(view, TestModel(), True)
        self._run_dry_permission_field_checks(view, TestModel(), None, True)

    def test_false_base_object_permissions(self):
        class TestModel(DummyModel, BaseObjectMixin, BaseGlobalMixin):
            base_object_allowed = False

        class TestSerializer(DummySerializer):
            class Meta:
                model = TestModel

        class TestViewSet(DummyViewSet):
            serializer_class = TestSerializer

        view = TestViewSet()

        self._run_permission_checks(view, TestModel(), False)
        self._run_dry_permission_field_checks(view, TestModel(), None, False)

    def test_false_base_global_permissions(self):
        class TestModel(DummyModel, BaseObjectMixin, BaseGlobalMixin):
            base_global_allowed = False

        class TestSerializer(DummySerializer):
            class Meta:
                model = TestModel

        class TestViewSet(DummyViewSet):
            serializer_class = TestSerializer

        view = TestViewSet()

        self._run_permission_checks(view, TestModel(), False)
        self._run_dry_permission_field_checks(view, TestModel(), None, False)

    def test_true_specific_permissions(self):
        class TestModel(
                DummyModel, BaseObjectMixin, BaseGlobalMixin,
                SpecificObjectMixin, SpecificGlobalMixin):
            base_global_allowed = False
            base_object_allowed = False

        class TestSerializer(DummySerializer):
            class Meta:
                model = TestModel

        class TestViewSet(DummyViewSet):
            serializer_class = TestSerializer

        view = TestViewSet()

        self._run_permission_checks(view, TestModel(), True)
        self._run_dry_permission_field_checks(view, TestModel(), True, False)

    def test_true_base_not_defined_permissions(self):
        class TestModel(DummyModel, SpecificObjectMixin, SpecificGlobalMixin):
            pass

        class TestSerializer(DummySerializer):
            class Meta:
                model = TestModel

        class TestViewSet(DummyViewSet):
            serializer_class = TestSerializer

        view = TestViewSet()

        self._run_permission_checks(view, TestModel(), True)
        self._run_dry_permission_field_checks(view, TestModel(), True, None)

    def test_false_specific_object_permissions(self):
        class TestModel(
                DummyModel, BaseObjectMixin, BaseGlobalMixin,
                SpecificObjectMixin, SpecificGlobalMixin):
            specific_object_allowed = False

        class TestSerializer(DummySerializer):
            class Meta:
                model = TestModel

        class TestViewSet(DummyViewSet):
            serializer_class = TestSerializer

        view = TestViewSet()

        self._run_permission_checks(view, TestModel(), False)
        self._run_dry_permission_field_checks(view, TestModel(), False, True)

    def test_false_specific_global_permissions(self):
        class TestModel(
                DummyModel, BaseObjectMixin, BaseGlobalMixin,
                SpecificObjectMixin, SpecificGlobalMixin):
            specific_global_allowed = False

        class TestSerializer(DummySerializer):
            class Meta:
                model = TestModel

        class TestViewSet(DummyViewSet):
            serializer_class = TestSerializer

        view = TestViewSet()

        self._run_permission_checks(view, TestModel(), False)
        self._run_dry_permission_field_checks(view, TestModel(), False, True)

    def test_true_no_global_permissions(self):
        class TestModel(
                DummyModel, BaseObjectMixin, BaseGlobalMixin,
                SpecificObjectMixin, SpecificGlobalMixin):
            base_global_allowed = False
            specific_global_allowed = False

        class TestSerializer(DummySerializer):
            permissions = DRYPermissionsField(object_only=True, additional_actions=['custom_action1', 'custom_action2'])

            class Meta:
                model = TestModel

        class TestViewSet(DummyViewSet):
            serializer_class = TestSerializer
            permission_classes = (DRYObjectPermissions, )

        view = TestViewSet()

        self._run_permission_checks(view, TestModel(), True)
        self._run_dry_permission_field_checks(view, TestModel(), True, True)

    def test_true_no_object_permissions(self):
        class TestModel(
                DummyModel, BaseObjectMixin, BaseGlobalMixin,
                SpecificObjectMixin, SpecificGlobalMixin):
            base_object_allowed = False
            specific_object_allowed = False

        class TestSerializer(DummySerializer):
            permissions = DRYPermissionsField(global_only=True, additional_actions=['custom_action1', 'custom_action2'])

            class Meta:
                model = TestModel

        class TestViewSet(DummyViewSet):
            serializer_class = TestSerializer
            permission_classes = (DRYGlobalPermissions, )

        view = TestViewSet()

        self._run_permission_checks(view, TestModel(), True)
        self._run_dry_permission_field_checks(view, TestModel(), True, True)

    def test_list_filter_backend(self):
        class DummyFilter(object):
            pass

        class TestModel(DummyModel):
            pass

        class TestSerializer(DummySerializer):

            class Meta:
                model = TestModel

        class TestFilterBackend(DRYPermissionFiltersBase):
            def filter_list_queryset(self, request, queryset, view):
                return DummyFilter()

        class TestViewSet(DummyViewSet):
            serializer_class = TestSerializer
            queryset = TestModel.objects.all()
            filter_backends = (TestFilterBackend,)

        view = TestViewSet()
        view.request = self.request_list
        view.action = 'list'
        view.kwargs = []
        query_set = view.filter_queryset(view.get_queryset())
        self.assertEqual(query_set.__class__, DummyFilter)

    def test_action_filter_backend(self):
        class DummyFilter(object):
            pass

        class TestModel(DummyModel):
            pass

        class TestSerializer(DummySerializer):

            class Meta:
                model = TestModel

        class TestFilterBackend(DRYPermissionFiltersBase):
            action_routing = True

            def filter_list_queryset(self, request, queryset, view):
                return None

            def filter_custom_action1_queryset(self, request, queryset, view):
                return DummyFilter()

        class TestViewSet(DummyViewSet):
            serializer_class = TestSerializer
            queryset = TestModel.objects.all()
            filter_backends = (TestFilterBackend,)

        view = TestViewSet()
        view.request = self.request_custom_action1
        view.action = 'custom_action1'
        view.kwargs = []
        query_set = view.filter_queryset(view.get_queryset())
        self.assertEqual(query_set.__class__, DummyFilter)
