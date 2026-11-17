#!/usr/bin/env python3
import json
import urllib.request
import urllib.error
import sys
import time

def check_endpoint(url, timeout=5):
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "amano-dns-probe/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = int((time.time() - t0) * 1000)
            return True, data, elapsed
    except Exception as e:
        elapsed = int((time.time() - t0) * 1000)
        return False, str(e), elapsed

def main():
    hosts = [
        ("w1", "http://100.113.200.45:19601"),
        ("w2", "http://100.75.169.8:19602"),
        ("w3", "http://100.81.66.86:19603"),
        ("w4", "http://100.82.123.35:19604")
    ]
    
    online = 0
    total = len(hosts)
    views = []
    committed = []
    
    print("=== amano chain & dns probe ===")
    for name, base in hosts:
        ok, res, ms = check_endpoint(f"{base}/health")
        if ok and res.get("ok"):
            online += 1
            v = res.get("view")
            c = res.get("committed-height")
            views.append(v)
            committed.append(c)
            print(f"MEASURE\twitness_{name}_health\tUP\t{ms}ms\tview={v}\tcommitted={c}")
        else:
            print(f"MEASURE\twitness_{name}_health\tDOWN\t{ms}ms\t{res}")
            
    print(f"MEASURE\twitness_online_ratio\t{online}/{total}")
    if online >= 3:
        print("MEASURE\tquorum_status\tMET")
    else:
        print("MEASURE\tquorum_status\tDEGRADED")

    # Check test dns mapping ref
    ok_ref, ref_res, _ = check_endpoint(f"http://100.113.200.45:19601/committed?ref=amano/ping")
    if ok_ref and ref_res.get("ok"):
        print(f"MEASURE\tdns_record_ping\tFOUND\t{ref_res.get('records')} records in store")
    else:
        print(f"MEASURE\tdns_record_ping\tMISSING\t{ref_res}")

if __name__ == "__main__":
    main()
