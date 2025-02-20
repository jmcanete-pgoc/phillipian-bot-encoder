import datetime
from datetime import datetime as nowtime
import requests
import json
import time
import re
import sys
import os
import subprocess
import random
from ..tools import ProgramLog, POS_Pancake
from ..services import ApiClient1, ApiClient2
from ..utils import get_redis_connection
import pytz 
import sqlite3
import traceback

import ast
from difflib import SequenceMatcher




class WorkerTagger:
    
    def __init__(self, access_token, page_name, task_id):
        self.logger = ProgramLog(f"{page_name} (TAGGER)")
        self.access_token = access_token
        self.page_id = None
        self.page_name = page_name
        self.page_access_token = None
        self.log_file_name = None
        self.shop_id = None
        self.id_it_tag = None
        self.order_it_tag = None
        self.id_incomplete_tag = None
        self.order_incomplete_tag = None
        self.id_cancel_tag = None
        self.order_cancel_tag = None
        self.cutoff_time = datetime.datetime.strptime('16:00:00', '%H:%M:%S').time()
        self.sleep_scan = False
        self.kill_process = False
        self.iterate_index_for_groqtoken=0
        self.it_tagging_count = 0
        self.inc_tagging_count = 0
        self.generated_address = 0
        self.public_sku_name=None
        self.debug = False
        self.address_rows = ApiClient2().select_address().get("response")

        self.from_ai_brgy_city_province = None

        self.redis = get_redis_connection()  # Store the Redis connection
        self.task_id = task_id  # Store the task ID
        

    def run(self):
        
        try:
            
            while True:
                if self.redis.get(f"cancel_flag:{self.task_id}") == b"True":  # Check Redis
                    self.logs(text=f"Task {self.task_id} was cancelled.", type="info")
                    return
            
                try:

                    # if self.address_rows is None:
                    #     self.logs(text="Error: Unable to retrieve address data. Retry in 3 seconds.")
                    #     self.address_rows = ApiClient2().select_address().get("response")
                    #     time.sleep(3)
                    #     continue

                    # self.start_event.emit("Program (tagger) is now running...")
                    self.logs(text=f"Program (tagger) is now running...")
                    self.processing()
                    break
                except Exception as e:
                    self.logs(text=f"Program (tagger) failed on while loop. Error: {e}")
                    break
            # self.end_event.emit()

        except Exception as e:
            self.logs(text=f"Program (tagger) failed to start. Error: {e}")
        finally:
            return
        
    
    
    def processing(self):
        
        __class_module = FuncModules()
       
        self.get_page_id()
        
        if self.page_id is None:
            self.logs(type="error",text="Error: Unable to retrieve page ID. Exiting.")
            return
        

        self.get_page_settings()
        
        exported_tag_id = self.get_exported_tag_id()
        encoded_tag_id = self.get_encoded_tag_id()
        
        self.logs(text=f"ID of 'EXPORTED' tag: {exported_tag_id}")
        self.logs(text=f"ID of 'ENCODED' tag: {encoded_tag_id}")

        if self.id_it_tag is None or self.order_it_tag is None or self.shop_id is None or self.id_incomplete_tag is None or self.order_incomplete_tag is None:
            self.logs(text="Error: Unable to retrieve settings. Exiting.")
            return
        

        try:
            self.__class_pos_pancake = POS_Pancake(self.shop_id,self.access_token) 
            pos_inc_city , pos_inc_province, pos_inc_barangay , pos_inc_street ,pos_cc_changed_mind , pos_encoded = self.__class_pos_pancake.get_pos_tags()[0:6]
            blacklisted_tags = self.__class_pos_pancake.get_blacklist_tags()
            if pos_inc_city is None or pos_inc_province is None or pos_inc_barangay is None or pos_inc_street is None or pos_cc_changed_mind is None or pos_encoded is None:
                self.logs(text="Error: Unable to retrieve POS tags. Exiting.")
                return
        
        except Exception as e:
            print("POS ERROR > ", e)
            self.logs(text=f"POS ERROR > {e}")
            return
        

        count_of_new_unread_messages = 0
        self.logs(text=f"Data tagger is now running..")

        print(f"**** [TAGGER] ==> PAGE: {self.page_name}")
        while True:
            
            # Kill when window is closed
            if self.kill_process: return

            if self.redis.get(f"cancel_flag:{self.task_id}") == b"True":  # Check Redis
                self.logs(text=f"Task {self.task_id} was cancelled.", type="info")
                return

        return
        
        while True:
            
            # Kill when window is closed
            if self.kill_process: return


            try:
                self.logs_on_t2(color="black",text=f"New loop checking conversations {'...' * 30}")
                
                self.log_file_name = self.prepare_log_file()
                # len of conversation with NO INC/EXPORTED/IT/ENCODED tag
                
                response_data = ApiClient1(self.server_ip).get_data_addresses_for_tagging(self.page_name)
                if response_data.get("success", False):
                    conversations = response_data.get("response", [])
                else:
                    conversations = []
                
                

                if len(conversations) > 0:
                    for conv_index, conversation in enumerate(conversations):
                        # Kill when window is closed
                        if self.kill_process: return

                        __class_addr_validator = AddressValidator(self.server_ip)
                        __class_mysqlapi_areainfo = MysqlAreaInfoAPI(self.server_ip)
                        __class_sqlite_validator = SQLITE_BASED_ADDRESS_VALIDATOR_V1()

                        self.logs(text=f">>>>>> New Conversation Loop >>>>> Index={conv_index+1}/{len(conversations)} >> CONV ID: {conversation['conversation_id']}")
                        
                        conversation_id = conversation["conversation_id"]
                        customer_id = conversation['customer_id']

                        latest_order_info, req_code = self.get_latest_order_info(conversation_id, customer_id)
                        if req_code == 500:
                            body={
                                    "conversation_id": conversation_id,
                                    "customer_id": customer_id,
                            }
                            data = MysqlApiServices(self.server_ip).delete_data_from_db(body)

                        if latest_order_info:
                            latest_order_tags = latest_order_info.get('tags')
                            latest_order_inserted_at = latest_order_info.get('inserted_at')

                            return_for_next_loop = False

                            if latest_order_tags and (exported_tag_id in latest_order_tags or encoded_tag_id in latest_order_tags):
                                self.logs(text="Skipping conversation as tags EXPORTED or ENCODED are present.")
                                return_for_next_loop=True

                            if latest_order_tags and encoded_tag_id in latest_order_tags:
                                self.logs(text="Skipping conversation as tags ENCODED are present.")
                                return_for_next_loop=True

                            if latest_order_tags and exported_tag_id in latest_order_tags :
                                self.logs(text="Skipping conversation as tags EXPORTED are present.")
                                return_for_next_loop=True

                            if latest_order_tags and self.contains_any(latest_order_tags,blacklisted_tags):
                                self.logs(text="Skipping conversation as tags in blacklisted tags are present.")
                                return_for_next_loop=True
                                
                            # if not self.is_within_window(latest_order_inserted_at):
                            #     self.logs(text=f"Inserted_at date [{latest_order_inserted_at}] is not within the desired window. Conversation will still proceed.")
                            #     #self.logs(text=f"Inserted_at date [{latest_order_inserted_at}] is not within the desired window.  Skipping conversation.")
                            #     #continue


                            if return_for_next_loop:
                                body={
                                    "conversation_id": conversation_id,
                                    "customer_id": customer_id,
                                    "tag": "ENCODED"
                                }
                                data = MysqlApiServices(self.server_ip).update_tag_from_db(body)
                                continue

                            count_of_new_unread_messages += 1

                            latest_order_id = latest_order_info.get('id',"")
                            send_order_url = f"https://pos.pages.fm/api/v1/shops/{self.shop_id}/orders/{latest_order_id}?access_token={self.access_token}"
                            
                            messages = self.get_messages(conversation_id, customer_id)
                            if messages:
                                self.logs(text=f"Conversation ID: {conversation_id}")
                                self.logs(text=f"Customer: {conversation['customer_name']}")
                                self.logs(text="Messages:")
                                original_messages = []
                                

                                latest_sku = None
                                latest_sku_id = None
                                latest_product_id = None
                                latest_variation_id = None
                                latest_quantity = None

                                '''if lat and lng:
                                    postal_code = get_postal_code(lat, lng, postal_df)
                                    self.logs(text=f"Postal Code: {postal_code}")'''

                                try:
                                    for message in messages:
                                        # Kill when window is closed
                                        if self.kill_process: return
                                        
                                        if 'from' in message and 'id' in message['from']:
                                            if message['from']['id'] == conversation['customer_fb_id']:
                                                original_message = message.get('original_message', '(No original message)')
                                                original_messages.append(original_message)
                                                # self.logs(text=f"- {original_message}")

                                            elif message['from']['id'] == self.page_id:
                                                message_text = message.get('original_message', '')
                                                
                                                sku = self.get_last_sku(message_text)

                                                if sku:
                                                    self.public_sku_name = sku # this will be used once failed to determine sku name for the next loop

                                                    sku_id, product_id, variation_id, quantity = self.get_sku_id(sku)
                                                    
                                                    if sku_id and product_id and variation_id and quantity:
                                                        # self.logs(text=f"SKU ID: {sku_id}, Product ID: {product_id}, Variation ID: {variation_id}, Quantity: {quantity}")
                                                        latest_sku = sku
                                                        latest_sku_id = sku_id
                                                        latest_product_id = product_id
                                                        latest_variation_id = variation_id
                                                        latest_quantity = quantity
                                                    # else:
                                                    #     self.logs(text="Failed to retrieve SKU ID, product ID, variation ID, or quantity.")
                                                    #     continue
                                    
                                    splitted_messages = conversation["chats"].split(" <===> ")
                                    
                                    # print("!!!!!!" * 20)
                                    # print(">>", len(" ".join(original_messages)), len(splitted_messages[-1]))
                                    # print(">>", " ".join(original_messages))
                                    # print(">>", splitted_messages[-1])
                                    # print("!!!!!!" * 20)

                                    stringed_message = " ".join(original_messages)
                                    if any(len(stringed_message) == len(s) for s in splitted_messages):
                                        pass
                                        self.logs(text=f"{conversation['chats']}")
                                    else:
                                        difference = __class_module.get_non_matching_parts(conversation['chats'],stringed_message)
                                        if not difference.strip():
                                            formatted_message = conversation['chats']
                                            self.logs(text=f"No Difference between old chats and new")
                                        else:
                                            formatted_message = f"{conversation['chats']} <===> {difference}"
                                            self.logs(text=f"{stringed_message}")
                                            self.logs(text=f"{conversation['chats']}")
                
                                            print("Formatted messages >>> " , formatted_message , "length : ",len(formatted_message))
                                            
                                            body={
                                                "conversation_id": conversation_id,
                                                "customer_id": customer_id,
                                                "original_messages": formatted_message
                                            }
                                            
                                            data = MysqlApiServices(self.server_ip).update_original_messages_from_db(body)
                                        self.logs(text=f"{formatted_message}")
                                        
                                except Exception as e:
                                    self.logs(text=f">> Error occured during loop ong messages. Skip for next conversation loop. ERROR:{e} \nTraceback: {traceback.format_exc()}")
                                    continue

                                if not latest_sku:
                                    if self.public_sku_name:
                                        sku_id, product_id, variation_id, quantity = self.get_sku_id(self.public_sku_name)
                                        # print(f"SKU ID: {sku_id}, Product ID: {product_id}, Variation ID: {variation_id}, Quantity: {quantity}")
                                        if sku_id and product_id and variation_id and quantity:
                                            self.logs(text=f"SKU ID: {sku_id}, Product ID: {product_id}, Variation ID: {variation_id}, Quantity: {quantity}")
                                            latest_sku = self.public_sku_name
                                            latest_sku_id = sku_id
                                            latest_product_id = product_id
                                            latest_variation_id = variation_id
                                            latest_quantity = quantity
                                        else:
                                            self.logs(text="Failed to retrieve SKU ID, product ID, variation ID, or quantity.")
                                            # continue

                                if not original_messages:
                                    original_messages = conversation["chats"].split(" ")

                                # If SKU is found with messages, request to openai for address, tag if IT/INC, and order send to POS.
                                if latest_sku and original_messages:
                        
                                    openai_response = None
                                    llama_result_ok = False
                                    street_landmark = ""

                                    try:
                                        if conversation["address"]:
                                            
                                            try:
                                    
                                                addr_from_message = json.loads(conversation["address"])
                                            except json.decoder.JSONDecodeError:
                                                print("addr_from_message wrong format")
                                                addr_from_message = conversation["address"]
                                                addr_from_message = re.sub(r'"\s*:\s*(,|})', r'": ""\1', addr_from_message)
                                                addr_from_message = json.loads(addr_from_message)

                                            self.logs(text=f"[1000] AI-Generated address from messages: {addr_from_message}")
                                            if addr_from_message is not None and "province" in addr_from_message and "city" in addr_from_message and "barangay" in addr_from_message:
                                                province = addr_from_message.get("province", "")
                                                city=addr_from_message.get("city", "")
                                                barangay=addr_from_message.get("barangay", "")
                                                self.from_ai_brgy_city_province = f"{barangay}, {city}, {province}"

                                                if province and city and barangay:
                                                    street_landmark = f"{addr_from_message.get("street_purok","")} {addr_from_message.get("landmark","")}" 

                                                    self.logs(text=f"[1000 - 1] Searching for address code using SQLITE database.")
                                                    found = __class_sqlite_validator.get_address_code(province, city, barangay)
                                                    if found.get("exist", False):
                                                        openai_response_dict = {
                                                            "province_id": found.get("province_id", ""),
                                                            "district_id": found.get("district_id", ""),
                                                            "commune_id": found.get("commune_id", ""),
                                                            "address": street_landmark,
                                                            "full_address": f"{street_landmark}, {found.get("barangay", "")}, {found.get("city", "")}, {found.get("province", "")}"
                                                            }
                                                        openai_response = json.dumps(openai_response_dict, indent=4)
                                                    else:
                                                        self.logs(text=f"[1000 - 2] Address code not found. Trying another method to search for address code.")
                                                        __class_sql = SQLDataStruct()

                                                        found = __class_sql.get_address_code(province, city, barangay,self.address_rows)
                                                        if found.get("exist", False):
                                                            openai_response_dict = {
                                                                "province_id": found.get("province_id", ""),
                                                                "district_id": found.get("district_id", ""),
                                                                "commune_id": found.get("commune_id", ""),
                                                                "address": street_landmark,
                                                                "full_address": f"{street_landmark}, {found.get("full_address", "")}"
                                                                }
                                                            openai_response = json.dumps(openai_response_dict, indent=4)
                                                            
                                                        else:
                                                            self.logs(text=f"[1001] Address code not found. Trying another method to search for address code.")
                                                            found = __class_mysqlapi_areainfo.get_address_code(barangay,city,province)
                                                            
                                                            if "success" in found and found.get("success", False) and found.get("response", None):
                                                                found = found.get("response", [])
                                                                # self.logs(text=f">>>>>>>>>>> Found address code: [{barangay},{city},{province}] - {found}")

                                                                if isinstance(found, list):
                                                                    openai_response_dict = {
                                                                    "province_id": found[5],
                                                                    "district_id": found[4],
                                                                    "commune_id": found[3],
                                                                    "address": street_landmark,
                                                                    "full_address": f"{street_landmark}, {found[0]}, {found[1]}, {found[2]}"
                                                                    }

                                                                    openai_response = json.dumps(openai_response_dict, indent=4)
                                                                else:
                                                                    openai_response_dict = {
                                                                    "province_id": None,
                                                                    "district_id": None,
                                                                    "commune_id": None,
                                                                    "address": f"{street_landmark}",
                                                                    "full_address": f"{street_landmark},,,"
                                                                    }
                                                                    openai_response = json.dumps(openai_response_dict, indent=4)
                                                            else:
                                                                self.logs(text=f"[1002] Address code not found. Trying another method to search for address code.")
                                                                # find again from the database using SP:get_barangay_city_province_code()
                                                                
                                                                found = __class_mysqlapi_areainfo.get_barangay_city_province_code(barangay,city,province)
                                                                if "success" in found and found.get("success", False):
                                                                    found = found.get("response", [])

                                                                    if isinstance(found, list):
                                                                
                                                                        openai_response_dict = {
                                                                            "province_id": found[0],
                                                                            "district_id": found[1],
                                                                            "commune_id": found[2],
                                                                            "address": f"{street_landmark}",
                                                                            "full_address": f"{street_landmark}, {found[3]}, {found[4]}, {found[5]}"
                                                                        }

                                                                        openai_response = json.dumps(openai_response_dict, indent=4)
                                                                    else:
                                                                        openai_response_dict = {
                                                                        "province_id": None,
                                                                        "district_id": None,
                                                                        "commune_id": None,
                                                                        "address": f"{street_landmark}",
                                                                        "full_address": f"{street_landmark},,,"
                                                                        }
                                                                        openai_response = json.dumps(openai_response_dict, indent=4)
                                                                else:
                                                                    openai_response_dict = {
                                                                        "province_id": None,
                                                                        "district_id": None,
                                                                        "commune_id": None,
                                                                        "address": f"{street_landmark}",
                                                                        "full_address": f"{street_landmark},,,"
                                                                        }
                                                                    openai_response = json.dumps(openai_response_dict, indent=4)
                                                
                                                elif province or city or barangay:
                                                    
                                                    self.logs(text=f"[1003] Address code not found. Trying another method to search for address code.")
                                                    # find again from the database using SP:get_barangay_city_province_code()

                                                    street_landmark = f"{addr_from_message.get("street_purok","")} {addr_from_message.get("landmark","")}"

                                                    found = __class_mysqlapi_areainfo.get_address_code(barangay,city,province)
                                                        
                                                    if "success" in found and found.get("success", False):
                                                        found = found.get("response", [])
                                                        

                                                        openai_response_dict = {
                                                        "province_id": found[5],
                                                        "district_id": found[4],
                                                        "commune_id": found[3],
                                                        "address": street_landmark,
                                                        "full_address": f"{street_landmark}, {found[0]}, {found[1]}, {found[2]}"
                                                        }

                                                        openai_response = json.dumps(openai_response_dict, indent=4)

                                                    else: 
                                                    
                                                        found = __class_mysqlapi_areainfo.get_barangay_city_province_code(barangay,city,province)
                                                        if "success" in found and found.get("success", False):
                                                            found = found.get("response", [])

                                                            if isinstance(found, list):
                                                                
                                                                openai_response_dict = {
                                                                    "province_id": found[0],
                                                                    "district_id": found[1],
                                                                    "commune_id": found[2],
                                                                    "address": f"{street_landmark}",
                                                                    "full_address": f"{street_landmark}, {found[3]}, {found[4]}, {found[5]}"
                                                                }

                                                                openai_response = json.dumps(openai_response_dict, indent=4)
                                                            else:
                                                                openai_response_dict = {
                                                                "province_id": None,
                                                                "district_id": None,
                                                                "commune_id": None,
                                                                "address": f"{street_landmark}",
                                                                "full_address": f"{street_landmark},,,"
                                                                }
                                                                openai_response = json.dumps(openai_response_dict, indent=4)
                                                        else:
                                                            openai_response_dict = {
                                                                "province_id": None,
                                                                "district_id": None,
                                                                "commune_id": None,
                                                                "address": f"{street_landmark}",
                                                                "full_address": f"{street_landmark},,,"
                                                                }
                                                            
                                                            openai_response = json.dumps(openai_response_dict, indent=4)

                                    except json.decoder.JSONDecodeError as e:
                                        self.logs(type="error", text=f"Error decoding JSON address: {e}")
                                        

                                    except Exception as e:
                                        self.logs(type="error", text=f"Error exception on address decoding: {e} \nTraceback: {traceback.format_exc()}")



                                    if openai_response:
                                        self.logs(text=f"JSON Results: {json.loads(openai_response)}")
                                        self.generated_address += 1
                                        try:
                                            
                                            try:
                                                openai_response_json = ast.literal_eval(openai_response)
                                            except:
                                                try:
                                                    openai_response_json = json.loads(openai_response)
                                                except:
                                                    json_start = openai_response.find('{')
                                                    json_end = openai_response.rfind('}') + 1
                                                    data=openai_response[json_start:json_end]
                                                    openai_response_json = json.loads(data)

                                            # self.logs(text=f"openai_response_json -----> {openai_response_json} , {type(openai_response_json)}")
                                            # print("openai_response_json ----->", openai_response_json, type(openai_response_json))

                                            json_response = {
                                                "country_code": "63",
                                                "province_id": openai_response_json.get("province_id", ""),
                                                "district_id": openai_response_json.get("district_id", ""),
                                                "commune_id": openai_response_json.get("commune_id", ""),
                                                "address": openai_response_json.get("address", "")
                                            }


                                            
                                            if not llama_result_ok:
                                                try:
                                                    

                                                    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                                                    self.logs(text=f"[1st Validation Method] Non-AI Validator Script.") 

                                                    # Initialize Customer data as Dictionary; This will be used for address validation script.
                                                    get_chat_messages = {
                                                        "chat_messages":[
                                                            {
                                                                "commune_id": json_response.get("commune_id",""),
                                                                "district_id": json_response.get("district_id",""),
                                                                "province_id": json_response.get("province_id",""),
                                                                "customer": conversation['customer_name'],
                                                                "messages": original_messages,
                                                                "full_address": openai_response_json.get("full_address", "")
                                                            }]
                                                    }
                                                    result = __class_addr_validator.run(get_chat_messages)
                                                    try:
                                                        if result.get("valid", False) == True:
                                                            # get the street details right away if validation is True
                                                            # landmark = __class_findlmrk.get_nearest_landmark(" ".join(original_messages))
                                                            # if landmark:
                                                            #     json_response["address"] = f"{openai_response_json.get("address", "")} {landmark}"

                                                            if result is not None and "address_code" in result:
                                                                # update the address code
                                                                json_response["province_id"] = result.get("address_code")["province_id"]
                                                                json_response["district_id"] = result.get("address_code")["district_id"]
                                                                json_response["commune_id"] = result.get("address_code")["commune_id"]
                                                                self.logs(text=f"Address code was found during 1st validation process. Result: {result}")
                                                                llama_result_ok = True

                                                            elif json_response.get("address","") == "" and json_response.get("province_id","") and json_response.get("district_id","") and json_response.get("commune_id",""):
                                                                self.logs(text=f"Incomplete address. Maybe one of the required field is empty.")  

                                                            else:
                                                                self.logs(type="error", text=f"Missing data from 1st validation result. More details: {result}")
                                                                
                                                        else:
                                                            self.logs(text=f"Failed to validated the AI-generated address in 1st validation using Non-AI Validator Script. \n{result}")        
                                                    except Exception as e:
                                                        self.logs(type="error", text=f"Error exception on 1st Validation method: {e}")
                                                        llama_result_ok = False
                                                        
    
                                                except Exception as e:
                                                    self.logs(type="error", text=f"Error exception on validation process: {e}")
                                                    llama_result_ok = False
                                                    
                                                
                                            try:
                                                # check and repair street/purok/landmark details
                                                first_street_landmarks = __class_module.clean_strings(json_response.get("address",""))
                                                
                                                validated_streetpurok_info = self.validate_street_info(first_street_landmarks.strip(), " ".join(original_messages))
                                                
                                                if isinstance(validated_streetpurok_info, dict):
                                                    landmark_street_info = f"{validated_streetpurok_info.get("street","")} {validated_streetpurok_info.get("purok","")} {validated_streetpurok_info.get("zone","")} {validated_streetpurok_info.get("landmarks","")}"
                                                    first_street_landmarks = landmark_street_info
                                                    if str(landmark_street_info).strip() == "":
                                                        # self.logs(text=f"street is none 1 {validated_streetpurok_info}")
                                                        result.update({"INC_Street" : True})
                                                        llama_result_ok = False

                                                elif isinstance(validated_streetpurok_info, str):
                                                    if validated_streetpurok_info.lower() in ["", "[]", "unknown", "null"]:
                                                        # self.logs(text=f"street is none 2 {validated_streetpurok_info}")
                                                        result.update({"INC_Street" : True})
                                                        llama_result_ok = False

                                                # clean address from STREET/PUROK/Landmark/etc.
                                                if not llama_result_ok:
                                                    json_response["address"] = f"({self.from_ai_brgy_city_province}) " + __class_module.clean_strings(first_street_landmarks)
                                                else:
                                                    json_response["address"] = __class_module.clean_strings(first_street_landmarks)

                                            except Exception as e:
                                                self.logs(type="error", text=f"Error on street validation: {e}")
                                                

                                            # wether the validation address is true/false, order send to POS.
                                            # Check if ENCODED / EXPORTED is present before Sending data to POS-PANCAKE
                                            latest_order_info, req_code = self.get_latest_order_info(conversation_id, customer_id)
                                            if latest_order_info:
                                                latest_order_tags = latest_order_info.get('tags')

                                                in_pos =  self.__class_pos_pancake.check_encoded_exported_tag_in_pos(send_order_url,conversation_id)

                                                if latest_order_tags and (exported_tag_id in latest_order_tags or encoded_tag_id in latest_order_tags):
                                                    self.logs(text="!!!!!! Skipping conversation as tags EXPORTED or ENCODED are present. !!!!!!")
                                                    body={
                                                        "conversation_id": conversation_id,
                                                        "customer_id": customer_id,
                                                        "tag": "ENCODED"
                                                    }
                                                    data = MysqlApiServices(self.server_ip).update_tag_from_db(body)
                                                    continue
                                                 
                                                if in_pos == True:
                                                    # print("!!!!!! [POS] Skipping conversation as tags EXPORTED or ENCODED are present. !!!!!!")
                                                    self.logs(text="!!!!!! [POS] Skipping conversation as tags are inside black listed tags. !!!!!!")
                                                    body={
                                                        "conversation_id": conversation_id,
                                                        "customer_id": customer_id,
                                                        "tag": "ENCODED"
                                                    }
                                                    data = MysqlApiServices(self.server_ip).update_tag_from_db(body)
                                                    continue

                                                if result is not None and result.get("cancel",False) == True:
                                                    tagged_as = "CANCEL"
                                                    tags = [pos_cc_changed_mind]
                                                    body={
                                                        "conversation_id": conversation_id,
                                                        "customer_id": customer_id,
                                                        "tag": "CANCELED",
                                                        "remarks":"Canceled order"
                                                    }

                                                elif llama_result_ok:
                                                    tagged_as = "IT"
                                                    tags = [pos_encoded]
                                                    self.it_tagging_count +=1
                                                    body={
                                                        "conversation_id": conversation_id,
                                                        "customer_id": customer_id,
                                                        "tag": "IT",
                                                        "remarks":"Completed"
                                                    }

                                                else:

                                                    tagged_as = "INC"
                                                    tags = self.__class_pos_pancake.specific_inc(result,pos_inc_province,pos_inc_city,pos_inc_barangay,pos_inc_street)
                                                    body={
                                                        "conversation_id": conversation_id,
                                                        "customer_id": customer_id,
                                                        "tag": "INC",
                                                        "remarks":"Failed validation"
                                                    }
                                                    

                                                if self.debug == False:

                                                    if latest_sku:
                                                        pos_response_code = self.send_order_to_pos(
                                                                    send_order_url, json_response, latest_sku_id, 
                                                                    latest_product_id, latest_variation_id, latest_quantity,tags
                                                                )
                                                    else:
                                                        
                                                        pos_response_code = self.send_order_no_sku(send_order_url,json_response)
                                                    # self.logs(text=f"status_code: {pos_response_code} URL >> {send_order_url}")
                                                else:
                                                    pos_response_code = 200
                                            else:
                                                continue

                                            if pos_response_code == 200:
                                                match tagged_as:
                                                    case "CANCEL":
                                                        
                                                        self.all_tagging(self.debug,conversation_id,tagged_as,self.id_cancel_tag)
                                                        self.logs(text="Cancel phrases was found in the conversation. Order Tagged as 'CANCEL'")
                                                        self.logs_on_t2(color="darkYellow",text=f"Index={conv_index+1}/{len(conversations)} | Chat ID: {conversation_id} | Customer: {conversation['customer_name']} | Tag='CANCEL'")
                                                        
                                                    case "IT":
                                                        
                                                        self.all_tagging(self.debug,conversation_id,tagged_as,self.id_it_tag)
                                                        self.logs(text="Successfully tagged as 'IT' -> complete shipping address.")
                                                        self.logs_on_t2(color="darkGreen",text=f"Index={conv_index+1}/{len(conversations)} | Chat ID: {conversation_id} | Customer: {conversation['customer_name']} | Tag='IT'")
                                                        final_completed_address = json.dumps(json_response, indent=4)
                                                        self.logs(text=f"Final validated address => {final_completed_address} \n")

                                                    case "INC":
                                                        
                                                        self.all_tagging(self.debug,conversation_id,tagged_as,self.id_incomplete_tag)
                                                        self.logs(text=f"Failed to validate address. Order tagged as 'INC' or incomplete.")
                                                        self.logs_on_t2(color="red",text=f"Index={conv_index+1}/{len(conversations)} | Chat ID: {conversation_id} | Customer: {conversation['customer_name']} | Tag='INC'")
                                                        log_tags = {
                                                        "INC_PROVINCE" : result.get("INC_Province"),
                                                        "INC_CITY" : result.get("INC_City"),
                                                        "INC_BARANGAY" : result.get("INC_Barangay"),
                                                        "INC_STREET" : result.get("INC_Street"),
                                                        }
                                                        log_tags = json.dumps(log_tags)
                                                        self.logs(text=f"TAGS > {log_tags}")                                                        

                                                data = MysqlApiServices(self.server_ip).update_tag_from_db(body)
                                            
                                            else:
                                                # print(f"[101] Name:{conversation['customer_name']}; ------> FAILED to POST")
                                                self.logs(type="error", text=f"Error occurred while sending order to POS. Response code: {pos_response_code}")
                                                success = self.all_tagging(self.debug,conversation_id,"INC",self.id_incomplete_tag)

                                                if success:
                                                    self.logs(text=f"Posting order to POS with errors.")
                                                    self.logs_on_t2(color="red",text=f"Index={conv_index+1}/{len(conversations)} | Chat ID: {conversation_id} | Customer: {conversation['customer_name']} | Tag='INC'")
                                                    
                                                    body={
                                                        "conversation_id": conversation_id,
                                                        "customer_id": customer_id,
                                                        "tag": "",
                                                        "remarks":"POS error"
                                                    }
                                                    data = MysqlApiServices(self.server_ip).update_tag_from_db(body)

                                        except json.decoder.JSONDecodeError as e:
                                            self.logs(type="error", text=f"Error decoding JSON response: {e}")
                                        except Exception as e:
                                            if openai_response:
                                                self.logs(type="error", text=openai_response_json)
                                            self.logs(type="error", text=f"Error exception: {e}\nTraceback: {traceback.format_exc()}")
                                            continue
                                    else:
                                        # print(f"[102] Name:{conversation['customer_name']}; ------> FAILED to POST :: NO address provided or incomplete")
                                        success = self.all_tagging(self.debug,conversation_id,"INC",self.id_incomplete_tag)
                                        if success:
                                           
                                            self.logs(text=f"NO address provided or incomplete. Order tagged as 'INC' or incomplete.")
                                            self.logs_on_t2(color="red",text=f"Index={conv_index+1}/{len(conversations)} | Chat ID: {conversation_id} | Customer: {conversation['customer_name']} | Tag='INC'")
                                            
                                            body={
                                                "conversation_id": conversation_id,
                                                "customer_id": customer_id,
                                                "tag": "INC",
                                                "remarks":"No addresses"
                                            }
                                            
                                            data = MysqlApiServices(self.server_ip).update_tag_from_db(body)

                                else:
                                    print(f"[103] Name:{conversation['customer_name']}; ------> FAILED to POST")
                                    self.logs(text="Missing SKU ID, product ID, variation ID, or quantity. Skipping OpenAI request and order sending.")
                                    try:
                                        if conversation["address"]:
                                            
                                            addr_from_message = json.loads(conversation["address"])
                                            
                                            self.send_order_no_sku(send_order_url, json_response)
                                    except Exception as e:
                                        print("MISSING SKU ERROR > ",e)
                                        continue
                self.logs(text="======================")
                self.logs(text=f"Iteration end timestamp: {datetime.datetime.now()}")
                self.logs(text=f"Logs for this iteration have been saved to: ~/.pgocapp/logs/{self.log_file_name}")
                self.logs(text="Waiting for 1 minutes before checking conversations again... You can skip waiting by pressing the button 'Restart Iteration'.")
                
                # update on tagging count
                data = MysqlApiServices(self.server_ip).get_totalcount_inc_data(self.page_name)
                self.inc_tagging_count = data.get("response", 0)[0]

                data = MysqlApiServices(self.server_ip).get_totalcount_it_data(self.page_name)
                self.it_tagging_count = data.get("response", 0)[0]

                self.on_tagging.emit(self.it_tagging_count, self.inc_tagging_count)
                # 300 seconds = 5 minutes
                self.set_program_sleep_5_minutes(seconds=1)


            except requests.exceptions.HTTPError as e:
                print("[Conversation Loop] - (requests.exceptions.HTTPError) An error code: ", e.response.status_code)

            except Exception as e:
                self.logs(type="error", text=f"[Conversation Loop] - (Exception) An error occurred: More details: {e} \nTraceback: {traceback.format_exc()}")
                
            finally:
                self.on_tagging.emit(self.it_tagging_count, self.inc_tagging_count)
                


    
        



    def fetch_street_purok(self,message):
        with open('assets/spoken_landmarks.json', 'r') as f:
            landmarks_data = json.load(f)

        # Construct the system content with formatted dataset_json
        system_content = f"""{{
            "instructions": [
                "You will receive message logs from our customers in the Philippines.",
                "Find the message and decode the address wich refers to street name, zone, purok or sitio, or landmarks.",
                "You can also use the spoken_landmarks data given below which is the most common spoken words of filipinos to determine the nearest landmarks from the message.",
                "The address must not exceed of more than 300 characters",
                "Output in JSON format only.",
                "Do not explain."
            ],
            "spoken_landmarks": {landmarks_data},
            "response_format": "JSON",
            "output_format": {{
                "street": "Street name",
                "purok":"purok name", 
                "zone":"zone name or sitio",
                "landmarks":"landmarks or building names"
            }}
            }}"""
        
        messages=[
                {
                    "role": "system",
                    "content": system_content
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        def remove_non_bmp_chars(text):
            return "".join(char for char in text if ord(char) < 0x10000)
        
        # self.scraper.new_instructions(remove_non_bmp_chars(f"""{system_content} , {messages}"""))
        


    def remove_tag_by_customer(self, customer_id=None, tagged_as='', tags=[]):
        if customer_id is None: return False

        url = f"https://pancake.ph/api/public_api/v1/pages/{self.page_id}/conversations/{customer_id}/tags?page_access_token={self.page_access_token}"


        match tagged_as:
            case "CANCEL":
                payload={
                "action":"remove",
                "tag_id":self.id_it_tag
                }
            case "IT":
                payload={
                "action":"remove",
                "tag_id":self.id_it_tag
                }
            case "INC":
                payload={
                "action":"remove",
                "tag_id":self.id_incomplete_tag
                }

        headers = {
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(url, data=json.dumps(payload))
            if response.status_code == 200:
                data = response.json()
                return True
        except Exception as e:
            self.logs(type="critical",text=f"An error occurred while API POST for ../conversation/tags: {e}")
        return False
    



    def get_page_id(self):
        
        url = f"https://pancake.ph/api/v1/pages?access_token={self.access_token}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                pages = data.get("categorized", {}).get("activated", [])
                for page in pages:
                    if page["name"].lower() == self.page_name.lower():
                        self.page_id = page["id"]  # Set PAGE_ID value
                        self.logs(text=f"Page ID: {self.page_id}")
                        return
                self.logs(text="Page not found.")
            else:
                self.logs(type="error",text=f"Failed to retrieve data. Status code: {response.status_code}")
        except Exception as e:
            self.logs(type="critical",text=f"An error occurred: {e}")


    # Function to get ID_IT_TAG, ORDER_IT_TAG, SHOP_ID
    def get_page_settings(self):
        url = f"https://pancake.ph/api/v1/pages/{self.page_id}/settings?access_token={self.access_token}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                self.shop_id = data.get("shop_id", None)
                if self.shop_id is not None:
                    self.logs(text=f"Shop ID: {self.shop_id}")
                else:
                    self.logs(text="Shop ID not found.")


                self.page_access_token = data["settings"].get("page_access_token", None)
                if self.page_access_token is not None:
                    self.logs(text="Page access token is available.")
                else:
                    self.logs(text="Page access token is missing or not found.")

                # Get all tags
                tags = data["settings"].get("tags", [])

                # Get IT Tag
                IT_tag = next((tag for tag in tags if tag["text"] == "IT"), None)
                if IT_tag:
                    ID_IT_TAG = IT_tag["id"]
                    ORDER_IT_TAG = tags.index(IT_tag)
                    self.logs(text=f"ID_IT_TAG: {ID_IT_TAG}")
                    self.logs(text=f"ORDER_IT_TAG: {ORDER_IT_TAG}")

                    self.id_it_tag = ID_IT_TAG
                    self.order_it_tag = ORDER_IT_TAG
                else:
                    self.logs(text="Tag with name 'IT' not found.")

                # Get INC = Incomplete Tag
                INC_tag = next((tag for tag in tags if tag["text"] == "INC"), None)
                if INC_tag:
                    ID_INC_TAG = INC_tag["id"]
                    ORDER_INC_TAG = tags.index(INC_tag)
                    self.logs(text=f"ID_INC_TAG: {ID_INC_TAG}")
                    self.logs(text=f"ORDER_INC_TAG: {ORDER_INC_TAG}")

                    self.id_incomplete_tag = ID_INC_TAG
                    self.order_incomplete_tag = ORDER_INC_TAG
                else:
                    self.logs(text="Tag with name 'INC' not found.")

                CANCEL_tag = next((tag for tag in tags if tag["text"] == "CANCEL"), None)

                if CANCEL_tag:
                    ID_CANCEL_TAG = CANCEL_tag["id"]
                    ORDER_CANCEL_TAG = tags.index(CANCEL_tag)
                    self.logs(text=f"ID_INC_TAG: {ID_CANCEL_TAG}")

                    self.id_cancel_tag = ID_CANCEL_TAG
                    self.order_cancel_tag = ORDER_CANCEL_TAG
                else:
                    self.logs(text="Tag with name 'CANCEL' not found.")

            else:
                self.logs(type="error",text=f"Failed to retrieve data. Status code: {response.status_code}")
        except Exception as e:
            self.logs(type="critical",text=f"An error occurred: {e}")


    def get_exported_tag_id(self):
        try:
            url = f"https://pos.pages.fm/api/v1/shops/{self.shop_id}?access_token={self.access_token}&load_promotion=1"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            shop = data.get("shop", {})
            order_tags = shop.get("order_tags", [])
            for tag in order_tags:
                if tag.get("name") == "EXPORTED":
                    return tag.get("id")
            return None
        except requests.exceptions.RequestException as e:
            self.logs(type="error",text=f"HTTP request failed: {e}")
            return None
        except ValueError as e:
            self.logs(type="critical",text=f"Failed to parse JSON response: {e}")
            return None
        

    def get_encoded_tag_id(self):
        try:
            url = f"https://pos.pages.fm/api/v1/shops/{self.shop_id}?access_token={self.access_token}&load_promotion=1"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            shop = data.get("shop", {})
            order_tags = shop.get("order_tags", [])
            for tag in order_tags:
                if tag.get("name") == "ENCODED":
                    return tag.get("id")
            return None
        except requests.exceptions.RequestException as e:
            self.logs(type="error",text=f"HTTP request failed: {e}")
            return None
        except ValueError as e:
            self.logs(type="critical",text=f"Failed to parse JSON response: {e}")
            return None

    def get_unattended_orders(self,exported_tag_id , encoded_tag_id) -> list:
        try:
            hour = datetime.datetime.now(pytz.timezone('UTC')).hour
            unattended_orders = [dict]
            for end_hour in range(hour):
                if self.kill_process: return
                current_date = datetime.datetime.now(pytz.timezone('UTC'))
                start_date = current_date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
                end_date = current_date.replace(hour=end_hour, minute=59, second=59, microsecond=999999)
                START_DATE = int(start_date.timestamp())
                END_DATE = int(end_date.timestamp())
                conversations = self.get_conversations(START_DATE,END_DATE, [self.id_it_tag, self.order_it_tag])
                if conversations:
                    for conv in conversations:
                        if self.kill_process: return
                        if not exported_tag_id in conv['tags'] and not encoded_tag_id in conv['tags'] and not self.id_it_tag in conv['tags']: #and not self.id_incomplete_tag in conv['tags']:
                            if conv not in unattended_orders:
                                # print(f"unattended order - {type(conv)}")
                                unattended_orders.append(conv)
            
            if unattended_orders:
                return unattended_orders
            else:
                return None
        except Exception as e:
            print("EXCEPTION = ", e)

    def get_conversations(self, START_DATE, END_DATE,  exceptTags=[]) -> list:
        get_conversations_url = f"https://pancake.ph/api/v1/pages/{self.page_id}/conversations?unread_first=true&type=PHONE,DATE:{START_DATE}+-+{END_DATE},INBOX&mode=OR&tags=%22ALL%22&except_tags={exceptTags}&access_token={self.access_token}&from_platform=web"
        # print("get_conversations_url >> ", get_conversations_url)
        response = requests.get(get_conversations_url)
        if response.status_code == 200:
            data = response.json()
            conversations = data.get('conversations', [])
            if not conversations:
                self.logs(text="Warning: Status code 200, but no conversations found.")
                self.logs(text=get_conversations_url)
            return conversations
        else:
            self.logs(type="error",text=f"Error: {response.status_code}")
            self.logs(type="error",text=get_conversations_url)
            return None
    
    def get_latest_order_info(self, conversation_id, customer_id):
        url = f"https://pancake.ph/api/v1/pages/{self.page_id}/conversations/{conversation_id}/messages/recent_orders"
        params = {
            "customer_id": customer_id,
            "access_token": self.access_token
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            recent_orders = data.get('recent_orders', [])
            if recent_orders:
                latest_order = recent_orders[0]
                return latest_order, 200
            else:
                self.logs(type="error",text="Error: No recent orders found.")
                return None, 200
        else:
            self.logs(type="error",text=f"Error: {response.status_code}")
            return None, 500    

    def is_within_window(self,inserted_at):
        try:
            inserted_at_local = datetime.datetime.strptime(inserted_at, "%Y-%m-%dT%H:%M:%S") + datetime.timedelta(hours=8)
            now_local = datetime.datetime.now() + datetime.timedelta(hours=8)
            cutoff_yesterday = datetime.datetime.combine((now_local - datetime.timedelta(days=1)).date(), self.cutoff_time)
            cutoff_today = datetime.datetime.combine(now_local.date(), self.cutoff_time)
            self.logs(f"[TIME WITHIN WINDOW] inserted_at_local={inserted_at_local} | now_local={now_local} | cutoff_ysdy={cutoff_yesterday} | cutoff_tdy={cutoff_today}")
            return cutoff_yesterday <= inserted_at_local <= cutoff_today
        except ValueError:
            self.logs(type="error",text=f"Error: Invalid inserted_at format: {inserted_at}")
            return False
        

    def get_messages(self, conversation_id, customer_id):
        url = f"https://pancake.ph/api/v1/pages/{self.page_id}/conversations/{conversation_id}/messages"
        params = {
            "customer_id": customer_id,
            "access_token": self.access_token,
            "user_view": "true",
            "is_new_api": "true"
        }
        response = requests.get(url, params=params)


        if response.status_code == 200:
            data = response.json()
            try:
                return data['messages']
            except:
                return None
        else:
            self.logs(type="error",text=f"Error: {response.status_code}")
            return None
        
    def get_last_sku(self, message_text):
        # Find the last SKU in the message using a regular expression
        sku_matches = re.findall(r'\b[\d\w\+]+=\d+\b', message_text)
        if not sku_matches:
            return None
        return sku_matches[-1]  # Return the last matched SKU
    

    def get_sku_id(self, sku_name):
        sku_id = None
        product_ids = []
        variation_ids = []
        quantities = []

        try:
            # Split the SKU name by '='
            items_and_total_cost = sku_name.rsplit('=', 1)
            if len(items_and_total_cost) != 2:
                self.logs(text="Invalid SKU format.")
                return None, None, None, None
            
            items = items_and_total_cost[0].split('+')
            total_cost = items_and_total_cost[1]
            
            # Extract quantities and item names
            for item in items:
                qty = ''
                item_name = ''
                for char in item:
                    if char.isdigit():
                        qty += char
                    else:
                        item_name += char

                if not qty.isdigit():
                    # self.logs(text=f"Invalid quantity format for item: {item} ({qty})")
                    continue
                
                qty = int(qty)
                quantities.append(qty)
                #log_to_ui(f"Item: {item_name}, Quantity: {qty}")
            
            # URL for fetching SKU ID, product IDs, and variation IDs based on the SKU name
            combo_url = f"https://pos.pages.fm/api/v1/shops/{self.shop_id}/combo_products"
            combo_params = {
                "search": sku_name.lower(),
                "access_token": self.access_token
            }

            # Fetching combo product information
            combo_response = requests.get(combo_url, params=combo_params)
            if combo_response.status_code == 200:
                combo_data = combo_response.json()
                for combo_product in combo_data.get('data', []):
                    if combo_product.get('name').lower() == sku_name.lower():
                        sku_id = combo_product.get('id')
                        #log_to_ui(f"SKU ID: {sku_id}")
                        for variation in combo_product.get('variations', []):
                            product_id = variation.get('product_id')
                            variation_id = variation.get('id')
                            product_ids.append(product_id)
                            variation_ids.append(variation_id)
                            #log_to_ui(f"Product ID: {product_id}, Variation ID: {variation_id}")
                        break
            else:
                self.logs(type="error", text=f"Error fetching combo product ID: {combo_response.status_code}")

        except IndexError as e:
            self.logs(type="critical", text=f"IndexError: {e}")
        except KeyError as e:
            self.logs(type="critical", text=f"KeyError: {e}")
        except Exception as e:
            self.logs(type="critical", text=f"An unexpected error occurred: {e}")
        
        # Return the gathered information
        return sku_id, product_ids, variation_ids, quantities
    
    def send_order_no_sku(self,url,json_response):

        payload = {
            "order": {
                "shop_id": self.shop_id,
                "page_id": self.page_id,
                "shipping_address": json_response,
                },
            }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.access_token
        }

        # response = requests.put(url, headers=headers, data=json.dumps(payload))
            
        # return response.status_code
    
    def send_order_to_pos(self, url, json_response, sku_id, product_ids, variation_ids, quantities,tags:list):
        # print(f"URL >> {url}")
        items = []
        combo_product_variations = []
        combo_variation_ids = []  # For storing unique IDs for combo product variations

        # Process items
        for prod_id, var_id, qty in zip(product_ids, variation_ids, quantities):
            item = {
                "quantity": qty,
                "variation_id": var_id,
                "product_id": prod_id
            }
            items.append(item)

        # Process combo product variations
        for prod_id, var_id, qty in zip(product_ids, variation_ids, quantities):
            # Generate a unique ID for each combo product variation
            combo_variation_id = f"{sku_id}_{prod_id}_{var_id}"
            if combo_variation_id not in combo_variation_ids:
                combo_variation_ids.append(combo_variation_id)
                combo_variation = {
                    "count": qty,
                    "id": combo_variation_id,
                    "product_id": prod_id,
                    "variation_id": var_id
                }
                combo_product_variations.append(combo_variation)
            else:
                # If the combo variation ID already exists, find its index and update the count
                index = combo_variation_ids.index(combo_variation_id)
                combo_product_variations[index]["count"] += qty

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.access_token
        }

        if tags:
            pass
            # payload = {
            #     "tags": tags
            # }
            # response = requests.put(url, headers=headers, data=json.dumps(payload))
            print("Pos Has Tags")
        else:
            print("No Pos Tags")

        payload = {
            "order": {
                "shop_id": self.shop_id,
                "page_id": self.page_id,
                "shipping_address": json_response,
                "items": items,
                "activated_combo_products": [
                    {
                        "combo_product_id": sku_id,
                        "combo_product_info": {
                            "combo_product_variations": combo_product_variations
                        }
                    }
                ]
            },
        }
        
        response = requests.put(url, headers=headers, data=json.dumps(payload))
        # if response.json().get("data").get("tags",[]) != tags:
        #     response = requests.put(url, headers=headers, data=json.dumps(payload))
        #     self.logs("resending orders...")
    
        return response.status_code
    
    def contains_any(self, lst, check_list):
        check_set = set(check_list)
        return any(elem in check_set for elem in lst)
    
    def toggle_tag(self, conversation_id, id_tag=None):
        if id_tag is not None:
            url = f"https://pancake.ph/api/v1/pages/{self.page_id}/conversations/{conversation_id}/toggle_tag?access_token={self.access_token}"
            # payload = {'tag_id': self.id_it_tag, 'value': '1'}
            payload = {'tag_id': id_tag, 'value': '1'}
            headers = {}
            response = requests.request("POST", url, headers=headers, data=payload)
            if response.status_code == 200:
                self.logs(text="Order successfully Tagged.")
                return True
            else:
                self.logs(type="error", text=f"Error occurred while toggling tag. Status code: {response.status_code}")
                return False
        
        self.logs(type="error", text=f"Error occurred while toggling tag. Unkown ID Tag: {id_tag} | Affected conversation_id: {conversation_id}")
        return False

    def prepare_log_file(self):
        current_date = datetime.datetime.now().strftime("%m_%d")
        return f"logs_{self.page_name}_seq_{current_date}.logs"
        
    def logs(self, type="info", text=""):
        now = nowtime.now().strftime("%m/%d/%y, %H:%M:%S")
        text = " [ " +now + " ] - " + str(text) 
        # if type=="error": self.logger.write_log_error(text)
        # elif type=="critical": self.logger.write_log_critical(text)
        # else: self.logger.write_log_info(text)


    def logs_on_t2(self, type="info", text="", color="black"):
        pass

    def all_tagging(self,debug : bool,conversation_id :str,completed : str ,id_tag):
        if debug == False:
            self.remove_tag_by_customer(conversation_id, completed)
            toggle_tag_response_code = self.toggle_tag(conversation_id,id_tag)
            self.mark_as_read(conversation_id)
            return toggle_tag_response_code
        return False

    def set_program_sleep_5_minutes(self, seconds=300):
        self.sleep_scan = True
        self.on_sleep_scan.emit(True)
        # 1 seconds x 300 = 300 seconds = 5 minutes
        for i in range(0, seconds):
            # Kill when window is closed
            if self.kill_process: return
            if not self.sleep_scan: break
            time.sleep(1)
        self.sleep_scan = False
        self.on_sleep_scan.emit(False)

    def validate_street_info(self, street_purok="", message=""):
        orig = street_purok
        # try:
        #     if len(street_purok) > 100:
        #         self.fetch_street_purok(street_purok)
        #         loop = QEventLoop()
        #         self.scraper.send_message.connect(loop.quit)
        #         QTimer.singleShot(15000, loop.quit)
        #         print("Before loop")
        #         loop.exec()
        #         print("self.fetch_street_purok")
        #         streetpurok = self.scraper_finished
        #         self.scraper_finished = None
        #         return streetpurok
        #     elif street_purok == "" or street_purok == "[]" or street_purok.lower() == "none":
        #         self.fetch_street_purok(message)
        #         loop = QEventLoop()
        #         self.scraper.send_message.connect(loop.quit)
        #         QTimer.singleShot(15000, loop.quit)
        #         print("Before loop")
        #         loop.exec()
        #         print("self.fetch_street_purok")
        #         streetpurok = self.scraper_finished
        #         self.scraper_finished = None
        #         return streetpurok
        # except Exception as e:
        #     print("\n>> Error on street/purok info validation with Llama: More details here:", e)
        return orig

    def mark_as_read(self,customer_id=None):
        url = f"https://pancake.ph/api/public_api/v1/pages/{self.page_id}/conversations/{customer_id}/read?page_access_token={self.page_access_token}"
        try:
            response = requests.post(url)
            if response.status_code == 200:
                return True
        except Exception as e:
            self.logs(type="critical",text=f"An error occurred while API POST for ../conversation/tags: {e}")
        return False

    def delete_from_database(self,conversation_id):
        with sqlite3.connect("db/generate_address.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversations WHERE conversation_id = ?",(conversation_id,))
            conn.commit()
        print(f"{conversation_id} is deleted")


    def cleanup(self):
        self.kill_process = True
        self.logs(text="Cleaning up resources...")



class FuncModules:
    def __init__(self) -> None:
        pass

    def get_non_matching_parts(self,string1, string2):
        """
        Returns non-matching parts in string2 compared to string1.

        Args:
            string1 (str): The reference string.
            string2 (str): The string to compare.

        Returns:
            str: Non-matching parts in string2.
        """
        # Split both strings into words and convert to sets
        words1 = set(string1.split())
        words2 = string2.split()

        # Find non-matching parts in string2
        non_matching = [word2 for word2 in words2 if word2 not in words1]

        # Join the non-matching parts with a space
        return " ".join(non_matching).strip()



    def get_value_from_full_address(self, address=None):
        # Function to extract the last three values
        def extract_last_values(address):
            parts = address.split(', ')
            
            if parts[len(parts)-1] == "Philippines":
                value1, value2, value3, exempt = parts[-4:] if len(parts) >= 4 else (None, None, None, None)
                value4 = ', '.join(parts[:-3]) if len(parts) > 3 else ''
                return value3, value2, value1, value4
            else:
                value1, value2, value3 = parts[-3:] if len(parts) >= 3 else (None, None, None)
                value4 = ', '.join(parts[:-3]) if len(parts) > 3 else ''
                return value3, value2, value1, value4

        if address is not None:
            value1, value2, value3, value4 = extract_last_values(address)
            return {
                "value1": value1, "value2": value2, "value3": value3, "value4": value4
            }
            
        return None
    

    def remove_emojis(self, text):
        emoji_pattern = re.compile(
            "[" 
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"  # other symbols
            u"\U000024C2-\U0001F251" 
            "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)
    

    def clean_strings(self, string):
        # Extracting the list part from the string using regex
        match = re.search(r"\[(.*?)\]", string)

        # If a match is found, process the list
        if match:
            # Extract the content within the brackets
            list_content = match.group(1)
            
            # Convert it into a list of strings
            list_items = re.findall(r"'(.*?)'", list_content)
            
            # Join the list items with a comma and space
            additional_text = ", ".join(list_items)
            
            # Replace the list part with the formatted text
            output = re.sub(r"\[.*?\]", additional_text, string).strip()

            # Print the output
            return output
        return string