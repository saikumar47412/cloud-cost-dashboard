"""
Cloud Cost Fetcher
Run this manually to fetch latest costs and save to data.json
"""

import boto3
import json
import datetime
from config import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_ACCOUNT_NAME,
    AWS_ORG_ACCESS_KEY_ID, AWS_ORG_SECRET_ACCESS_KEY, AWS_ORG_REGION,
)

def get_mtd_range():
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    return today.replace(day=1).strftime("%Y-%m-%d"), tomorrow.strftime("%Y-%m-%d")

def get_last7_range():
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    return (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d"), tomorrow.strftime("%Y-%m-%d")

def fetch_cost_by_service(access_key, secret_key, region, start, end):
    client = boto3.client("ce", region_name=region,
        aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    response = client.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end},
        Granularity="MONTHLY", Metrics=["BlendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    total, breakdown = 0.0, {}
    for result in response["ResultsByTime"]:
        for group in result["Groups"]:
            amt = float(group["Metrics"]["BlendedCost"]["Amount"])
            if amt > 0.01:
                breakdown[group["Keys"][0]] = round(amt, 2)
                total += amt
    return round(total, 2), breakdown

def fetch_org_accounts(start, end):
    client = boto3.client("ce", region_name=AWS_ORG_REGION,
        aws_access_key_id=AWS_ORG_ACCESS_KEY_ID, aws_secret_access_key=AWS_ORG_SECRET_ACCESS_KEY)
    response = client.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end},
        Granularity="MONTHLY", Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}],
    )
    # Get account names
    org_client = boto3.client("organizations", region_name=AWS_ORG_REGION,
        aws_access_key_id=AWS_ORG_ACCESS_KEY_ID, aws_secret_access_key=AWS_ORG_SECRET_ACCESS_KEY)
    account_names = {}
    try:
        for page in org_client.get_paginator("list_accounts").paginate():
            for a in page["Accounts"]:
                account_names[a["Id"]] = a["Name"]
    except: pass

    total, accounts = 0.0, []
    for result in response["ResultsByTime"]:
        for group in result["Groups"]:
            amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
            if amt > 0.01:
                acct_id = group["Keys"][0]
                accounts.append({"id": acct_id, "name": account_names.get(acct_id, "Unknown"), "cost": round(amt, 2)})
                total += amt
    accounts.sort(key=lambda x: x["cost"], reverse=True)
    return round(total, 2), accounts

def main():
    now = datetime.datetime.now().strftime("%d-%b-%Y %I:%M %p IST")
    mtd_s, mtd_e = get_mtd_range()
    l7_s,  l7_e  = get_last7_range()

    print("📊 Fetching costs...")
    data = {"last_updated": now, "mtd": {}, "last7": {}}

    # AWS Normal
    print("  🟠 AWS Normal account...")
    n_mtd, n_mtd_bd = fetch_cost_by_service(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, mtd_s, mtd_e)
    n_l7,  n_l7_bd  = fetch_cost_by_service(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, l7_s,  l7_e)

    # AWS Org
    print("  🏢 AWS Org accounts...")
    o_mtd, o_mtd_accts = fetch_org_accounts(mtd_s, mtd_e)
    o_l7,  o_l7_accts  = fetch_org_accounts(l7_s,  l7_e)

    # TODO: Add Azure and GCP here when ready
    azure_mtd = 0.0
    azure_l7  = 0.0
    gcp_mtd   = 0.0
    gcp_l7    = 0.0

    data["mtd"] = {
        "aws_normal_total": n_mtd, "aws_normal_services": n_mtd_bd,
        "aws_org_total": o_mtd,    "aws_org_accounts": o_mtd_accts,
        "azure_total": azure_mtd,  "azure_subscriptions": {},
        "gcp_total": gcp_mtd,
    }
    data["last7"] = {
        "aws_normal_total": n_l7,  "aws_normal_services": n_l7_bd,
        "aws_org_total": o_l7,     "aws_org_accounts": o_l7_accts,
        "azure_total": azure_l7,   "azure_subscriptions": {},
        "gcp_total": gcp_l7,
    }

    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n✅ data.json saved! Last updated: {now}")
    print(f"   AWS Normal MTD: ${n_mtd:,.2f}")
    print(f"   AWS Org MTD:    ${o_mtd:,.2f}")
    print(f"   Linked accounts: {len(o_mtd_accts)}")

if __name__ == "__main__":
    main()
