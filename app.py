#!/bin/python

import requests
import schedule
import time
import os

def get_servicenow_incidents(instance_url, username, password):
    """Fetches incidents from a ServiceNow instance using REST API.

    Args:
        instance_url (str): Your ServiceNow instance URL (e.g., https://yourinstance.service-now.com)
        username (str): Your ServiceNow username
        password (str): Your ServiceNow password

    Returns:
        list: A list of dictionaries, each representing an incident.
    """
    
    url = f"{instance_url}/api/now/table/incident"
    headers = {"Accept": "application/json"}  # Specify JSON response

    try:
        response = requests.get(url, auth=(username, password), headers=headers)
    except Exception as e:
        print(f"Error: received exception connecting to the SNow instance {instance_url}")
        print(e)
    if response.status_code == 200:
        data = response.json()
        return data.get("result", [])  # Extract incident list or empty list if not found
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []  # Return empty list in case of errorsimport requests

def post_text_to_webservice(text, url):
    """Sends a POST request to a web service with the provided text.

    Args:
        text (str): The text content to include in the POST request body.
        url (str): The URL of the web service endpoint.

    Returns:
        requests.Response: The response object from the web service.
    """

    try:
        # Set up headers (optional but recommended)
        headers = {'Content-Type': 'application/json'}  # Common for JSON data
        # Create payload (if needed by the web service)
        data = {'text': text}  # Adjust this based on your web service's requirements
        # Send the POST request
        response = requests.post(url, headers=headers, json=data) 

        if response.status_code != 200:
            print(f"Error: POST request failed with status code {response.status_code}")
        
        return response

    except requests.exceptions.RequestException as e:
        print(f"Error sending POST request: {e}")
        return None  # Return None to indicate an error


def update_servicenow_incident(snow_url, snow_user, snow_pass, incident_sys_id, new_state, new_assigned_to, work_notes):
    """Updates a ServiceNow incident with new state, assignment, and work notes.

    Args:
        instance_url (str): Your ServiceNow instance URL (e.g., "https://yourinstance.service-now.com")
        username (str): Your ServiceNow username
        password (str): Your ServiceNow password
        incident_sys_id (str): The sys_id of the incident to update
        new_state (str): The new state value (e.g., "2" for In Progress)
        new_assigned_to (str): The sys_id of the user to assign the incident to
        work_notes (str): The update message to add as a work note

    Returns:
        bool: True if the update was successful, False otherwise.
    """

    url = f"{snow_url}/api/now/table/incident/{incident_sys_id}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    # Data payload for the update
    data = {
        "state": new_state,
        "assigned_to": new_assigned_to,
        "work_notes": work_notes
    }

    response = requests.patch(url, auth=(snow_user, snow_pass), headers=headers, json=data)

    if response.status_code == 200:
        print("Incident updated successfully!")
        return True
    else:
        print(f"Error updating incident: {response.status_code} - {response.text}")
        return False

def aap_start_automation(aap_url, aap_base_path, aap_user, aap_pass, snow_url, snow_user, snow_pass, snow_inc_number, category, host, workflow_template_id):
    # Headers definition
    headers = {'Content-Type': 'application/json'}

    # Launch Workflow Template
    data = {}
    data["extra_vars"] = {
        "snow_inc_number": f"{snow_inc_number}",
        "category": f"{category}",
        "snow_instance": f"{snow_url}",
        "snow_user": f"{snow_user}",
        "snow_pass": f"{snow_pass}",
    }
    data["limit"] = f"{host}"

    #print(data)

    launch_response = requests.post(
        f"{aap_url}/{aap_base_path}/v2/workflow_job_templates/{workflow_template_id}/launch/",
        headers=headers,
        auth=(aap_user, aap_pass),
        json=data
    )

    #print(launch_response.text)

    launch_response.raise_for_status()

    # Get Workflow Job ID
    workflow_job_id = launch_response.json()["id"]
    print(f"Workflow Job launched with ID: {workflow_job_id}")

def check_and_update_tickets():
    print("Running your function at", time.ctime())
    incidents = get_servicenow_incidents(snow_url, snow_user, snow_pass)

    # Process the incidents (e.g., print details)
    for incident in incidents:
        if incident['state'] == "1" and incident['assigned_to'] == "": 
            snow_inc_number = incident['number']
            snow_inc_desc = incident['short_description']
            snow_inc_host = incident['u_host']
            print(f"Number: {snow_inc_number}, Description: {snow_inc_desc}, Host: {snow_inc_host}")
            
            response = post_text_to_webservice(snow_inc_desc, webservice_url)
            response_dict = response.json()
            snow_inc_category = response_dict['category']
            print("The ticket has been classified as: "+snow_inc_category)
            # Now it's time to call AAP passing the response_dict['category'] and response_dict['u_host']
            aap_start_automation(aap_url, aap_base_path, aap_user, aap_pass, snow_url, snow_user, snow_pass, snow_inc_number, snow_inc_category, snow_inc_host, workflow_template_id)
            # Finally we can update the SNOW ticket
            success = update_servicenow_incident(snow_url, snow_user, snow_pass, incident['sys_id'], "2", assigned_to, work_notes+response_dict['category'])
            if success:
                print("Update was successful.")
            else:
                print("Update failed.")

# SNOW configuration
snow_url = os.environ['SNOW_URL']
snow_user = os.environ['SNOW_USER']
snow_pass = os.environ['SNOW_PASS']
assigned_to = os.environ['SNOW_ASSIGNED_TO']
work_notes = "Ansible Automation Platform is now working on the ticket resolution. AI/ML model classified the ticket as: "

# Predict webservice configuration
webservice_url = os.environ['ML_WS_URL']

# AAP configuration
aap_url = os.environ['AAP_URL']
aap_user = os.environ['AAP_USER']
aap_pass = os.environ['AAP_PASS']
aap_base_path = os.environ['AAP_BASE_PATH'] # AAP 2.5=/api/controller/ AAP 2.4=/api

workflow_template_id = os.environ['AAP_WF_ID']  # Replace with the actual ID 

# Run the function for the first time and then we will schedule it
check_and_update_tickets()

# Schedule the function to run every 1 minute
schedule.every(1).minutes.do(check_and_update_tickets)

# Keep the service running to execute the scheduled tasks
while True:
    schedule.run_pending()
    time.sleep(1)  # Sleep for a short duration to avoid excessive CPU usage
