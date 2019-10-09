<template>
    <div class="container-fluid" id="internalOrgInfo">
       <div class="row">
            <div class="col-sm-12">
                <div class="panel panel-default">
                  <div class="panel-heading">
                    <h3 class="panel-title">Organisation Details
                        <a class="panelClicker" :href="'#'+pdBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="pdBody">
                            <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                        </a>
                    </h3>
                  </div>
                  <div class="panel-body collapse in" :id="pdBody">
                      <!--form class="form-horizontal" name="personal_form" method="post"-->
                      <div class="form-horizontal">
                          <div class="form-group">
                            <label for="" class="col-sm-3 control-label">Name</label>
                            <div class="col-sm-6">
                                <input type="text" class="form-control" name="first_name" placeholder="" v-model="organisation.name">
                            </div>
                          </div>
                          <div class="form-group">
                            <label for="" class="col-sm-3 control-label" >ABN</label>
                            <div class="col-sm-6">
                                <input type="text" class="form-control" name="last_name" placeholder="" v-model="organisation.abn">
                            </div>
                          </div>
                       <!--/form-->
                       </div>
                  </div>
                </div>
            </div>
       </div>
       <div class="row">
            <div class="col-sm-12">
                <div class="panel panel-default">
                  <div class="panel-heading">
                    <h3 class="panel-title">Address Details
                        <a class="panelClicker" :href="'#'+adBody" data-toggle="collapse" expanded="false"  data-parent="#userInfo" :aria-controls="adBody">
                            <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                        </a>
                    </h3>
                  </div>
                  <div class="panel-body collapse " :id="adBody">
                      <!--form class="form-horizontal" action="index.html" method="post"-->
                      <div class="form-horizontal">
                          <div class="form-group">
                            <label for="" class="col-sm-3 control-label">Street</label>
                            <div class="col-sm-6">
                                <input type="text" class="form-control" name="street" placeholder="" v-model="organisation.address.line1">
                            </div>
                          </div>
                          <div class="form-group">
                            <label for="" class="col-sm-3 control-label" >Town/Suburb</label>
                            <div class="col-sm-6">
                                <input type="text" class="form-control" name="surburb" placeholder="" v-model="organisation.address.locality">
                            </div>
                          </div>
                          <div class="form-group">
                            <label for="" class="col-sm-3 control-label">State</label>
                            <div class="col-sm-2">
                                <input type="text" class="form-control" name="country" placeholder="" v-model="organisation.address.state">
                            </div>
                            <label for="" class="col-sm-2 control-label">Postcode</label>
                            <div class="col-sm-2">
                                <input type="text" class="form-control" name="postcode" placeholder="" v-model="organisation.address.postcode">
                            </div>
                          </div>
                          <div class="form-group">
                            <label for="" class="col-sm-3 control-label" >Country</label>
                            <div class="col-sm-4">
                                <select class="form-control" name="country" v-model="organisation.address.country">
                                    <option v-for="c in countries" :value="c.alpha2Code">{{ c.name }}</option>
                                </select>
                            </div>
                          </div>
                       <!--/form-->
                       </div>
                  </div>
                </div>
            </div>
        </div>
        <div class="form-group">
            <div class="col-sm-12">
                <div v-if="show_spinner"><i class='fa fa-2x fa-spinner fa-spin pull-right'></i></div>
                <div v-else>
                    <input
                        type="button" 
                        class="pull-right btn btn-primary" 
                        :disabled="!saveButtonEnabled"
                        :value="saveButtonText"
                        @click.prevent="saveData()" 
                    />
                </div>
            </div>
        </div>
   </div> 
</template>

<script>
import Vue from 'vue'
import { api_endpoints, helpers, cache_helper } from '@/utils/hooks'
import datatable from '@vue-utils/datatable.vue'
import AddContact from '@common-components/add_contact.vue'
import utils from '../internal/utils'
import api from '../internal/api'

export default {
    name: 'Organisation',
    data () {
        let vm = this;
        return {
            adBody: 'adBody'+vm._uid,
            aBody: 'aBody'+vm._uid,
            pdBody: 'pdBody'+vm._uid,
            pBody: 'pBody'+vm._uid,
            cdBody: 'cdBody'+vm._uid,
            cBody: 'cBody'+vm._uid,
            oBody: 'oBody'+vm._uid,
            dTab: 'dTab'+vm._uid,
            oTab: 'oTab'+vm._uid,
            idBody: 'idBody'+vm._uid,
            organisation: {
                address: {}
            },
            myorgperms: null,
            show_spinner: false,
            countries: [],
            saveButtonEnabled: false,
        }
    },
    props: {
        isEditable: {
            type: Boolean,
            default: false,
        },
        displayComponent: {
            type: Boolean,
            required: true,
            default: false,
        },
        organisationToUpdate: {
            type: Number,
            required: false,
        },
    },
    watch: {
        computedOrganisation: {
            deep: true,
            handler: function(newVal, oldVal) {
                if (oldVal.id && oldVal !== newVal) {
                    this.saveButtonEnabled = true;
                } else if (this.organisation && !this.organisation.id) {
                    this.saveButtonEnabled = true;
                } else {
                    this.saveButtonEnabled = false;
                }
            },
        },
    },
    components: {
        datatable,
    },
    computed: {
        computedOrganisation: function() {
            let computed_organisation = Object.assign({}, this.organisation);
            if (this.organisation && this.organisation.address) {
                Object.assign(computed_organisation.address, this.organisation.address);
            }
            return computed_organisation;
        },
        saveButtonText: function() {
            let buttonText = '';
            if (this.organisation && this.organisation.id) {
                buttonText = 'Update Organisation'
            } else {
                buttonText = 'Save New Organisation'
            }
            return buttonText;
        },

    },
    created: async function() {
        // Populate country drop-down list
        let returned_country_list = await cache_helper.getSetCacheList(
          'Countries',
          api.countries
          );
        Object.assign(this.countries, returned_country_list);
        // Set selected country to Australia
        //Vue.set(this.organisation.address, 'country', 'AU');
        if (this.organisationToUpdate) {
            this.setExistingOrganisation(this.organisationToUpdate);
        }
    },
    methods: {
        parentSave: async function() {
            if (this.saveButtonEnabled) {
                await this.saveData()
            }
        },
        saveData: async function() {
            try{
                let payload = {}
                Object.assign(payload, this.organisation)
                if (payload.address && !payload.address.line1) {
                    payload.address = null;
                }
                let fetchUrl = ''
                if (payload.id) {
                    if (!payload.address) {
                        await swal("Error", "Ensure Address Line 1 is not blank", "error");
                        return;
                    } else {
                        fetchUrl = helpers.add_endpoint_join(
                            api_endpoints.organisations_compliancemanagement, 
                            payload.id + '/update_postal_address/');
                    }
                } else {
                    if (!payload.abn || !payload.name) {
                        await swal("Error", "Ensure Name and ABN are not blank", "error");
                        fetchUrl = api_endpoints.organisations_compliancemanagement;
                    }
                }

                let savedOrganisation = await Vue.http.post(fetchUrl, payload);
                if (!savedOrganisation.body.address) {
                    savedOrganisation.body.address = this.getDefaultAddress()
                }
                Object.assign(this.organisation, savedOrganisation.body);
                await swal("Saved", "Organisation has been saved", "success");
                this.$emit('organisation-saved', {'organisation': savedOrganisation.body, 'errorMessage': null});
            } catch (err) {
                if (err.bodyText) {
                    this.$emit('organisation-saved', { 'organisation': null, 'errorMessage': err.bodyText });
                }
            }
        },

        getDefaultAddress: function(){
            let address_data = {
                    line1: '',
                    locality: '',
                    state: 'WA',
                    postcode: '',
                    country: 'AU'
                };
            return address_data;
        },
        setExistingOrganisation: async function(id) {
            let url = helpers.add_endpoint_join(api_endpoints.organisations_compliancemanagement, id)
            let res = await Vue.http.get(url)
            console.log(res)
            Object.assign(this.organisation, res.body)
            if (!this.organisation.address) {
                this.organisation.address = this.getDefaultAddress()
            }


            //let initialisers = [utils.fetchComplianceManagementOrganisation(id)];
            //Promise.all(initialisers).then(data => {
            //    console.log(data)
            //    Object.assign(this.organisation, data[0])
            //    if (!this.organisation.address) {
            //        this.organisation.address = this.getDefaultAddress()
            //    }
            //});
        },
        //setPersonId: function(id){
        //    this.email_user.id = id;
        //},
        //setDefaultPerson: function(){
        //    let user_data = {
        //        id: null,
        //        first_name: '',
        //        last_name: '',
        //        dob: null,
        //        residential_address: {
        //            line1: '',
        //            locality: '',
        //            state: 'WA',
        //            postcode: '',
        //            country: 'AU'
        //        },
        //        phone_number: '',
        //        mobile_number: '',
        //        email: '',
        //    };
        //    Object.assign(this.email_user, user_data);
        //},
        //save: async function() {
        //    this.show_spinner = true;
        //    let post_url = '/api/organisations_compliancemanagement/';
        //    //let payload = new FormData();
        //    //payload.append('organisation', this.organisation);
        //    //console.log(payload)
        //    
        //    let returnedOrganisation = await Vue.http.post(post_url, JSON.stringify(this.organisation));
        //    console.log(returnedOrganisation)
        //    if (returnedOrganisation.ok) {
        //        // do something
        //    }
        //    
        //    this.show_spinner = false;
        //},
    },
    mounted: function(){
    },
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.top-buffer-s {
    margin-top: 10px;
}
.actionBtn {
    cursor: pointer;
}
.hidePopover {
    display: none;
}
</style>
