import datetime
from datetime import datetime as nowtime
import requests
import time
import re
from ..tools import ProgramLog , POS_Pancake
import pytz 
import traceback
from ..models import Conversations
from ..utils import get_redis_connection


class WorkerFetcher:
    
    def __init__(self, access_token, page_name, task_id):
        super().__init__()
        self.logger = ProgramLog(f"{page_name} (FETCHER)")
        self.access_token= access_token
        self.page_id = None
        self.page_name = page_name
        self.page_access_token = None
        self.log_file_name = None
        self.shop_id = None
        self.id_it_tag = None
        self.order_it_tag = None
        self.id_incomplete_tag = None
        self.order_incomplete_tag = None
        self.cutoff_time = datetime.datetime.strptime('16:00:00', '%H:%M:%S').time()
        self.sleep_scan = False
        self.kill_process = False
        self.public_sku_name=None
        self.server_ip=None
        self.redis = get_redis_connection()  # Store the Redis connection
        self.task_id = task_id  # Store the task ID


    def run(self):
        try:
            while True:
                try:
                    # self.start_event.emit("Program (fetcher) is now running...")
                    self.processing()
                    break
                except Exception as e:
                    self.logs(text=f"Exception: {e}", type="error")
                    break
            

        except Exception as e:
            self.logs(text=f"Exception: {e}",type="error")
        finally:
            self.logs(text=f"Program (fetcher) has stopped.")




    def processing(self):
        
        iteration_logs = []

        self.get_page_id()
        if self.page_id is None:
            # self.logs(type="error",text="Error: Unable to retrieve page ID. Exiting.")
            return

        self.get_page_settings()
        exported_tag_id = self.get_exported_tag_id()
        encoded_tag_id = self.get_encoded_tag_id()
        # self.logs(text=f"ID of 'EXPORTED' tag: {exported_tag_id}")
        # self.logs(text=f"ID of 'ENCODED' tag: {encoded_tag_id}")
        self.__class_pos_pancake = POS_Pancake(self.shop_id,self.access_token)
        blacklisted_tags = self.__class_pos_pancake.get_blacklist_tags()

        if self.id_it_tag is None or self.order_it_tag is None or self.shop_id is None or self.id_incomplete_tag is None or self.order_incomplete_tag is None:
            # self.logs(text="Error: Unable to retrieve settings. Exiting.")
            return
        
        count_of_new_unread_messages = 0
        self.logs(text=f"Data fetcher is now running..")
        while True:
            print(f"[FETCHER] PAGE: {self.page_name}")
            # Kill when window is closed
            if self.kill_process: 
                return

            if self.redis.get(f"cancel_flag:{self.task_id}") == b"True":  # Check Redis
                self.logs(text=f"Task {self.task_id} was cancelled.", type="info")
                return

            try:
                current_date = datetime.datetime.now(pytz.timezone('Asia/Manila')) #- datetime.timedelta(days=1)
                start_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = current_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                START_DATE = int(start_date.timestamp())
                END_DATE = int(end_date.timestamp())

                self.log_file_name = self.prepare_log_file()

                # self.logs(text="Checking conversations...")
                # self.logs_on_t2(color="black",text=f"New loop checking conversations.........................")
                conversations = self.get_conversations(START_DATE, END_DATE, [self.id_it_tag, self.order_it_tag]) #self.id_incomplete_tag, self.order_incomplete_tag

                # len of conversation with NO INC/EXPORTED/IT/ENCODED tag
                if count_of_new_unread_messages and count_of_new_unread_messages < 50 or True:
                    # unattended_orders = self.get_unattended_orders(exported_tag_id,encoded_tag_id)
                    
                    unattended_orders = self.get_conversation_v2(self.page_access_token,self.page_id,START_DATE,END_DATE,[])  
                    # print(f"got unattended orders > {len(unattended_orders)}")
                    if unattended_orders:       
                        for order in unattended_orders:
                            # Kill when window is closed
                            if self.kill_process: return

                            if self.redis.get(f"cancel_flag:{self.task_id}") == b"True":  # Check Redis
                                self.logs(text=f"Task {self.task_id} was cancelled.", type="info")
                                return
                            if type(order) == dict:
                                conversations.append(order)
                    count_of_new_unread_messages = 0
                    # print("Unattended orders total recovered:", len(unattended_orders))
                
                iteration_logs.clear()
                if conversations:
                    self.logs(text=f"{'-----' * 20}")
                    self.logs(text=f"Fetch orders from Pancake. Total = {len(conversations)}")
                    self.logs(text=f"{'-----' * 20}")
                    for conv_index, conversation in enumerate(conversations):
                        # Kill when window is closed
                        if self.kill_process: return

                        if self.redis.get(f"cancel_flag:{self.task_id}") == b"True":  # Check Redis
                            self.logs(text=f"Task {self.task_id} was cancelled.", type="info")
                            return


                        # self.logs(text=f">>>>>> New Conversation Loop >>>>> Index={conv_index}/{len(conversations)-1} >> CONV ID: {conversation['id']}")
                        #self.logs_on_t2(color="black",text=f">>>>> Index={conv_index}/{len(conversations)-1}")
                        customer = conversation['customers'][0]
                        conversation_id = conversation['id']
                        customer_id = customer['id']

                        latest_order_info = self.get_latest_order_info(conversation_id, customer_id)
                        if latest_order_info:
                            latest_order_tags = latest_order_info.get('tags')

                            if latest_order_tags and (exported_tag_id in latest_order_tags or encoded_tag_id in latest_order_tags):
                                # self.logs(text="Skipping conversation as tags EXPORTED or ENCODED are present.")
                                continue

                            if latest_order_tags and encoded_tag_id in latest_order_tags:
                                # self.logs(text="Skipping conversation as tags ENCODED are present.")
                                continue

                            if latest_order_tags and exported_tag_id in latest_order_tags :
                                # self.logs(text="Skipping conversation as tags EXPORTED are present.")
                                continue
                            
                            if latest_order_tags and self.contains_any(latest_order_tags,blacklisted_tags):
                                continue

                            if conversation['tags'] and (self.id_it_tag in conversation['tags']):
                                # self.logs(text="Skipping conversation as tags 'IT' is present.")
                                continue

                            count_of_new_unread_messages += 1

                            

                            messages = self.get_messages(conversation_id, customer_id)
                            if messages:
                                # self.logs(text=f"Conversation ID: {conversation_id}")
                                # self.logs(text=f"Customer: {customer['name']}")
                                # self.logs(text="Messages:")
                                original_messages = []
                                latest_sku = None

                                try:
                                    for message in messages:
                                        # Kill when window is closed
                                        if self.kill_process: return

                                        if self.redis.get(f"cancel_flag:{self.task_id}") == b"True":  # Check Redis
                                            self.logs(text=f"Task {self.task_id} was cancelled.", type="info")
                                            return
                                        
                                        if 'from' in message and 'id' in message['from']:
                                            if message['from']['id'] == customer['fb_id']:
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
                                                    else:
                                                        pass
                                                        # self.logs(text="Failed to retrieve SKU ID, product ID, variation ID, or quantity.")
                                
                                except Exception as e:
                                    self.logs(text=">> Error occured during loop on messages. Skip for next conversation loop.")
                                    print(f"[FETCHER :: ERROR] >> Error occured during loop on messages. Skip for next conversation loop.")
                                    continue

                                
                                "This is the part where we will save the data to the database"
                                body={
                                    "conversation_id": conversation_id,
                                    "customer_id": customer_id,
                                    "customer_fb_id": customer['fb_id'],
                                    "customer_name": customer['name'],
                                    "chats": " ".join(original_messages),
                                    "address": "",
                                    "tag": "",
                                    "page_name": self.page_name,
                                    "status": "0"
                                }
                                # print(f" Fetcher ===> {body['customer_name']} <=== Fetcher")
                                self.save_to_conversations(body)

                                
                        else:
                            # print("No latest orders")
                            pass


                        
                        # else:
                        #     self.logs(text="Error: Unable to fetch latest order info.")
                            
                        iteration_logs.append("Placeholder log for conversation processing")


            except requests.exceptions.HTTPError as e:
                print(f"[FETCHER :: ERROR] HTTPError: {e}")
                pass

            except Exception as e:
                print(f"[FETCHER :: ERROR] Exception: {e}")
                pass

            finally:
                continue



    def get_page_id(self):
        
        url = f"https://pancake.ph/api/v1/pages?access_token={self.access_token}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                pages = data.get("categorized", {}).get("activated", [])
                for page in pages:
                    if self.kill_process: return

                    if self.redis.get(f"cancel_flag:{self.task_id}") == b"True":  # Check Redis
                        self.logs(text=f"Task {self.task_id} was cancelled.", type="info")
                        return
            
                    if page["name"].lower() == self.page_name.lower():
                        self.page_id = page["id"]  # Set PAGE_ID value
                        self.logs(text=f"Page ID: {self.page_id}")
                        return
                self.logs(text="Page not found.")
            else:
                self.logs(type="error",text=f"Failed to retrieve data. Status code: {response.status_code}")
        except Exception as e:
            self.logs(type="critical",text=f"An error occurred: {e}")

    def contains_any(self, lst, check_list):
        check_set = set(check_list)
        return any(elem in check_set for elem in lst)

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
            hour = datetime.datetime.now(pytz.timezone('Asia/Manila')).hour
            unattended_orders = [dict]
            for end_hour in range(hour):
                if self.kill_process: return

                if self.redis.get(f"cancel_flag:{self.task_id}") == b"True":  # Check Redis
                    self.logs(text=f"Task {self.task_id} was cancelled.", type="info")
                    return
                
                current_date = datetime.datetime.now(pytz.timezone('Asia/Manila'))
                start_date = current_date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
                end_date = current_date.replace(hour=end_hour, minute=59, second=59, microsecond=999999)
                START_DATE = int(start_date.timestamp())
                END_DATE = int(end_date.timestamp())
                conversations = self.get_conversations(START_DATE,END_DATE, [self.id_it_tag, self.order_it_tag, self.id_incomplete_tag, self.order_incomplete_tag])
                if conversations:
                    for conv in conversations:
                        if self.kill_process: return

                        if self.redis.get(f"cancel_flag:{self.task_id}") == b"True":  # Check Redis
                            self.logs(text=f"Task {self.task_id} was cancelled.", type="info")
                            return
                        
                        # if not exported_tag_id in conv['tags'] and not encoded_tag_id in conv['tags'] and not self.id_it_tag in conv['tags']: #and not self.id_incomplete_tag in conv['tags']:
                        if conv not in unattended_orders:
                            # print(f"unattended order - {type(conv)}")
                            unattended_orders.append(conv)
            
            if unattended_orders:
                return unattended_orders
            else:
                return None
        except Exception as e:
            print("EXCEPTION = ", e)


    def get_conversation_v2(self,page_access_token, page_id, START_DATE, END_DATE, tags,last_conversation_id =''):
        try:
            if last_conversation_id:
                new_list = []
                max_retries = 5
                retries = 0
                while retries < max_retries:
                    try:
                        if self.kill_process == True: return []
                        get_conversations_url = f"https://pages.fm/api/public_api/v2/pages/{page_id}/conversations?page_access_token={page_access_token}&page_id={page_id}&type=INBOX&since={START_DATE}&until={END_DATE}&page_number=1&last_conversation_id={last_conversation_id}"
                        response = requests.get(get_conversations_url)
                        if response.status_code == 200:
                            data = response.json()
                            conversations = data.get('conversations', [])
                            if conversations:
                                for conversation in conversations:
                                    if START_DATE < nowtime.fromisoformat(conversation.get("updated_at")).timestamp():
                                        new_list.append(conversation)
                                    else: return new_list
                                last_conversation_id = conversations[-1].get("id","")
                                if len(conversations) != 60: return new_list
                            else:
                                return new_list
                    except requests.exceptions.ConnectionError as e:
                        print(f"Connection error: {e}. Retrying in {2**retries} seconds...")
                        time.sleep(2**retries)
                        retries += 1
            else:
                get_conversations_url = f"https://pages.fm/api/public_api/v2/pages/{page_id}/conversations?page_access_token={page_access_token}&page_id={page_id}&unread_first=true&type=INBOX&since={START_DATE}&until={END_DATE}&page_number=1"
                # print("get_conversations_url >> ",get_conversations_url)
                response = requests.get(get_conversations_url)
                if response.status_code == 200:
                    data = response.json()
                    conversations = data.get('conversations', [])
                    if not conversations:
                        return None
                    return self.get_conversation_v2(page_access_token, page_id, START_DATE, END_DATE, tags,conversations[-1].get("id"))
                return None
        except Exception as e:
            self.logs(text=f"get_conversation_v2 error >> {e} \nTraceback: {traceback.format_exc()}")


    def get_conversations(self, START_DATE, END_DATE,  exceptTags=[]) -> list:
        get_conversations_url = f"https://pancake.ph/api/v1/pages/{self.page_id}/conversations?unread_first=true&type=PHONE,DATE:{START_DATE}+-+{END_DATE},INBOX&mode=OR&tags=%22ALL%22&except_tags={exceptTags}&access_token={self.access_token}&from_platform=web"
        # print("get_conversations_url >> ", get_conversations_url)
        response = requests.get(get_conversations_url)
        if response.status_code == 200:
            data = response.json()
            conversations = data.get('conversations', [])
            if not conversations:
                # self.logs(text="Warning: Status code 200, but no conversations found.")
                # self.logs(text=get_conversations_url)
                pass
            return conversations
        else:
            self.logs(type="error",text=f"Error: {response.status_code}")
            # self.logs(type="error",text=get_conversations_url)
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
                return latest_order
            else:
                return None
        else:
            self.logs(type="error",text=f"Error: {response.status_code}")
            return None

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
        # print(f"get_messages url >>> {url}")
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
                # self.logs(text="Invalid SKU format.")
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
                    # self.logs(text=f"Invalid quantity format for item: {item}")
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

    def prepare_log_file(self):
        current_date = datetime.datetime.now().strftime("%m_%d")
        return f"logs_{self.page_name}_seq_{current_date}.logs"

    def logs(self, type="info", text=""):
        now = nowtime.now().strftime("%m/%d/%y, %H:%M:%S")
        text = " [ " +now + " ] - " +text 
        # if type=="error": self.logger.write_log_error(text)
        # elif type=="critical": self.logger.write_log_critical(text)
        # else: self.logger.write_log_info(text)
        # print(type, text)

    def logs_on_t2(self, type="info", text="", color="black"):
        print(type, text, color)

    def set_program_sleep_5_minutes(self, seconds=300):
        self.sleep_scan = True
       
        # 1 seconds x 300 = 300 seconds = 5 minutes
        for i in range(0, seconds):
            # Kill when window is closed
            if self.kill_process: return

            if self.redis.get(f"cancel_flag:{self.task_id}") == b"True":  # Check Redis
                self.logs(text=f"Task {self.task_id} was cancelled.", type="info")
                return
            

            if not self.sleep_scan: break
            time.sleep(1)
        self.sleep_scan = False



    def save_to_conversations(self, body):
        try:
            duplicate = Conversations.objects.filter(conversation_id=body['conversation_id']).exists()
            if duplicate:
                self.logs(text="Conversation already exists. Skipping...")
                return
            
            conversation = Conversations.objects.create(**body)
            conversation.save()
            self.logs(text="Conversation saved.")
        except Exception as e:
            self.logs(type="error",text=f"Error: {e}")


    def cleanup(self):
        self.kill_process = True
        self.logs(text="Cleaning up resources...")
        