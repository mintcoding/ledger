import Vue from 'vue';
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks';

export const sanctionOutcomeStore = {
    namespaced: true,
    state: {
        sanction_outcome: {
            
        },
    },
    getters: {
        sanction_outcome: state => state.sanction_outcome,
    },
    mutations: {
        updateSanctionOutcome(state, sanction_outcome) {
            Vue.set(state, 'sanction_outcome', {
                ...sanction_outcome
            });
            if (state.sanction_outcome.date_of_issue) {
                state.sanction_outcome.date_of_issue = moment(state.sanction_outcome.date_of_issue, 'YYYY-MM-DD').format('DD/MM/YYYY');
            }
            let commsLogsDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.sanction_outcome,
                state.sanction_outcome.id + "/process_comms_log_document/"
                )
            Vue.set(state.sanction_outcome, 'commsLogsDocumentUrl', commsLogsDocumentUrl); 
        },
        updateAssignedToId(state, assigned_to_id) {
            Vue.set(state.sanction_outcome, 'assigned_to_id', assigned_to_id);
        },
        updateCanUserAction(state, can_user_action) {
            Vue.set(state.sanction_outcome, 'can_user_action', can_user_action);
        },
        updateRelatedItems(state, related_items) {
            Vue.set(state.sanction_outcome, 'related_items', related_items);
        },
    },
    actions: {
        async loadSanctionOutcome({ dispatch, }, { sanction_outcome_id }) {
            console.log("loadSanctionOutcome");
            try {
                const returnedSanctionOutcome = await Vue.http.get(
                    helpers.add_endpoint_json(
                        api_endpoints.sanction_outcome, 
                        sanction_outcome_id)
                    );
                await dispatch("setSanctionOutcome", returnedSanctionOutcome.body);
            } catch (err) {
                console.log(err);
            }
        },
        async saveSanctionOutcome({ dispatch, state }) {
            console.log('saveSanctionOutcome');
            //try {
                // Construct url endpoint
                let putUrl = helpers.add_endpoint_join(api_endpoints.sanction_outcome, state.sanction_outcome.id + '/');
                console.log(putUrl);

                // Construct payload to store data to be sent
                let payload = {};
                Object.assign(payload, state.sanction_outcome);

                // format 'type'
                payload.type = payload.type.id;

                // Send data to the server
                let savedSanctionOutcome = await Vue.http.put(putUrl, payload);

                // Update sanction outcome in the vuex store
                await dispatch("setSanctionOutcome", savedSanctionOutcome.body);

                // Display message
                await swal("Saved", "The record has been saved", "success");

                // Return the saved data just in case needed
                return savedSanctionOutcome;
          //  } catch (err) {
          //      console.log('err');
          //      console.log(err);
          //      if (err.body.non_field_errors){
          //          await swal("Error", err.body.non_field_errors[0], "error");
          //      } else {
          //          await swal("Error", "There was an error saving the record", "error");
          //      }
          //  }
        },
        setSanctionOutcome({ commit, }, sanction_outcome) {
            commit("updateSanctionOutcome", sanction_outcome);
        },
        setAssignedToId({ commit, }, assigned_to_id) {
            commit("updateAssignedToId", assigned_to_id);
        },
        setCanUserAction({ commit, }, can_user_action) {
            commit("updateCanUserAction", can_user_action);
        },
        setRelatedItems({ commit }, related_items ) {
            commit("updateRelatedItems", related_items);
        },
    },
}