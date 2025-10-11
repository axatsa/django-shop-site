from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from django.http import HttpResponse

schema_view = get_schema_view(
    openapi.Info(
        title="Shop API",
        default_version='v1',
        description="API documentation",
    ),
    public=True,
    permission_classes=(AllowAny,),
)

def home(request):
    return HttpResponse(
        """
        <!DOCTYPE html>
        <html lang=\"ru\">
        <head>
            <meta charset=\"UTF-8\" />
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
            <title>Главная — Shop API</title>
            <style>
                body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin:0; background:#0f172a; color:#e2e8f0; }
                .wrap { max-width: 920px; margin: 0 auto; padding: 48px 20px; }
                h1 { font-size: 32px; margin: 0 0 8px; }
                p.lead { color:#94a3b8; margin: 0 0 24px; }
                .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:16px; margin-top: 24px; }
                a.card { display:block; padding:16px; border-radius:12px; text-decoration:none; color:inherit; background:#111827; border:1px solid #1f2937; transition: transform .1s ease, border-color .1s ease; }
                a.card:hover { transform: translateY(-2px); border-color:#334155; }
                .title { font-weight:600; margin-bottom:6px; }
                .desc { color:#94a3b8; font-size: 14px; }
                footer { margin-top: 36px; color:#64748b; font-size: 13px; }
                code { background: #0b1220; border:1px solid #1f2937; padding: 1px 6px; border-radius:6px; }
            </style>
        </head>
        <body>
            <div class=\"wrap\">
                <h1>Shop API</h1>
                <p class=\"lead\">Django REST Framework + JWT + Swagger + ReDoc. Быстрые ссылки:</p>

                <div class=\"grid\">
                    <a class=\"card\" href=\"/api/\">
                        <div class=\"title\">DRF API Root</div>
                        <div class=\"desc\">Обозреваемый API от Django REST Framework</div>
                    </a>
                    <a class=\"card\" href=\"/swagger/\">
                        <div class=\"title\">Swagger UI</div>
                        <div class=\"desc\">Интерактивная документация API (OpenAPI)</div>
                    </a>
                    <a class=\"card\" href=\"/redoc/\">
                        <div class=\"title\">ReDoc</div>
                        <div class=\"desc\">Альтернативная документация API</div>
                    </a>
                    <a class=\"card\" href=\"/admin/\">
                        <div class=\"title\">Django Admin</div>
                        <div class=\"desc\">Управление товарами и заказами</div>
                    </a>
                </div>

                <footer>
                    Авторизация JWT: <code>POST /api/auth/login/</code>, профиль: <code>GET /api/auth/me/</code>
                </footer>
            </div>
        </body>
        </html>
        """,
        content_type="text/html; charset=utf-8",
    )

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('site_app.urls')),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
