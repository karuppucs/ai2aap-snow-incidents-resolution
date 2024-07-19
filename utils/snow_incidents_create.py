#!/bin/python
import requests

def create_servicenow_incident(instance_url, username, password, description, host):
    """Creates a new incident in ServiceNow with the given description.

    Args:
        instance_url (str): Your ServiceNow instance URL (e.g., "https://yourinstance.service-now.com")
        username (str): Your ServiceNow username
        password (str): Your ServiceNow password
        description (str): The description of the incident
        host: The host to troubleshoot

    Returns:
        dict: The response from ServiceNow, including the sys_id of the new incident if successful.
    """

    url = f"{instance_url}/api/now/table/incident"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    # Payload with incident details
    data = {
        "short_description": description,
        "u_host": host
    }

    response = requests.post(url, auth=(username, password), headers=headers, json=data)

    if response.status_code == 201:
        result = response.json()
        sys_id = result['result']['sys_id']  # Extract sys_id if creation successful
        print(f"Incident created successfully with sys_id: {sys_id}")
        return result
    else:
        print(f"Error creating incident: {response.status_code} - {response.text}")
        return None  # Return None on failure
    


# Example Usage:
instance_url = "https://YOUR_INSTANCE.service-now.com"
username = "alejandro.mascall"
password = "YOUR_PASSWORD"
descriptions = [ ["Database performance is degraded in the test environment, maybe it's a network congestion or storage latency, please investigate", "node2"],
                ["Virtual machine 'develop15' failing due to insufficient disk space. Please do cleanup or archival actions or evaluate storage expansion options.","node3"], 
                ["Website performance is significantly degraded after upgrade, please rollback to the previous version and investigate the issue.","node1"]]


for desc in descriptions:
    response_data = create_servicenow_incident(instance_url, username, password, desc[0], desc[1])
    #if response_data is not None:
    #    # Optionally, process the response data
    #    print("Response Data:", response_data)
