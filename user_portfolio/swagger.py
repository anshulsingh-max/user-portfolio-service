"""
    Swagger Schema generator
"""
from drf_yasg.generators import OpenAPISchemaGenerator


class HttpAndHttpsSchemaGenerator(OpenAPISchemaGenerator):
    """
       Class of swagger schema generator
    """
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ["http", "https"]
        return schema
