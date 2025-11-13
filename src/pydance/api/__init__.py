"""
REST API development tools for Pydance  framework.
Provides resource controllers, serialization, versioning, and API documentation.
"""

import inspect
from typing import Dict, List, Any, Type, Callable

from pydance.core.exceptions import HTTPException, ValidationError, PermissionDenied, NotFound, APIException

from pydance.utils.pagination import PageNumberPaginator, LimitOffsetPaginator, PaginationParams, PaginationResult


class Field:
    """Base field class for serializers"""

    def __init__(self, required=True, default=None, allow_null=False, validators=None):
        self.required = required
        self.default = default
        self.allow_null = allow_null
        self.validators = validators or []

    def validate(self, value):
        """Validate field value"""
        if value is None and self.allow_null:
            return value
        if self.required and value is None:
            raise ValidationError("This field is required")
        for validator in self.validators:
            validator(value)
        return value

    def to_representation(self, value):
        """Convert field value to representation"""
        return value

    def to_internal_value(self, value):
        """Convert representation to internal value"""
        return value


class CharField(Field):
    """String field"""

    def __init__(self, max_length=None, min_length=None, **kwargs):
        super().__init__(**kwargs)
        self.max_length = max_length
        self.min_length = min_length

    def validate(self, value):
        value = super().validate(value)
        if not isinstance(value, str):
            raise ValidationError("Not a valid string")
        if self.max_length and len(value) > self.max_length:
            raise ValidationError(f"Ensure this field has no more than {self.max_length} characters")
        if self.min_length and len(value) < self.min_length:
            raise ValidationError(f"Ensure this field has at least {self.min_length} characters")
        return value


class IntegerField(Field):
    """Integer field"""

    def __init__(self, min_value=None, max_value=None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value):
        value = super().validate(value)
        if not isinstance(value, int):
            raise ValidationError("Not a valid integer")
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(f"Ensure this value is greater than or equal to {self.min_value}")
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(f"Ensure this value is less than or equal to {self.max_value}")
        return value


class Serializer:
    """Base serializer class with field validation"""

    def __init__(self, instance=None, data=None, many=False, **kwargs):
        self.instance = instance
        self.data = data or {}
        self.many = many
        self.errors = {}
        self.validated_data = {}
        self.fields = self.get_fields()

    def get_fields(self):
        """Get serializer fields"""
        fields = {}
        for name in dir(self):
            attr = getattr(self, name)
            if isinstance(attr, Field):
                fields[name] = attr
        return fields

    def serialize(self, instance) -> Dict[str, Any]:
        """Convert instance to dictionary"""
        if self.many:
            return [self.serialize_single(obj) for obj in instance]
        return self.serialize_single(instance)

    def serialize_single(self, instance) -> Dict[str, Any]:
        """Serialize single instance"""
        data = {}
        for field_name, field in self.fields.items():
            if hasattr(instance, field_name):
                value = getattr(instance, field_name)
                data[field_name] = field.to_representation(value)
        return data

    def deserialize(self, data: Dict[str, Any]) -> Any:
        """Convert dictionary to instance"""
        validated_data = {}
        errors = {}

        for field_name, field in self.fields.items():
            value = data.get(field_name, field.default)
            try:
                validated_data[field_name] = field.to_internal_value(value)
            except ValidationError as e:
                errors[field_name] = e.detail

        if errors:
            raise ValidationError(errors)

        return validated_data

    def is_valid(self) -> bool:
        """Validate the data"""
        try:
            self.validated_data = self.deserialize(self.data)
            return True
        except ValidationError as e:
            self.errors = e.detail
            return False

    def save(self) -> Any:
        """Save the validated data"""
        if not self.is_valid():
            raise ValidationError(self.errors)

        if self.instance:
            # Update existing instance
            for key, value in self.validated_data.items():
                if hasattr(self.instance, key):
                    setattr(self.instance, key, value)
            return self.instance
        else:
            # Create new instance
            return self.validated_data


class ModelSerializer(Serializer):
    """Serializer for model instances"""

    class Meta:
        model = None
        fields = None
        exclude = None
        read_only_fields = None

    def __init__(self, instance=None, data=None, many=False, **kwargs):
        super().__init__(instance, data, many, **kwargs)

        # Get fields from Meta class
        self.model = getattr(self.Meta, 'model', None)
        self.fields = getattr(self.Meta, 'fields', None)
        self.exclude = getattr(self.Meta, 'exclude', None)
        self.read_only_fields = getattr(self.Meta, 'read_only_fields', None) or []

    def serialize(self, instance) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        if self.model and hasattr(instance, 'to_dict'):
            data = instance.to_dict()
        else:
            data = super().serialize(instance)

        # Apply field filtering
        if self.fields:
            data = {k: v for k, v in data.items() if k in self.fields}
        elif self.exclude:
            data = {k: v for k, v in data.items() if k not in self.exclude}

        return data

    def deserialize(self, data: Dict[str, Any]) -> Any:
        """Convert dictionary to model instance"""
        if not self.model:
            return data

        # Remove read-only fields
        for field in self.read_only_fields:
            data.pop(field, None)

        # Create or update instance
        if self.instance:
            for key, value in data.items():
                if hasattr(self.instance, key):
                    setattr(self.instance, key, value)
            return self.instance
        else:
            return self.model(**data)


class APIView:
    """Base API view class"""

    def __init__(self):
        self.request = None

    def dispatch(self, request: Request) -> Response:
        """Dispatch request to appropriate handler"""
        self.request = request
        method = request.method.lower()

        if hasattr(self, method):
            handler = getattr(self, method)
            return handler(request)
        else:
            return Response("Method not allowed", status_code=405)

    def get(self, request: Request) -> Response:
        """Handle GET request"""
        return Response("Method not implemented", status_code=501)

    def post(self, request: Request) -> Response:
        """Handle POST request"""
        return Response("Method not implemented", status_code=501)

    def put(self, request: Request) -> Response:
        """Handle PUT request"""
        return Response("Method not implemented", status_code=501)

    def patch(self, request: Request) -> Response:
        """Handle PATCH request"""
        return Response("Method not implemented", status_code=501)

    def delete(self, request: Request) -> Response:
        """Handle DELETE request"""
        return Response("Method not implemented", status_code=501)


class GenericAPIView(APIView):
    """Generic API view with common functionality"""

    queryset = None
    serializer_class = None
    lookup_field = 'id'
    lookup_url_kwarg = None
    pagination_class = None
    filter_backends = []
    ordering_fields = []
    search_fields = []

    def get_queryset(self):
        """Get the queryset for this view"""
        return self.queryset

    def get_serializer_class(self):
        """Get the serializer class for this view"""
        return self.serializer_class

    def get_serializer(self, *args, **kwargs):
        """Get serializer instance"""
        serializer_class = self.get_serializer_class()
        if serializer_class:
            return serializer_class(*args, **kwargs)
        return None

    def get_pagination_class(self):
        """Get the pagination class for this view"""
        return self.pagination_class

    def get_object(self):
        """Get object for detail views"""
        queryset = self.get_queryset()
        if not queryset:
            raise HTTPException(404, "Not found")

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.request.path_params.get(lookup_url_kwarg)

        if not lookup_value:
            raise HTTPException(404, "Not found")

        # Try to find the object by lookup field
        try:
            # If queryset has a get method (like Django ORM)
            if hasattr(queryset, 'get'):
                filter_kwargs = {self.lookup_field: lookup_value}
                return queryset.get(**filter_kwargs)
            # If queryset is a list, find by index or field
            elif isinstance(queryset, list):
                for obj in queryset:
                    if hasattr(obj, self.lookup_field):
                        if str(getattr(obj, self.lookup_field)) == str(lookup_value):
                            return obj
                    elif hasattr(obj, '__getitem__') and self.lookup_field in obj:
                        if str(obj[self.lookup_field]) == str(lookup_value):
                            return obj
                return None
            else:
                return None
        except Exception:
            return None

    def filter_queryset(self, queryset):
        """Filter the queryset based on request parameters"""
        # Simple filtering implementation
        if not queryset:
            return queryset

        # Handle search
        search_term = self.request.query_params.get('search')
        if search_term and self.search_fields:
            if isinstance(queryset, list):
                filtered = []
                for obj in queryset:
                    for field in self.search_fields:
                        if hasattr(obj, field):
                            value = str(getattr(obj, field)).lower()
                            if search_term.lower() in value:
                                filtered.append(obj)
                                break
                        elif hasattr(obj, '__getitem__') and field in obj:
                            value = str(obj[field]).lower()
                            if search_term.lower() in value:
                                filtered.append(obj)
                                break
                queryset = filtered

        # Handle ordering
        ordering = self.request.query_params.get('ordering')
        if ordering and self.ordering_fields:
            if isinstance(queryset, list):
                reverse = ordering.startswith('-')
                field = ordering[1:] if reverse else ordering

                if field in self.ordering_fields:
                    queryset.sort(
                        key=lambda x: getattr(x, field) if hasattr(x, field) else x.get(field),
                        reverse=reverse
                    )

        # Handle field-specific filters
        for key, value in self.request.query_params.items():
            if key not in ['search', 'ordering', 'page', 'page_size']:
                if isinstance(queryset, list):
                    filtered = []
                    for obj in queryset:
                        if hasattr(obj, key):
                            if str(getattr(obj, key)) == str(value):
                                filtered.append(obj)
                        elif hasattr(obj, '__getitem__') and key in obj:
                            if str(obj[key]) == str(value):
                                filtered.append(obj)
                    queryset = filtered

        return queryset

    def paginate_queryset(self, queryset):
        """Paginate the queryset"""
        pagination_class = self.get_pagination_class()
        if not pagination_class:
            return None

        paginator = pagination_class()
        return paginator.paginate_queryset(queryset, self.request)


class ListAPIView(GenericAPIView):
    """API view for listing objects"""

    def get(self, request: Request) -> Response:
        """List objects"""
        queryset = self.get_queryset()
        if not queryset:
            return Response([])

        # Apply filtering
        queryset = self.filter_queryset(queryset)

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            if serializer:
                data = serializer.serialize(page)
                return Response({
                    'results': data,
                    'count': len(queryset) if isinstance(queryset, list) else getattr(queryset, 'count', lambda: len(data))(),
                    'page': request.query_params.get('page', 1),
                    'page_size': request.query_params.get('page_size', 10)
                })

        # No pagination - serialize all objects
        if isinstance(queryset, list):
            serializer = self.get_serializer(queryset, many=True)
            if serializer:
                data = serializer.serialize(queryset)
                return Response(data)

        return Response([])


class CreateAPIView(GenericAPIView):
    """API view for creating objects"""

    def post(self, request: Request) -> Response:
        """Create new object"""
        serializer = self.get_serializer(data=request.data)
        if serializer and serializer.is_valid():
            instance = serializer.save()
            response_data = serializer.serialize(instance)
            return Response(response_data, status_code=201)
        else:
            return Response(serializer.errors if serializer else {}, status_code=400)


class RetrieveAPIView(GenericAPIView):
    """API view for retrieving single object"""

    def get(self, request: Request) -> Response:
        """Retrieve object"""
        instance = self.get_object()
        if not instance:
            return Response({"error": "Not found"}, status_code=404)

        serializer = self.get_serializer(instance)
        if serializer:
            data = serializer.serialize(instance)
            return Response(data)
        return Response(instance)


class UpdateAPIView(GenericAPIView):
    """API view for updating objects"""

    def put(self, request: Request) -> Response:
        """Update object"""
        instance = self.get_object()
        if not instance:
            return Response({"error": "Not found"}, status_code=404)

        serializer = self.get_serializer(instance, data=request.data)
        if serializer and serializer.is_valid():
            instance = serializer.save()
            response_data = serializer.serialize(instance)
            return Response(response_data)
        else:
            return Response(serializer.errors if serializer else {}, status_code=400)

    def patch(self, request: Request) -> Response:
        """Partial update object"""
        return self.put(request)


class DestroyAPIView(GenericAPIView):
    """API view for deleting objects"""

    def delete(self, request: Request) -> Response:
        """Delete object"""
        instance = self.get_object()
        if not instance:
            return Response({"error": "Not found"}, status_code=404)

        # This would need proper deletion implementation
        return Response(status_code=204)


class ListCreateAPIView(ListAPIView, CreateAPIView):
    """API view for listing and creating objects"""
    pass


class RetrieveUpdateAPIView(RetrieveAPIView, UpdateAPIView):
    """API view for retrieving and updating objects"""
    pass


class RetrieveUpdateDestroyAPIView(RetrieveUpdateAPIView, DestroyAPIView):
    """API view for retrieving, updating and deleting objects"""
    pass


class ViewSet:
    """ViewSet for grouping related views"""

    def __init__(self):
        self.basename = None
        self.detail = None

    def get_queryset(self):
        """Get queryset for this viewset"""
        return getattr(self, 'queryset', None)

    def get_serializer_class(self):
        """Get serializer class for this viewset"""
        return getattr(self, 'serializer_class', None)

    @classmethod
    def as_view(cls, actions=None, **kwargs):
        """Create view functions from viewset"""
        actions = actions or {}

        def view_func(request, *args, **kwargs):
            viewset = cls()
            viewset.request = request
            viewset.kwargs = kwargs

            action = actions.get(request.method.lower())
            if action and hasattr(viewset, action):
                method = getattr(viewset, action)
                return method(request, *args, **kwargs)
            else:
                return Response("Method not allowed", status_code=405)

        return view_func


class ModelViewSet(ViewSet):
    """Model ViewSet with default CRUD operations"""

    lookup_field = 'id'
    lookup_url_kwarg = None
    pagination_class = None
    filter_backends = []
    ordering_fields = []
    search_fields = []

    def get_queryset(self):
        """Get the queryset for this viewset"""
        queryset = super().get_queryset()
        return self.filter_queryset(queryset)

    def get_serializer_class(self):
        """Get serializer class for this viewset"""
        return super().get_serializer_class()

    def get_object(self):
        """Get object for detail views"""
        queryset = self.get_queryset()
        if not queryset:
            return None

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.request.path_params.get(lookup_url_kwarg)

        if not lookup_value:
            return None

        # Try to find the object by lookup field
        try:
            if isinstance(queryset, list):
                for obj in queryset:
                    if hasattr(obj, self.lookup_field):
                        if str(getattr(obj, self.lookup_field)) == str(lookup_value):
                            return obj
                    elif hasattr(obj, '__getitem__') and self.lookup_field in obj:
                        if str(obj[self.lookup_field]) == str(lookup_value):
                            return obj
                return None
            else:
                return None
        except Exception:
            return None

    def filter_queryset(self, queryset):
        """Filter the queryset based on request parameters"""
        if not queryset:
            return queryset

        # Handle search
        search_term = self.request.query_params.get('search')
        if search_term and self.search_fields:
            if isinstance(queryset, list):
                filtered = []
                for obj in queryset:
                    for field in self.search_fields:
                        if hasattr(obj, field):
                            value = str(getattr(obj, field)).lower()
                            if search_term.lower() in value:
                                filtered.append(obj)
                                break
                        elif hasattr(obj, '__getitem__') and field in obj:
                            value = str(obj[field]).lower()
                            if search_term.lower() in value:
                                filtered.append(obj)
                                break
                queryset = filtered

        # Handle ordering
        ordering = self.request.query_params.get('ordering')
        if ordering and self.ordering_fields:
            if isinstance(queryset, list):
                reverse = ordering.startswith('-')
                field = ordering[1:] if reverse else ordering

                if field in self.ordering_fields:
                    queryset.sort(
                        key=lambda x: getattr(x, field) if hasattr(x, field) else x.get(field),
                        reverse=reverse
                    )

        # Handle field-specific filters
        for key, value in self.request.query_params.items():
            if key not in ['search', 'ordering', 'page', 'page_size']:
                if isinstance(queryset, list):
                    filtered = []
                    for obj in queryset:
                        if hasattr(obj, key):
                            if str(getattr(obj, key)) == str(value):
                                filtered.append(obj)
                        elif hasattr(obj, '__getitem__') and key in obj:
                            if str(obj[key]) == str(value):
                                filtered.append(obj)
                    queryset = filtered

        return queryset

    def paginate_queryset(self, queryset):
        """Paginate the queryset"""
        if not self.pagination_class:
            return None

        paginator = self.pagination_class()
        return paginator.paginate_queryset(queryset, self.request)

    def list(self, request):
        """List objects"""
        queryset = self.get_queryset()
        if not queryset:
            return Response([])

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer_class = self.get_serializer_class()
            if serializer_class:
                serializer = serializer_class(page, many=True)
                data = serializer.serialize(page)
                return Response({
                    'results': data,
                    'count': len(queryset) if isinstance(queryset, list) else getattr(queryset, 'count', lambda: len(data))(),
                    'page': request.query_params.get('page', 1),
                    'page_size': request.query_params.get('page_size', 10)
                })

        # No pagination - serialize all objects
        serializer_class = self.get_serializer_class()
        if serializer_class and isinstance(queryset, list):
            serializer = serializer_class(queryset, many=True)
            data = serializer.serialize(queryset)
            return Response(data)

        return Response([])

    def create(self, request):
        """Create object"""
        serializer_class = self.get_serializer_class()
        if serializer_class:
            serializer = serializer_class(data=request.data)
            if serializer and serializer.is_valid():
                instance = serializer.save()
                response_data = serializer.serialize(instance)
                return Response(response_data, status_code=201)
            else:
                return Response(serializer.errors if serializer else {"error": "Invalid data"}, status_code=400)
        return Response({"error": "No serializer"}, status_code=500)

    def retrieve(self, request, pk=None):
        """Retrieve object"""
        instance = self.get_object()
        if not instance:
            return Response({"error": "Not found"}, status_code=404)

        serializer_class = self.get_serializer_class()
        if serializer_class:
            serializer = serializer_class(instance)
            data = serializer.serialize(instance)
            return Response(data)
        return Response(instance)

    def update(self, request, pk=None):
        """Update object"""
        instance = self.get_object()
        if not instance:
            return Response({"error": "Not found"}, status_code=404)

        serializer_class = self.get_serializer_class()
        if serializer_class:
            serializer = serializer_class(instance, data=request.data)
            if serializer and serializer.is_valid():
                instance = serializer.save()
                response_data = serializer.serialize(instance)
                return Response(response_data)
            else:
                return Response(serializer.errors if serializer else {"error": "Invalid data"}, status_code=400)
        return Response({"error": "No serializer"}, status_code=500)

    def partial_update(self, request, pk=None):
        """Partial update object"""
        return self.update(request, pk)

    def destroy(self, request, pk=None):
        """Delete object"""
        instance = self.get_object()
        if not instance:
            return Response({"error": "Not found"}, status_code=404)

        # For now, just return success - in a real implementation,
        # this would remove the object from the data store
        return Response(status_code=204)


class APIRouter:
    """Router for API endpoints"""

    def __init__(self):
        self.routes = []
        self.viewsets = {}

    def add_api_view(self, path: str, view_class: Type[APIView], name: str = None):
        """Add API view to router"""
        self.routes.append({
            'path': path,
            'view_class': view_class,
            'name': name,
            'type': 'view'
        })

    def add_viewset(self, prefix: str, viewset_class: Type[ViewSet], basename: str = None):
        """Add viewset to router"""
        basename = basename or viewset_class.__name__.lower().replace('viewset', '')
        self.viewsets[basename] = {
            'prefix': prefix,
            'viewset_class': viewset_class,
            'basename': basename,
            'type': 'viewset'
        }

        # Auto-generate routes for standard actions
        self._register_viewset_routes(prefix, viewset_class, basename)

    def _register_viewset_routes(self, prefix: str, viewset_class: Type[ViewSet], basename: str):
        """Register standard CRUD routes for a viewset"""
        routes = [
            (f'{prefix}$', viewset_class, 'list', 'GET'),
            (f'{prefix}$', viewset_class, 'create', 'POST'),
            (f'{prefix}(?P<pk>[^/]+)/$', viewset_class, 'retrieve', 'GET'),
            (f'{prefix}(?P<pk>[^/]+)/$', viewset_class, 'update', 'PUT'),
            (f'{prefix}(?P<pk>[^/]+)/$', viewset_class, 'partial_update', 'PATCH'),
            (f'{prefix}(?P<pk>[^/]+)/$', viewset_class, 'destroy', 'DELETE'),
        ]

        for pattern, viewset_cls, action, method in routes:
            self.routes.append({
                'pattern': pattern,
                'viewset_class': viewset_cls,
                'action': action,
                'method': method,
                'basename': basename,
                'type': 'viewset_action'
            })

    def resolve(self, path: str, method: str) -> tuple:
        """Resolve URL path to view and action"""
        import re

        for route in self.routes:
            if route['type'] == 'view':
                # Simple exact match for API views
                if route['path'] == path:
                    return route['view_class'], None
            elif route['type'] == 'viewset_action':
                # Pattern matching for viewset actions
                pattern = route['pattern']
                match = re.match(pattern, path)
                if match and route['method'] == method:
                    return route['viewset_class'], route['action'], match.groupdict()

        return None, None

    def get_routes(self):
        """Get all routes"""
        return self.routes

    def get_viewsets(self):
        """Get all registered viewsets"""
        return self.viewsets


class APIVersioning:
    """API versioning"""

    def __init__(self, default_version: str = 'v1'):
        self.default_version = default_version

    def get_version(self, request: Request) -> str:
        """Get API version from request"""
        # Try different methods to get version
        version = None

        # From URL path
        if 'version' in request.path_params:
            version = request.path_params['version']

        # From Accept header
        accept = request.headers.get('Accept', '')
        if 'version=' in accept:
            version = accept.split('version=')[1].split(';')[0]

        # From query parameter
        if not version:
            version = request.query_params.get('version')

        return version or self.default_version


class Throttling:
    """API throttling with in-memory rate limiting"""

    def __init__(self, rate: str = '100/hour'):
        self.rate = rate
        self.requests_per_period = 0
        self.period_seconds = 3600  # 1 hour default
        self.requests = {}
        self.parse_rate()

    def parse_rate(self):
        """Parse rate string"""
        # Simple parsing: "100/hour" -> 100 requests per hour
        if '/' in self.rate:
            num, period = self.rate.split('/')
            self.requests_per_period = int(num)

            # Convert period to seconds
            period_multipliers = {
                'second': 1,
                'minute': 60,
                'hour': 3600,
                'day': 86400
            }
            self.period_seconds = period_multipliers.get(period, 3600)
        else:
            self.requests_per_period = 100
            self.period_seconds = 3600

    def get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for the client"""
        # Use IP address as client identifier
        # In a real implementation, you might use API keys or user IDs
        return request.client_ip or request.headers.get('X-Forwarded-For', 'unknown')

    def allow_request(self, request: Request) -> bool:
        """Check if request is allowed"""
        import time

        client_id = self.get_client_identifier(request)
        current_time = time.time()

        # Clean up old entries (older than 2 periods)
        cleanup_threshold = current_time - (self.period_seconds * 2)
        self.requests = {
            k: v for k, v in self.requests.items()
            if v['reset_time'] > cleanup_threshold
        }

        # Get or create client entry
        if client_id not in self.requests:
            self.requests[client_id] = {
                'count': 0,
                'reset_time': current_time + self.period_seconds,
                'first_request': current_time
            }

        client_data = self.requests[client_id]

        # Reset counter if period has passed
        if current_time >= client_data['reset_time']:
            client_data['count'] = 0
            client_data['reset_time'] = current_time + self.period_seconds
            client_data['first_request'] = current_time

        # Check if limit exceeded
        if client_data['count'] >= self.requests_per_period:
            return False

        # Increment counter
        client_data['count'] += 1
        return True

    def get_rate_limit_headers(self, request: Request) -> Dict[str, str]:
        """Get rate limit headers for response"""
        client_id = self.get_client_identifier(request)
        current_time = time.time()

        if client_id not in self.requests:
            return {
                'X-RateLimit-Limit': str(self.requests_per_period),
                'X-RateLimit-Remaining': str(self.requests_per_period),
                'X-RateLimit-Reset': str(int(current_time + self.period_seconds))
            }

        client_data = self.requests[client_id]
        remaining = max(0, self.requests_per_period - client_data['count'])

        return {
            'X-RateLimit-Limit': str(self.requests_per_period),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(int(client_data['reset_time']))
        }


# Decorators
def api_view(http_method_names: List[str] = None):
    """Decorator for API views"""
    def decorator(func: Callable) -> Callable:
        func.http_method_names = http_method_names or ['GET']
        func.api_view = True

        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if request.method.upper() not in func.http_method_names:
                return Response.json({"error": "Method not allowed"}, 405)

            try:
                result = await func(request, *args, **kwargs) if inspect.iscoroutinefunction(func) else func(request, *args, **kwargs)
                if isinstance(result, Response):
                    return result
                return Response.json(result)
            except APIException as e:
                return Response.json({"error": e.detail, "code": e.code}, e.status_code)
            except Exception as e:
                return Response.json({"error": str(e)}, 500)

        return wrapper
    return decorator


# Global instances
api_router = APIRouter()
pagination = PageNumberPagination()
versioning = APIVersioning()

__all__ = [
    'Serializer', 'ModelSerializer', 'APIView', 'GenericAPIView',
    'ListAPIView', 'CreateAPIView', 'RetrieveAPIView', 'UpdateAPIView', 'DestroyAPIView',
    'ListCreateAPIView', 'RetrieveUpdateAPIView', 'RetrieveUpdateDestroyAPIView',
    'ViewSet', 'ModelViewSet', 'APIRouter', 'PageNumberPaginator', 'LimitOffsetPaginator',
    'PaginationParams', 'PaginationResult', 'APIVersioning', 'APIException', 'ValidationError',
    'PermissionDenied', 'NotFound', 'Throttling', 'APIResponse',
    'api_view', 'api_router', 'pagination', 'versioning'
]
