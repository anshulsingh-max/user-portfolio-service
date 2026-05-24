# admin.py
from urllib.parse import unquote

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from multitenant.tenant_context import get_current_tenant


class TenantAwareModelAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        db = get_current_tenant()
        self.tenant_id = db
        return super().get_queryset(request).using(db)

    def save_model(self, request, obj, form, change):
        db = get_current_tenant()
        obj.save(using=db)

    def delete_model(self, request, obj):
        db = get_current_tenant()
        obj.delete(using=db)

    def save_related(self, request, form, formsets, change):
        db = get_current_tenant()
        for formset in formsets:
            formset.save(using=db)

    def response_add(self, request, obj, post_url_continue=None):
        """
        Overrides the default response after adding an object to redirect
        to the tenant-specific changelist page.
        """
        tenant_id = request.tenant_id
        if '_addanother' in request.POST:
            # "Save and add another" was clicked
            url = reverse(f'tenant_admin:{obj._meta.app_label}_{obj._meta.model_name}_add')
        elif '_continue' in request.POST:
            # "Save and continue editing" was clicked
            url = reverse(f'tenant_admin:{obj._meta.app_label}_{obj._meta.model_name}_change', args=(obj.pk,))
        else:
            # Default to returning to the changelist view
            url = reverse(f'tenant_admin:{obj._meta.app_label}_{obj._meta.model_name}_changelist')

        unquote_url = unquote(url)
        if tenant_id:
            unquote_url = unquote_url.replace('^', tenant_id)
        return HttpResponseRedirect(unquote_url)

    def response_change(self, request, obj):
        """
        Overrides the default response after editing an object to redirect
        to the tenant-specific changelist page.
        """
        tenant_id = getattr(request, 'tenant_id', None)  # Adjust based on your tenant implementation
        if '_continue' in request.POST:
            # "Save and continue editing" was clicked
            url = reverse(f'tenant_admin:{obj._meta.app_label}_{obj._meta.model_name}_change', args=[obj.pk])
        elif '_addanother' in request.POST:
            # "Save and add another" was clicked
            url = reverse(f'tenant_admin:{obj._meta.app_label}_{obj._meta.model_name}_add')
        else:
            # Default to returning to the changelist view
            url = reverse(f'tenant_admin:{obj._meta.app_label}_{obj._meta.model_name}_changelist')
        unquote_url = unquote(url)
        if tenant_id:
            unquote_url = unquote_url.replace('^', tenant_id)  # Adjust this line based on your URL structure

        return HttpResponseRedirect(unquote_url)
