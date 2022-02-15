# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.
# Before running this sample, please:
# - create a Durable orchestration function
# - create a Durable HTTP starter function
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt

import logging
import os

from azure.mgmt.containerservice import ContainerServiceClient
from azure.identity import ClientSecretCredential
from azure.mgmt.subscription import SubscriptionClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.containerservice.models import (ManagedClusterAgentPoolProfile, ManagedCluster)
from azure.appconfiguration import AzureAppConfigurationClient, ConfigurationSetting

from azure.data.tables import TableClient
from azure.data.tables import UpdateMode


def main(env: str) -> str:
    logging.info('Python aks-upgrade function processed a request.')
    print("Environment:", env)
    if env:
      credential = ClientSecretCredential(
        tenant_id = os.environ["tenant_id"],
        client_id = os.environ["function_client_id"],  
        client_secret= os.environ["function_client_secret"]
      )
      sub_client = SubscriptionClient(credential=credential)
      table_client = TableClient.from_connection_string(
           conn_str=os.environ["AzureWebJobsStorage"],
           table_name="AKSVersion"
      )
      print("Listing Subscriptions....")
      for sub in sub_client.subscriptions.list():   
            print("Sub_Name:", sub.display_name, "Environment:", env)
            if env in sub.display_name and "sandbox" not in sub.display_name:
              print("Updating process on Dev, Test and Prod environments!")
              resource_client = ResourceManagementClient(credential, sub.subscription_id)
              # Retrieve the list of resource groups
              group_list = resource_client.resource_groups.list()
  
              for group in list(group_list):
                print("ResourceGroupName:", group.name)
                resource_list = resource_client.resources.list_by_resource_group(group.name)
                print("Fetching AKS resources...\n")
                
                for resource in list(resource_list):
                  if resource.type== "Microsoft.ContainerService/managedClusters":
                    location=resource.location
                    print("Location:", location)
                    containerservice_client = ContainerServiceClient(credential, sub.subscription_id)
                    print("Getting availabele versions on AKS Cluster....")
                    aks_get_version = containerservice_client.managed_clusters.get_upgrade_profile(group.name, resource.name)
  
                    aks_get_upgrade = aks_get_version.control_plane_profile
                    upgrades = aks_get_upgrade.upgrades
                    print("ResourceName:", resource.name, "AKS_current_Version", aks_get_upgrade.kubernetes_version)
                    current_version = aks_get_upgrade.kubernetes_version
                    agent_pool=containerservice_client.agent_pools.list(group.name, resource.name)
                    if upgrades:
                      latest_version=list()
                      preview=list()
                      for i in upgrades:
                        ##AKSAvailable_Versions_List shows the latest supported minor version.
                        print("ResourceName:", resource.name, "AKSAvailable_Versions_List:", i.kubernetes_version, "Preview:" , i.is_preview) 
                        latest_version.append(i.kubernetes_version)
                        preview.append(i.is_preview)
                        latest_stable_version = latest_version[-1]
                        version_preview_for_stable=preview[-1]    
                        print("latest_stable_version",latest_stable_version,"version_preview_for_stable",version_preview_for_stable)
                      ##Stable Version is the latest supported patch release on minor version N-1 which N is the latest supported minor version.  
                      print("Latest Stable Available Version:", latest_stable_version)   
                      for x in agent_pool:
                          agent_pool_name=x.name
                          print("Agent_Pool_Name:",x.name)
                      ##Fetching version (the latest version on Sandbox) from Azure Storage Table    
                      entity = table_client.get_entity(partition_key="aksversion", row_key="1")  
                      print("Received entity: {}".format(entity["versionnumber"]))  
                      latest_version = entity["versionnumber"]
                      if version_preview_for_stable == None and latest_version != current_version :
                        print("Upgrading to a new version....")
                        param=ManagedCluster(location=location, kubernetes_version=latest_version,agent_pool_profiles=[ManagedClusterAgentPoolProfile(orchestrator_version=latest_version,name=agent_pool_name,mode=x.mode,type=x.type_properties_type)])
                        update_aks=containerservice_client.managed_clusters.begin_create_or_update(resource_group_name=group.name,resource_name=resource.name,parameters=param) 
                                               
                      else:
                        print("Either kubernetes version is the latest one or the stable version is in preview!") 
                    else:
                      print("There is no new updates available!")   

                  else:
                    print("Not an AKS resource")    
            else:
              print("Env is not in sub-name:", sub.display_name)              
      return f"Hello, Updateding process is Done!"
    else:
        return f"Environment's input doesn't exist!"
