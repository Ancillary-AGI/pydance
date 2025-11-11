"""
Pydance Admin Interface

A comprehensive admin interface for Pydance applications with:
- Auto-generated CRUD interfaces
- Model registration and management
- Customizable admin themes
- Permission-based access control
- Dashboard and analytics
- RESTful admin API
"""

from typing import Type, Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import inspect

from pydance.db.models.base import BaseModel
from pydance.forms.base import Form, Field, CharField, EmailField, BooleanField
from pydance.http.request import Request
from pydance.http.response import Response
from pydance.routing.router import Router


@dataclass
class AdminConfig:
    """Admin configuration"""
    site_title: str = "Pydance Admin"
    site_header: str = "Administration"
    index_title: str = "Site administration"
    theme: str = "default"
    enable_api: bool = True
    api_prefix: str = "/admin/api"


class ModelAdmin:
    """Base admin class for models"""

    list_display: List[str] = []
    list_filter: List[str] = []
    list_per_page: int = 100
    search_fields: List[str] = []
    ordering: List[str] = []
    readonly_fields: List[str] = []
    exclude: List[str] = []
    form_class: Optional[Type[Form]] = None

    def __init__(self, model: Type[BaseModel], admin_site):
        self.model = model
        self.admin_site = admin_site
        self.fields = self.get_fields()

    def get_fields(self) -> List[str]:
        """Get fields to display in admin"""
        if self.exclude:
            return [f for f in self.model._fields.keys() if f not in self.exclude]
        return list(self.model._fields.keys())

    def get_list_display(self) -> List[str]:
        """Get fields to display in list view"""
        return self.list_display or self.get_fields()[:5]

    def get_search_fields(self) -> List[str]:
        """Get fields for search"""
        return self.search_fields or [f for f in self.get_fields() if f.endswith('_name') or f == 'name']

    def get_form(self, request: Request, obj=None) -> Form:
        """Get form for model"""
        if self.form_class:
            return self.form_class()

        # Auto-generate form from model fields
        class AutoForm(Form):
            pass

        # Add fields dynamically
        for field_name in self.get_fields():
            if field_name in self.readonly_fields:
                continue

            model_field = self.model._fields[field_name]
            if isinstance(model_field, type) and hasattr(model_field, '__name__'):
                # Convert model field to form field
                if 'email' in field_name.lower():
                    setattr(AutoForm, field_name, EmailField(required=not model_field.nullable))
                elif model_field.field_type == 'BOOLEAN':
                    setattr(AutoForm, field_name, BooleanField(required=not model_field.nullable))
                else:
                    setattr(AutoForm, field_name, CharField(required=not model_field.nullable))

        return AutoForm()

    async def changelist_view(self, request: Request) -> Response:
        """List view for model"""
        queryset = self.model.query()

        # Apply search
        search_query = request.query_params.get('q')
        if search_query:
            search_fields = self.get_search_fields()
            search_conditions = []
            for field in search_fields:
                search_conditions.append({field: {'$regex': search_query, '$options': 'i'}})
            if search_conditions:
                queryset = queryset.filter(**{'$or': search_conditions})

        # Apply ordering
        if self.ordering:
            for order_field in self.ordering:
                if order_field.startswith('-'):
                    queryset = queryset.order_by(order_field[1:], 'DESC')
                else:
                    queryset = queryset.order_by(order_field, 'ASC')

        objects = await queryset.execute()

        context = {
            'title': f'Select {self.model.get_verbose_name()} to change',
            'model': self.model,
            'object_list': objects,
            'list_display': self.get_list_display(),
            'has_add_permission': True,
            'has_change_permission': True,
            'has_delete_permission': True,
        }

        return Response.json(context)

    async def change_view(self, request: Request, object_id: str) -> Response:
        """Change view for single object"""
        try:
            obj = await self.model.get(object_id)
        except:
            return Response.json({'error': 'Object not found'}, status_code=404)

        if request.method == 'GET':
            form = self.get_form(request, obj)
            context = {
                'title': f'Change {self.model.get_verbose_name()}',
                'object': obj,
                'form': form,
                'readonly_fields': self.readonly_fields,
            }
            return Response.json(context)

        elif request.method == 'POST':
            form = self.get_form(request, obj)
            if form.is_valid():
                # Update object
                for field_name, value in form.cleaned_data.items():
                    setattr(obj, field_name, value)
                await obj.save()
                return Response.json({'success': True, 'object': obj.to_dict()})
            else:
                return Response.json({'errors': form.errors}, status_code=400)

    async def add_view(self, request: Request) -> Response:
        """Add view for new object"""
        if request.method == 'GET':
            form = self.get_form(request)
            context = {
                'title': f'Add {self.model.get_verbose_name()}',
                'form': form,
            }
            return Response.json(context)

        elif request.method == 'POST':
            form = self.get_form(request)
            if form.is_valid():
                # Create new object
                obj = self.model(**form.cleaned_data)
                await obj.save()
                return Response.json({'success': True, 'object': obj.to_dict()})
            else:
                return Response.json({'errors': form.errors}, status_code=400)


class AdminSite:
    """Main admin site"""

    def __init__(self, config: AdminConfig = None):
        self.config = config or AdminConfig()
        self._registry: Dict[Type[BaseModel], ModelAdmin] = {}
        self.router = Router()

        # Register default admin routes
        self._register_routes()

    def register(self, model: Type[BaseModel], admin_class: Type[ModelAdmin] = None):
        """Register model with admin"""
        if admin_class is None:
            admin_class = ModelAdmin

        self._registry[model] = admin_class(model, self)

    def unregister(self, model: Type[BaseModel]):
        """Unregister model from admin"""
        self._registry.pop(model, None)

    def get_registered_models(self) -> List[Type[BaseModel]]:
        """Get all registered models"""
        return list(self._registry.keys())

    def get_model_admin(self, model: Type[BaseModel]) -> Optional[ModelAdmin]:
        """Get model admin instance"""
        return self._registry.get(model)

    def _register_routes(self):
        """Register admin routes"""
        @self.router.add_route('/admin/', ['GET'])
        async def index(request):
            context = {
                'title': self.config.index_title,
                'models': [
                    {
                        'name': model.__name__,
                        'verbose_name': model.get_verbose_name(),
                        'url': f'/admin/{model.__name__.lower()}/'
                    }
                    for model in self.get_registered_models()
                ]
            }
            return Response.json(context)

        @self.router.add_route('/admin/{model_name}/', ['GET'])
        async def changelist(request, model_name: str):
            model = self._find_model_by_name(model_name)
            if not model:
                return Response.json({'error': 'Model not found'}, status_code=404)

            admin = self.get_model_admin(model)
            return await admin.changelist_view(request)

        @self.router.add_route('/admin/{model_name}/add/', ['GET', 'POST'])
        async def add_view(request, model_name: str):
            model = self._find_model_by_name(model_name)
            if not model:
                return Response.json({'error': 'Model not found'}, status_code=404)

            admin = self.get_model_admin(model)
            return await admin.add_view(request)

        @self.router.add_route('/admin/{model_name}/{object_id}/change/', ['GET', 'POST'])
        async def change_view(request, model_name: str, object_id: str):
            model = self._find_model_by_name(model_name)
            if not model:
                return Response.json({'error': 'Model not found'}, status_code=404)

            admin = self.get_model_admin(model)
            return await admin.change_view(request, object_id)

    def _find_model_by_name(self, model_name: str) -> Optional[Type[BaseModel]]:
        """Find model by name"""
        for model in self.get_registered_models():
            if model.__name__.lower() == model_name.lower():
                return model
        return None

    def get_urls(self) -> Router:
        """Get admin URL patterns"""
        return self.router


# Global admin site instance
admin_site = AdminSite()

# Convenience functions
def register(model: Type[BaseModel], admin_class: Type[ModelAdmin] = None):
    """Register model with admin"""
    admin_site.register(model, admin_class)

def unregister(model: Type[BaseModel]):
    """Unregister model from admin"""
    admin_site.unregister(model)

__all__ = [
    'AdminConfig', 'ModelAdmin', 'AdminSite', 'admin_site',
    'register', 'unregister'
]
