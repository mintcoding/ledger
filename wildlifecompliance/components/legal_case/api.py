import json
import re
import operator
import traceback
import os
import base64
import geojson
from django.db.models import Q, Min, Max
from django.db import transaction
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from django.conf import settings
from wildlifecompliance import settings
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework import viewsets, serializers, status, generics, views, filters
import rest_framework.exceptions as rest_exceptions
from rest_framework.decorators import (
    detail_route,
    list_route,
    renderer_classes,
    parser_classes,
    api_view
)
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser, BasePermission
from rest_framework.pagination import PageNumberPagination
from collections import OrderedDict
from django.core.cache import cache
from ledger.accounts.models import EmailUser, Address
from ledger.address.models import Country
from ledger.checkout.utils import calculate_excl_gst
from datetime import datetime, timedelta, date
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from wildlifecompliance.components.main.api import save_location
from wildlifecompliance.components.main.models import TemporaryDocumentCollection
from wildlifecompliance.components.main.process_document import (
        process_generic_document, 
        save_comms_log_document_obj
        )
from wildlifecompliance.components.main.email import prepare_mail
from wildlifecompliance.components.users.serializers import (
    UserAddressSerializer,
    ComplianceUserDetailsSerializer,
)
from wildlifecompliance.helpers import is_customer, is_internal
from wildlifecompliance.components.legal_case.models import (
        LegalCase,
        LegalCaseUserAction,
        LegalCaseCommsLogEntry,
        LegalCaseCommsLogDocument,
        LegalCasePriority,
        LegalCaseRunningSheetEntry,
)

from wildlifecompliance.components.call_email.models import (
        CallEmailUserAction,
        )
from wildlifecompliance.components.legal_case.serializers import (
        LegalCaseSerializer,
        SaveLegalCaseSerializer,
        LegalCaseUserActionSerializer,
        LegalCaseCommsLogEntrySerializer,
        LegalCaseDatatableSerializer,
        UpdateAssignedToIdSerializer,
        LegalCasePrioritySerializer,
        CreateLegalCaseRunningSheetEntrySerializer,
        SaveLegalCaseRunningSheetEntrySerializer,
        LegalCaseRunningSheetSerializer,
        )
from wildlifecompliance.components.users.models import (
    CompliancePermissionGroup,    
)
from wildlifecompliance.components.organisations.models import (
    Organisation,    
)
from django.contrib.auth.models import Permission, ContentType
#from utils import SchemaParser

from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.renderers import DatatablesRenderer

from wildlifecompliance.components.legal_case.email import (
    send_mail)
from reversion.models import Version
#import unicodedata


class LegalCaseFilterBackend(DatatablesFilterBackend):

    def filter_queryset(self, request, queryset, view):
        #import ipdb; ipdb.set_trace()
        # Get built-in DRF datatables queryset first to join with search text, then apply additional filters
        # super_queryset = super(CallEmailFilterBackend, self).filter_queryset(request, queryset, view).distinct()

        total_count = queryset.count()
        status_filter = request.GET.get('status_description')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        search_text = request.GET.get('search[value]')

        if search_text:
            search_text = search_text.lower()
            search_text_legal_case_ids = []
            for legal_case in queryset:
                #lodged_on_str = time.strftime('%d/%m/%Y', call_email.lodged_on)
                case_created_date_str = legal_case.case_created_date.strftime('%d/%m/%Y') if legal_case.case_created_date else ''
                if (search_text in (legal_case.number.lower() if legal_case.number else '')
                    or search_text in (legal_case.status.lower() if legal_case.status else '')
                    or search_text in (case_created_date_str.lower() if case_created_date_str else '')
                    or search_text in (legal_case.title.lower() if legal_case.title else '')
                    or search_text in (
                        legal_case.assigned_to.first_name.lower() + ' ' + legal_case.assigned_to.last_name.lower()
                        if legal_case.assigned_to else ''
                        )
                    ):
                    search_text_legal_case_ids.append(legal_case.id)

            # use pipe to join both custom and built-in DRF datatables querysets (returned by super call above)
            # (otherwise they will filter on top of each other)
            #_queryset = queryset.filter(id__in=search_text_callemail_ids).distinct() | super_queryset
            # BB 20190704 - is super_queryset necessary?
            queryset = queryset.filter(id__in=search_text_legal_case_ids)

        status_filter = status_filter.lower() if status_filter else 'all'
        if status_filter != 'all':
            status_filter_legal_case_ids = []
            for legal_case in queryset:
                if status_filter == legal_case.get_status_display().lower():
                    status_filter_legal_case_ids.append(legal_case.id)
            queryset = queryset.filter(id__in=status_filter_legal_case_ids)

        if date_from:
            queryset = queryset.filter(case_created_date__gte=date_from)
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(case_created_date__lte=date_to)

        # override queryset ordering, required because the ordering is usually handled
        # in the super call, but is then clobbered by the custom queryset joining above
        # also needed to disable ordering for all fields for which data is not an
        # CallEmail model field, as property functions will not work with order_by
        
        getter = request.query_params.get
        fields = self.get_fields(getter)
        ordering = self.get_ordering(getter, fields)
        if len(ordering):
            for num, item in enumerate(ordering):
                #if item == 'planned_for':
                #    # ordering.pop(num)
                #    # ordering.insert(num, 'planned_for_date')
                #    ordering[num] = 'planned_for_date'
                #elif item == '-planned_for':
                #    # ordering.pop(num)
                #    # ordering.insert(num, '-planned_for_date')
                #    ordering[num] = '-planned_for_date'
                if item == 'status__name':
                    # ordering.pop(num)
                    # ordering.insert(num, 'status')
                    ordering[num] = 'status'
                elif item == '-status__name':
                    # ordering.pop(num)
                    # ordering.insert(num, '-status')
                    ordering[num] = '-status'

            queryset = queryset.order_by(*ordering)

        setattr(view, '_datatables_total_count', total_count)
        return queryset


class LegalCaseRenderer(DatatablesRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if 'view' in renderer_context and hasattr(renderer_context['view'], '_datatables_total_count'):
            data['recordsTotal'] = renderer_context['view']._datatables_total_count
        return super(LegalCaseRenderer, self).render(data, accepted_media_type, renderer_context)


class LegalCasePaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (LegalCaseFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    renderer_classes = (LegalCaseRenderer,)
    queryset = LegalCase.objects.none()
    serializer_class = LegalCaseDatatableSerializer
    page_size = 10
    
    def get_queryset(self):
        # import ipdb; ipdb.set_trace()
        user = self.request.user
        if is_internal(self.request):
            return LegalCase.objects.all()
        return LegalCase.objects.none()

    @list_route(methods=['GET', ])
    def get_paginated_datatable(self, request, *args, **kwargs):
        print(request.GET)
        queryset = self.get_queryset()

        queryset = self.filter_queryset(queryset)
        self.paginator.page_size = queryset.count()
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = LegalCaseDatatableSerializer(
            result_page, many=True, context={'request': request})
        return self.paginator.get_paginated_response(serializer.data)


class LegalCaseViewSet(viewsets.ModelViewSet):
    queryset = LegalCase.objects.all()
    serializer_class = LegalCaseSerializer

    def get_queryset(self):
        # import ipdb; ipdb.set_trace()
        user = self.request.user
        if is_internal(self.request):
            return LegalCase.objects.all()
        return LegalCase.objects.none()

    @list_route(methods=['GET', ])
    def datatable_list(self, request, *args, **kwargs):
        try:
            qs = self.get_queryset()
            serializer = LegalCaseDatatableSerializer(
                qs, many=True, context={'request': request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @list_route(methods=['GET', ])    
    def status_choices(self, request, *args, **kwargs):
        res_obj = [] 
        for choice in LegalCase.STATUS_CHOICES:
            res_obj.append({'id': choice[0], 'display': choice[1]});
        res_json = json.dumps(res_obj)
        return HttpResponse(res_json, content_type='application/json')
    
    @detail_route(methods=['GET', ])
    def action_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.action_logs.all()
            serializer = LegalCaseUserActionSerializer(qs, many=True)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET', ])
    def comms_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.comms_logs.all()
            serializer = LegalCaseCommsLogEntrySerializer(qs, many=True)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST', ])
    @renderer_classes((JSONRenderer,))
    def add_comms_log(self, request, instance=None, workflow=False, *args, **kwargs):
        try:
            with transaction.atomic():
                # create Inspection instance if not passed to this method
                if not instance:
                    instance = self.get_object()
                # add Inspection attribute to request_data
                request_data = request.data.copy()
                request_data['legal_case'] = u'{}'.format(instance.id)
                if request_data.get('comms_log_id'):
                    comms = LegalCaseCommsLogEntry.objects.get(
                        id=request_data.get('comms_log_id')
                        )
                    serializer = LegalCaseCommsLogEntrySerializer(
                        instance=comms, 
                        data=request.data)
                else:
                    serializer = LegalCaseCommsLogEntrySerializer(
                        data=request_data
                        )
                serializer.is_valid(raise_exception=True)
                # overwrite comms with updated instance
                comms = serializer.save()
                
                if workflow:
                    return comms
                else:
                    return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    #@list_route(methods=['GET', ])
    #def optimised(self, request, *args, **kwargs):
    #    queryset = self.get_queryset().exclude(location__isnull=True)

    #    filter_inspection_type = request.query_params.get('inspection_type', '')
    #    filter_inspection_type = '' if filter_inspection_type.lower() == 'all' else filter_inspection_type
    #    filter_status = request.query_params.get('status', '')
    #    filter_status = '' if filter_status.lower() == 'all' else filter_status
    #    filter_date_from = request.query_params.get('date_from', '')
    #    filter_date_to = request.query_params.get('date_to', '')

    #    q_list = []
    #    if filter_inspection_type:
    #        q_list.append(Q(inspection_type__id=filter_inspection_type))
    #    if filter_status:
    #        q_list.append(Q(status__exact=filter_status))
    #    if filter_date_from:
    #        date_from = datetime.strptime(filter_date_from, '%d/%m/%Y')
    #        q_list.append(Q(planned_for_date__gte=date_from))
    #    if filter_date_to:
    #        date_to = datetime.strptime(filter_date_to, '%d/%m/%Y')
    #        q_list.append(Q(planned_for_date__lte=date_to))

    #    print q_list

    #    queryset = queryset.filter(reduce(operator.and_, q_list)) if len(q_list) else queryset

    #    serializer = InspectionOptimisedSerializer(queryset, many=True)
    #    return Response(serializer.data)


    #@detail_route(methods=['PUT', ])
    @renderer_classes((JSONRenderer,))
    #def inspection_save(self, request, workflow=False, *args, **kwargs):
    def update(self, request, workflow=False, *args, **kwargs):
        print(request.data)
        try:
            with transaction.atomic():
                running_sheet_entries = request.data.get('running_sheet_transform')
                running_sheet_saved = None
                if running_sheet_entries and len(running_sheet_entries) > 0:
                    for entry in running_sheet_entries:
                        entry_copy = dict(entry)
                        description = entry_copy.get('description', '')
                        clean_description = description.replace(u'\xa0', u' ')
                        entry_copy.update({'description': clean_description})
                        entry_id = LegalCaseRunningSheetEntry.objects.get(id = entry_copy.get('id'))
                        running_sheet_entry_serializer = SaveLegalCaseRunningSheetEntrySerializer(
                                instance=entry_id, 
                                data=entry_copy)
                        running_sheet_entry_serializer.is_valid(raise_exception=True)
                        if running_sheet_entry_serializer.is_valid():
                            running_sheet_entry_serializer.save()
                    running_sheet_saved = True

                instance = self.get_object()
                serializer = SaveLegalCaseSerializer(instance, data=request.data)
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid() and \
                    (not running_sheet_entries or (running_sheet_entries and running_sheet_saved)):
                    serializer.save()
                    instance.log_user_action(
                            LegalCaseUserAction.ACTION_SAVE_LEGAL_CASE.format(
                            instance.number), request)
                    headers = self.get_success_headers(serializer.data)
                    return_serializer = LegalCaseSerializer(instance, context={'request': request})
                    return Response(
                            return_serializer.data,
                            status=status.HTTP_201_CREATED,
                            headers=headers
                            )
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST', ])
    @renderer_classes((JSONRenderer,))
    def update_assigned_to_id(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = None

            validation_serializer = LegalCaseSerializer(instance, context={'request': request})
            user_in_group = validation_serializer.data.get('user_in_group')

            if request.data.get('current_user') and user_in_group:
                serializer = UpdateAssignedToIdSerializer(
                        instance=instance,
                        data={
                            'assigned_to_id': request.user.id,
                            }
                        )
            elif user_in_group:
                serializer = UpdateAssignedToIdSerializer(instance=instance, data=request.data)
            
            if serializer:
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    serializer.save()
                    return_serializer = LegalCaseSerializer(instance=instance,
                            context={'request': request}
                            )
                    headers = self.get_success_headers(return_serializer.data)
                    return Response(
                            return_serializer.data, 
                            status=status.HTTP_201_CREATED,
                            headers=headers
                            )
            else:
                return Response(validation_serializer.data, 
                                status=status.HTTP_201_CREATED
                                )
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def process_default_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            returned_data = process_generic_document(request, instance)
            if returned_data:
                return Response(returned_data)
            else:
                return Response()

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0].encode('utf-8')))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def process_comms_log_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            returned_data = process_generic_document(
                request, 
                instance, 
                document_type='comms_log'
                )
            if returned_data:
                return Response(returned_data)
            else:
                return Response()

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0].encode('utf-8')))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def create(self, request, *args, **kwargs):
        print("create")
        print(request.data)
        try:
            with transaction.atomic():
                serializer = SaveLegalCaseSerializer(
                        data=request.data, 
                        partial=True
                        )
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    print("serializer.validated_data")
                    print(serializer.validated_data)
                    instance = serializer.save()
                    instance.log_user_action(
                            LegalCaseUserAction.ACTION_CREATE_LEGAL_CASE.format(
                            instance.number), request)
                    # Create comms_log and send mail
                    res = self.workflow_action(request, instance, create_legal_case=True)
                    if instance.call_email:
                        print("update parent")
                        self.update_parent(request, instance)
                    return res
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0].encode('utf-8')))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def update_parent(self, request, instance, *args, **kwargs):
        # Log parent actions and update status
        if instance.call_email:
            instance.call_email.log_user_action(
                    CallEmailUserAction.ACTION_ALLOCATE_FOR_LEGAL_CASE.format(
                    instance.call_email.number), request)
            #instance.call_email.status = 'open_inspection'
            #instance.call_email.save()
            instance.call_email.close(request)

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def workflow_action(self, request, instance=None, create_legal_case=None, *args, **kwargs):
        print("workflow action")
        print(request.data)
        try:
            with transaction.atomic():
                # email recipient
                #recipient_id = None

                if not instance:
                    instance = self.get_object()

                comms_log_id = request.data.get('inspection_comms_log_id')
                if comms_log_id and comms_log_id is not 'null':
                    workflow_entry = instance.comms_logs.get(
                            id=comms_log_id)
                else:
                    workflow_entry = self.add_comms_log(request, instance, workflow=True)
                    temporary_document_collection_id = request.data.get('temporary_document_collection_id')
                    if temporary_document_collection_id:
                        temp_doc_collection, created = TemporaryDocumentCollection.objects.get_or_create(
                                id=temporary_document_collection_id)
                        if temp_doc_collection:
                            for doc in temp_doc_collection.documents.all():
                                save_comms_log_document_obj(instance, workflow_entry, doc)
                            temp_doc_collection.delete()

                ## Set Inspection status depending on workflow type
                #workflow_type = request.data.get('workflow_type')
                #if workflow_type == 'send_to_manager':
                #    instance.send_to_manager(request)
                #elif workflow_type == 'request_amendment':
                #    instance.request_amendment(request)
                #elif workflow_type == 'endorse':
                #    instance.endorse(request)
                #elif workflow_type == 'close':
                #    instance.close(request)

                #if not workflow_type or workflow_type in ('', ''):
                if create_legal_case:
                    instance.region_id = None if not request.data.get('region_id') else request.data.get('region_id')
                    instance.district_id = None if not request.data.get('district_id') else request.data.get('district_id')
                    instance.assigned_to_id = None if not request.data.get('assigned_to_id') else request.data.get('assigned_to_id')
                    instance.legal_case_priority_id = None if not request.data.get('legal_case_priority_id') else request.data.get('legal_case_priority_id')
                    instance.allocated_group_id = None if not request.data.get('allocated_group_id') else request.data.get('allocated_group_id')
                    instance.call_email_id = None if not request.data.get('call_email_id') else request.data.get('call_email_id')
                    instance.details = None if not request.data.get('details') else request.data.get('details')
                ##elif workflow_type not in ('send_to_manager', 'request_amendment'):
                # #   instance.assigned_to_id = None if not request.data.get('assigned_to_id') else request.data.get('assigned_to_id')
                #else:
                #    instance.assigned_to_id = None
                #    instance.allocated_group_id = None if not request.data.get('allocated_group_id') else request.data.get('allocated_group_id')
                #    #recipient_id = instance.inspection_team_lead_id

                instance.save()
                #
                ## Needed for create inspection
                #if create_inspection:
                #    instance = self.modify_inspection_team(request, instance, workflow=True, user_id=instance.assigned_to_id)

                ## send email
                email_data = prepare_mail(request, instance, workflow_entry, send_mail)
                #if workflow_type in ('send_to_manager', 'request_amendment') and instance.inspection_team_lead_id:
                #    email_data = prepare_mail(request, instance, workflow_entry, send_mail, instance.inspection_team_lead_id)
                #else:
                #    email_data = prepare_mail(request, instance, workflow_entry, send_mail)

                serializer = LegalCaseCommsLogEntrySerializer(instance=workflow_entry, data=email_data, partial=True)
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    serializer.save()
                    return_serializer = LegalCaseSerializer(instance=instance, 
                            context={'request': request}
                            ) 
                    headers = self.get_success_headers(return_serializer.data)
                    return Response(
                            return_serializer.data, 
                            status=status.HTTP_201_CREATED,
                            headers=headers
                            )
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))
    
    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def create_legal_case_process_comms_log_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # process docs
            returned_data = process_generic_document(request, instance, document_type='comms_log')
            # delete Inspection if user cancels modal
            action = request.data.get('action')
            if action == 'cancel' and returned_data:
                # returned_data = instance.delete()
                instance.status = 'discarded'
                instance.save()
            # return response
            if returned_data:
                return Response(returned_data)
            else:
                return Response()

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0].encode('utf-8')))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def create_running_sheet_entry(self, request, *args, **kwargs):
        try:
            instance = self.get_object()

            request_data = {
                            "legal_case_id": instance.id,
                            "user_id": request.user.id
                            }
            print("request_data")
            print(request_data)
            serializer = CreateLegalCaseRunningSheetEntrySerializer(data=request_data)
            serializer.is_valid(raise_exception=True)
            if serializer.is_valid():
                print("serializer.validated_data")
                print(serializer.validated_data)
                serializer.save()
                #instance.log_user_action(
                #        LegalCaseUserAction.ACTION_SAVE_LEGAL_CASE.format(
                #        instance.number), request)
                headers = self.get_success_headers(serializer.data)
                #return_serializer = LegalCaseRunningSheetSerializer(instance, context={'request': request})
                return_serializer = LegalCaseRunningSheetSerializer(instance)
                return Response(
                        return_serializer.data,
                        status=status.HTTP_201_CREATED,
                        headers=headers
                        )

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0].encode('utf-8')))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


class LegalCasePriorityViewSet(viewsets.ModelViewSet):
   queryset = LegalCasePriority.objects.all()
   serializer_class = LegalCasePrioritySerializer

   def get_queryset(self):
       # user = self.request.user
       if is_internal(self.request):
           return LegalCasePriority.objects.all()
       return LegalCasePriority.objects.none()

   #@detail_route(methods=['GET',])
   #@renderer_classes((JSONRenderer,))
   #def get_schema(self, request, *args, **kwargs):
   #    instance = self.get_object()
   #    try:
   #        serializer = InspectionTypeSchemaSerializer(instance)
   #        return Response(
   #            serializer.data,
   #            status=status.HTTP_201_CREATED,
   #            )
   #    except serializers.ValidationError:
   #        print(traceback.print_exc())
   #        raise
   #    except ValidationError as e:
   #        print(traceback.print_exc())
   #        raise serializers.ValidationError(repr(e.error_dict))
   #    except Exception as e:
   #        print(traceback.print_exc())
   #        raise serializers.ValidationError(str(e))

