"""8维度融资意向评分模型。

维度与权重：
  1. 企业规模       15%
  2. 行业属性       15%
  3. 资质认证       20%
  4. 注册资本       10%
  5. 经营年限       10%
  6. 企业状态       10%
  7. 参保人数       10%
  8. 上市信息       10%
"""
from datetime import datetime
from typing import Optional

DIMENSIONS = [
    {"key": "scale",         "name": "企业规模", "weight": 15},
    {"key": "industry",      "name": "行业属性", "weight": 15},
    {"key": "qualification", "name": "资质认证", "weight": 20},
    {"key": "capital",       "name": "注册资本", "weight": 10},
    {"key": "years",         "name": "经营年限", "weight": 10},
    {"key": "status",        "name": "企业状态", "weight": 10},
    {"key": "insurance",     "name": "参保人数", "weight": 10},
    {"key": "listing",       "name": "上市信息", "weight": 10},
]


def _parse_capital(capital_str: str) -> float:
    """从注册资本字符串提取万元数值。"""
    if not capital_str:
        return 0.0
    s = capital_str.replace(",", "").replace("，", "")
    val = 0.0
    try:
        if "亿" in s:
            num = float(s.replace("万", "").replace("亿", "").replace("人民币", "").strip())
            val = num * 10000
        elif "万" in s:
            num = float(s.replace("万", "").replace("人民币", "").strip())
            val = num
        else:
            num_str = "".join(c for c in s if c.isdigit() or c == ".")
            val = float(num_str) if num_str else 0.0
    except (ValueError, AttributeError):
        pass
    return val


def _score_scale(scale: Optional[str]) -> int:
    if not scale:
        return 55
    s = scale.strip()
    if "大型" in s:
        return 95
    if "中型" in s:
        return 80
    if "小型" in s:
        return 65
    if "微型" in s:
        return 45
    return 55


def _score_industry(scope: str, industry: str) -> int:
    text = f"{scope or ''} {industry or ''}"
    hi_kw = ["科技", "半导体", "芯片", "微电子", "新能源", "智能", "人工智能", "生物", "医药", "高端制造", "专精特新"]
    mid_kw = ["电子", "机械", "自动化", "材料", "环保", "软件", "数据", "通信", "航空"]
    for kw in hi_kw:
        if kw in text:
            return 92
    for kw in mid_kw:
        if kw in text:
            return 78
    return 55


def _score_qualification(scope: str, name: str) -> int:
    text = f"{scope or ''} {name or ''}"
    if "专精特新" in text or "小巨人" in text:
        return 96
    if "高新技术" in text or "高新" in text:
        return 88
    if "科技" in text:
        return 72
    return 50


def _score_capital(capital_str: str) -> int:
    wan = _parse_capital(capital_str)
    if wan >= 10000:
        return 92
    if wan >= 5000:
        return 82
    if wan >= 1000:
        return 72
    if wan >= 100:
        return 60
    return 50


def _score_years(establish_date: str) -> int:
    if not establish_date:
        return 55
    try:
        year_str = establish_date[:4]
        year = int(year_str)
        now_year = datetime.now().year
        years = now_year - year
        if years >= 10:
            return 92
        if years >= 5:
            return 80
        if years >= 2:
            return 70
        return 55
    except (ValueError, IndexError):
        return 55


def _score_status(status: str) -> int:
    if not status:
        return 55
    if "存续" in status or "在营" in status or "开业" in status:
        return 92
    if "迁出" in status or "歇业" in status:
        return 40
    if "注销" in status or "吊销" in status:
        return 10
    return 55


def _score_insurance(count: int) -> int:
    if not count or count <= 0:
        return 50
    if count >= 500:
        return 92
    if count >= 100:
        return 82
    if count >= 50:
        return 72
    if count >= 10:
        return 62
    return 52


def _score_listing(is_listed: bool) -> int:
    return 92 if is_listed else 60


def score_lead(lead_data: dict) -> tuple[float, str, dict]:
    """对单条线索进行8维度评分，返回 (总分, 意向等级, 明细)。"""
    dims = {}

    sc = _score_scale(lead_data.get("enterprise_scale"))
    dims["scale"] = {"name": "企业规模", "score": sc, "weight": 15, "weighted": round(sc * 0.15, 1)}

    ind = _score_industry(lead_data.get("business_scope", ""), lead_data.get("industry", ""))
    dims["industry"] = {"name": "行业属性", "score": ind, "weight": 15, "weighted": round(ind * 0.15, 1)}

    qual = _score_qualification(lead_data.get("business_scope", ""), lead_data.get("company_name", ""))
    dims["qualification"] = {"name": "资质认证", "score": qual, "weight": 20, "weighted": round(qual * 0.20, 1)}

    cap = _score_capital(lead_data.get("registered_capital", ""))
    dims["capital"] = {"name": "注册资本", "score": cap, "weight": 10, "weighted": round(cap * 0.10, 1)}

    yrs = _score_years(lead_data.get("establish_date", ""))
    dims["years"] = {"name": "经营年限", "score": yrs, "weight": 10, "weighted": round(yrs * 0.10, 1)}

    st = _score_status(lead_data.get("enterprise_status", ""))
    dims["status"] = {"name": "企业状态", "score": st, "weight": 10, "weighted": round(st * 0.10, 1)}

    ins = _score_insurance(lead_data.get("insurance_count", 0))
    dims["insurance"] = {"name": "参保人数", "score": ins, "weight": 10, "weighted": round(ins * 0.10, 1)}

    lis = _score_listing(lead_data.get("is_listed", False))
    dims["listing"] = {"name": "上市信息", "score": lis, "weight": 10, "weighted": round(lis * 0.10, 1)}

    total = round(sum(d["weighted"] for d in dims.values()), 1)

    if total >= 80:
        level = "high"
    elif total >= 60:
        level = "mid"
    else:
        level = "low"

    return total, level, dims
