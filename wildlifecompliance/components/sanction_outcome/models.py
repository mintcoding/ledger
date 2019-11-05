import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save

from ledger.accounts.models import EmailUser, RevisionedMixin
from wildlifecompliance.components.main.models import Document, UserAction, CommunicationsLogEntry
from wildlifecompliance.components.main.related_item import can_close_record
from wildlifecompliance.components.offence.models import Offence, Offender, AllegedOffence
from wildlifecompliance.components.section_regulation.models import SectionRegulation
from wildlifecompliance.components.users.models import RegionDistrict, CompliancePermissionGroup


class SanctionOutcomeActiveManager(models.Manager):
    def get_queryset(self):
        return super(SanctionOutcomeActiveManager, self).get_queryset().exclude(
            Q(status=SanctionOutcome.STATUS_CLOSED) |
            Q(status=SanctionOutcome.STATUS_WITHDRAWN) |
            Q(status=SanctionOutcome.STATUS_DECLINED)
        )


class SanctionOutcomeExternalManager(models.Manager):
    def get_queryset(self):
        return super(SanctionOutcomeExternalManager, self).get_queryset().filter(
            Q(offender__removed=False) &
            Q(status__in=(SanctionOutcome.STATUS_AWAITING_PAYMENT,
                          SanctionOutcome.STATUS_AWAITING_REMEDIATION_ACTIONS,
                          SanctionOutcome.STATUS_CLOSED)))


class SanctionOutcome(models.Model):
    WORKFLOW_SEND_TO_MANAGER = 'send_to_manager'
    WORKFLOW_ENDORSE = 'endorse'
    WORKFLOW_DECLINE = 'decline'
    WORKFLOW_WITHDRAW_BY_MANAGER = 'withdraw_by_manager'
    WORKFLOW_WITHDRAW_BY_INC = 'withdraw_by_inc'  # INC: infringement notice coordinator
    WORKFLOW_RETURN_TO_OFFICER = 'return_to_officer'
    WORKFLOW_CLOSE = 'close'

    PAYMENT_STATUS_UNPAID = 'unpaid'
    PAYMENT_STATUS_PAID = 'paid'
    PAYMENT_STATUS_CHOICES = (
        (PAYMENT_STATUS_PAID, 'Paid'),
        (PAYMENT_STATUS_UNPAID, 'Unpaid')
    )
    STATUS_DRAFT = 'draft'
    STATUS_AWAITING_ENDORSEMENT = 'awaiting_endorsement'
    STATUS_AWAITING_PAYMENT = 'awaiting_payment'
    STATUS_AWAITING_REVIEW = 'awaiting_review'
    STATUS_AWAITING_REMEDIATION_ACTIONS = 'awaiting_remediation_actions'
    STATUS_DECLINED = 'declined'
    STATUS_WITHDRAWN = 'withdrawn'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES_FOR_EXTERNAL = (
        (STATUS_AWAITING_PAYMENT, 'Awaiting Payment'),
        (STATUS_AWAITING_REMEDIATION_ACTIONS, 'Awaiting Remediation Actions'),
        # (STATUS_DECLINED, 'Declined'),
        # (STATUS_WITHDRAWN, 'Withdrawn'),
        (STATUS_CLOSED, 'closed'),
    )
    FINAL_STATUSES = (STATUS_DECLINED, STATUS_CLOSED, STATUS_WITHDRAWN,)
    STATUS_CHOICES = (
        (STATUS_DRAFT, 'Draft'),
        (STATUS_AWAITING_ENDORSEMENT, 'Awaiting Endorsement'),
        (STATUS_AWAITING_PAYMENT, 'Awaiting Payment'),  # TODO: implement pending closuer of SanctionOutcome with type RemediationActions
                                                        # This is pending closure status
        (STATUS_AWAITING_REVIEW, 'Awaiting Review'),
        (STATUS_AWAITING_REMEDIATION_ACTIONS, 'Awaiting Remediation Actions'),  # TODO: implement pending closuer of SanctionOutcome with type RemediationActions
                                                                                # This is pending closure status
                                                                                # Once all the remediation actions are closed, this status should become closed...
        (STATUS_DECLINED, 'Declined'),
        (STATUS_WITHDRAWN, 'Withdrawn'),
        (STATUS_CLOSED, 'closed'),
    )

    TYPE_INFRINGEMENT_NOTICE = 'infringement_notice'
    TYPE_CAUTION_NOTICE = 'caution_notice'
    TYPE_LETTER_OF_ADVICE = 'letter_of_advice'
    TYPE_REMEDIATION_NOTICE = 'remediation_notice'

    TYPE_CHOICES = (
        (TYPE_INFRINGEMENT_NOTICE, 'Infringement Notice'),
        (TYPE_CAUTION_NOTICE, 'Caution Notice'),
        (TYPE_LETTER_OF_ADVICE, 'Letter of Advice'),
        (TYPE_REMEDIATION_NOTICE, 'Remediation Notice'),
    )

    __original_status = STATUS_DRAFT

    type = models.CharField(max_length=30, choices=TYPE_CHOICES, blank=True,)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default=__original_status,)
    payment_status = models.CharField(max_length=40, choices=PAYMENT_STATUS_CHOICES, blank=True,)

    region = models.ForeignKey(RegionDistrict, related_name='sanction_outcome_region', null=True,)
    district = models.ForeignKey(RegionDistrict, related_name='sanction_outcome_district', null=True,)

    identifier = models.CharField(max_length=50, blank=True,)
    lodgement_number = models.CharField(max_length=50, blank=True,)
    offence = models.ForeignKey(Offence, related_name='offence_sanction_outcomes', null=True, on_delete=models.SET_NULL,)
    offender = models.ForeignKey(Offender, related_name='sanction_outcome_offender', null=True, on_delete=models.SET_NULL,)

    # TODO: this field is not probably used anymore.
    alleged_offences = models.ManyToManyField(SectionRegulation, blank=True, related_name='sanction_outcome_alleged_offences')

    alleged_committed_offences = models.ManyToManyField(AllegedOffence, related_name='sanction_outcome_alleged_committed_offences', through='AllegedCommittedOffence')
    issued_on_paper = models.BooleanField(default=False) # This is always true when type is letter_of_advice
    paper_id = models.CharField(max_length=50, blank=True,)
    description = models.TextField(blank=True)

    assigned_to = models.ForeignKey(EmailUser, related_name='sanction_outcome_assigned_to', null=True)
    allocated_group = models.ForeignKey(CompliancePermissionGroup, related_name='sanction_outcome_allocated_group', null=True)
    # This field is used as recipient when manager returns a sanction outcome for amendment
    # Updated whenever the sanction outcome is sent to the manager
    responsible_officer = models.ForeignKey(EmailUser, related_name='sanction_outcome_responsible_officer', null=True)

    # Only editable when issued on paper. Otherwise pre-filled with date/time when issuing electronically.
    date_of_issue = models.DateField(null=True, blank=True)
    time_of_issue = models.TimeField(null=True, blank=True)

    # Following atributes should be determined at the moment of issue
    penalty_amount_1st =  models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    penalty_amount_2nd =  models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    due_date_auto_1st = models.DateField(null=True, blank=True)  # Null means not extended
    due_date_auto_2nd = models.DateField(null=True, blank=True)  # Null means not extended, but this is extended even when 1st due date is extended manually.
    due_date_extended_max = models.DateField(null=True, blank=True)

    # Only when the due dates are manually extended, these should have values
    due_date_manual_1st = models.DateField(null=True, blank=True)
    due_date_manual_2nd = models.DateField(null=True, blank=True)

    objects = models.Manager()
    objects_active = SanctionOutcomeActiveManager()
    objects_for_external = SanctionOutcomeExternalManager()

    @property
    def infringement_penalty_invoice_reference(self):
        try:
            if self.payment_status == SanctionOutcome.PAYMENT_STATUS_PAID:
                ip = self.infringement_penalties.all().last()
                if ip:
                    ipv = ip.infringement_penalty_invoices.all().last()
                    if ipv:
                        return ipv.invoice_reference
            return None

        except Exception as e:
            return None

    @property
    def prefix_lodgement_nubmer(self):
        prefix_lodgement = ''
        if self.type == self.TYPE_INFRINGEMENT_NOTICE:
            prefix_lodgement = 'IF'
        elif self.type == self.TYPE_LETTER_OF_ADVICE:
            prefix_lodgement = 'LA'
        elif self.type == self.TYPE_CAUTION_NOTICE:
            prefix_lodgement = 'CN'
        elif self.type == self.TYPE_REMEDIATION_NOTICE:
            prefix_lodgement = 'RN'

        return prefix_lodgement

    def delete(self):
        if self.lodgement_number:
            raise ValidationError('Sanction outcome saved in the database with the logement number cannot be deleted.')

        super(SanctionOutcome, self).delete()

    def log_user_action(self, action, request):
        return SanctionOutcomeUserAction.log_action(self, action, request.user)

    def save(self, *args, **kwargs):
        super(SanctionOutcome, self).save(*args, **kwargs)

        need_save = False

        # Construct lodgement_number
        if not self.lodgement_number:
            self.lodgement_number = self.prefix_lodgement_nubmer + '{0:06d}'.format(self.pk)
            need_save = True

        # No documents are attached when issued_on_paper=False
        if not self.issued_on_paper:
            if self.documents.all().count():
                print('[Warn] This sanction outcome has not been issued on paper, but has documents.')
                # self.documents.all().delete()
                # need_save = True

        if need_save:
            self.save()  # Be carefull, this might lead to the infinite loop

        self.__original_status = self.status


    def __str__(self):
        return 'Type : {}, Identifier: {}'.format(self.type, self.identifier)
    
    @property
    def get_related_items_identifier(self):
        #return self.identifier
        return self.lodgement_number

    @property
    def get_related_items_descriptor(self):
        #return '{0}, {1}'.format(self.identifier, self.description)
        return self.identifier

    @property
    def regionDistrictId(self):
        return self.district.id if self.district else self.region.id

    @staticmethod
    def get_compliance_permission_group(regionDistrictId, workflow_type):
        region_district = RegionDistrict.objects.filter(id=regionDistrictId)

        # 2. Determine which permission(s) is going to be apllied
        compliance_content_type = ContentType.objects.get(model="compliancepermissiongroup")
        codename = 'officer'
        if workflow_type == SanctionOutcome.WORKFLOW_SEND_TO_MANAGER:
            codename = 'manager'
            per_district = True
        elif workflow_type == SanctionOutcome.WORKFLOW_DECLINE:
            codename = '---'
            per_district = False
        elif workflow_type == SanctionOutcome.WORKFLOW_ENDORSE:
            codename = 'infringement_notice_coordinator'
            per_district = False
        elif workflow_type == SanctionOutcome.WORKFLOW_RETURN_TO_OFFICER:
            codename = 'officer'
            per_district = True
        elif workflow_type == SanctionOutcome.WORKFLOW_WITHDRAW_BY_INC:
            codename = 'infringement_notice_coordinator'
            per_district = False
        elif workflow_type == SanctionOutcome.WORKFLOW_WITHDRAW_BY_MANAGER:
            codename = 'manager'
            per_district = True
        elif workflow_type == SanctionOutcome.WORKFLOW_CLOSE:
            codename = '---'
            per_district = False
        else:
            # Should not reach here
            # instance.save()
            pass

        permissions = Permission.objects.filter(codename=codename, content_type_id=compliance_content_type.id)

        # 3. Find groups which has the permission(s) determined above in the regionDistrict.
        if per_district:
            groups = CompliancePermissionGroup.objects.filter(region_district__in=region_district, permissions__in=permissions)
        else:
            groups = CompliancePermissionGroup.objects.filter(permissions__in=permissions)

        return groups.first()

    def send_to_manager(self, request):
        if self.issued_on_paper:
            self.status = self.STATUS_AWAITING_ENDORSEMENT
        else:
            self.status = self.STATUS_AWAITING_REVIEW
        new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_SEND_TO_MANAGER)
        self.allocated_group = new_group
        self.assigned_to = None
        self.responsible_officer = request.user
        self.log_user_action(SanctionOutcomeUserAction.ACTION_SEND_TO_MANAGER.format(self.lodgement_number), request)
        self.save()

    def retrieve_issue_due_date_window(self):
        # Expecting this function is called only for an infringement notice which can have only one alleged offence.
        date_window = self.alleged_committed_offences.first().section_regulation.issue_due_date_window
        return date_window

    @property
    def offence_occurrence_date(self):
        if self.offence.occurrence_from_to:
            return self.offence.occurrence_date_to
        else:
            return self.offence.occurrence_date_from

    def endorse(self, request):
        current_datetime = datetime.datetime.now()
        if not self.issued_on_paper:
            self.date_of_issue = current_datetime.date()
            self.time_of_issue = current_datetime.time()
        elif not self.date_of_issue:
            raise ValidationError('Sanction outcome cannot be endorsed without setting date of issue.')

        if self.type == SanctionOutcome.TYPE_INFRINGEMENT_NOTICE:
            date_window = self.retrieve_issue_due_date_window()
            issue_due_date = self.offence_occurrence_date + relativedelta(days=date_window)
            if self.date_of_issue > issue_due_date:
                raise ValidationError('Infringement notice must be issued before %s' % issue_due_date.strftime("%d-%m-%Y"))

            self.status = SanctionOutcome.STATUS_AWAITING_PAYMENT
            self.payment_status = SanctionOutcome.PAYMENT_STATUS_UNPAID
            amounts = self.retrieve_penalty_amounts_by_date()
            self.penalty_amount_1st = amounts.amount
            self.penalty_amount_2nd = amounts.amount_after_due
            due_date_config = SanctionOutcomeDueDateConfiguration.get_config_by_date(self.date_of_issue)
            self.due_date_auto_1st = self.date_of_issue + relativedelta(days=due_date_config.due_date_window_1st)
            self.due_date_auto_2nd = self.date_of_issue + relativedelta(days=due_date_config.due_date_window_1st + due_date_config.due_date_window_2nd)
            self.due_date_extended_max =self.date_of_issue + relativedelta(years=1)

        elif self.type in (SanctionOutcome.TYPE_CAUTION_NOTICE, SanctionOutcome.TYPE_LETTER_OF_ADVICE):
            self.status = SanctionOutcome.STATUS_CLOSED
            self.save()  # This makes sure this sanction outcome status sets to 'closed'

        elif self.type == SanctionOutcome.TYPE_REMEDIATION_NOTICE:
            self.status = SanctionOutcome.STATUS_AWAITING_REMEDIATION_ACTIONS

        new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_ENDORSE)
        self.allocated_group = new_group
        self.save()

        self.log_user_action(SanctionOutcomeUserAction.ACTION_ENDORSE.format(self.lodgement_number), request)

    def decline(self, request):
        self.status = self.STATUS_DECLINED
        new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_DECLINE)
        self.allocated_group = new_group
        self.log_user_action(SanctionOutcomeUserAction.ACTION_DECLINE.format(self.lodgement_number), request)
        self.save()

    def return_to_officer(self, request):
        self.status = self.STATUS_DRAFT
        new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_RETURN_TO_OFFICER)
        self.allocated_group = new_group
        self.log_user_action(SanctionOutcomeUserAction.ACTION_RETURN_TO_OFFICER.format(self.lodgement_number), request)
        self.save()

    def withdraw_by_inc(self, request):
        self.status = self.STATUS_WITHDRAWN
        new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_WITHDRAW_BY_INC)
        self.allocated_group = new_group
        self.log_user_action(SanctionOutcomeUserAction.ACTION_WITHDRAW.format(self.lodgement_number), request)
        self.save()

    def withdraw_by_namager(self, request):
        self.status = self.STATUS_WITHDRAWN
        new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_WITHDRAW_BY_MANAGER)
        self.allocated_group = new_group
        self.log_user_action(SanctionOutcomeUserAction.ACTION_WITHDRAW.format(self.lodgement_number), request)
        self.save()

    def retrieve_penalty_amounts_by_date(self):
        qs_aco = AllegedCommittedOffence.objects.filter(Q(sanction_outcome=self) & Q(included=True))
        if qs_aco.count() != 1:  # Only infringement notice can have penalty. Infringement notice can have only one alleged offence.
            raise ValidationError('There are multiple alleged committed offences in this sanction outcome.')
        else:
            return qs_aco.first().retrieve_penalty_amounts_by_date(self.date_of_issue)

    @property
    def due_date_1st(self):
        if self.due_date_manual_1st:
            return self.due_date_manual_1st
        return self.due_date_auto_1st

    def extend_due_date(self, target_date):
        now_datetime = datetime.now()
        due_date_config = SanctionOutcomeDueDateConfiguration.get_config_by_date(self.date_of_issue)
        if target_date <= self.due_date_extended_max:
            if now_datetime <= self.due_date_1st:
                self.due_date_manual_1st = target_date
                self.due_date_manual_2nd = target_date + relativedelta(days=due_date_config.due_date_window_2nd)
            elif now_datetime <= self.due_date_2nd:
                self.due_date_manual_2nd = target_date
        self.save()

    @property
    def due_date_2nd(self):
        if self.due_date_manual_2nd:
            return self.due_date_manual_2nd
        return self.due_date_auto_2nd

    def determine_penalty_amount_by_date(self, date_payment):
        if self.offence_occurrence_date <= date_payment:
            if date_payment <= self.due_date_1st:
                return self.penalty_amount_1st
            elif date_payment <= self.due_date_2nd:
                return self.penalty_amount_2nd
            else:
                # Should not reach here
                # Details of the sanction outcome is uploaded to the Fines Enforcement system after the 2nd due
                # After that, the sanciton outcome should be closed (??? External user should still be able to see the sanction outcome???)
                raise ValidationError('Overdue')
        else:
            # Should not reach here
            raise ValidationError('Payment must be after the offence occurrence date.')

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_SanctionOutcome'
        verbose_name_plural = 'CM_SanctionOutcomes'
        ordering = ['-id']


def perform_can_close_record(sender, instance, **kwargs):
    # Trigger the close() function of each parent entity of this sanction outcome
    if instance.status in (SanctionOutcome.FINAL_STATUSES):
        close_record, parents = can_close_record(instance)
        for parent in parents:
            if parent.status == 'pending_closure':
                parent.close()

post_save.connect(perform_can_close_record, sender=SanctionOutcome)


class AllegedCommittedOffence(RevisionedMixin):
    alleged_offence = models.ForeignKey(AllegedOffence, null=False,)
    sanction_outcome = models.ForeignKey(SanctionOutcome, null=False,)
    included = models.BooleanField(default=True)  # True means sanction_outcome is included in the sanction_outcome

    # TODO: following three fields are not used probably
    # reason_for_removal = models.TextField(blank=True)
    # removed = models.BooleanField(default=False)  # Never make this field False once becomes True. Rather you have to create another record making this field False.
    # removed_by = models.ForeignKey(EmailUser, null=True, related_name='alleged_committed_offence_removed_by')
    # objects = models.Manager()
    # objects_active = AllegedCommittedOffenceActiveManager()

    def retrieve_penalty_amounts_by_date(self, date_of_issue):
        return self.alleged_offence.retrieve_penalty_amounts_by_date(date_of_issue)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_AllegedCommittedOffence'
        verbose_name_plural = 'CM_AllegedCommittedOffences'


class RemediationAction(models.Model):
    action = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    sanction_outcome = models.ForeignKey(SanctionOutcome, related_name='remediation_action_sanction_outcome', null=True, on_delete=models.SET_NULL,)

    # validate if the sanction outcome is remediation_notice
    def clean_fields(self, exclude=None):
        if self.sanction_outcome.type != 'remediation_notice':
            raise ValidationError({'sanction_outcome': [u'The type of the sanction outcome must be Remediation-Notice when saving a remediation action.']})
        super(RemediationAction, self).clean_fields(exclude)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_RemediationAction'
        verbose_name_plural = 'CM_RemediationActions'

    def __str__(self):
        return '{}'.format(self.action,)


def update_compliance_doc_filename(instance, filename):
    return 'wildlifecompliance/sanction_outcome/{}/documents/{}'.format(
        instance.sanction_outcome.id, filename)


class SanctionOutcomeDocument(Document):
    sanction_outcome = models.ForeignKey(SanctionOutcome, related_name='documents')
    _file = models.FileField(max_length=255, upload_to=update_compliance_doc_filename)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_SanctionOutcomeDocument'
        verbose_name_plural = 'CM_SanctionOutcomeDocuments'


class SanctionOutcomeCommsLogDocument(Document):
    log_entry = models.ForeignKey('SanctionOutcomeCommsLogEntry', related_name='documents')
    _file = models.FileField(max_length=255)

    class Meta:
        app_label = 'wildlifecompliance'


class SanctionOutcomeCommsLogEntry(CommunicationsLogEntry):
    sanction_outcome = models.ForeignKey(SanctionOutcome, related_name='comms_logs')

    class Meta:
        app_label = 'wildlifecompliance'


class SanctionOutcomeUserAction(models.Model):
    ACTION_SEND_TO_MANAGER = "Send Sanction Outcome {} to manager"
    ACTION_SAVE = "Save Sanction Outcome {}"
    ACTION_ENDORSE = "Endorse Sanction Outcome {}"
    ACTION_DECLINE = "Decline Sanction Outcome {}"
    ACTION_RETURN_TO_OFFICER = "Request amendment for Sanction Outcome {}"
    ACTION_WITHDRAW = "Withdraw Sanction Outcome {}"
    ACTION_CLOSE = "Close Sanction Outcome {}"
    ACTION_ADD_WEAK_LINK = "Create manual link between Sanction Outcome: {} and {}: {}"
    ACTION_REMOVE_WEAK_LINK = "Remove manual link between Sanction Outcome: {} and {}: {}"
    ACTION_REMOVE_ALLEGED_COMMITTED_OFFENCE = "Remove alleged committed offence: {}"
    ACTION_RESTORE_ALLEGED_COMMITTED_OFFENCE = "Restore alleged committed offence: {}"
    ACTION_INCLUDE_ALLEGED_COMMITTED_OFFENCE = "Include alleged committed offence: {}"

    who = models.ForeignKey(EmailUser, null=True, blank=True)
    when = models.DateTimeField(null=False, blank=False, auto_now_add=True)
    what = models.TextField(blank=False)
    sanction_outcome = models.ForeignKey(SanctionOutcome, related_name='action_logs')

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, obj, action, user):
        return cls.objects.create(
            sanction_outcome=obj,
            who=user,
            what=str(action)
        )


class SanctionOutcomeDueDateConfiguration(RevisionedMixin):
    due_date_window_1st =  models.PositiveSmallIntegerField(blank=True, null=True, )  # unit: [days]
    due_date_window_2nd =  models.PositiveSmallIntegerField(blank=True, null=True, )  # unit: [days]
    date_of_enforcement = models.DateField(blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_SanctionOutcomeDueDateConfiguration'
        verbose_name_plural = 'CM_SanctionOutcomeDueDateConfiguration'
        ordering = ('date_of_enforcement', )  # oldest record first, latest record last

    @classmethod
    def get_config_by_date(cls, date_of_issue):
        return cls.objects.filter(Q(date_of_enforcement__lte=date_of_issue)).order_by('date_of_enforcement', ).last()

    def __str__(self):
        return '1st due date window: {} days, 2nd due date window: {} days, enforcement date: {})'.format(self.due_date_window_1st, self.due_date_window_2nd, self.date_of_enforcement)
