"""模拟数据采集层（降级方案：无企查查凭证时使用）。"""
import random

COMPANY_PREFIXES = [
    "华芯", "中科", "聚能", "拓微", "光启", "量子", "智造", "凌云",
    "创远", "亿华", "盛合", "锐进", "德邦", "瑞泰", "恒泰", "新材",
    "天工", "精工", "启明", "鸿远", "致远", "汇通", "安达", "嘉合",
    "鼎立", "同辉", "长盛", "万方", "泰克", "联众", "沃德", "普泰",
    "海纳", "正大", "金辉", "科创", "博远", "华信", "恒辉", "中天",
    "新维", "融智", "朗星", "迈拓", "云图", "极光", "三友", "绿能",
    "领航", "远景",
]
COMPANY_SUFFIXES = [
    "微电子", "半导体", "新材料", "智能科技", "新能源", "信息技术",
    "精密机械", "电子科技", "自动化", "生物科技", "环保科技", "光电",
]
INDUSTRIES = [
    "半导体集成电路", "新能源电池", "人工智能", "生物医药", "高端装备制造",
    "新材料", "工业互联网", "智能终端", "电子元器件", "环保设备",
]
REGIONS = ["上海", "北京", "深圳", "苏州", "杭州", "合肥", "南京", "成都"]
STATUSES = ["存续", "存续", "存续", "在营", "在营", "存续"]
SCALES = ["大型", "中型", "中型", "小型", "小型", "微型"]


def generate_leads(keyword: str, count: int = 50) -> list[dict]:
    """生成模拟线索数据（带评分信号）。"""
    random.seed(hash(keyword) % 2**31)
    leads = []
    used_names = set()
    for i in range(count):
        while True:
            prefix = random.choice(COMPANY_PREFIXES)
            suffix = random.choice(COMPANY_SUFFIXES)
            name = f"{prefix}{suffix}"
            if name not in used_names:
                used_names.add(name)
                break
        full_name = f"{name}有限公司"
        region = random.choice(REGIONS)
        cap = random.choice([100, 200, 500, 1000, 2000, 5000, 10000])
        years = random.randint(1, 15)
        ins = random.choice([5, 20, 50, 80, 150, 300, 800])

        lead = {
            "company_name": full_name,
            "credit_code": f"91310{random.randint(1000000000, 9999999999)}",
            "legal_representative": random.choice(["张明", "李华", "王强", "陈伟", "刘洋", "赵磊"]),
            "registered_capital": f"{cap}万人民币",
            "paid_in_capital": f"{int(cap * random.uniform(0.3, 0.9))}万人民币",
            "registered_address": f"{region}市{random.choice(['浦东', '南山', '海淀', '园区'])}路{random.randint(1,999)}号",
            "business_scope": f"{random.choice(['半导体芯片设计', '锂电池研发', '人工智能算法', '医疗器械生产', '精密机械加工'])}；{random.choice(['技术开发', '技术服务', '技术咨询', '技术推广'])}",
            "establish_date": f"{2026 - years}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "enterprise_status": random.choice(STATUSES),
            "industry": random.choice(INDUSTRIES),
            "phone": f"021-6{random.randint(10000000,99999999)}" if random.random() > 0.3 else "",
            "email": f"contact@{prefix.lower()}.cn" if random.random() > 0.5 else "",
            "website": f"www.{prefix.lower()}-tech.cn" if random.random() > 0.6 else "",
            "is_small_micro": cap < 500,
            "enterprise_scale": random.choice(SCALES),
            "insurance_count": ins,
            "is_listed": random.random() < 0.08,
            "stock_code": f"6{random.randint(10000,99999)}" if random.random() < 0.08 else "",
            "longitude": "",
            "latitude": "",
            "key_no": f"k{random.randint(100000,999999)}",
            "data_source": "mock",
        }
        leads.append(lead)
    return leads
