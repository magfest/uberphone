#!/usr/bin/env python3
from dateutil.parser import parse
import datetime
import requests
import json
import math
import time
import sys
import re

class UberApi:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token

    def do_request(self, method, *params):
        data = {"method": method}
        
        if params:
            data["params"] = params
            
        res = requests.post(
            self.base_url,
            json=data,
            headers={"X-Auth-Token": self.token}
        )

        res.raise_for_status()

        return res.json()["result"]

    def dept_list(self):
        return self.do_request("dept.list")

    def shifts(self, dept_id, start_time=None, end_time=None):
        if start_time and end_time:
            return self.do_request("shifts.lookup", dept_id, start_time, end_time)
        else:
            return self.do_request("shifts.lookup", dept_id)

    def attendee_search(self, query, full=False):
        return self.do_request("attendee.search", query, full)

def numerify(val):
    return re.sub("[^0-9]", "", val)

def shift_ongoing(shift):
    return parse(shift["start_time"]) \
        < datetime.datetime.now() \
        < parse(shift["end_time"])

def ceil_dt(dt):
    # how many secs have passed this hour
    nsecs = dt.minute*60 + dt.second + dt.microsecond*1e-6  
    # number of seconds to next quarter hour mark
    # Non-analytic (brute force is fun) way:  
    #   delta = next(x for x in xrange(0,3601,900) if x>=nsecs) - nsecs
    # analytic way:
    delta = math.ceil(nsecs / 900) * 900 - nsecs
    #time + number of seconds to quarter hour mark.
    return dt + datetime.timedelta(seconds=delta)

class EscalationCalculator:
    def __init__(self, uber_url, uber_token, config):
        self.api = UberApi(uber_url, uber_token)
        self.depts = config

        self._dept_cache = {}
        self._people_cache = {}
        self._shift_cache = {}
        self._shift_expire = datetime.datetime.now()

    def get_dept_id(self, dept_name):
        if not self._dept_cache:
            self._dept_cache.update({v: k for k, v in self.api.dept_list().items()})
            
        return self._dept_cache.get(dept_name, None)

    def get_shifts(self, dept_name):
        dept_id = self.get_dept_id(dept_name)

        if not self._shift_cache or self._shift_expire <= datetime.datetime.now():
            self._shift_expire = ceil_dt(datetime.datetime.now())
            self._shift_cache[dept_name] = [shift for shift in self.api.shifts(dept_id) if shift_ongoing(shift)]

        return self._shift_cache.get(dept_name, None)

    def find_person(self, name):
        if name not in self._people_cache:
            self._people_cache.update({
                p["full_name"]: numerify(p["cellphone"])
                for p in self.api.attendee_search(name)
                if p["full_name"] == name
                and p["cellphone"]
                and (p["staffing"] or "Volunteer" in p["ribbon_labels"])
            })

        return self._people_cache.get(name, None)

    def get_escalation(self, dept_name):
        if dept_name not in self.depts:
            return []

        if self.get_dept_id(dept_name) is None:
            return []

        all_shifts = self.get_shifts(dept_name)

        esc_numbers = []
        for step in self.depts[dept_name].get("escalation", []):
            step_numbers = []
            
            if "phones" in step:
                step_numbers.extend([numerify(n) for n in step["phones"]])

            if "shifts" in step:
                for name in step["shifts"]:
                    jobs = [job for job in all_shifts if name.lower() in job["name"].lower()]
                    if not jobs:
                        print("Warning! No current shifts found matching '{}'".format(name))

                    step_numbers.extend([
                        numerify(shift["attendee"]["cellphone"])
                        for job in jobs
                        for shift in job["shifts"]
                        if shift["attendee"] and shift["attendee"]["cellphone"]
                    ])

            if "people" in step:
                step_numbers.extend([self.find_person(name) for name in step["people"]])

            if step_numbers:
                esc_numbers.append(step_numbers)

        return esc_numbers

    def full_escalation(self):
        return {dept: self.get_escalation(dept) for dept in self.depts}


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "/etc/uberphone.json"
    config = {}
    
    with open(config_path) as f:
        config = json.load(f)

    calc = EscalationCalculator(config["uber"]["base_url"],
                                config["uber"]["token"],
                                config["depts"])

    for dept, escalation in calc.full_escalation().items():
        print("Escalation for department '{}'".format(dept))
        for group in escalation:
            print("*", ', '.join(group))
            print()
