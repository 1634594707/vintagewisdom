// 领域枚举体系（当前聚焦）
// 4 个主领域 + 二级子类（与后端 AI 分类枚举保持一致）

export interface SubDomain {
  code: string;
  name: string;
  nameEn: string;
}

export interface Domain {
  code: string;
  name: string;
  nameEn: string;
  icon: string;
  subDomains: SubDomain[];
}

// 核心领域定义
export const DOMAINS: Domain[] = [
  {
    code: "HIS",
    name: "历史政治",
    nameEn: "History & Politics",
    icon: "\u{1F3DB}\u{FE0F}",
    subDomains: [
      { code: "HIS-POL", name: "政治制度/权力", nameEn: "Politics" },
      { code: "HIS-WAR", name: "战争/冲突", nameEn: "War" },
      { code: "HIS-DIP", name: "外交/谈判", nameEn: "Diplomacy" },
      { code: "HIS-ECO", name: "经济政策/治理", nameEn: "Economy" },
      { code: "HIS-SOC", name: "社会治理/阶层", nameEn: "Society" },
      { code: "HIS-IDE", name: "思想/意识形态", nameEn: "Ideology" },
    ],
  },
  {
    code: "FIN",
    name: "财务金融",
    nameEn: "Finance",
    icon: "\u{1F4B0}",
    subDomains: [
      { code: "FIN-INV", name: "投资/配置", nameEn: "Investment" },
      { code: "FIN-MKT", name: "交易/投机", nameEn: "Markets" },
      { code: "FIN-RISK", name: "风险管理", nameEn: "Risk" },
      { code: "FIN-DEB", name: "债务/杠杆", nameEn: "Debt" },
      { code: "FIN-INS", name: "保险/保障", nameEn: "Insurance" },
      { code: "FIN-MAC", name: "宏观/政策", nameEn: "Macro" },
    ],
  },
  {
    code: "CAR",
    name: "职业发展",
    nameEn: "Career",
    icon: "\u{1F4BC}",
    subDomains: [
      { code: "CAR-JOB", name: "求职就业", nameEn: "Job Search" },
      { code: "CAR-TRA", name: "职业转型", nameEn: "Transition" },
      { code: "CAR-ADV", name: "晋升发展", nameEn: "Advancement" },
      { code: "CAR-ENT", name: "创业", nameEn: "Entrepreneurship" },
      { code: "CAR-NEG", name: "薪酬谈判", nameEn: "Negotiation" },
      { code: "CAR-BAL", name: "工作生活平衡", nameEn: "Work-Life" },
    ],
  },
  {
    code: "TEC",
    name: "技术工程",
    nameEn: "Technology",
    icon: "\u{1F527}",
    subDomains: [
      { code: "TEC-ARC", name: "架构设计", nameEn: "Architecture" },
      { code: "TEC-CHO", name: "技术选型", nameEn: "Choice" },
      { code: "TEC-REF", name: "重构演进", nameEn: "Refactoring" },
      { code: "TEC-INN", name: "技术创新", nameEn: "Innovation" },
      { code: "TEC-OPS", name: "运维/可靠性", nameEn: "Operations" },
      { code: "TEC-DAT", name: "数据工程/治理", nameEn: "Data" },
    ],
  },
];

// 快速标签
export const QUICK_TAGS = [
  { code: "urgent", name: "紧急", color: "#ef4444" },
  { code: "important", name: "重要", color: "#f59e0b" },
  { code: "irreversible", name: "不可逆", color: "#8b5cf6" },
  { code: "high_emotion", name: "高情绪", color: "#ec4899" },
];

// 特殊标记
export const SPECIAL_MARKS = [
  { code: "X", name: "跨领域", description: "涉及3+领域" },
  { code: "U", name: "未知/新兴", description: "待分类" },
  { code: "P", name: "个人独特", description: "专属标签" },
];

// 交叉领域组合示例
export const CROSS_DOMAINS = [
  { code: "FIN+TEC", name: "金融科技", description: "FinTech创业、量化投资、区块链" },
  { code: "CAR+ENT", name: "内部创业", description: "Intrapreneurship、企业创新" },
  { code: "REL+MGT", name: "领导力关系", description: "向上管理、影响力、团队信任" },
  { code: "HEA+CAR", name: "职业健康", description: "burnout、工作成瘾、退休规划" },
  { code: "EDU+TEC", name: "技术学习", description: "编程教育、技术传播、知识付费" },
  { code: "LIF+FIN", name: "财务自由", description: "FIRE、数字游民、地理套利" },
];

// 获取所有领域代码列表
export function getAllDomainCodes(): string[] {
  const codes: string[] = [];
  for (const domain of DOMAINS) {
    codes.push(domain.code);
    for (const sub of domain.subDomains) {
      codes.push(sub.code);
    }
  }
  return codes;
}

// 根据代码获取领域信息
export function getDomainByCode(code: string): Domain | SubDomain | null {
  for (const domain of DOMAINS) {
    if (domain.code === code) return domain;
    for (const sub of domain.subDomains) {
      if (sub.code === code) return sub;
    }
  }
  return null;
}

// 获取主领域
export function getMainDomain(subCode: string): Domain | null {
  const mainCode = subCode.split("-")[0];
  return DOMAINS.find((d) => d.code === mainCode) || null;
}

// 领域代码映射（用于AI自动分类）
export const DOMAIN_KEYWORDS: Record<string, string[]> = {
  "HIS-POL": ["政变", "选举", "政权", "制度", "党", "改革"],
  "HIS-WAR": ["战争", "战役", "入侵", "军队", "冲突"],
  "HIS-DIP": ["外交", "谈判", "条约", "联盟", "制裁"],
  "HIS-ECO": ["财政", "货币", "通胀", "税", "政策"],
  "HIS-SOC": ["民生", "阶层", "治理", "社会"],
  "HIS-IDE": ["意识形态", "宣传", "思想", "运动"],

  "FIN-INV": ["投资", "股票", "基金", "房产", "理财", "资产配置"],
  "FIN-MKT": ["交易", "投机", "追涨杀跌", "期货", "合约"],
  "FIN-RISK": ["止损", "回撤", "风控", "风险管理"],
  "FIN-DEB": ["债务", "杠杆", "信用", "借贷", "爆仓"],
  "FIN-INS": ["保险", "人寿", "健康险", "保障"],
  "FIN-MAC": ["宏观", "周期", "利率", "政策"],
  "CAR-JOB": ["求职", "面试", "offer", "简历", "跳槽"],
  "CAR-TRA": ["转行", "转型", "跨领域", "职业切换"],
  "CAR-ADV": ["晋升", "升职", "职业发展", "管理岗"],
  "CAR-ENT": ["创业", "创始人", " startup", "融资", "公司"],
  "CAR-NEG": ["谈判", "薪资", "薪酬", "福利", "股权"],
  "CAR-BAL": ["work life balance", "工作生活", "burnout", "加班"],
  "TEC-ARC": ["架构", "系统设计", "技术架构", "微服务"],
  "TEC-CHO": ["技术选型", "框架", "语言", "工具选择"],
  "TEC-REF": ["重构", "代码质量", "技术债务", "现代化"],
  "TEC-INN": ["创新", "研发", "新技术", "实验"],
  "TEC-OPS": ["运维", "可靠性", "性能", "安全", "DevOps"],
  "TEC-DAT": ["数据", "指标", "口径", "数仓", "治理"],
};

// 简单的关键词匹配自动分类
export function autoClassifyDomain(text: string): { domain: string; confidence: number }[] {
  const results: { domain: string; confidence: number }[] = [];
  const lowerText = text.toLowerCase();

  for (const [domainCode, keywords] of Object.entries(DOMAIN_KEYWORDS)) {
    let matchCount = 0;
    for (const keyword of keywords) {
      if (lowerText.includes(keyword.toLowerCase())) {
        matchCount++;
      }
    }
    if (matchCount > 0) {
      const confidence = Math.min(matchCount / keywords.length * 2, 1);
      results.push({ domain: domainCode, confidence });
    }
  }

  return results.sort((a, b) => b.confidence - a.confidence).slice(0, 3);
}
