"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView, TemplateView
from django.contrib.sitemaps.views import sitemap
from issue.sitemaps import IssueSitemap, ArticleSitemap

sitemaps = {
    'issues': IssueSitemap,
    'articles': ArticleSitemap,
}

urlpatterns = [
    path('rosetta/', include('rosetta.urls')),  # Rosetta URLs first
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),  # robots
]

urlpatterns += i18n_patterns(
    path("", include("core.urls")),
    path("subscribe/", include("subscribe.urls")),
    path("about/", include("about.urls")),
    path("submit/", include("submit.urls")),
    path("issue/", include("issue.urls")),
)
