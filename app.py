from fastapi import FastAPI, HTTPException, Request
from concurrent.futures import ThreadPoolExecutor, TimeoutError, CancelledError
import uvicorn
from pydantic import BaseModel
import random
import time
import configparser
import sys
import traceback
import threading
from api_response import APIResponse
from datetime import datetime, timedelta
from collections import defaultdict
import requests
import json

app = FastAPI()

# Rate limiting configuration
rate_limit_window = timedelta(minutes=1)  # 1 minute window
request_limit = 60  # 60 requests per window
request_counts = defaultdict(lambda: {"count": 0, "reset_time": datetime.now() + rate_limit_window})

class BankInfo(BaseModel):
    account_number: str
    bank_name: str
    account_name: str

def is_rate_limited():
    current_time = datetime.now()
    if request_counts["global"]["reset_time"] <= current_time:
        request_counts["global"]["count"] = 0
        request_counts["global"]["reset_time"] = current_time + rate_limit_window

    if request_counts["global"]["count"] >= request_limit:
        return True
    
    request_counts["global"]["count"] += 1
    return False

@app.post('/check_bank_name', tags=["check_bank_name"])
def check_bank_name(input: BankInfo, request: Request):
    try:
        if is_rate_limited():
            raise HTTPException(status_code=429, detail="Mình set giới hạn 60 request/phút nhé.")

        account_number = input.account_number
        bank_name = input.bank_name
        account_name = input.account_name

        url = "https://check-account-name.onrender.com/check_bank_name"

        payload = json.dumps({
            "account_number": account_number,
            "bank_name": bank_name,
            "account_name": account_name
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print(response.text)
        return APIResponse.json_format(response.json())
    except Exception as e:
        response = str(e)
        print(traceback.format_exc())
        print(sys.exc_info()[2])
        return APIResponse.json_format(response)

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=3000)
