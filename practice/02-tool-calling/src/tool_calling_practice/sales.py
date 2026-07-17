import re
from typing import Any

SALES_DATA = {
    ("2026-05", "华东"): 1300000,
    ("2026-06", "华东"): 1250000,
    ("2026-06", "华南"): 980000,
    ("2026-06", "华北"): 860000,
}

SUPPORTED_REGIONS = {"华东", "华南", "华北"}
MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def query_sales(month: str, region: str) -> dict[str, Any]:
    if not MONTH_PATTERN.fullmatch(month):
        return {
            "success": False,
            "error_code": "INVALID_MONTH",
            "message": "month 必须使用 YYYY-MM 格式",
            "retryable": False,
        }

    if region not in SUPPORTED_REGIONS:
        return {
            "success": False,
            "error_code": "INVALID_REGION",
            "message": f"不支持地区：{region}",
            "retryable": False,
        }

    sales = SALES_DATA.get((month, region))
    if sales is None:
        return {
            "success": False,
            "error_code": "NO_DATA",
            "message": f"{month} {region}没有销售数据",
            "retryable": False,
        }

    return {
        "success": True,
        "data": {
            "month": month,
            "region": region,
            "sales": sales,
            "currency": "CNY",
            "unit": "元",
        },
    }
