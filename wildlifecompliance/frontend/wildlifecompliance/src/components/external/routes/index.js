import ExternalDashboard from '../dashboard.vue'
import ExternalDashboardSanctionOutcome from '../dashboard_sanction_outcome.vue'
import Application from '../application.vue'
import ApplicationApply from '../application_apply.vue'
import ApplicationApplyOrganisation from '../application_apply_organisation.vue'
import ApplicationApplyLicence from '../application_apply_licence.vue'
import ApplicationSubmit from '../application_submit.vue'
import Organisation from '../organisations/manage.vue'
import Returns from '../returns/return.vue'
import RemediationAction from '../remediation_action.vue'
export default
{
    path: '/external',
    component:
    {
        render(c)
        {
            return c('router-view')
        }
    },
    children: [
        {
            path: '/',
            component: ExternalDashboard,
            name: 'external-applications-dash'
        },
        {
            path: 'sanction_outcome',
            component: ExternalDashboardSanctionOutcome,
            name: 'external-sanction-outcome-dash'
        },
        {
            path: 'remediation_action/:remediation_action_id',
            component: RemediationAction,
            name: 'external-remediation-action-detail'
        },
        {
            path: 'organisations/manage/:org_id',
            component: Organisation
        },
        {
            path: 'return/:return_id',
            component: Returns
        },
        {
            path: 'application',
            component:
            {
                render(c)
                {
                    return c('router-view')
                }
            },
            children: [
                {
                    path: '/',
                    component: ApplicationApply,
                    name:"apply_application"
                },
                {
                    path: 'org_select',
                    component: ApplicationApplyOrganisation,
                    name:"apply_application_organisation"
                },
                {
                    path: 'licence_select',
                    component: ApplicationApplyLicence,
                    name:"apply_application_licence"
                },
                {
                    path: 'submit',
                    component: ApplicationSubmit,
                    name:"submit_application"
                },
                {
                    path: ':application_id',
                    component: Application,
                    name:"draft_application"
                },
            ]
        }
    ]
}
