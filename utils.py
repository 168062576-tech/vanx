"""
Shared utilities: validation, escaping, region definitions, agent display formatting.
"""
import re
import hashlib
import random

# ============================================================
# Security helpers
# ============================================================

def validate_world_name(name):
    if not name or not re.match(r'^[a-zA-Z0-9_]+$', name):
        return None
    return name

def safe_limit(val, default=20, maximum=500):
    return max(1, min(val, maximum))

def escape_html(text):
    if not isinstance(text, str):
        return str(text)
    return text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')


# ============================================================
# Region definitions
# ============================================================

REGION_DEFINITIONS = {
    'commercial': {'name': '商业区', 'name_en': 'Commercial', 'icon': '🏢',
        'bounds': {'x1': 30, 'y1': 0, 'x2': 70, 'y2': 40}, 'color': '#4ECDC4'},
    'residential': {'name': '住宅区', 'name_en': 'Residential', 'icon': '🏠',
        'bounds': {'x1': 0, 'y1': 0, 'x2': 30, 'y2': 50}, 'color': '#FF6B6B'},
    'industrial': {'name': '工业区', 'name_en': 'Industrial', 'icon': '🏭',
        'bounds': {'x1': 0, 'y1': 50, 'x2': 40, 'y2': 100}, 'color': '#FFE66D'},
    'education': {'name': '教育区', 'name_en': 'Education', 'icon': '🎓',
        'bounds': {'x1': 70, 'y1': 0, 'x2': 100, 'y2': 35}, 'color': '#95E1D3'},
    'medical': {'name': '医疗区', 'name_en': 'Medical', 'icon': '🏥',
        'bounds': {'x1': 70, 'y1': 35, 'x2': 100, 'y2': 65}, 'color': '#F38181'},
    'suburban': {'name': '郊区', 'name_en': 'Suburbs', 'icon': '🌾',
        'bounds': {'x1': 40, 'y1': 65, 'x2': 100, 'y2': 100}, 'color': '#FCBAD3'},
}

OCCUPATION_REGION_MAP = {
    # 中文
    '农业': 'suburban', '制造业': 'industrial', '服务业': 'commercial',
    '信息技术': 'commercial', '医疗': 'medical', '教育': 'education',
    '金融': 'commercial', '政府': 'commercial', '其他': 'residential',
    # 引擎英文职业 → 区域
    'CEO': 'commercial', 'CTO': 'commercial', 'CFO': 'commercial', 'COO': 'commercial',
    'Engineering Manager': 'commercial', 'Sales Manager': 'commercial',
    'Marketing Manager': 'commercial', 'Operations Manager': 'commercial',
    'Senior Engineer': 'commercial', 'Senior Sales': 'commercial',
    'Senior Marketing': 'commercial', 'Senior Operation': 'commercial',
    'Junior Engineer': 'industrial', 'Junior Sales': 'commercial',
    'Junior Marketing': 'commercial', 'Junior Operation': 'industrial',
    'Engineer': 'commercial', 'Developer': 'commercial', 'Designer': 'commercial',
    'Manager': 'commercial', 'Director': 'commercial', 'Executive': 'commercial',
    'Doctor': 'medical', 'Nurse': 'medical', 'Teacher': 'education', 'Professor': 'education',
    'Farmer': 'suburban', 'Worker': 'industrial', 'Driver': 'industrial',
    'Unemployed': 'residential', 'unemployed': 'residential', 'Retired': 'residential',
}

# 英文职业 → 中文显示名
OCCUPATION_CN_MAP = {
    'CEO': '首席执行官', 'CTO': '首席技术官', 'CFO': '首席财务官', 'COO': '首席运营官',
    'Engineering Manager': '工程经理', 'Sales Manager': '销售经理',
    'Marketing Manager': '市场经理', 'Operations Manager': '运营经理',
    'Senior Engineer': '高级工程师', 'Senior Sales': '高级销售',
    'Senior Marketing': '高级市场', 'Senior Operation': '高级运营',
    'Junior Engineer': '初级工程师', 'Junior Sales': '初级销售',
    'Junior Marketing': '初级市场', 'Junior Operation': '初级运营',
    'Engineer': '工程师', 'Developer': '开发者', 'Designer': '设计师',
    'Manager': '经理', 'Director': '总监', 'Executive': '高管',
    'Doctor': '医生', 'Nurse': '护士', 'Teacher': '教师', 'Professor': '教授',
    'Farmer': '农民', 'Worker': '工人', 'Driver': '司机',
    'Unemployed': '待业', 'unemployed': '待业', 'Retired': '退休',
}

OCCUPATION_COLORS = {
    '农业': '#8B4513', '制造业': '#708090', '服务业': '#FF69B4',
    '信息技术': '#4169E1', '医疗': '#DC143C', '教育': '#228B22',
    '金融': '#DAA520', '政府': '#9932CC', '其他': '#808080'
}

EVENT_TYPE_META = {
    'agent_created': {'label': '出生', 'emoji': '👶', 'cat': 'birth'},
    'agent_died': {'label': '死亡', 'emoji': '💀', 'cat': 'death'},
    'marriage_decision': {'label': '结婚', 'emoji': '🎉', 'cat': 'marriage'},
    'employment_started': {'label': '入职', 'emoji': '💼', 'cat': 'job'},
    'career_change': {'label': '换工作', 'emoji': '🔄', 'cat': 'job'},
    'crime_decision': {'label': '犯罪', 'emoji': '🚨', 'cat': 'crime'},
    'housing_change': {'label': '搬家', 'emoji': '🏠', 'cat': 'house'},
}


def get_region_for_agent(agent):
    occ = agent.get('occupation', '其他')
    return OCCUPATION_REGION_MAP.get(occ, 'residential')


def assign_position_in_region(agent_id, region_key):
    region = REGION_DEFINITIONS.get(region_key, REGION_DEFINITIONS['residential'])
    b = region['bounds']
    seed = int(hashlib.md5(str(agent_id).encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    mx = max(1, (b['x2'] - b['x1']) * 0.05)
    my = max(1, (b['y2'] - b['y1']) * 0.05)
    x = rng.uniform(b['x1'] + mx, b['x2'] - mx)
    y = rng.uniform(b['y1'] + my, b['y2'] - my)
    return round(x, 2), round(y, 2)


NATIONALITIES = ['chinese','japanese','korean','english','german','french','spanish','arabic','indian','russian']
NATIONALITY_CN = {'chinese':'中国','japanese':'日本','korean':'韩国','english':'英国','german':'德国','french':'法国','spanish':'西班牙','arabic':'沙特','indian':'印度','russian':'俄罗斯'}
CONTINENT_MAP = {'chinese':'亚洲','japanese':'亚洲','korean':'亚洲','english':'欧洲','german':'欧洲','french':'欧洲','spanish':'欧洲','arabic':'中东','indian':'亚洲','russian':'欧洲'}


def format_agent_for_display(agent, narrator=None):
    """Convert raw agent dict to display format with region coordinates."""
    agent_id = agent.get('id', 'unknown')
    
    # Occupation: translate English to Chinese display name
    raw_occ = agent.get('occupation', '其他')
    display_occ = OCCUPATION_CN_MAP.get(raw_occ, raw_occ)
    
    # Use raw occupation for region mapping (it knows both CN and EN)
    region_key = get_region_for_agent(agent)
    x, y = assign_position_in_region(agent_id, region_key)
    region_name = REGION_DEFINITIONS.get(region_key, {}).get('name', '住宅区')

    # Name: use narrator with nationality
    name = agent.get('name', '')
    nationality = agent.get('nationality', '')
    if not nationality or nationality in ('未知', 'unknown', ''):
        rng = random.Random(agent_id if isinstance(agent_id, int) else hash(agent_id))
        nationality = rng.choice(NATIONALITIES)
    
    if (not name or name.startswith('Agent-') or name.startswith('CEO')) and narrator:
        try:
            gender = agent.get('gender', 'male')
            name = narrator.generate_name(agent_id, gender, nationality)
        except Exception:
            try:
                name = narrator.generate_name(agent_id, gender)
            except Exception:
                pass
    if not name:
        name = escape_html(agent.get('name', f'Agent-{agent_id}'))

    nat_cn = NATIONALITY_CN.get(nationality, nationality)
    continent = CONTINENT_MAP.get(nationality, '未知')

    return {
        'id': agent_id,
        'name': name,
        'age': agent.get('age', 0),
        'gender': '男' if agent.get('gender') == 'male' else '女' if agent.get('gender') == 'female' else agent.get('gender', '未知'),
        'occupation': display_occ,
        'nationality': nat_cn,
        'continent': continent,
        'income': agent.get('income_monthly', agent.get('income', 0)),
        'skill_level': round(agent.get('skill_level', 1), 1),
        'education': agent.get('education', agent.get('education_level', '未知')),
        'satisfaction': round(agent.get('satisfaction', agent.get('life_satisfaction', 3.0)), 2),
        'status': 'alive' if agent.get('is_alive', True) else 'dead',
        'happiness': agent.get('happiness', 50),
        'health_score': agent.get('health_score', 75),
        'x': x, 'y': y,
        'region': region_name,
    }
