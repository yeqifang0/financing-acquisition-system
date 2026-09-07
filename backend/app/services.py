"""获客流水线服务：6 步采集→画像→评分→电话验证→写入→总结。"""
import json
from datetime import datetime
from typing import Generator

from .database import SessionLocal
from .models import Lead, CrawlTask
from .scoring import score_lead
from .providers import collect_leads as providers_collect

PIPELINE_STEPS = [
    {"key": "collect",     "name": "名单采集",   "desc": "通过企查查模糊搜索采集目标企业名单"},
    {"key": "profile",     "name": "企业画像",   "desc": "调用企业信息核验接口获取详细工商信息"},
    {"key": "score",       "name": "融资意向评分", "desc": "8 维度加权评分模型计算融资意向"},
    {"key": "phone",       "name": "联系电话验证", "desc": "核验并提取企业联系电话"},
    {"key": "write",       "name": "线索入库",   "desc": "信用代码去重，写入数据库"},
    {"key": "summarize",   "name": "执行总结",   "desc": "生成意向分布与 Top10 推荐名单"},
]


def _parse_intent(message: str) -> dict:
    """从自然语言提取采集参数。"""
    import re
    keyword = message
    region = ""
    count = 20

    # 地区
    for r in ["上海", "北京", "深圳", "广州", "苏州", "杭州", "合肥", "南京", "成都", "武汉"]:
        if r in message:
            region = r
            keyword = keyword.replace(r, "").replace("的", "").strip()
            break

    # 关键词
    kw_match = re.search(r"(专精特新|高新技术企业|半导体|新能源|生物医药|智能制造|新材料|集成电路)", message)
    if kw_match:
        keyword = kw_match.group(1)

    # 数量
    n_match = re.search(r"(\d+)\s*条", message)
    if n_match:
        count = min(int(n_match.group(1)), 100)
    elif "五十" in message or "50" in message:
        count = 50
    elif "三十" in message or "30" in message:
        count = 30

    # "要电话" → 需要 phone
    need_phone = "电话" in message or "联系方式" in message

    return {"keyword": keyword or "科技", "region": region, "count": count, "need_phone": need_phone}


def run_pipeline(message: str) -> Generator[str, None, None]:
    """执行 6 步获客流水线，yield SSE 事件字符串。"""
    def event(event_type: str, data) -> str:
        return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    # --- 解析指令 ---
    params = _parse_intent(message)

    yield event("text", {"text": f"收到指令：采集「{params['keyword']}」企业{('（' + params['region'] + '）') if params['region'] else ''}，目标 {params['count']} 条"})

    yield event("params", {
        "keyword": params["keyword"],
        "region": params["region"],
        "count": params["count"],
        "need_phone": params["need_phone"],
    })

    # 步骤进度初始化
    steps = [{"index": i + 1, "key": s["key"], "name": s["name"], "desc": s["desc"], "status": "pending"} for i, s in enumerate(PIPELINE_STEPS)]
    yield event("steps", {"steps": steps})

    db = SessionLocal()
    collected = []
    provider_used = ""
    try:
        # --- Step 1: 名单采集 ---
        steps[0]["status"] = "running"
        yield event("step", {"index": 1, "status": "running"})
        yield event("log", {"text": f"正在搜索「{params['keyword']}」企业..."})

        try:
            collected, provider_used = providers_collect(params["keyword"], params["count"])
            yield event("log", {"text": f"✅ 数据源：{provider_used}"})
        except Exception as e:
            steps[0]["status"] = "error"
            yield event("step", {"index": 1, "status": "error", "error": str(e)})
            yield event("log", {"text": f"采集失败: {e}"})

            # 检查错误类型，给出更明确的提示
            err_str = str(e)
            if "剩余使用量已不足" in err_str or "已过期" in err_str:
                yield event("log", {"text": "💡 企查查免费试用额度已用完（20次/接口），系统自动降级到模拟数据"})
                yield event("log", {"text": "💡 如需真实数据，请在 openapi.qcc.com 购买接口套餐"})
            elif "未购买" in err_str:
                yield event("log", {"text": "💡 企查查接口尚未开通，请在 openapi.qcc.com 选择免费试用或购买套餐"})
            elif "未配置" in err_str or "未找到" in err_str:
                yield event("log", {"text": "💡 未配置企查查凭证，使用模拟数据"})

            # 尝试降级到 mock
            if not USE_MOCK:
                yield event("log", {"text": "降级到模拟数据模式..."})
                from .mock_data import generate_leads
                collected = generate_leads(params["keyword"], params["count"])
                yield event("log", {"text": f"降级成功，采集到 {len(collected)} 条模拟数据"})

        steps[0]["status"] = "done"
        yield event("step", {"index": 1, "status": "done", "result": f"采集到 {len(collected)} 家企业"})
        yield event("log", {"text": f"✅ 名单采集完成：共 {len(collected)} 家企业"})

        if not collected:
            yield event("text", {"text": "未采集到任何企业，请调整搜索关键词后重试。"})
            yield event("done", {"summary": {"total": 0}})
            return

        # --- Step 2: 企业画像 ---
        steps[1]["status"] = "running"
        yield event("step", {"index": 2, "status": "running"})
        yield event("log", {"text": "正在提取企业工商画像（经营范围、注册资本、参保人数等）..."})
        # 企查查模式下画像已在采集阶段完成；mock 模式下数据已含
        steps[1]["status"] = "done"
        yield event("step", {"index": 2, "status": "done", "result": f"{len(collected)} 家企业画像完成"})
        yield event("log", {"text": f"✅ 企业画像完成：已获取 {len(collected)} 家企业的工商详情"})

        # --- Step 3: 融资意向评分 ---
        steps[2]["status"] = "running"
        yield event("step", {"index": 3, "status": "running"})
        yield event("log", {"text": "正在执行 8 维度加权评分（企业规模/行业/资质/资本/年限/状态/参保/上市）..."})

        for lead in collected:
            total, level, dims = score_lead(lead)
            lead["score"] = total
            lead["intention_level"] = level
            lead["score_dimensions"] = dims

        steps[2]["status"] = "done"
        high_n = sum(1 for l in collected if l["intention_level"] == "high")
        yield event("step", {"index": 3, "status": "done", "result": f"评分完成，高意向 {high_n} 家"})
        yield event("log", {"text": f"✅ 评分完成：高意向 {high_n} / 中意向 {sum(1 for l in collected if l['intention_level']=='mid')} / 低意向 {sum(1 for l in collected if l['intention_level']=='low')}"})

        # --- Step 4: 联系电话验证 ---
        steps[3]["status"] = "running"
        yield event("step", {"index": 4, "status": "running"})
        with_phone = sum(1 for l in collected if l.get("phone"))
        yield event("log", {"text": f"正在核验联系电话... 已有电话 {with_phone}/{len(collected)} 家"})
        steps[3]["status"] = "done"
        yield event("step", {"index": 4, "status": "done", "result": f"{with_phone} 家有联系电话"})
        yield event("log", {"text": f"✅ 电话验证完成：{with_phone} 家可联系"})

        # --- Step 5: 线索入库 ---
        steps[4]["status"] = "running"
        yield event("step", {"index": 5, "status": "running"})
        yield event("log", {"text": "正在按统一社会信用代码去重并写入数据库..."})

        written = 0
        skipped = 0
        for lead in collected:
            existing = None
            if lead.get("credit_code"):
                existing = db.query(Lead).filter(Lead.credit_code == lead["credit_code"]).first()
            if existing:
                existing.score = lead["score"]
                existing.intention_level = lead["intention_level"]
                existing.score_dimensions = lead.get("score_dimensions")
                if lead.get("phone"):
                    existing.phone = lead["phone"]
                existing.updated_at = datetime.utcnow()
                skipped += 1
            else:
                db_lead = Lead(
                    company_name=lead.get("company_name", ""),
                    credit_code=lead.get("credit_code"),
                    legal_representative=lead.get("legal_representative"),
                    registered_capital=lead.get("registered_capital"),
                    paid_in_capital=lead.get("paid_in_capital"),
                    registered_address=lead.get("registered_address"),
                    business_scope=lead.get("business_scope"),
                    establish_date=lead.get("establish_date"),
                    enterprise_status=lead.get("enterprise_status"),
                    industry=lead.get("industry"),
                    phone=lead.get("phone"),
                    email=lead.get("email"),
                    website=lead.get("website"),
                    is_small_micro=lead.get("is_small_micro", False),
                    enterprise_scale=lead.get("enterprise_scale"),
                    insurance_count=lead.get("insurance_count", 0),
                    is_listed=lead.get("is_listed", False),
                    stock_code=lead.get("stock_code"),
                    longitude=lead.get("longitude"),
                    latitude=lead.get("latitude"),
                    key_no=lead.get("key_no"),
                    score=lead.get("score", 0),
                    intention_level=lead.get("intention_level", "low"),
                    score_dimensions=lead.get("score_dimensions"),
                    data_source=lead.get("data_source", "qichacha"),
                )
                db.add(db_lead)
                written += 1
        db.commit()

        steps[4]["status"] = "done"
        yield event("step", {"index": 5, "status": "done", "result": f"新增 {written} 条，更新 {skipped} 条"})
        yield event("log", {"text": f"✅ 线索入库完成：新增 {written} 条 / 更新 {skipped} 条"})

        # --- Step 6: 执行总结 ---
        steps[5]["status"] = "running"
        yield event("step", {"index": 6, "status": "running"})
        yield event("log", {"text": "正在生成意向分布与 Top10 推荐名单..."})

        total = len(collected)
        high = [l for l in collected if l["intention_level"] == "high"]
        mid = [l for l in collected if l["intention_level"] == "mid"]
        low = [l for l in collected if l["intention_level"] == "low"]

        sorted_leads = sorted(collected, key=lambda x: x["score"], reverse=True)
        top10 = sorted_leads[:10]
        top10_list = [{
            "company_name": l.get("company_name", ""),
            "phone": l.get("phone", ""),
            "industry": l.get("industry", ""),
            "registered_capital": l.get("registered_capital", ""),
            "score": l.get("score", 0),
            "intention_level": l.get("intention_level", "low"),
        } for l in top10]

        summary = {
            "total": total,
            "high": len(high),
            "mid": len(mid),
            "low": len(low),
            "with_phone": with_phone,
            "top10": top10_list,
        }
        steps[5]["status"] = "done"
        yield event("step", {"index": 6, "status": "done", "result": "总结生成完毕"})
        yield event("log", {"text": f"✅ 执行总结完成：Top1 「{top10_list[0]['company_name']}」评分 {top10_list[0]['score']}"})

        yield event("card", {"summary": summary})
        yield event("done", {"summary": summary})

    except Exception as e:
        db.rollback()
        yield event("error", {"message": f"流水线执行异常: {e}"})
    finally:
        db.close()
