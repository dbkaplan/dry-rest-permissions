"""
Provides a set of pluggable permission classes, filter classes and
field classes that can be used with django-rest-framework.
The goal of these classes is to allow easy development of permissions
for CRUD actions, list actions and custom actions.  It also allows
permission checks to be returned by the api per object so that
they can be consumed by a front end application.
"""
from functools import wraps

from rest_framework import filters
from rest_framework import permissions
from rest_framework import fields


class DRYPermissionFiltersBase(filters.BaseFilterBackend):
    """
    This class is a base that should be inherited, not used directly on
    a view. This base is intended to be used to limit the records a
    requester can retrieve in a list request for permission purposes.
    This class abstracts away the logic for determining whether the request
    is a list type request.

    override filter_list_queryset(self, request, queryset, view) to limit
    list type requests.

    If action_routing is set to True then you can add additional methods
    to filter custom actions.  The format for those methods is
    filter_{action}_queryset
    e.g. filter_owned_queryset for a custom 'owned' list type requested
    created on a view with the @list_route decorator.
    """
    action_routing = False

    def filter_queryset(self, request, queryset, view):
        """
        This method overrides the standard filter_queryset method.
        This method will check to see if the view calling this is from
        a list type action. This function will also route the filter
        by action type if action_routing is set to True.
        """
        # Check if this is a list type request
        if view.lookup_field not in view.kwargs:
            if not self.action_routing:
                return self.filter_list_queryset(request, queryset, view)
            else:
                method_name = "filter_{action}_queryset".format(action=view.action)
                return getattr(self, method_name)(request, queryset, view)
        return queryset

    def filter_list_queryset(self, request, queryset, view):
        """
        Override this function to add filters.
        This should return a queryset so start with queryset.filter({your filters})
        """
        assert False, "Method filter_list_queryset must be overridden on '%s'" % view.__class__.__name__


class DRYPermissions(permissions.BasePermission):
    """
    This class can be used directly by a DRF view or can be used as a
    base class for a custom permissions class. This class helps to organize
    permission methods that are defined on the model class that is defined
    on the serializer for this view.

    DRYPermissions will call action based methods on the model in the following order:
    1) Global permissions (format has_{action}_permission):
        1a) specific action permissions (e.g. has_retrieve_permission)
        1b) general action permissions  (e.g. has_read_permission)
    2) Object permissions for a specific object (format has_object_{action}_permission):
        2a) specific action permissions (e.g. has_object_retrieve_permission)
        2b) general action permissions  (e.g. has_object_read_permission)

    If either of the specific permissions do not exist, the DRYPermissions will
    simply check the general permission.
    If any step in this process returns False then the checks stop there and
    throw a permission denied. If there is a "specific action" step then the
    "generic step" is skipped. In order to have permission there must be True returned
    from both the Global and Object permissions categories, unless the global_permissions
    or object_permissions attributes are set to False.

    Specific action permissions take their name from the action name,
    which is either DRF defined (list, retrieve, update, destroy, create)
    or developer defined for custom actions created using @list_route or @detail_route.

    Options that may be overridden when using as a base class:
    global_permissions: If set to False then global permissions are not checked.
    object_permissions: If set to False then object permissions are not checked.
    partial_update_is_update: If set to False then specific permissions for
        partial_update can be set, otherwise they will just use update permissions.

    """
    global_permissions = True
    object_permissions = True
    partial_update_is_update = True

    def has_permission(self, request, view):
        """
        Overrides the standard function and figures out methods to call for global permissions.
        """
        if not self.global_permissions:
            return True

        serializer_class = view.get_serializer_class()

        assert serializer_class.Meta.model is not None, (
            "global_permissions set to true without a model "
            "set on the serializer for '%s'" % view.__class__.__name__
        )

        model_class = serializer_class.Meta.model

        action_method_name = None
        if hasattr(view, 'action'):
            action = self._get_action(view.action)
            action_method_name = "has_{action}_permission".format(action=action)
            # If the specific action permission exists then use it, otherwise use general.
            if hasattr(model_class, action_method_name):
                return getattr(model_class, action_method_name)(request)

        if request.method in permissions.SAFE_METHODS:
            assert hasattr(model_class, 'has_read_permission'), \
                self._get_error_message(model_class, 'has_read_permission', action_method_name)
            return model_class.has_read_permission(request)
        else:
            assert hasattr(model_class, 'has_write_permission'), \
                self._get_error_message(model_class, 'has_write_permission', action_method_name)
            return model_class.has_write_permission(request)

    def has_object_permission(self, request, view, obj):
        """
        Overrides the standard function and figures out methods to call for object permissions.
        """
        if not self.object_permissions:
            return True

        serializer_class = view.get_serializer_class()
        model_class = serializer_class.Meta.model
        action_method_name = None
        if hasattr(view, 'action'):
            action = self._get_action(view.action)
            action_method_name = "has_object_{action}_permission".format(action=action)
            # If the specific action permission exists then use it, otherwise use general.
            if hasattr(obj, action_method_name):
                return getattr(obj, action_method_name)(request)

        if request.method in permissions.SAFE_METHODS:
            assert hasattr(obj, 'has_object_read_permission'), \
                self._get_error_message(model_class, 'has_object_read_permission', action_method_name)
            return obj.has_object_read_permission(request)
        else:
            assert hasattr(obj, 'has_object_write_permission'), \
                self._get_error_message(model_class, 'has_object_write_permission', action_method_name)
            return obj.has_object_write_permission(request)

    def _get_action(self, action):
        """
        Utility function that consolidates actions if necessary.
        """
        return_action = action
        if self.partial_update_is_update and action == 'partial_update':
            return_action = 'update'
        return return_action

    def _get_error_message(self, model_class, method_name, action_method_name):
        """
        Get assertion error message depending if there are actions permissions methods defined.
        """
        if action_method_name:
            return "'{}' does not have '{}' or '{}' defined.".format(model_class, method_name, action_method_name)
        else:
            return "'{}' does not have '{}' defined.".format(model_class, method_name)


class DRYGlobalPermissions(DRYPermissions):
    """
    This is a shortcut class that can be used to only check global permissions on a model.
    """
    object_permissions = False


class DRYObjectPermissions(DRYPermissions):
    """
    This is a shortcut class that can be used to only check object permissions on a model.
    """
    global_permissions = False


class DRYPermissionsField(fields.Field):
    """
    This is a field that can be used on a DRF model serializer class. Often a user interface
    needs to know what permissions a user has so that it can change the interface accordingly.
    This field will call the same developer defined model methods (hence the DRY) that DRYPermissions
    uses and create    a dictionary of all permissions defined and whether the requester currently
    has access or not.

    This will only return permissions that are defined by methods. For example it will not return
    retrieve: True if the read permission is defined.

    This will combine object and global permissions to only return True if both are True. If you
    need to know whether a requester specifically has object or global permissions for informational
    purposes then use the global_only or object_only parameters.

    other parameters:
    actions: Add a list of strings here to specifically identify the actions this looks up. If left as None
        then it will return the default CRUD actions along with list and read and write.
    additional_actions: Add a list of strings here to add on to the default actions, without having to repeat them.
    """
    default_actions = ['create', 'retrieve', 'update', 'destroy', 'write', 'read']

    def __init__(self, actions=None, additional_actions=None, global_only=False, object_only=False, **kwargs):
        """See class description for parameters and usage"""
        assert not (global_only and object_only), (
            "Both global_only and object_only cannot be set to true "
            "on a DRYPermissionsField"
        )
        self.action_method_map = {}

        self.global_only = global_only
        self.object_only = object_only
        self.actions = self.default_actions if (actions is None) else actions
        if additional_actions is not None:
            self.actions = self.actions + additional_actions

        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(DRYPermissionsField, self).__init__(**kwargs)

    def bind(self, field_name, parent):
        """
        Check the model attached to the serializer to see what methods are defined and save them.
        """
        assert parent.Meta.model is not None, \
            "DRYPermissions is used on '{}' without a model".format(parent.__class__.__name__)

        for action in self.actions:

            if not self.object_only:
                global_method_name = "has_{action}_permission".format(action=action)
                if hasattr(parent.Meta.model, global_method_name):
                    self.action_method_map[action] = {'global': global_method_name}

            if not self.global_only:
                object_method_name = "has_object_{action}_permission".format(action=action)
                if hasattr(parent.Meta.model, object_method_name):
                    if self.action_method_map.get(action, None) is None:
                        self.action_method_map[action] = {}
                    self.action_method_map[action]['object'] = object_method_name

        super(DRYPermissionsField, self).bind(field_name, parent)

    def to_representation(self, value):
        """
        Calls the developer defined permission methods
        (both global and object) and formats the results into a dictionary.
        """
        results = {}
        for action, method_names in self.action_method_map.items():
            # If using global permissions and the global method exists for this action.
            if not self.object_only and method_names.get('global', None) is not None:
                results[action] = getattr(self.parent.Meta.model, method_names['global'])(self.context['request'])
            # If using object permissions, the global permission did not already evaluate to False and the object
            # method exists for this action.
            if not self.global_only and results.get(action, True) and method_names.get('object', None) is not None:
                results[action] = getattr(value, method_names['object'])(self.context['request'])
        return results


def allow_staff_or_superuser(func):
    """
    This decorator is used to abstract common is_staff and is_superuser functionality
    out of permission checks. It determines which parameter is the request based on name.
    """
    is_object_permission = "has_object" in func.__name__

    @wraps(func)
    def func_wrapper(*args, **kwargs):
        request = args[0]
        # use second parameter if object permission
        if is_object_permission:
            request = args[1]

        if request.user.is_staff or request.user.is_superuser:
            return True

        return func(*args, **kwargs)

    return func_wrapper


def authenticated_users(func):
    """
    This decorator is used to abstract common authentication checking functionality
    out of permission checks. It determines which parameter is the request based on name.
    """
    is_object_permission = "has_object" in func.__name__

    @wraps(func)
    def func_wrapper(*args, **kwargs):
        request = args[0]
        # use second parameter if object permission
        if is_object_permission:
            request = args[1]

        if not(request.user and request.user.is_authenticated):
            return False

        return func(*args, **kwargs)

    return func_wrapper


def unauthenticated_users(func):
    """
    This decorator is used to abstract common unauthentication checking functionality
    out of permission checks. It determines which parameter is the request based on name.
    """
    is_object_permission = "has_object" in func.__name__

    @wraps(func)
    def func_wrapper(*args, **kwargs):
        request = args[0]
        # use second parameter if object permission
        if is_object_permission:
            request = args[1]

        if request.user and request.user.is_authenticated:
            return False

        return func(*args, **kwargs)

    return func_wrapper
