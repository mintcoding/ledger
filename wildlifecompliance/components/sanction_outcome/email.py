import logging
import traceback

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.utils.encoding import smart_text
from django.core.urlresolvers import reverse
from django.conf import settings

from ledger.accounts.models import EmailUser
from ledger.payments.pdf import create_invoice_pdf_bytes
from ledger.payments.models import Invoice
from wildlifecompliance.components.main.utils import get_choice_value
from wildlifecompliance.components.emails.emails import TemplateEmailBase
from wildlifecompliance.components.main.email import prepare_attachments, _extract_email_headers
import os

from wildlifecompliance.components.users.models import CompliancePermissionGroup

logger = logging.getLogger(__name__)

SYSTEM_NAME = 'Wildlife Licensing Automated Message'


class SanctionOutcomeIssueNotificationEmail(TemplateEmailBase):
    subject = 'Issued Sanction Outcome'
    html_template = 'wildlifecompliance/emails/issue_sanction_outcome_notification.html'
    txt_template = 'wildlifecompliance/emails/issue_sanction_outcome_notification.txt'


class InfringementNoticeEmail(TemplateEmailBase):
    subject = 'Infringement Notice'
    html_template = 'wildlifecompliance/emails/infringement_notice.html'
    txt_template = 'wildlifecompliance/emails/infringement_notice.txt'


class InfringementNoticeDueDateExtendedEmail(TemplateEmailBase):
    subject = 'Infringement notice due date extended'
    html_template = 'wildlifecompliance/emails/due_date_extended_email.html'
    txt_template = 'wildlifecompliance/emails/due_date_extended_email.txt'


def send_due_date_extended_mail(select_group, sanction_outcome, workflow_entry, request=None):
    email = InfringementNoticeDueDateExtendedEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={ 'sanction_outcome_id': sanction_outcome.id }))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }
    email_group = [item.email for item in select_group]
    msg = email.send(email_group,
                     context=context,
                     attachments=
                     prepare_attachments(workflow_entry.documents)
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_mail(select_group, sanction_outcome, workflow_entry, request=None):
    email = SanctionOutcomeIssueNotificationEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={ 'sanction_outcome_id': sanction_outcome.id }))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }
    email_group = [item.email for item in select_group]
    msg = email.send(email_group, 
        context=context,
        attachments= 
        prepare_attachments(workflow_entry.documents)
        )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_infringement_notice(select_group, sanction_outcome, workflow_entry, request=None):
    email = InfringementNoticeEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('external'))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }
    email_group = [item.email for item in select_group]
    msg = email.send(email_group,
                     context=context,
                     attachments=
                     prepare_attachments(workflow_entry.documents)
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data

