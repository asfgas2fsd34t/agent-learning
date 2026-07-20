from typing import Any


SALES_DATA: dict[tuple[str, str], int] = {
    ("2026-06", "华东"): 1_250_000,
    ("2026-06", "华南"): 980_000,
    ("2026-06", "华北"): 860_000,
}
VALID_REGIONS = {"华东", "华南", "华北"}


def query_sales(month: str, region: str) -> dict[str, Any]:
    if len(month) != 7 or month[4] != "-" or not month.replace("-", "").isdigit():
        return {
            "success": False,
            "error_code": "INVALID_MONTH",
            "message": "月份格式必须是 YYYY-MM",
            "retryable": False,
        }

    if region not in VALID_REGIONS:
        return {
            "success": False,
            "error_code": "UNKNOWN_REGION",
            "message": f"不支持的地区：{region}",
            "retryable": False,
        }

    sales = SALES_DATA.get((month, region))
    if sales is None:
        return {
            "success": False,
            "error_code": "NO_DATA",
            "message": f"{month} {region} 没有销售数据",
            "retryable": False,
        }

    return {
        "success": True,
        "data": {"month": month, "region": region, "sales": sales},
    }
