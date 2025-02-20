import requests
from datetime import datetime
import json

class POS_Pancake:

    def __init__(self,shop_id : str,access_token : str) -> None:
        
        self.shop_id = shop_id
        self.access_token = access_token
        
    def check_encoded_exported_tag_in_pos(self,order_url,fb_id : str) -> bool:
        
        pos_tags = self.get_pos_tags()
        encoded_tag_id = pos_tags[-2]
        exported_tag_id = pos_tags[-1]
        blacklist_tags = self.get_blacklist_tags()
        inc_tags = self.get_inc_tags()
        response = requests.get(order_url)
        data = response.json()
        data = data.get("data")
        
        pos_conversation_id = data.get("conversation_id", "")
        pos_customer_tags = data.get("tags")
        if fb_id == pos_conversation_id:
            
            if exported_tag_id in pos_customer_tags or encoded_tag_id in pos_customer_tags:
                return True
            
            elif self.contains_any(blacklist_tags,pos_customer_tags):
                return True
            
            elif self.contains_any(pos_customer_tags,inc_tags) and not self.contains_all(pos_customer_tags,inc_tags):
                return True
                
        return False
    
    def contains_any(self, lst, check_list):
        check_set = set(check_list)
        return any(elem in check_set for elem in lst)

    def contains_all(self, lst, check_list):
        check_set = set(check_list)
        return all(elem in check_set for elem in lst)
    
    def get_inc_tags(self) -> list:
        try:
            url = f"https://pos.pages.fm/api/v1/shops/{self.shop_id}/orders/tags?access_token={self.access_token}"    
            response = requests.get(url)
            data = response.json().get("data")
            list_of_tags = []
            
            for tag_data in data:
                blacklisted_tag  = None
                match tag_data.get("name"):
                    case "INC NO BRGY":
                        blacklisted_tag = tag_data.get("id")
                    case "INC NO PUROK/LM":    
                        blacklisted_tag = tag_data.get("id")
                    case "INC NO PROVINCE":    
                        blacklisted_tag = tag_data.get("id")
                    case "INC NO CITY":    
                        blacklisted_tag = tag_data.get("id")
                    case "INC NAME":    
                        blacklisted_tag = tag_data.get("id")
                if blacklisted_tag:
                    list_of_tags.append(blacklisted_tag)
            return list_of_tags
        except Exception as e:
            print("get_pos_tags error >> ",e)
            return []

    def get_pos_tags(self) -> tuple:
        
        try:
            url = f"https://pos.pages.fm/api/v1/shops/{self.shop_id}/orders/tags?access_token={self.access_token}"    
            response = requests.get(url)
            data = response.json().get("data")
            inc_city , inc_province, inc_barangay ,inc_street, cc_changed_mind , encoded , exported = None,None,None,None,None,None,None
            for tag_data in data:
                match tag_data.get("name"):
                    case "INC NO CITY":
                        inc_city = tag_data.get("id")
                    case "INC NO PROVINCE":    
                        inc_province = tag_data.get("id")
                    case "INC NO BRGY":    
                        inc_barangay = tag_data.get("id")
                    case "INC NO PUROK/LM":    
                        inc_street = tag_data.get("id")
                    case "CC CHANGED MIND":    
                        cc_changed_mind = tag_data.get("id")
                    case "ENCODED":    
                        encoded = tag_data.get("id")
                    case "EXPORTED":    
                        exported = tag_data.get("id")

            return inc_city , inc_province, inc_barangay , inc_street, cc_changed_mind , encoded , exported
        except Exception as e:
            print("get_pos_tags error >> ",e)
            return None,None,None,None,None,None,None
    
    def get_blacklist_tags(self) -> list:
        
        try:
            url = f"https://pos.pages.fm/api/v1/shops/{self.shop_id}/orders/tags?access_token={self.access_token}"    
            response = requests.get(url)
            data = response.json().get("data")
            list_of_tags = []
            for tag_data in data:
                blacklisted_tag = None
                match tag_data.get("name"):
                    case "INC NO CITY":
                        blacklisted_tag = tag_data.get("id")
                    case "CC CHANGED MIND":    
                        blacklisted_tag = tag_data.get("id")
                    case "MULTIPLE TICKET":    
                        blacklisted_tag = tag_data.get("id")
                    case "CC RELOCATION":    
                        blacklisted_tag = tag_data.get("id")
                    case "CC AUTOMATION":    
                        blacklisted_tag = tag_data.get("id")
                    case "CC BUDGET CONCERN":    
                        blacklisted_tag = tag_data.get("id")
                    case "CC Trippings":    
                        blacklisted_tag = tag_data.get("id")
                if blacklisted_tag:
                    list_of_tags.append(blacklisted_tag)
            return list_of_tags
        except Exception as e:
            print("get_pos_tags error >> ",e)
            return []

    def update_pos_tag(self, tagged_as: list[int] = [],send_order_url:str = "") -> None:
        "Used to update pos tags"
        try:
            tag_data = {
                "tags" : tagged_as
            }

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + self.access_token
            }
            
            requests.put(url=send_order_url, data=json.dumps(tag_data), headers=headers)
            # print(f"tag data > {tag_data}")
            # print("send_order_url: ",send_order_url)

        except Exception as e:
            print("update_pos_tag error >> ",e)
    
    def specific_inc(self,result,inc_province,inc_city,inc_barangay,inc_street):

        to_tag = []
        if result.get("INC_Province",False) == True:
            to_tag.append(inc_province)
        if result.get("INC_City",False) == True:
            to_tag.append(inc_city)
        if result.get("INC_Barangay",False) == True:
            to_tag.append(inc_barangay)
        if result.get("INC_Street",False) == True:
            to_tag.append(inc_street)

        return to_tag

    def send_order_to_pos(self, url, json_response, sku_id, product_ids, variation_ids, quantities,tags:list):
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
            "tags" : tags
        }

        #log_to_ui(f"Payload: {json.dumps(payload, indent=2)}")

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.access_token
        }
        
        response = requests.put(url, headers=headers, data=json.dumps(payload))
        return response.status_code

if __name__ == "__main__":


    shop_id = 1720001288
    access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1aWQiOiIzZDc4NjZiNS01ZDQxLTQ5YWMtOThjNS1jNTc1NzVhYjVhMTkiLCJzZXNzaW9uX2lkIjoiRk9nRXR0cGN6ZE13TlhLeWg0SlRIYnRDNmVVbW04WVJnMmZWQmZoZDk4YyIsIm5hbWUiOiJFdmFuZ2VsaW5lIEFyY2FuZ2VsZXMiLCJsb2dpbl9zZXNzaW9uIjpudWxsLCJpbmZvIjp7Im9zIjpudWxsLCJkZXZpY2VfdHlwZSI6MywiY2xpZW50X2lwIjoiMTM2LjE1OC40OS4yMDUiLCJicm93c2VyIjoxfSwiaWF0IjoxNzM2MTkzNTg5LCJmYl9uYW1lIjoiRXZhbmdlbGluZSBBcmNhbmdlbGVzIiwiZmJfaWQiOiIxMjIxMTg1NTM5NzYxODI1MzQiLCJleHAiOjE3NDM5Njk1ODksImFwcGxpY2F0aW9uIjoxfQ.OHLnYuOtt1wHkKIZTJtObob-hq6nZ6CY9yQR8Zf_yFI"
    customer = "Cañete Jeeson"
    __class_pos_pancake = POS_Pancake(shop_id,access_token)
    pos_inc_city , pos_inc_province, pos_inc_barangay , pos_inc_street ,pos_cc_changed_mind , pos_encoded = __class_pos_pancake.get_pos_tags()[0:6]
    print(__class_pos_pancake.get_pos_tags()[0:6])



    "Jessie Espares"
    shop_id = 1720001289
    order_id = 180150466253730
    
