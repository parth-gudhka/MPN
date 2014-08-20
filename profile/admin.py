from django.contrib import admin
# Please refer to this site for explanation of why this is done:
from django.db.models import Q
from operator import __or__ as OR
# http://simeonfranklin.com/blog/2011/jun/14/best-way-or-list-django-orm-q-objects/
from profile.models import Membership, Center, Profile
from masters.models import Role
from .models import (Profile, YMHTMobile,
                    YMHTEmail, YMHTAddress, YMHTEducation, YMHTJob,
                    Membership,
                    GNCSewaDetails, LocalEventSewaDetails, GlobalEventSewaDetails)
from Sessions.models import *
from django_countries.fields import CountryField
from django import forms


class YMHTMobileInline(admin.StackedInline):
    model = YMHTMobile
    extra = 1
class YMHTEmailInline(admin.StackedInline):
    model = YMHTEmail
    extra = 1
    
class YMHTAddressInline(admin.StackedInline):
    model = YMHTAddress
    extra = 1

class YMHTEducationInline(admin.StackedInline):
    

    model = YMHTEducation
    extra = 1
class YMHTJobInline(admin.StackedInline):
    model = YMHTJob
    extra = 1

class RequiredFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(RequiredFormSet, self).__init__(*args, **kwargs)
        self.forms[0].empty_permitted = False

class YMHTMembershipInline(admin.StackedInline):
    fields = ('ymht' , 'center' , 'age_group' , 'role', 'since', 'till', 'is_active')
    model = Membership
    formset = RequiredFormSet
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if request.user.is_superuser:
            return super(YMHTMembershipInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

        if not Profile.objects.filter(user=request.user).exists():
            print "Does not exist"
            return super(YMHTMembershipInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

        current_profile = Profile.objects.get(user=request.user)
        current_members = Membership.objects.filter(ymht=current_profile)
        #DEBUG: print current_members 
        current_centers_pk = []
        current_age_group_pk = []
        current_roles = []
        for member in current_members:
            if member.is_active:
                print member.center
                current_centers_pk.append(member.center.pk)
                current_age_group_pk.append(member.age_group.pk)
                current_roles.append(member.role.level)
        # print "Length of centers:", len(current_members)
        # print current_members
        if db_field.name == 'center':
            kwargs['queryset'] = Center.objects.filter(pk__in=current_centers_pk)
        if db_field.name == 'age_group':
            kwargs['queryset'] = AgeGroup.objects.filter(pk__in=current_age_group_pk)
        if db_field.name == 'role':
            kwargs['queryset'] = Role.objects.filter(level__lt=max(current_roles))
        #permission for role to be decide later

        # if db_field.name == 'role':
        #     kwargs['queryset'] = Role.objects.exclude(role='Coordinator')
        return super(YMHTMembershipInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    extra = 1

#     def formfield_for_foreignkey(self, db_field, request, **kwargs):
#         if request.user.is_superuser:
#             return super(YMHTMembershipInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
# # If Profile for current user does not exist, then what to do?
#         if not Profile.objects.filter(user=request.user).exists():
#             return super(YMHTMembershipInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

#         current_profile = Profile.objects.get(user=request.user)
#         current_members = Membership.objects.filter(ymht=current_profile)
#         current_centers_pk = []
#         current_age_group_pk = []
#         for member in current_members:
#             if member.is_active:
#                 current_centers_pk.append(member.center.pk)
#                 current_age_group_pk.append(member.age_group.pk)    
#         if db_field.name == 'center':
#             kwargs['queryset'] = Center.objects.filter(pk__in=current_centers_pk)
#         if db_field.name == 'age_group':
#             kwargs['queryset'] = AgeGroup.objects.filter(pk__in=current_age_group_pk)
#         return super(YMHTMembershipInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

class GlobalEventSewaDetailsInline(admin.StackedInline):
    #fields = ('event', 'ymht' , 'coordinator', 'attended' , 'attended_days' , 'comments')
    model = GlobalEventSewaDetails
    extra = 1


class LocalEventSewaDetailsInline(admin.StackedInline):
    #fields = ('event', 'ymht' , 'coordinator', 'attended' , 'attended_days' , 'comments')
    model = LocalEventSewaDetails
    extra = 1

class GNCSewaDetailsInline(admin.StackedInline):
    #fields = ('event', 'ymht' , 'coordinator', 'attended' , 'attended_days' , 'comments')
    model = GNCSewaDetails
    extra = 1

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'date_of_birth', 'gnan_date')
    list_filter = ('first_name',)
    search_fields = ('first_name','last_name')
    inlines = [
        YMHTMobileInline,
        YMHTEmailInline,
        YMHTAddressInline,
        YMHTEducationInline,
        YMHTJobInline,
        YMHTMembershipInline,
        GlobalEventSewaDetailsInline,
        LocalEventSewaDetailsInline,
        GNCSewaDetailsInline,
    ]

    def queryset(self, request):
        qs = super(ProfileAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs

        if not Profile.objects.filter(user=request.user).exists():
            return Profile.objects.none()
        current_profile = Profile.objects.get(user=request.user)
        
        if not Membership.objects.filter(ymht=current_profile).exists():
            return Profile.objects.none()
        
        current_members = Membership.objects.filter(ymht=current_profile)
        current_centers = []
        current_age_groups = []
        current_roles = []
        for member in current_members:
            if member.is_active:
                current_roles.append(member.role.level)
                current_centers.append(member.center)
                current_age_groups.append(member.age_group)
        memberships = []
# For clarification on how to operate on list of Querysets, please visit:
# http://simeonfranklin.com/blog/2011/jun/14/best-way-or-list-django-orm-q-objects/
        for i,item in enumerate(current_roles):
            if current_roles[i]>2:
                memberships.append(Membership.objects.filter(center=current_centers[i],
                    age_group=current_age_groups[i], role__level__lte=current_roles[i]))
            else:
                memberships.append(Membership.objects.filter(center=current_centers[i],
                    age_group=current_age_groups[i], role__level__lt=current_roles[i]))

        #Filtered the queryset twice based on age_group & center
        # filtered_qs = qs.filter(membership__in=memberships)
        qs =  qs.filter(membership__in=reduce(OR, memberships))
        return qs.distinct()
    #extra = 1            

admin.site.register(Profile, ProfileAdmin)
