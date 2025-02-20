import json
import requests
import time
import os

class ApiClient1:
    def __init__(self):
        self.server_ip = os.environ.get("LOCAL_HOST", "http://localhost")
        self.base_url_endpoint = f"{self.server_ip}:8000/pancake/"

    def get_empty_addresses(self, page_name):
    
        url = f"{self.base_url_endpoint}/select"

        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "page_name": page_name
            }
            # Convert the data dictionary to a JSON string
            json_data = json.dumps(data)

            r = requests.post(url, data=json_data, headers=headers)
            

            response_json_data = json.loads(r.text)

            if r.status_code == 200:
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"result":f"Excemption error occurs. More details: {e}", "success":False}
        

    
    def get_data_addresses_for_tagging(self, page_name):
    
        url = f"{self.base_url_endpoint}/select/tagging"

        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "page_name": page_name
            }
            # Convert the data dictionary to a JSON string
            json_data = json.dumps(data)

            r = requests.post(url, data=json_data, headers=headers)
            

            response_json_data = json.loads(r.text)

            if r.status_code == 200:
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"result":f"Excemption error occurs. More details: {e}", "success":False}
        

    def get_distinct_pages(self):
    
        url = f"{self.base_url_endpoint}/select/pages"

        try:
            headers = {"Content-Type": "application/json"}
            
            r = requests.get(url, headers=headers)
            

            response_json_data = json.loads(r.text)

            if r.status_code == 200:
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"result":f"Excemption error occurs. More details: {e}", "success":False}
        

    def set_data_to_db(self, body={}):
        headers = {"Content-Type": "application/json"}

        
        url = f"{self.base_url_endpoint}/insert"

        try:

            # Convert the data dictionary to a JSON string
            json_data = json.dumps(body)

            r = requests.post(url, data=json_data, headers=headers)
            
            response_json_data = json.loads(r.text)

            if r.status_code == 201:
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"response":f"Excemption error occurs. More details: {e}", "success":False}
        

    
    def update_address_from_db(self, body={}):
        headers = {"Content-Type": "application/json"}

        
        url = f"{self.base_url_endpoint}/update/address"

        try:

            # Convert the data dictionary to a JSON string
            json_data = json.dumps(body)

            r = requests.put(url, data=json_data, headers=headers)
            
            response_json_data = json.loads(r.text)

            if r.status_code == 201:
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"response":f"Excemption error occurs. More details: {e}", "success":False}
        

    def update_original_messages_from_db(self, body={}):
        headers = {"Content-Type": "application/json"}

        
        url = f"{self.base_url_endpoint}/update/chats/original_message"

        try:

            # Convert the data dictionary to a JSON string
            json_data = json.dumps(body)

            r = requests.put(url, data=json_data, headers=headers)
            
            response_json_data = json.loads(r.text)

            if r.status_code == 201:
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"response":f"Excemption error occurs. More details: {e}", "success":False}
        

    
    def update_status_from_db(self, body={}):
        headers = {"Content-Type": "application/json"}

        
        url = f"{self.base_url_endpoint}/update/status"

        try:

            # Convert the data dictionary to a JSON string
            json_data = json.dumps(body)

            r = requests.put(url, data=json_data, headers=headers)
            
            response_json_data = json.loads(r.text)

            if r.status_code == 201:
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"response":f"Excemption error occurs. More details: {e}", "success":False}
        

    
    def update_tag_from_db(self, body={}):
        headers = {"Content-Type": "application/json"}

        
        url = f"{self.base_url_endpoint}/update/tag"

        try:

            # Convert the data dictionary to a JSON string
            json_data = json.dumps(body)

            r = requests.put(url, data=json_data, headers=headers)
            
            response_json_data = json.loads(r.text)

            if r.status_code == 201:
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"response":f"Excemption error occurs. More details: {e}", "success":False}
        
        

    def update_chats_from_db(self, body={}):
        headers = {"Content-Type": "application/json"}

        
        url = f"{self.base_url_endpoint}/update/chats"

        try:

            # Convert the data dictionary to a JSON string
            json_data = json.dumps(body)

            r = requests.put(url, data=json_data, headers=headers)
            
            response_json_data = json.loads(r.text)

            if r.status_code == 201:
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"response":f"Excemption error occurs. More details: {e}", "success":False}
        

    

    def delete_data_from_db(self, body={}):
        headers = {"Content-Type": "application/json"}

        
        url = f"{self.base_url_endpoint}/delete"

        try:

            # Convert the data dictionary to a JSON string
            json_data = json.dumps(body)

            r = requests.delete(url, data=json_data, headers=headers)
            
            response_json_data = json.loads(r.text)

            if r.status_code == 200:
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"response":f"Excemption error occurs. More details: {e}", "success":False}
        


    def get_totalcount_inc_data(self, page_name):
    
        url = f"{self.base_url_endpoint}/select/inc"

        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "page_name": page_name
            }
            # Convert the data dictionary to a JSON string
            json_data = json.dumps(data)

            r = requests.post(url, data=json_data, headers=headers)
            

            response_json_data = json.loads(r.text)

            if r.status_code == 200:
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"result":f"Excemption error occurs. More details: {e}", "success":False}
    

    def get_totalcount_it_data(self, page_name):
    
        url = f"{self.base_url_endpoint}/select/it"

        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "page_name": page_name
            }
            # Convert the data dictionary to a JSON string
            json_data = json.dumps(data)

            r = requests.post(url, data=json_data, headers=headers)
            

            response_json_data = json.loads(r.text)

            if r.status_code == 200:
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"result":f"Excemption error occurs. More details: {e}", "success":False}

class ApiClient2:
    def __init__(self):
        self.server_ip = os.environ.get("LOCAL_HOST", "http://localhost")
        self.base_url_endpoint = f"{self.server_ip}:8000/pancake/"
        

    def select_id_by_address(self, province,city,barangay):
    
        url = f"{self.base_url_endpoint}/select_id_by_address"

        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "province": province,
                "city" : city,
                "barangay" : barangay
            }
            # Convert the data dictionary to a JSON string
            json_data = json.dumps(data)

            r = requests.post(url, data=json_data, headers=headers)
            

            response_json_data = json.loads(r.text)

            if r.status_code == 200:
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"result":f"Excemption error occurs. More details: {e}", "success":False}

    def select_address(self):
    
        url = f"{self.base_url_endpoint}/select_address"

        try:
            headers = {"Content-Type": "application/json"}
            data = {}
            # Convert the data dictionary to a JSON string
            json_data = json.dumps(data)

            r = requests.post(url, data=json_data, headers=headers)
            

            response_json_data = json.loads(r.text)

            if r.status_code == 200:
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"result":f"Excemption error occurs. More details: {e}", "success":False}
        
    def select_province(self,city,barangay):
    
        url = f"{self.base_url_endpoint}/select_province"

        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "barangay" : barangay,
                "city" : city
            }
            # Convert the data dictionary to a JSON string
            json_data = json.dumps(data)

            r = requests.post(url, data=json_data, headers=headers)
            
            response_json_data = json.loads(r.text)

            if r.status_code == 200:
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"result":f"Excemption error occurs. More details: {e}", "success":False}
    
    def get_address_code(self,barangay,city,province):
    
        url = f"{self.base_url_endpoint}/get_data_address_code"

        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "barangay" : barangay,
                "city" : city ,
                "province" : province
            }
            # Convert the data dictionary to a JSON string
            json_data = json.dumps(data)

            r = requests.post(url, data=json_data, headers=headers)
            
            response_json_data = json.loads(r.text)

            if r.status_code == 200:
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"result":f"Excemption error occurs. More details: {e}", "success":False}
        


    def get_barangay_city_province_code(self,barangay,city,province):
    
        url = f"{self.base_url_endpoint}/find/address/bcp/code"

        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "barangay" : barangay,
                "city" : city ,
                "province" : province
            }
            # Convert the data dictionary to a JSON string
            json_data = json.dumps(data)

            r = requests.post(url, data=json_data, headers=headers)
            
            response_json_data = json.loads(r.text)

            if r.status_code == 200:
                print(f"get_address_code >> {response_json_data} Type:{type(response_json_data)}\n get_address_code data sent >> {data}")
                return response_json_data
            else:
                return {"response":f"Code [{r.status_code}]. More details: {r}", "success":False}
            
        except Exception as e:
            return {"result":f"Excemption error occurs. More details: {e}", "success":False}
        
        
if __name__ == "__main__":

    print("Api Client 1")