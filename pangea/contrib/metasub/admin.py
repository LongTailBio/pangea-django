from django.contrib import admin

# MetaSUB has no models to register.
from .models import (
    KoboAsset,
    MetaSUBCity,
    KoboUser,
    KoboResult,
)


@admin.register(KoboAsset)
class KoboAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'city', 'result_count')

    def result_count(self, obj):
        return obj.kobo_results.count()


@admin.register(MetaSUBCity)
class MetaSUBCityAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'latitude', 'asset_count')

    def asset_count(self, obj):
        return obj.kobo_assets.count()


@admin.register(KoboUser)
class KoboUserAdmin(admin.ModelAdmin):
    list_display = ('username',)


@admin.register(KoboResult)
class KoboResultAdmin(admin.ModelAdmin):
    list_display = ('kobo_id',)
